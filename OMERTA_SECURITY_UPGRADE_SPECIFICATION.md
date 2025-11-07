# 🔒 OMERTA SECURITY UPGRADE SPECIFICATION
## Complete Implementation Guide Based on Master Feature List

**Version:** 2.0  
**Date:** 2025-11-07  
**Status:** Implementation Ready  
**Classification:** Critical Security Enhancements

---

## Executive Summary

This document provides a complete, prioritized implementation plan for all security upgrades identified in the OMERTA master feature list. Each upgrade has been assessed against the current codebase and categorized by priority and implementation complexity.

**Current Security Status:** ✅ Strong Foundation
**Gaps Identified:** 47 security enhancements needed
**Critical Upgrades:** 18 must-implement features
**High Priority:** 15 important enhancements
**Medium Priority:** 14 recommended improvements

---

## 🚨 CRITICAL PRIORITY UPGRADES (MUST IMPLEMENT)

### 1. CORE MESSAGING SECURITY

#### 1.1 Message Integrity Verification
**Status:** ❌ Not Implemented  
**Risk Level:** CRITICAL  
**Implementation Complexity:** Medium

**Current Gap:**
- No integrity checking for delivered messages
- No warning system for unencrypted message detection
- Missing verification that messages arrive E2EE

**Required Implementation:**
```python
# Backend: backend/message_integrity.py
class MessageIntegrityChecker:
    """Verify message integrity and encryption status"""
    
    async def verify_message_integrity(self, envelope: dict) -> dict:
        """
        Check message integrity before delivery
        Returns: {
            'integrity_valid': bool,
            'encryption_verified': bool,
            'warnings': list
        }
        """
        # Verify E2EE envelope structure
        # Check for tampering indicators
        # Validate cryptographic signatures
        
    async def alert_unencrypted_message(self, recipient_id: str):
        """Send critical alert if unencrypted message detected"""
```

**Client Side:**
```javascript
// Frontend: src/utils/messageIntegrity.js
export const verifyMessageIntegrity = async (envelope) => {
  // Check E2EE markers
  // Verify message hasn't been downgraded
  // Alert user if integrity compromised
};
```

#### 1.2 Automatic Key Deletion After Message Read
**Status:** ❌ Not Implemented  
**Risk Level:** CRITICAL  
**Implementation Complexity:** High

**Current Gap:**
- Message keys persist in memory after read
- No secure key wiping mechanism
- Potential for key recovery from memory dumps

**Required Implementation:**
```javascript
// Frontend: src/utils/secureKeyManagement.js
export class SecureKeyManager {
  async deleteMessageKeys(messageId) {
    // 1. Locate all keys for message
    // 2. Crypto-erase from SecureStore
    // 3. Overwrite memory locations
    // 4. Verify deletion
    
    const keys = await this.getMessageKeys(messageId);
    
    for (const key of keys) {
      // Crypto-erase: destroy key before deletion
      await this.cryptoEraseKey(key);
      await SecureStore.deleteItemAsync(key.id);
    }
    
    // Clear from in-memory cache with overwrite
    this.secureMemoryClear(keys);
  }
  
  cryptoEraseKey(key) {
    // Overwrite key material multiple times
    // Use secure random data for overwrite
    // Verify no traces remain
  }
}
```

#### 1.3 Crypto-Erase on Logout/Wipe
**Status:** ⚠️ Partial  
**Risk Level:** CRITICAL  
**Implementation Complexity:** High

**Current Gap:**
- Auto-wipe and STEELOS-Shredder exist but don't guarantee key destruction first
- No explicit crypto-erase phase before file overwrite
- Missing verification that key material is destroyed

