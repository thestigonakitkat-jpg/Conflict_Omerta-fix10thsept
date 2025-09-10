import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import uuid
from pathlib import Path
import bleach

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, validator

# Import our real-world security engine
from security_engine import security_engine, rate_limit_middleware, brute_force_protection
from pin_security import router as pin_router
from livekit_manager import livekit_manager
from admin_system import admin_system, AdminAuthRequest, MultiSigInitRequest, MultiSigSignRequest
from graphite_defense import router as graphite_router
from file_sharing import router as file_sharing_router
from voice_messages import router as voice_messages_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Input sanitization function
def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize and validate input text"""
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Invalid input: text must be a non-empty string")
    
    # Length check
    if len(text) > max_length:
        raise HTTPException(status_code=400, detail=f"Input too long: maximum {max_length} characters")
    
    # Enhanced dangerous patterns detection - be more specific to avoid false positives
    dangerous_patterns = [
        '<script', '</script', 'javascript:', 'onload=', 'onerror=', 'eval(', 'document.',
        'drop table', 'delete from', 'insert into', 'update set', 'union select',
        'exec(', 'execute(', 'xp_', 'sp_', '../', '..\\', '/etc/passwd', 'drop table devices'
    ]
    
    # SQL injection specific patterns (more precise)
    sql_patterns = [';--', '; --', '/*', '*/', '; drop table']
    
    text_lower = text.lower()
    
    # Check for dangerous patterns
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            raise HTTPException(status_code=400, detail="Invalid input: potentially dangerous content detected")
    
    # Check for SQL injection patterns (but allow legitimate -- in PGP messages)
    for pattern in sql_patterns:
        if pattern in text_lower:
            # Allow if it's part of a PGP message structure
            if not ('-----begin' in text_lower and '-----end' in text_lower):
                raise HTTPException(status_code=400, detail="Invalid input: potentially dangerous content detected")
    
    # Basic HTML escape for non-encrypted content (if it looks like HTML)
    if '<' in text and '>' in text and not ('-----begin' in text_lower and '-----end' in text_lower):
        text = bleach.clean(text, tags=[], attributes=[], strip=True)
    
    return text.strip()

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Add comprehensive security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "cross-origin"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
            
        return response

# MongoDB connection (used for non-ephemeral tasks). Do NOT store notes/attachments/envelopes here.
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Custom key function to get real client IP behind proxy/ingress
def get_client_ip(request: Request):
    """Get real client IP from headers when behind proxy/ingress"""
    # Try X-Forwarded-For first (most common)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Try X-Real-IP (used by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to remote address
    return get_remote_address(request)

# Initialize rate limiter with custom key function for proxy/ingress environments
limiter = Limiter(key_func=get_client_ip)

# Create the main app
app = FastAPI(title="OMERTA Secure API", version="2.0.0")

# CRITICAL: Add limiter to app state BEFORE adding middleware
app.state.limiter = limiter

# Add exception handler for rate limiting (use default handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure for production
app.add_middleware(SecurityHeadersMiddleware)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ---------------------------
# Models
# ---------------------------
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Secure Note (RAM-only, OMERTÀ-Vanish-style)
MAX_TTL_SECONDS = 7 * 24 * 60 * 60  # up to one week
MIN_READ_LIMIT = 1
MAX_READ_LIMIT = 1  # CRITICAL: Always 1-time read only, link purged after single read

class NoteCreate(BaseModel):
    ciphertext: str  # base64 or opaque string, server does not inspect
    meta: Optional[Dict] = None
    ttl_seconds: int = Field(..., gt=0, le=MAX_TTL_SECONDS)
    read_limit: int = Field(1, ge=MIN_READ_LIMIT, le=MAX_READ_LIMIT)

    @validator('ciphertext')
    def non_empty_cipher(cls, v: str):
        if not v or not isinstance(v, str):
            raise ValueError("ciphertext must be a non-empty string")
        return v

class NoteCreateResponse(BaseModel):
    id: str
    expires_at: datetime
    views_left: int

class NoteReadResponse(BaseModel):
    id: str
    ciphertext: str
    meta: Optional[Dict] = None
    views_left: int
    expires_at: datetime

# Messaging envelopes (RAM-only, delete-on-delivery)
UNDLV_TTL_SECONDS = 48 * 60 * 60

class EnvelopeSend(BaseModel):
    to_oid: str
    from_oid: str
    ciphertext: str  # opaque string, client handles E2EE
    ts: Optional[datetime] = None

class Envelope(BaseModel):
    id: str
    to_oid: str
    from_oid: str
    ciphertext: str
    ts: datetime
    expires_at: datetime

class EnvelopePollResponse(BaseModel):
    messages: List[Dict]

# LiveKit Video Calling Models
class LiveKitTokenRequest(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=100)
    participant_name: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict] = None
    ttl_hours: int = Field(4, ge=1, le=24)
    
    @validator('room_name')
    def validate_room_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Room name must contain only alphanumeric characters, hyphens, and underscores")
        return v

class LiveKitTokenResponse(BaseModel):
    token: str
    ws_url: str
    session_id: str
    room_name: str
    participant_identity: str
    participant_name: str
    expires_at: str
    server_info: Dict

class LiveKitRoomCreate(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=100)
    max_participants: int = Field(4, ge=2, le=10)
    is_private: bool = Field(False)
    requires_approval: bool = Field(False)
    voice_scrambler_enabled: bool = Field(True)
    face_blur_enabled: bool = Field(True)
    recording_enabled: bool = Field(False)
    
    @validator('room_name')
    def validate_room_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Room name must contain only alphanumeric characters, hyphens, and underscores")
        return v

class LiveKitRoomInfo(BaseModel):
    room_name: str
    created_at: str
    participant_count: int
    max_participants: int
    is_private: bool
    requires_approval: bool

class LiveKitSessionEnd(BaseModel):
    session_id: str

# ---------------------------
# RAM-only stores and housekeeping
# ---------------------------
class RamNote:
    def __init__(self, note_id: str, ciphertext: str, meta: Optional[Dict], read_limit: int, ttl_seconds: int):
        self.id = note_id
        self.ciphertext = ciphertext
        self.meta = meta
        self.read_limit = read_limit
        self.views = 0
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    @property
    def views_left(self) -> int:
        return max(self.read_limit - self.views, 0)

    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

# In-memory dict: id -> RamNote
NOTES_STORE: Dict[str, RamNote] = {}

# Envelopes by recipient OID
ENVELOPES: Dict[str, List[Envelope]] = {}

# WebSocket subscribers per OID
SUBS: Dict[str, List[WebSocket]] = {}

_cleanup_stop = asyncio.Event()

async def cleanup_notes_loop():
    try:
        while not _cleanup_stop.is_set():
            # Sweep notes
            to_delete = []
            for k, v in list(NOTES_STORE.items()):
                if v.expired() or v.views_left <= 0:
                    to_delete.append(k)
            for k in to_delete:
                NOTES_STORE.pop(k, None)

            # Sweep envelopes by TTL
            now = datetime.now(timezone.utc)
            for oid, lst in list(ENVELOPES.items()):
                new_lst = [e for e in lst if e.expires_at > now]
                ENVELOPES[oid] = new_lst
            await asyncio.sleep(30)
    except Exception as e:
        logger.exception("cleanup_notes_loop error: %s", e)

# ---------------------------
# Routes
# ---------------------------
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Secure Notes endpoints (RAM-only) with REAL-WORLD security
@api_router.post("/notes", response_model=NoteCreateResponse)
async def create_note(request: Request, payload: NoteCreate):
    # REAL-WORLD rate limiting that works behind proxies
    await rate_limit_middleware(request, "notes_create")
    
    # Sanitize input
    sanitized_ciphertext = sanitize_input(payload.ciphertext, max_length=50000)  # Allow larger encrypted content
    
    # CRITICAL: Enforce 1-time read only policy
    if payload.read_limit != 1:
        raise HTTPException(status_code=400, detail="Read limit must be 1 (one-time read only)")
    
    note_id = str(uuid.uuid4())
    note = RamNote(
        note_id=note_id,
        ciphertext=sanitized_ciphertext,
        meta=payload.meta,
        read_limit=1,  # CRITICAL: Always 1-time read only, link purged after single read
        ttl_seconds=payload.ttl_seconds,
    )
    NOTES_STORE[note_id] = note
    logger.info(f"Created 1-TIME READ secure note {note_id}, expires at {note.expires_at}, PURGES AFTER SINGLE READ")
    return NoteCreateResponse(id=note_id, expires_at=note.expires_at, views_left=1)

@api_router.get("/notes/{note_id}")
async def read_note(request: Request, note_id: str):
    # REAL-WORLD rate limiting that works behind proxies  
    await rate_limit_middleware(request, "notes_read")
    
    if note_id not in NOTES_STORE:
        raise HTTPException(status_code=404, detail="not_found_or_expired")
    
    note = NOTES_STORE[note_id]
    
    # Check expiry
    now_utc = datetime.now(timezone.utc)
    if now_utc > note.expires_at:
        del NOTES_STORE[note_id]
        raise HTTPException(status_code=410, detail="expired")
    
    # Consume view
    note.views += 1
    
    if note.views_left <= 0:
        ciphertext = note.ciphertext
        del NOTES_STORE[note_id]
        return {"ciphertext": ciphertext, "views_left": 0}
    
    return {"ciphertext": note.ciphertext, "views_left": note.views_left}

# Messaging envelopes (RAM-only delete-on-delivery) with REAL-WORLD security
@api_router.post("/envelopes/send")
async def send_envelope(request: Request, payload: EnvelopeSend):
    # REAL-WORLD rate limiting that works behind proxies
    await rate_limit_middleware(request, "envelopes_send")
    # Sanitize inputs
    sanitized_to_oid = sanitize_input(payload.to_oid, max_length=100)
    sanitized_from_oid = sanitize_input(payload.from_oid, max_length=100)
    sanitized_ciphertext = sanitize_input(payload.ciphertext, max_length=50000)  # Allow larger encrypted content
    
    env = Envelope(
        id=str(uuid.uuid4()),
        to_oid=sanitized_to_oid,
        from_oid=sanitized_from_oid,
        ciphertext=sanitized_ciphertext,
        ts=payload.ts or datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=UNDLV_TTL_SECONDS),
    )
    # If there are active subscribers, push immediately and do not queue
    subs = SUBS.get(env.to_oid, [])
    delivered = False
    if subs:
        # build frame
        frame = {
            "id": env.id,
            "from_oid": env.from_oid,
            "ciphertext": env.ciphertext,
            "ts": env.ts.isoformat(),
        }
        stale = []
        for ws in subs:
            try:
                await ws.send_json({"messages": [frame]})
                delivered = True
            except Exception:
                stale.append(ws)
        # cleanup stale
        for ws in stale:
            try:
                subs.remove(ws)
            except ValueError:
                pass
        SUBS[env.to_oid] = subs
    if not delivered:
        ENVELOPES.setdefault(env.to_oid, []).append(env)
    return {"id": env.id}

@api_router.get("/envelopes/poll", response_model=EnvelopePollResponse)
async def poll_envelopes(request: Request, oid: str, max: int = 50):
    # REAL-WORLD rate limiting that works behind proxies
    await rate_limit_middleware(request, "envelopes_poll")
    lst = ENVELOPES.get(oid, [])
    if not lst:
        return {"messages": []}
    # deliver up to max and delete them (delete-on-delivery)
    deliver = lst[:max]
    ENVELOPES[oid] = lst[max:]
    return {"messages": [
        {
            "id": e.id,
            "from_oid": e.from_oid,
            "ciphertext": e.ciphertext,
            "ts": e.ts.isoformat(),
        } for e in deliver
    ]}

# STEELOS-SHREDDER Endpoint
class ShredderRequest(BaseModel):
    device_id: str
    trigger_type: str  # "panic_pin", "emergency_nuke", "anti_forensics", "manual"
    confirmation_token: Optional[str] = None
    
class ShredderResponse(BaseModel):
    shredder_activated: bool
    kill_token_generated: bool
    destruction_initiated: bool
    message: str

@api_router.post("/steelos-shredder/deploy", response_model=ShredderResponse)
async def deploy_steelos_shredder(request: Request, payload: ShredderRequest):
    """
    💊 DEPLOY CYANIDE TABLET - STEELOS-SHREDDER Data Destruction
    Generates signed kill token and initiates complete data obliteration
    """
    try:
        # REAL-WORLD rate limiting that works behind proxies
        await rate_limit_middleware(request, "shredder_deploy")
        
        # Sanitize inputs
        device_id = sanitize_input(payload.device_id, max_length=100)
        trigger_type = sanitize_input(payload.trigger_type, max_length=50)
        
        logger.critical(f"💊🧬 STEELOS-SHREDDER DEPLOYMENT: Device {device_id}, Trigger: {trigger_type}")
        
        # Generate signed kill token for STEELOS-SHREDDER
        import hmac
        import hashlib
        import time
        
        timestamp = int(time.time())
        kill_token_data = f"STEELOS_SHREDDER:{device_id}:{timestamp}:{trigger_type}:CYANIDE_TABLET_DEPLOYED"
        
        # Generate cryptographic signature
        signature = hmac.new(
            b"STEELOS_SHREDDER_KILL_TOKEN_SECRET_2025_NSA_GRADE",
            kill_token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        kill_token = {
            "command": "STEELOS_SHREDDER_KILL_TOKEN",
            "device_id": device_id,
            "wipe_type": "steelos_shredder_obliteration",
            "timestamp": timestamp,
            "trigger_type": trigger_type,
            "reason": f"STEELOS-SHREDDER triggered by {trigger_type}",
            "signature": signature,
            "token_data": kill_token_data,
            "auto_execute": True,
            "show_cyanide_animation": True,
            "kill_method": "steelos_shredder",
            "bypass_user_confirmation": True,
            "destruction_phases": [
                "secure_store_annihilation",
                "file_system_destruction", 
                "memory_clearing",
                "cache_data_destruction",
                "metadata_destruction"
            ]
        }
        
        # Store kill token for device retrieval
        if device_id not in security_engine.user_sessions:
            security_engine.user_sessions[device_id] = {}
            
        security_engine.user_sessions[device_id]["steelos_shredder_token"] = kill_token
        
        logger.critical(f"💀 CYANIDE TABLET DEPLOYED: Device {device_id} - STEELOS-SHREDDER KILL TOKEN GENERATED")
        logger.critical(f"🧬 DNA DESTRUCTION Signature: {signature}")
        
        return ShredderResponse(
            shredder_activated=True,
            kill_token_generated=True,
            destruction_initiated=True,
            message="CYANIDE TABLET DEPLOYED - STEELOS-SHREDDER ACTIVATED"
        )
        
    except Exception as e:
        logger.error(f"STEELOS-SHREDDER deployment failed: {e}")
        return ShredderResponse(
            shredder_activated=False,
            kill_token_generated=False,
            destruction_initiated=False,
            message="STEELOS-SHREDDER deployment failed"
        )

@api_router.get("/steelos-shredder/status/{device_id}")
async def get_shredder_status(request: Request, device_id: str):
    """Check if STEELOS-SHREDDER kill token is waiting for device"""
    try:
        # REAL-WORLD rate limiting that works behind proxies
        await rate_limit_middleware(request, "shredder_status")
        
        device_id = sanitize_input(device_id, max_length=100)
        
        if device_id in security_engine.user_sessions:
            session = security_engine.user_sessions[device_id]
            
            # Check for STEELOS-SHREDDER kill token
            if "steelos_shredder_token" in session:
                kill_token = session["steelos_shredder_token"]
                
                logger.critical(f"💊 STEELOS-SHREDDER TOKEN RETRIEVED: Device {device_id}")
                
                # Remove token after retrieval (one-time use)
                del session["steelos_shredder_token"]
                
                return {
                    "shredder_pending": True,
                    "kill_token": kill_token,
                    "cyanide_deployed": True
                }
        
        return {
            "shredder_pending": False,
            "kill_token": None,
            "cyanide_deployed": False
        }
        
    except Exception as e:
        logger.error(f"STEELOS-SHREDDER status check failed: {e}")
        return {
            "shredder_pending": False,
            "kill_token": None,
            "cyanide_deployed": False,
            "error": str(e)
        }

# WebSocket for real-time delivery
@app.websocket("/api/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    # Expect a query param oid
    oid = ws.query_params.get("oid")
    if not oid:
        await ws.close(code=1008)
        return
    SUBS.setdefault(oid, []).append(ws)
    try:
        # On connect: flush any queued envelopes for this oid (deliver and delete)
        pending = ENVELOPES.get(oid, [])
        if pending:
            frames = [
                {
                    "id": e.id,
                    "from_oid": e.from_oid,
                    "ciphertext": e.ciphertext,
                    "ts": e.ts.isoformat(),
                } for e in pending
            ]
            ENVELOPES[oid] = []
            await ws.send_json({"messages": frames})
        # Keepalive loop
        while True:
            try:
                # wait for ping/pong or small sleep
                await asyncio.sleep(5)
                await ws.send_json({"type": "ping", "t": datetime.now(timezone.utc).isoformat()})
            except (RuntimeError, ConnectionResetError):
                # Normal connection closure scenarios
                break
            except Exception as e:
                # Handle WebSocket connection errors
                from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
                if isinstance(e, (ConnectionClosedOK, ConnectionClosedError)):
                    # Normal WebSocket closure - don't log as error
                    break
                else:
                    # Actual error - log it
                    logger.exception("WebSocket error")
                    break
    except WebSocketDisconnect:
        # Normal FastAPI WebSocket disconnect
        pass
    except Exception as e:
        # Handle other exceptions, but don't log normal closures
        from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
        if not isinstance(e, (ConnectionClosedOK, ConnectionClosedError)):
            logger.exception("WebSocket error")
    finally:
        # Remove from subs
        try:
            arr = SUBS.get(oid, [])
            if ws in arr:
                arr.remove(ws)
                SUBS[oid] = arr
        except Exception:
            pass
        try:
            await ws.close()
        except Exception:
            pass

# Import and include new feature routers
from contacts_vault import store_contacts_backup, retrieve_contacts_backup, clear_contacts_vault
from auto_wipe import configure_auto_wipe, update_activity, check_auto_wipe_status, get_wipe_token
from active_auth import configure_active_authentication, record_authentication, check_active_auth_status, get_active_auth_wipe_token, disable_active_auth
from emergency_revocation import get_emergency_portal_html, submit_emergency_revocation, get_emergency_revocation_token, check_emergency_revocation_status

# Add contacts vault endpoints
@api_router.post("/contacts-vault/store")
async def store_contacts(request: Request, payload: dict):
    """Store contacts backup in vault"""
    from contacts_vault import ContactsVaultRequest, store_contacts_backup
    validated_payload = ContactsVaultRequest(**payload)
    return await store_contacts_backup(request, validated_payload)

@api_router.get("/contacts-vault/retrieve/{device_id}")
async def retrieve_contacts(request: Request, device_id: str, encryption_key_hash: str):
    """Retrieve contacts backup from vault"""
    return await retrieve_contacts_backup(request, device_id, encryption_key_hash)

@api_router.delete("/contacts-vault/clear/{device_id}")
async def clear_contacts(request: Request, device_id: str):
    """Clear contacts vault for device"""
    return await clear_contacts_vault(request, device_id)

# Add auto-wipe endpoints
@api_router.post("/auto-wipe/configure")
async def configure_autowipe(request: Request, payload: dict):
    """Configure auto-wipe settings"""
    from auto_wipe import AutoWipeConfig, configure_auto_wipe
    validated_payload = AutoWipeConfig(**payload)
    return await configure_auto_wipe(request, validated_payload)

@api_router.post("/auto-wipe/activity")
async def update_device_activity(request: Request, payload: dict):
    """Update device activity timestamp"""
    from auto_wipe import ActivityUpdate, update_activity
    validated_payload = ActivityUpdate(**payload)
    return await update_activity(request, validated_payload)

@api_router.get("/auto-wipe/status/{device_id}")
async def get_autowipe_status(request: Request, device_id: str):
    """Check auto-wipe status for device"""
    return await check_auto_wipe_status(request, device_id)

@api_router.get("/auto-wipe/token/{device_id}")
async def get_autowipe_token(request: Request, device_id: str):
    """Get pending auto-wipe token for device"""
    return await get_wipe_token(request, device_id)

# Add active authentication endpoints
@api_router.post("/active-auth/configure")
async def configure_active_auth(request: Request, payload: dict):
    """Configure active authentication requirements"""
    from active_auth import ActiveAuthConfig, configure_active_authentication
    validated_payload = ActiveAuthConfig(**payload)
    return await configure_active_authentication(request, validated_payload)

@api_router.post("/active-auth/authenticate")
async def record_auth(request: Request, payload: dict):
    """Record successful authentication"""
    from active_auth import AuthenticationRecord, record_authentication
    validated_payload = AuthenticationRecord(**payload)
    return await record_authentication(request, validated_payload)

@api_router.get("/active-auth/status/{device_id}")
async def get_active_auth_status(request: Request, device_id: str):
    """Check active authentication status"""
    return await check_active_auth_status(request, device_id)

@api_router.get("/active-auth/token/{device_id}")
async def get_active_auth_token(request: Request, device_id: str):
    """Get pending active auth wipe token"""
    return await get_active_auth_wipe_token(request, device_id)

@api_router.delete("/active-auth/disable/{device_id}")
async def disable_active_authentication(request: Request, device_id: str):
    """Disable active authentication for device"""
    return await disable_active_auth(request, device_id)

# Add emergency revocation endpoints
@app.get("/emergency", response_class=HTMLResponse)
async def emergency_portal():
    """Serve emergency revocation portal HTML"""
    html_content = await get_emergency_portal_html()
    return HTMLResponse(content=html_content)

@api_router.post("/emergency/revoke")
async def submit_emergency_id_revocation(
    request: Request,
    omerta_id: str = Form(...),
    panic_passphrase: str = Form(...),
    emergency_contact_name: str = Form(...),
    emergency_contact_email: str = Form(...),
    reason: str = Form(...),
    immediate_execution: bool = Form(False)
):
    """Submit emergency ID revocation request via web form"""
    from emergency_revocation import EmergencyRevocationRequest, submit_emergency_revocation
    
    # Convert form data to model
    payload = EmergencyRevocationRequest(
        omerta_id=omerta_id,
        panic_passphrase=panic_passphrase,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_email=emergency_contact_email,
        reason=reason,
        immediate_execution=immediate_execution
    )
    
    result = await submit_emergency_revocation(request, payload)
    
    # Return HTML response for web form
    if result.success:
        html_response = f"""
        <!DOCTYPE html>
        <html><head><title>Emergency Revocation Submitted</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #2a2a3e; padding: 32px; border-radius: 16px; }}
            .success {{ background: #10b981; padding: 16px; border-radius: 8px; margin-bottom: 20px; }}
            .info {{ background: #3c4043; padding: 16px; border-radius: 8px; }}
        </style></head>
        <body>
        <div class="container">
            <div class="success">
                ✅ EMERGENCY REVOCATION SUBMITTED SUCCESSFULLY
            </div>
            <h2>Revocation Details:</h2>
            <p><strong>Revocation ID:</strong> {result.revocation_id}</p>
            <p><strong>OMERTA ID:</strong> {omerta_id}</p>
            <p><strong>Status:</strong> {"EXECUTED IMMEDIATELY" if immediate_execution else "SCHEDULED"}</p>
            <p><strong>Execute At:</strong> {datetime.fromtimestamp(result.execute_at).strftime('%Y-%m-%d %H:%M:%S UTC') if result.execute_at else "Immediate"}</p>
            <div class="info">
                <strong>Next Steps:</strong><br>
                • Save the Revocation ID for your records<br>
                • {"The OMERTA ID has been revoked and STEELOS-SHREDDER activated" if immediate_execution else "The target has 24 hours to cancel if conscious"}<br>
                • All associated devices will receive the revocation signal<br>
                • This action is irreversible once executed
            </div>
        </div>
        </body></html>
        """
        return HTMLResponse(content=html_response)
    else:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>Emergency Revocation Failed</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #2a2a3e; padding: 32px; border-radius: 16px; }}
            .error {{ background: #ef4444; padding: 16px; border-radius: 8px; }}
        </style></head>
        <body>
        <div class="container">
            <div class="error">
                ❌ EMERGENCY REVOCATION FAILED: {result.message}
            </div>
            <p><a href="/emergency" style="color: #10b981;">← Back to Emergency Portal</a></p>
        </div>
        </body></html>
        """
        return HTMLResponse(content=error_html)

@api_router.get("/emergency/token/{device_id}")
async def get_emergency_token(request: Request, device_id: str):
    """Get emergency revocation token for device"""
    return await get_emergency_revocation_token(request, device_id)

@api_router.get("/emergency/status/{revocation_id}")
async def get_emergency_status(request: Request, revocation_id: str):
    """Check emergency revocation status"""
    return await check_emergency_revocation_status(request, revocation_id)

# Import and add dual key system endpoints BEFORE including router
from dual_key_system import (
    initiate_dual_key_operation, authenticate_dual_key_operator, get_dual_key_operation_status,
    initiate_split_master_key_operation, provide_master_key_fragment, get_split_master_key_status,
    DualKeyAuthRequest, SplitMasterKeyRequest
)

# Dual Key System endpoints
@api_router.post("/dual-key/initiate")
async def dual_key_initiate(request: Request, payload: dict):
    """Initiate dual-key operation"""
    operation_type = payload.get('operation_type')
    operation_data = payload.get('operation_data', {})
    operator_a_id = payload.get('operator_a_id')
    operator_b_id = payload.get('operator_b_id')
    return await initiate_dual_key_operation(request, operation_type, operation_data, operator_a_id, operator_b_id)

@api_router.post("/dual-key/authenticate")
async def dual_key_authenticate(request: Request, auth_request: DualKeyAuthRequest):
    """Authenticate operator for dual-key operation"""
    return await authenticate_dual_key_operator(request, auth_request)

@api_router.get("/dual-key/status/{operation_id}")
async def dual_key_status(request: Request, operation_id: str):
    """Get dual-key operation status"""
    return await get_dual_key_operation_status(request, operation_id)

# Split Master Key System endpoints
@api_router.post("/split-master-key/initiate")
async def split_master_key_initiate(request: Request, payload: dict):
    """Initiate split master key operation"""
    operation_type = payload.get('operation_type')
    operation_data = payload.get('operation_data', {})
    return await initiate_split_master_key_operation(request, operation_type, operation_data)

@api_router.post("/split-master-key/fragment")
async def split_master_key_fragment(request: Request, fragment_request: SplitMasterKeyRequest):
    """Provide key fragment for split master key operation"""
    return await provide_master_key_fragment(request, fragment_request)

@api_router.get("/split-master-key/status/{operation_id}")
async def split_master_key_status(request: Request, operation_id: str):
    """Get split master key operation status"""
    return await get_split_master_key_status(request, operation_id)

# ---------------------------
# LiveKit Video Calling Endpoints
# ---------------------------

@api_router.post("/livekit/token", response_model=LiveKitTokenResponse)
@limiter.limit("10/minute")
async def generate_livekit_token(
    request: Request, 
    token_request: LiveKitTokenRequest
):
    """
    Generate LiveKit access token for video calling
    Rate limited to 10 requests per minute to prevent abuse
    """
    try:
        # Validate input
        room_name = sanitize_input(token_request.room_name, 100)
        participant_name = token_request.participant_name
        if participant_name:
            participant_name = sanitize_input(participant_name, 100)
        
        # Generate unique participant identity (could integrate with OMERTÀ user system)
        participant_identity = f"user_{str(uuid.uuid4())[:8]}"
        
        # TODO: Add user authentication validation here
        # user_id = get_authenticated_user(request)
        # if not livekit_manager.validate_room_access(user_id, room_name):
        #     raise HTTPException(status_code=403, detail="Access denied to room")
        
        # Generate token
        token_data = livekit_manager.generate_access_token(
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=participant_name,
            metadata=token_request.metadata,
            ttl_hours=token_request.ttl_hours
        )
        
        # Log security event
        security_logger.info(f"LiveKit token generated for room {room_name}, participant {participant_identity}")
        
        return LiveKitTokenResponse(**token_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LiveKit token generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token generation failed")

@api_router.post("/livekit/room/create")
@limiter.limit("5/minute")
async def create_livekit_room(
    request: Request,
    room_create: LiveKitRoomCreate
):
    """
    Create a new LiveKit room with specified configuration
    Rate limited to 5 requests per minute
    """
    try:
        # Validate input
        room_name = sanitize_input(room_create.room_name, 100)
        
        # TODO: Add user authentication
        # user_id = get_authenticated_user(request)
        creator_id = f"user_{str(uuid.uuid4())[:8]}"  # Temporary placeholder
        
        # Create room
        room_info = livekit_manager.create_room(
            room_name=room_name,
            creator_id=creator_id,
            room_config={
                "max_participants": room_create.max_participants,
                "is_private": room_create.is_private,
                "requires_approval": room_create.requires_approval,
                "voice_scrambler_enabled": room_create.voice_scrambler_enabled,
                "face_blur_enabled": room_create.face_blur_enabled,
                "recording_enabled": room_create.recording_enabled
            }
        )
        
        # Log security event
        security_logger.info(f"LiveKit room created: {room_name} by {creator_id}")
        
        return {"status": "success", "room": room_info}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LiveKit room creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Room creation failed")

@api_router.get("/livekit/rooms")
@limiter.limit("20/minute")
async def list_livekit_rooms(request: Request):
    """
    List active LiveKit rooms
    Rate limited to 20 requests per minute
    """
    try:
        # TODO: Add user authentication and filter by access
        # user_id = get_authenticated_user(request)
        # rooms = livekit_manager.list_active_rooms(user_id)
        
        rooms = livekit_manager.list_active_rooms()
        
        return {"status": "success", "rooms": rooms}
        
    except Exception as e:
        logger.error(f"LiveKit room listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Room listing failed")

@api_router.get("/livekit/room/{room_name}")
@limiter.limit("30/minute")
async def get_livekit_room_info(request: Request, room_name: str):
    """
    Get information about a specific LiveKit room
    Rate limited to 30 requests per minute
    """
    try:
        room_name = sanitize_input(room_name, 100)
        
        # TODO: Add user authentication and access validation
        # user_id = get_authenticated_user(request)
        # if not livekit_manager.validate_room_access(user_id, room_name):
        #     raise HTTPException(status_code=403, detail="Access denied to room")
        
        room_info = livekit_manager.get_room_info(room_name)
        
        if not room_info:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Remove sensitive information for public API
        public_info = {
            "room_name": room_info["room_name"],
            "created_at": room_info["created_at"],
            "participant_count": len(room_info.get("participants", [])),
            "max_participants": room_info.get("max_participants", 4),
            "is_private": room_info.get("is_private", False),
            "requires_approval": room_info.get("requires_approval", False),
            "voice_scrambler_enabled": room_info.get("voice_scrambler_enabled", True),
            "face_blur_enabled": room_info.get("face_blur_enabled", True)
        }
        
        return {"status": "success", "room": public_info}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LiveKit room info retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Room info retrieval failed")

@api_router.post("/livekit/session/end")
@limiter.limit("60/minute")
async def end_livekit_session(
    request: Request,
    session_end: LiveKitSessionEnd
):
    """
    End a LiveKit session and cleanup resources
    Rate limited to 60 requests per minute
    """
    try:
        session_id = sanitize_input(session_end.session_id, 100)
        
        success = livekit_manager.end_session(session_id)
        
        if success:
            security_logger.info(f"LiveKit session ended: {session_id}")
            return {"status": "success", "message": "Session ended successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LiveKit session end failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Session end failed")

# Admin System Endpoints
@api_router.post("/admin/authenticate")
@limiter.limit("5/minute")
async def admin_authenticate(request: Request, auth_request: AdminAuthRequest):
    """
    Authenticate admin with passphrase
    Rate limited to 5 requests per minute
    """
    try:
        # Validate input
        passphrase = sanitize_input(auth_request.admin_passphrase, 100)
        device_id = sanitize_input(auth_request.device_id, 100)
        
        # Authenticate admin
        auth_response = await admin_system.authenticate_admin(passphrase, device_id)
        
        security_logger.warning(f"Admin authentication: {auth_response.admin_id} from device {device_id}")
        
        return auth_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin authentication failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@api_router.post("/admin/multisig/initiate")
@limiter.limit("3/minute")
async def initiate_multisig_operation(request: Request, multisig_request: MultiSigInitRequest):
    """
    Initiate multi-signature operation (kill, revoke, update)
    Rate limited to 3 requests per minute
    """
    try:
        # Validate session token
        session_token = sanitize_input(multisig_request.session_token, 100)
        
        # Initiate multi-sig operation
        operation_result = await admin_system.initiate_multisig_operation(multisig_request)
        
        security_logger.critical(f"Multi-sig operation initiated: {multisig_request.operation_type} - {operation_result.get('operation_id')}")
        
        return operation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-sig initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Operation initiation failed")

@api_router.post("/admin/multisig/sign")
@limiter.limit("10/minute")
async def sign_multisig_operation(request: Request, sign_request: MultiSigSignRequest):
    """
    Sign multi-signature operation with admin credentials
    Rate limited to 10 requests per minute
    """
    try:
        # Validate operation ID
        operation_id = sanitize_input(sign_request.operation_id, 100)
        admin_passphrase = sanitize_input(sign_request.admin_passphrase, 100)
        admin_id = sanitize_input(sign_request.admin_id, 100)
        
        # Sign operation
        sign_result = await admin_system.sign_multisig_operation(sign_request)
        
        if sign_result.get('operation_completed'):
            security_logger.critical(f"Multi-sig operation EXECUTED: {operation_id} by admin {admin_id}")
        else:
            security_logger.warning(f"Multi-sig operation signed: {operation_id} by admin {admin_id}")
        
        return sign_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-sig signing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Operation signing failed")

@api_router.get("/admin/multisig/status/{operation_id}")
@limiter.limit("20/minute")
async def get_multisig_operation_status(request: Request, operation_id: str):
    """
    Get status of multi-signature operation
    Rate limited to 20 requests per minute
    """
    try:
        operation_id = sanitize_input(operation_id, 100)
        
        status = await admin_system.get_operation_status(operation_id)
        
        return {"status": "success", "operation": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-sig status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Status check failed")

@api_router.get("/admin/seed/info")
@limiter.limit("2/minute")
async def get_admin_seed_info(request: Request):
    """
    Get admin seed phrase information (for setup)
    Rate limited to 2 requests per minute
    """
    try:
        seed_info = await admin_system.get_admin_seed_info()
        
        security_logger.warning("Admin seed information requested")
        
        return {"status": "success", "seed_info": seed_info}
        
    except Exception as e:
        logger.error(f"Admin seed info retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Seed info retrieval failed")

@api_router.post("/admin/passphrase/change")
@limiter.limit("1/minute")
async def change_admin_passphrase(request: Request, current_passphrase: str = Form(...), new_passphrase: str = Form(...)):
    """
    Change admin passphrase
    Rate limited to 1 request per minute
    """
    try:
        current_passphrase = sanitize_input(current_passphrase, 100)
        new_passphrase = sanitize_input(new_passphrase, 100)
        
        change_result = await admin_system.change_admin_passphrase(current_passphrase, new_passphrase)
        
        security_logger.critical("Admin passphrase changed - all sessions invalidated")
        
        return change_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin passphrase change failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Passphrase change failed")

# Include the router in the main app
app.include_router(api_router)

# Include the PIN security router with /api prefix
app.include_router(pin_router, prefix="/api")

# Include the graphite defense router (already has /api prefix)
app.include_router(graphite_router)

# Include the file sharing router with /api prefix
app.include_router(file_sharing_router, prefix="/api", tags=["file-sharing"])

# Include the voice messages router with /api prefix
app.include_router(voice_messages_router, prefix="/api", tags=["voice-messages"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Configure logging with security event tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/omerta_security.log')
    ]
)
logger = logging.getLogger(__name__)

# Security event logger
security_logger = logging.getLogger("OMERTA_SECURITY")
security_handler = logging.FileHandler('/tmp/omerta_security_events.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - SECURITY_EVENT - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

@app.on_event("startup")
async def on_startup():
    # Start background cleanup for RAM-only stores
    asyncio.create_task(cleanup_notes_loop())

@app.on_event("shutdown")
async def on_shutdown():
    _cleanup_stop.set()
    client.close()