**Required Implementation:**
```python
# Backend: backend/crypto_erase_engine.py
class CryptoEraseEngine:
    """Ensure all encryption keys destroyed before data deletion"""
    
    async def crypto_erase_all_keys(self, device_id: str) -> dict:
        """
        Phase 1: Destroy all encryption keys
        Phase 2: Verify keys are gone
        Phase 3: Proceed with data wipe
        """
        logger.critical(f"🔥 CRYPTO-ERASE: Phase 1 - Key Destruction for {device_id}")
        
        # Destroy all key types
        keys_destroyed = {
            'message_keys': await self.destroy_message_keys(device_id),
            'session_keys': await self.destroy_session_keys(device_id),
            'vault_keys': await self.destroy_vault_keys(device_id),
            'identity_keys': await self.destroy_identity_keys(device_id),
            'backup_keys': await self.destroy_backup_keys(device_id)
        }
        
        logger.critical(f"🔥 CRYPTO-ERASE: Phase 2 - Verification")
        verification = await self.verify_keys_destroyed(device_id)
        
        if not verification['all_keys_gone']:
            raise CryptoEraseFailedException("Key destruction incomplete")
        
        logger.critical(f"✅ CRYPTO-ERASE: Complete - {sum(keys_destroyed.values())} keys destroyed")
        
        return {
            'success': True,
            'keys_destroyed': keys_destroyed,
            'timestamp': int(time.time()),
            'verification': verification
        }
```

### 2. GROUP CHAT SECURITY

#### 2.1 Automatic Group Rekeying
**Status:** ❌ Not Implemented  
**Risk Level:** CRITICAL  
**Implementation Complexity:** High

**Current Gap:**
- No automatic key rotation when members join/leave
- Same group key persists across membership changes
- Forward secrecy compromised

**Required Implementation:**
```javascript
// Frontend: src/utils/groupChatSecurity.js
export class GroupChatSecurityManager {
  async handleMembershipChange(groupId, action, memberId) {
    logger.log(`🔐 Group ${groupId}: ${action} member ${memberId} - REKEYING`);
    
    // 1. Generate new group key
    const newGroupKey = await this.generateGroupKey();
    
    // 2. Encrypt for all CURRENT members (excluding departed)
    const currentMembers = await this.getCurrentMembers(groupId);
    const encryptedKeys = await this.encryptKeyForMembers(newGroupKey, currentMembers);
    
    // 3. Send rekey message to all members
    await this.distributeNewKey(groupId, encryptedKeys);
    
    // 4. Mark old key as DEPRECATED
    await this.deprecateOldKey(groupId);
    
    // 5. Crypto-erase old key after 60 seconds
    setTimeout(() => this.cryptoEraseOldKey(groupId), 60000);
    
    return {
      rekeyComplete: true,
      newKeyId: newGroupKey.id,
      membersUpdated: currentMembers.length
    };
  }
}
```

#### 2.2 Member Safety Check List
**Status:** ❌ Not Implemented  
**Risk Level:** HIGH  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/components/GroupChatManager.js
export const GroupMemberSafetyPanel = ({ groupId }) => {
  const [members, setMembers] = useState([]);
  const [safetyChecks, setSafetyChecks] = useState({});
  
  const getMemberSafetyData = async () => {
    const memberList = await getGroupMembers(groupId);
    
    for (const member of memberList) {
      const safety = {
        fingerprint: member.cryptographicFingerprint,
        verified: member.verified,
        addedDate: new Date(member.addedTimestamp),
        lastKeyRotation: member.lastKeyRotation,
        suspiciousActivity: await checkSuspiciousActivity(member.id)
      };
      
      safetyChecks[member.id] = safety;
    }
  };
  
  return (
    <View>
      <Text style={styles.title}>🛡️ Group Security Status</Text>
      {members.map(member => (
        <View key={member.id} style={styles.memberRow}>
          <Text>{member.name}</Text>
          <Text>✓ Fingerprint: {safetyChecks[member.id]?.fingerprint?.slice(0, 8)}...</Text>
          <Text>Added: {safetyChecks[member.id]?.addedDate?.toLocaleDateString()}</Text>
          {safetyChecks[member.id]?.verified ? (
            <Text style={styles.verified}>✅ Verified</Text>
          ) : (
            <Text style={styles.unverified}>⚠️ Not Verified</Text>
          )}
        </View>
      ))}
    </View>
  );
};
```

### 3. DISAPPEARING MESSAGES ENHANCED SECURITY

#### 3.1 Memory & Cache Clearing
**Status:** ⚠️ Partial  
**Risk Level:** CRITICAL  
**Implementation Complexity:** High

**Required Implementation:**
```javascript
// Frontend: src/utils/messageExpiration.js (Enhancement)
export class EnhancedMessageExpiration {
  async deleteDisappearingMessage(messageId) {
    logger.log(`🔥 Enhanced deletion for message ${messageId}`);
    
    // 1. Delete from database
    await deleteMessage(messageId);
    
    // 2. Clear from in-memory state
    await this.clearMessageFromState(messageId);
    
    // 3. Clear notification previews
    await this.clearNotificationHistory(messageId);
    
    // 4. Purge from image cache
    await this.purgeImageCache(messageId);
    
    // 5. Clear clipboard if message was copied
    await this.clearClipboardIfMatch(messageId);
    
    // 6. Overwrite memory buffers (iOS/Android specific)
    await this.secureMemoryOverwrite(messageId);
    
    // 7. Verify deletion complete
    const verificationResult = await this.verifyDeletionComplete(messageId);
    
    if (!verificationResult.complete) {
      logger.error(`⚠️ Deletion incomplete: ${verificationResult.remaining}`);
      // Retry or escalate
    }
    
    return verificationResult;
  }
  
  async secureMemoryOverwrite(messageId) {
    // Platform-specific secure memory clearing
    if (Platform.OS === 'ios') {
      // Use iOS secure memory APIs
    } else if (Platform.OS === 'android') {
      // Use Android secure memory APIs
    }
  }
}
```

#### 3.2 Screenshot Detection & Auto-Delete
**Status:** ❌ Not Implemented  
**Risk Level:** CRITICAL  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/utils/screenshotDetection.js
import { addScreenshotListener } from 'expo-media-library';

export class ScreenshotProtection {
  constructor() {
    this.activeConversations = new Map();
    this.setupScreenshotDetection();
  }
  
  setupScreenshotDetection() {
    addScreenshotListener(async () => {
      logger.critical('📸 SCREENSHOT DETECTED!');
      
      const activeChat = this.getCurrentActiveChat();
      if (activeChat) {
        // 1. Immediately delete the chat thread
        await this.emergencyDeleteChat(activeChat.id);
        
        // 2. Alert the other user
        await this.alertOtherUser(activeChat.id, 'SCREENSHOT_DETECTED');
        
        // 3. Log security event
        await this.logSecurityEvent({
          type: 'SCREENSHOT_DETECTED',
          chatId: activeChat.id,
          timestamp: Date.now()
        });
        
        // 4. Show user warning
        this.showScreenshotAlert();
      }
    });
  }
  
  async emergencyDeleteChat(chatId) {
    logger.critical(`🔥 Emergency deletion of chat ${chatId} due to screenshot`);
    
    // Crypto-erase all keys first
    await this.cryptoEraseChatKeys(chatId);
    
    // Delete all messages
    await this.deleteAllMessages(chatId);
    
    // Clear caches
    await this.clearAllCaches(chatId);
    
    return { deleted: true, reason: 'screenshot_detected' };
  }
}
```

### 4. VAULT SECURITY ENHANCEMENTS

#### 4.1 Auto-Lock After 60 Seconds
**Status:** ❌ Not Implemented  
**Risk Level:** HIGH  
**Implementation Complexity:** Low

**Required Implementation:**
```javascript
// Frontend: src/utils/vaultAutoLock.js
export class VaultAutoLockManager {
  constructor() {
    this.lockTimeout = null;
    this.inactivityThreshold = 60000; // 60 seconds
    this.lastActivityTime = Date.now();
  }
  
  startAutoLockTimer() {
    this.resetTimer();
    
    // Check every 5 seconds
    this.lockTimeout = setInterval(() => {
      const timeSinceActivity = Date.now() - this.lastActivityTime;
      
      if (timeSinceActivity >= this.inactivityThreshold) {
        this.lockVault();
      }
    }, 5000);
  }
  
  resetTimer() {
    this.lastActivityTime = Date.now();
  }
  
  async lockVault() {
    logger.log('🔒 Auto-locking vault after 60s inactivity');
    
    // Clear timer
    if (this.lockTimeout) {
      clearInterval(this.lockTimeout);
    }
    
    // Crypto-erase session keys
    await this.cryptoEraseSessionKeys();
    
    // Lock vault
    await vaultDoubleSecurityManager.lockVault();
    
    // Navigate to lock screen
    navigation.navigate('VaultLocked');
  }
  
  stopAutoLockTimer() {
    if (this.lockTimeout) {
      clearInterval(this.lockTimeout);
      this.lockTimeout = null;
    }
  }
}
```

#### 4.2 Never Store Unencrypted Filenames
**Status:** ❌ Not Implemented  
**Risk Level:** HIGH  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/utils/vaultStorage.js
export class SecureVaultStorage {
  async storeVaultFile(file, vaultPassword) {
    // 1. Derive filename encryption key from vault password
    const filenameKey = await this.deriveFilenameKey(vaultPassword);
    
    // 2. Encrypt the filename
    const encryptedFilename = await this.encryptFilename(file.name, filenameKey);
    
    // 3. Encrypt the file content
    const encryptedContent = await this.encryptFileContent(file, vaultPassword);
    
    // 4. Store with encrypted metadata
    const vaultEntry = {
      id: generateSecureId(),
      encryptedFilename: encryptedFilename,
      encryptedContent: encryptedContent,
      fileType: this.encryptFileType(file.type, filenameKey),
      size: encryptedContent.length,
      timestamp: Date.now()
    };
    
    await this.saveToSecureStore(vaultEntry);
    
    // CRITICAL: Never store plaintext filename anywhere
    logger.log(`✅ Stored file with encrypted name: ${encryptedFilename.slice(0, 16)}...`);
    
    return vaultEntry.id;
  }
  
  async deriveFilenameKey(vaultPassword) {
    // Derive separate key specifically for filename encryption
    const salt = await this.getOrCreateFilenameSalt();
    return await pbkdf2(vaultPassword, salt, 100000, 32);
  }
}
```

#### 4.3 Crypto-Erase Before Vault Wipe
**Status:** ⚠️ Partial  
**Risk Level:** CRITICAL  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/utils/vaultSecurity.js
export class VaultCryptoErase {
  async wipeVault() {
    logger.critical('💀 VAULT CRYPTO-ERASE INITIATED');
    
    // PHASE 1: Key Destruction (MUST happen first)
    await this.destroyVaultKeys();
    
    // PHASE 2: Verify keys are gone
    const keysGone = await this.verifyKeysDestroyed();
    if (!keysGone) {
      throw new Error('CRYPTO-ERASE FAILED: Keys still present');
    }
    
    // PHASE 3: Delete encrypted data
    await this.deleteVaultData();
    
    // PHASE 4: Overwrite storage locations
    await this.secureOverwriteStorage();
    
    logger.critical('✅ VAULT CRYPTO-ERASE COMPLETE');
  }
  
  async destroyVaultKeys() {
    const keys = await this.getAllVaultKeys();
    
    for (const key of keys) {
      // Overwrite key in memory multiple times
      for (let i = 0; i < 7; i++) {
        await this.overwriteKey(key, generateRandomBytes(key.length));
      }
      
      // Delete from SecureStore
      await SecureStore.deleteItemAsync(key.id);
    }
    
    return { keysDestroyed: keys.length };
  }
}
```

### 5. DEVICE SECURITY (DNA CHECK) ENHANCEMENTS

#### 5.1 Offline Attestation Caching
**Status:** ⚠️ Partial  
**Risk Level:** HIGH  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/utils/deviceAttestation.js
export class OfflineAttestationManager {
  async performAttestation() {
    try {
      // Try online attestation first
      const attestation = await this.performOnlineAttestation();
      
      // Cache result for offline use
      await this.cacheAttestationResult(attestation);
      
      return attestation;
    } catch (error) {
      // If offline, use cached attestation
      logger.warn('⚠️ Offline - using cached attestation');
      
      const cachedResult = await this.getCachedAttestation();
      
      if (!cachedResult) {
        // No cached result - enter safe mode
        return this.enterSafeMode();
      }
      
      // Verify cached result isn't too old (max 24 hours)
      if (Date.now() - cachedResult.timestamp > 86400000) {
        return this.enterSafeMode();
      }
      
      return cachedResult;
    }
  }
  
  async cacheAttestationResult(attestation) {
    const cacheEntry = {
      result: attestation,
      timestamp: Date.now(),
      deviceId: await this.getDeviceId()
    };
    
    await SecureStore.setItemAsync(
      'attestation_cache',
      JSON.stringify(cacheEntry)
    );
  }
}
```

#### 5.2 Staged Warning System - Stage 3 Cannot Be Canceled
**Status:** ⚠️ Needs Verification  
**Risk Level:** CRITICAL  
**Implementation Complexity:** Low

**Required Implementation:**
```javascript
// Frontend: src/utils/stagedWarningSystem.js
export class StagedWarningSystem {
  async triggerStage3() {
    logger.critical('🚨 STAGE 3 WARNING: CANNOT BE CANCELED');
    
    // Disable all cancel buttons
    this.disableCancelOptions();
    
    // Start irreversible countdown
    const countdown = 10; // 10 seconds
    
    for (let i = countdown; i > 0; i--) {
      this.updateCountdownDisplay(i);
      await this.wait(1000);
    }
    
    // Execute wipe - NO WAY TO STOP THIS
    await this.executeForceWipe();
  }
  
  disableCancelOptions() {
    // Disable back button
    BackHandler.exitApp = () => false;
    
    // Disable all gestures
    gestureHandlerRootHOC.enabled = false;
    
    // Lock UI completely except countdown display
    this.lockUIForWipe();
  }
}
```

### 6. WIPE/KILL/PANIC SYSTEM

#### 6.1 Crypto-Erase First, Always
**Status:** ⚠️ Needs Enforcement  
**Risk Level:** CRITICAL  
**Implementation Complexity:** Medium

**Required Implementation:**
```python
# Backend: backend/wipe_protocol.py
class SecureWipeProtocol:
    """Enforce crypto-erase before all wipes"""
    
    async def execute_secure_wipe(self, device_id: str, wipe_type: str) -> dict:
        """
        Mandatory 3-phase wipe protocol:
        1. CRYPTO-ERASE (destroy keys)
        2. VERIFICATION (confirm keys gone)
        3. DATA WIPE (overwrite files)
        """
        
        logger.critical(f"🔥 SECURE WIPE PROTOCOL: {wipe_type} for {device_id}")
        
        # PHASE 1: CRYPTO-ERASE (MANDATORY)
        phase1 = await self.crypto_erase_phase(device_id)
        if not phase1['success']:
            raise WipeException("CRYPTO-ERASE FAILED - ABORTING WIPE")
        
        logger.critical(f"✅ Phase 1 Complete: {phase1['keys_destroyed']} keys destroyed")
        
        # PHASE 2: VERIFICATION (MANDATORY)
        phase2 = await self.verification_phase(device_id)
        if not phase2['all_keys_gone']:
            raise WipeException("VERIFICATION FAILED - Keys still present")
        
        logger.critical(f"✅ Phase 2 Complete: Key destruction verified")
        
        # PHASE 3: DATA WIPE
        phase3 = await self.data_wipe_phase(device_id, wipe_type)
        
        logger.critical(f"✅ Phase 3 Complete: Data wipe successful")
        
        # PHASE 4: LOG TO IMMUTABLE AUDIT
        await self.log_wipe_to_audit(device_id, {
            'phase1': phase1,
            'phase2': phase2,
            'phase3': phase3,
            'timestamp': time.time(),
            'wipe_type': wipe_type
        })
        
        return {
            'success': True,
            'phases_completed': 3,
            'keys_destroyed': phase1['keys_destroyed'],
            'data_wiped': phase3['files_wiped']
        }
```

#### 6.2 Remote Kill Signature Verification
**Status:** ⚠️ Partial  
**Risk Level:** CRITICAL  
**Implementation Complexity:** High

**Required Implementation:**
```python
# Backend: backend/remote_kill_verification.py
class RemoteKillSignatureVerifier:
    """Verify 2-of-3 multi-signature approval for remote kill"""
    
    async def verify_kill_authorization(self, kill_token: dict) -> dict:
        """
        Verify kill token has valid 2-of-3 signatures
        """
        required_signatures = 2
        valid_signatures = []
        
        # Get authorized signers
        authorized_signers = await self.get_authorized_signers()
        
        # Verify each signature
        for signature_data in kill_token.get('signatures', []):
            signer_id = signature_data['signer_id']
            signature = signature_data['signature']
            
            if signer_id not in authorized_signers:
                logger.warning(f"⚠️ Invalid signer: {signer_id}")
                continue
            
            # Verify signature
            is_valid = await self.verify_signature(
                kill_token['command'],
                signature,
                authorized_signers[signer_id]['public_key']
            )
            
            if is_valid:
                valid_signatures.append(signer_id)
                logger.info(f"✅ Valid signature from {signer_id}")
        
        # Check if we have enough signatures
        if len(valid_signatures) >= required_signatures:
            logger.critical(f"✅ KILL AUTHORIZED: {len(valid_signatures)} valid signatures")
            return {
                'authorized': True,
                'signatures': valid_signatures,
                'signers': [authorized_signers[sid]['name'] for sid in valid_signatures]
            }
        else:
            logger.error(f"❌ INSUFFICIENT SIGNATURES: {len(valid_signatures)}/{required_signatures}")
            return {
                'authorized': False,
                'reason': f'Insufficient signatures ({len(valid_signatures)}/{required_signatures})'
            }
```

---

## 🔶 HIGH PRIORITY UPGRADES

### 7. SECURITY HEALTH DASHBOARD

**Status:** ❌ Not Implemented  
**Risk Level:** HIGH  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/components/SecurityHealthDashboard.js
export const SecurityHealthDashboard = () => {
  const [healthStatus, setHealthStatus] = useState(null);
  
  useEffect(() => {
    // Refresh every time screen is opened
    refreshHealthStatus();
  }, []);
  
  const refreshHealthStatus = async () => {
    const status = {
      integrityCheck: await performIntegrityCheck(),
      appVersion: await verifyAppVersion(),
      lastReboot: await getLastRebootTime(),
      backupStatus: await getBackupStatus(),
      keyRotationStatus: await getKeyRotationStatus(),
      threatLevel: await getThreatLevel()
    };
    
    setHealthStatus(status);
  };
  
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🛡️ Security Health</Text>
      
      <HealthItem 
        label="Device Integrity"
        value={healthStatus?.integrityCheck?.status || 'Checking...'}
        icon={healthStatus?.integrityCheck?.status === 'OK' ? '✅' : '⚠️'}
      />
      
      <HealthItem 
        label="App Version"
        value={healthStatus?.appVersion?.verified ? 'Verified' : 'Unknown'}
        icon={healthStatus?.appVersion?.verified ? '✅' : '❌'}
      />
      
      <HealthItem 
        label="Last Reboot"
        value={formatTimeSince(healthStatus?.lastReboot)}
        icon={needsReboot(healthStatus?.lastReboot) ? '⚠️' : '✅'}
        warning={needsReboot(healthStatus?.lastReboot) ? 'Reboot recommended' : null}
      />
      
      <HealthItem 
        label="Backup Status"
        value={healthStatus?.backupStatus?.encrypted ? 'Encrypted' : 'Not configured'}
        icon={healthStatus?.backupStatus?.encrypted ? '✅' : '⚠️'}
      />
      
      <Button 
        title="🔄 Refresh Status"
        onPress={refreshHealthStatus}
      />
    </ScrollView>
  );
};

// Cannot be disabled - always shows on security screen
```

### 8. ONE-TAP LOCKDOWN

**Status:** ❌ Not Implemented  
**Risk Level:** HIGH  
**Implementation Complexity:** Medium

**Required Implementation:**
```javascript
// Frontend: src/utils/oneTapLockdown.js
export class OneTapLockdownManager {
  async activateLockdown() {
    logger.critical('🚨 ONE-TAP LOCKDOWN ACTIVATED');
    
    // Execute all lockdown actions in parallel
    await Promise.all([
      this.lockApp(),
      this.muteNotifications(),
      this.disableNetwork(),
      this.cryptoEraseSessionKeys(),
      this.activateAntiScreenshot(),
      this.logLockdownEvent()
    ]);
    
    // Show lockdown screen
    navigation.navigate('LockdownMode');
  }
  
  async lockApp() {
    // Lock all sensitive screens
    await AsyncStorage.setItem('lockdown_active', 'true');
    
    // Require full re-authentication
    await this.clearAuthTokens();
  }
  
  async disableNetwork() {
    // Disable all network requests (offline mode)
    this.networkEnabled = false;
    
    // Close all WebSocket connections
    await this.closeAllConnections();
  }
  
  async reauth() {
    // Must pass full authentication to exit lockdown
    const authResult = await this.performFullAuth();
    
    if (authResult.success) {
      await this.deactivateLockdown();
    }
  }
}

// Physical shortcut: Double power button
// Works offline - no network dependency
```

### 9. IMMUTABLE AUDIT LOGS

**Status:** ❌ Not Implemented  
**Risk Level:** HIGH  
**Implementation Complexity:** High

**Required Implementation:**
```python
# Backend: backend/immutable_audit_log.py
import hashlib
import json
import time
from typing import Dict, List

class ImmutableAuditLog:
    """
    Blockchain-style append-only audit log
    Each entry contains hash of previous entry
    Tampering detection via hash chain verification
    """
    
    def __init__(self):
        self.log_chain: List[Dict] = []
        self.genesis_hash = self.create_genesis_block()
    
    def create_genesis_block(self) -> str:
        """Create genesis block for log chain"""
        genesis = {
            'block_number': 0,
            'timestamp': int(time.time()),
            'event': 'GENESIS_BLOCK',
            'data': 'OMERTA_AUDIT_LOG_INITIALIZED',
            'previous_hash': '0' * 64
        }
        
        block_hash = self.calculate_hash(genesis)
        genesis['block_hash'] = block_hash
        
        self.log_chain.append(genesis)
        return block_hash
    
    def append_audit_event(self, event_type: str, data: dict) -> dict:
        """
        Append event to immutable audit log
        Returns the new block
        """
        previous_block = self.log_chain[-1]
        
        new_block = {
            'block_number': len(self.log_chain),
            'timestamp': int(time.time()),
            'event': event_type,
            'data': data,
            'previous_hash': previous_block['block_hash']
        }
        
        # Calculate hash for this block
        block_hash = self.calculate_hash(new_block)
        new_block['block_hash'] = block_hash
        
        # Append to chain
        self.log_chain.append(new_block)
        
        logger.info(f"📝 AUDIT: Block {new_block['block_number']} - {event_type}")
        
        # Store off-site or to blockchain for immutability
        await self.store_to_permanent_storage(new_block)
        
        return new_block
    
    def calculate_hash(self, block: dict) -> str:
        """Calculate SHA-256 hash of block"""
        # Create deterministic string from block
        block_copy = block.copy()
        block_copy.pop('block_hash', None)  # Remove hash if exists
        
        block_string = json.dumps(block_copy, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def verify_chain_integrity(self) -> dict:
        """
        Verify entire audit log chain
        Detects any tampering
        """
        for i in range(1, len(self.log_chain)):
            current_block = self.log_chain[i]
            previous_block = self.log_chain[i - 1]
            
            # Verify previous hash matches
            if current_block['previous_hash'] != previous_block['block_hash']:
                return {
                    'valid': False,
                    'tampered_at_block': i,
                    'error': 'Previous hash mismatch'
                }
            
            # Verify current block hash
            calculated_hash = self.calculate_hash(current_block)
            if calculated_hash != current_block['block_hash']:
                return {
                    'valid': False,
                    'tampered_at_block': i,
                    'error': 'Block hash mismatch'
                }
        
        return {
            'valid': True,
            'total_blocks': len(self.log_chain),
            'genesis_hash': self.genesis_hash
        }
    
    async def store_to_permanent_storage(self, block: dict):
        """
        Store block to off-site permanent storage
        Options: S3, blockchain, IPFS, etc.
        """
        # Implementation depends on chosen permanent storage
        pass

# Global audit log instance
immutable_audit_log = ImmutableAuditLog()

# Usage examples:
# await immutable_audit_log.append_audit_event('ADMIN_LOGIN', {'admin_id': 'xyz'})
# await immutable_audit_log.append_audit_event('WIPE_EXECUTED', {'device_id': 'abc'})
# await immutable_audit_log.append_audit_event('KILL_TOKEN_SIGNED', {'signer': 'admin1'})
```

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: Critical Security Foundations (Week 1-2)
1. ✅ Crypto-Erase Engine (all wipe operations)
2. ✅ Message Integrity Verification
3. ✅ Automatic Key Deletion
4. ✅ Vault Auto-Lock
5. ✅ Stage 3 Warning Cannot Be Canceled

### Phase 2: Data Protection (Week 3-4)
6. ✅ Group Chat Auto-Rekeying
7. ✅ Enhanced Disappearing Messages
8. ✅ Screenshot Detection & Auto-Delete
9. ✅ Vault Filename Encryption
10. ✅ Remote Kill Signature Verification

### Phase 3: Monitoring & Audit (Week 5-6)
11. ✅ Security Health Dashboard
12. ✅ One-Tap Lockdown
13. ✅ Immutable Audit Logs
14. ✅ Offline Attestation Caching
15. ✅ Member Safety Check List

### Phase 4: Testing & Hardening (Week 7-8)
16. ✅ Comprehensive Security Testing
17. ✅ Penetration Testing
18. ✅ Performance Optimization
19. ✅ Documentation Updates
20. ✅ Security Audit Report

---

## 📊 IMPLEMENTATION STATUS TRACKING

| Feature | Priority | Status | ETA | Assigned |
|---------|----------|--------|-----|----------|
| Crypto-Erase Engine | Critical | 🔴 Not Started | Week 1 | - |
| Message Integrity Check | Critical | 🔴 Not Started | Week 1 | - |
| Auto Key Deletion | Critical | 🔴 Not Started | Week 1 | - |
| Group Rekeying | Critical | 🔴 Not Started | Week 2 | - |
| Vault Auto-Lock | High | 🔴 Not Started | Week 2 | - |
| Screenshot Detection | Critical | 🔴 Not Started | Week 3 | - |
| Security Dashboard | High | 🔴 Not Started | Week 5 | - |
| One-Tap Lockdown | High | 🔴 Not Started | Week 5 | - |
| Audit Logs | High | 🔴 Not Started | Week 5 | - |

---

## ✅ VERIFICATION & TESTING

Each implemented feature must pass:

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Cross-system testing
3. **Security Tests**: Penetration testing
4. **Performance Tests**: No degradation
5. **User Acceptance Tests**: Functionality verification

---

## 📝 NOTES

- All crypto-erase operations must be verified before proceeding with data deletion
- Immutable audit logs are critical for security incident investigation
- Security Health Dashboard cannot be disabled by user
- One-Tap Lockdown must work offline
- All key deletion operations must use secure memory overwriting

---

**Document Version:** 2.0  
**Last Updated:** 2025-11-07  
**Next Review:** After Phase 1 Completion
