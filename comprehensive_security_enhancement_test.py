"""
🧪 COMPREHENSIVE SECURITY ENHANCEMENT TEST SUITE
Tests all newly implemented security features

Tests:
1. Crypto-Erase Engine
2. Message Integrity Verification
3. Auto-Wipe Integration
4. Emergency Revocation Integration
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

# Import the modules to test
import sys
sys.path.insert(0, 'backend')

from crypto_erase_engine import (
    crypto_erase_engine,
    CryptoEraseRequest,
    CryptoEraseResult,
    KeyCategory
)
from message_integrity import (
    message_integrity_checker,
    MessageIntegrityCheck
)
from security_engine import security_engine

class TestCryptoEraseEngine:
    """Test the Crypto-Erase Engine"""
    
    @pytest.mark.asyncio
    async def test_crypto_erase_all_keys(self):
        """Test complete key destruction"""
        device_id = "test_device_001"
        
        # Setup: Create mock keys in session
        security_engine.user_sessions[device_id] = {
            'message_key_1': 'secret_message_key_data_12345',
            'message_key_2': 'another_secret_key_67890',
            'session_token': 'session_auth_token_xyz',
            'vault_master_key': 'vault_encryption_master_key',
            'identity_key_private': 'private_identity_key_data',
            'backup_key_1': 'backup_recovery_key'
        }
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "test_client"
        
        # Create erase request
        erase_request = CryptoEraseRequest(
            device_id=device_id,
            erase_scope="all",
            emergency_mode=True
        )
        
        # Execute crypto-erase
        result = await crypto_erase_engine.crypto_erase_all_keys(mock_request, erase_request)
        
        # Assertions
        assert result.success == True
        assert result.verification_passed == True
        assert sum(result.keys_destroyed.values()) > 0
        
        # Verify keys are actually gone
        session = security_engine.user_sessions.get(device_id, {})
        
        # Check that message keys are gone
        assert 'message_key_1' not in session
        assert 'message_key_2' not in session
        assert 'session_token' not in session
        assert 'vault_master_key' not in session
        
        print(f"✅ Crypto-erase test passed: {sum(result.keys_destroyed.values())} keys destroyed")
    
    @pytest.mark.asyncio
    async def test_crypto_erase_by_scope(self):
        """Test scoped key destruction (e.g., only message keys)"""
        device_id = "test_device_002"
        
        # Setup: Create keys of different types
        security_engine.user_sessions[device_id] = {
            'message_key_1': 'message_key_data',
            'vault_master_key': 'vault_key_data',
            'session_token': 'session_token_data'
        }
        
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "test_client"
        
        # Erase only message keys
        erase_request = CryptoEraseRequest(
            device_id=device_id,
            erase_scope="messages",
            emergency_mode=True
        )
        
        result = await crypto_erase_engine.crypto_erase_all_keys(mock_request, erase_request)
        
        # Verify only message keys destroyed
        session = security_engine.user_sessions.get(device_id, {})
        
        assert 'message_key_1' not in session  # Should be destroyed
        assert 'vault_master_key' in session   # Should still exist
        assert 'session_token' in session      # Should still exist
        
        print(f"✅ Scoped crypto-erase test passed")
    
    @pytest.mark.asyncio
    async def test_secure_overwrite(self):
        """Test that keys are securely overwritten (7-pass)"""
        device_id = "test_device_003"
        
        original_key = "super_secret_key_12345_ABCDE"
        
        security_engine.user_sessions[device_id] = {
            'test_key': original_key
        }
        
        # Perform secure overwrite
        await crypto_erase_engine.secure_overwrite_key(
            security_engine.user_sessions[device_id],
            'test_key'
        )
        
        # Verify key was overwritten (should be zeros)
        overwritten_value = security_engine.user_sessions[device_id]['test_key']
        
        # Should NOT be the original value
        assert overwritten_value != original_key
        
        # Should be zeros (final pass)
        assert isinstance(overwritten_value, bytes)
        assert all(b == 0x00 for b in overwritten_value)
        
        print(f"✅ Secure overwrite test passed: Key properly overwritten")


class TestMessageIntegrity:
    """Test the Message Integrity Verification System"""
    
    @pytest.mark.asyncio
    async def test_valid_e2ee_message(self):
        """Test that valid E2EE messages pass integrity check"""
        
        # Create valid E2EE envelope
        valid_envelope = {
            'id': 'msg_12345',
            'to_oid': 'recipient_oid_001',
            'from_oid': 'sender_oid_002',
            'ciphertext': 'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY3ODkwYWJjZGVmZ2hpamtsbW5vcA==',  # Base64
            'signature': 'valid_cryptographic_signature_hash_12345',
            'ts': time.time()
        }
        
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "test_client"
        
        # Verify integrity
        result = await message_integrity_checker.verify_message_integrity(
            mock_request,
            valid_envelope,
            'recipient_oid_001'
        )
        
        # Assertions
        assert result.integrity_valid == True
        assert result.encryption_verified == True
        assert result.tampering_detected == False
        assert len(result.warnings) == 0
        
        print(f"✅ Valid E2EE message test passed")
    
    @pytest.mark.asyncio
    async def test_unencrypted_message_detection(self):
        """Test that unencrypted messages are detected and rejected"""
        
        # Create INVALID envelope with plaintext
        invalid_envelope = {
            'id': 'msg_67890',
            'to_oid': 'recipient_oid_001',
            'from_oid': 'sender_oid_002',
            'plaintext': 'This is a plaintext message!',  # SHOULD NOT EXIST
            'ciphertext': 'fake_ciphertext',
            'ts': time.time()
        }
        
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "test_client"
        
        # Verify integrity (should fail)
        result = await message_integrity_checker.verify_message_integrity(
            mock_request,
            invalid_envelope,
            'recipient_oid_001'
        )
        
        # Assertions
        assert result.integrity_valid == False
        assert result.encryption_verified == False
        assert len(result.warnings) > 0
        
        # Check for unencrypted content warning
        warnings_text = ' '.join(result.warnings).lower()
        assert 'unencrypted' in warnings_text or 'plaintext' in warnings_text
        
        print(f"✅ Unencrypted message detection test passed")
    
    @pytest.mark.asyncio
    async def test_replay_attack_detection(self):
        """Test that duplicate message IDs are detected (replay attack)"""
        
        envelope = {
            'id': 'msg_replay_test',
            'to_oid': 'recipient_oid_001',
            'from_oid': 'sender_oid_002',
            'ciphertext': 'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=',
            'ts': time.time()
        }
        
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "test_client"
        
        # First message - should pass
        result1 = await message_integrity_checker.verify_message_integrity(
            mock_request,
            envelope,
            'recipient_oid_001'
        )
        
        # Second message with SAME ID - should be detected as replay
        result2 = await message_integrity_checker.verify_message_integrity(
            mock_request,
            envelope,
            'recipient_oid_001'
        )
        
        # Assertions
        assert result1.integrity_valid == True  # First should pass
        assert result2.integrity_valid == False  # Second should fail (replay)
        
        # Check for replay warning
        warnings_text = ' '.join(result2.warnings).lower()
        assert 'replay' in warnings_text
        
        print(f"✅ Replay attack detection test passed")
    
    @pytest.mark.asyncio
    async def test_tampering_detection(self):
        """Test that tampered messages are detected"""
        
        # Create envelope with suspicious timestamp (far in past)
        tampered_envelope = {
            'id': 'msg_tampered',
            'to_oid': 'recipient_oid_001',
            'from_oid': 'sender_oid_002',
            'ciphertext': 'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=',
            'ts': time.time() - 7200  # 2 hours in past
        }
        
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "test_client"
        
        result = await message_integrity_checker.verify_message_integrity(
            mock_request,
            tampered_envelope,
            'recipient_oid_001'
        )
        
        # Should have tampering warnings
        assert len(result.warnings) > 0
        
        print(f"✅ Tampering detection test passed")


class TestIntegration:
    """Test integration of crypto-erase with existing systems"""
    
    @pytest.mark.asyncio
    async def test_auto_wipe_integration(self):
        """Test that auto-wipe calls crypto-erase first"""
        device_id = "test_device_autowipe"
        
        # Setup device session with keys
        security_engine.user_sessions[device_id] = {
            'message_key_1': 'secret_data',
            'vault_master_key': 'vault_data',
            'auto_wipe_config': {
                'enabled': True,
                'days_inactive': 7,
                'wipe_type': 'full_nuke',
                'warning_days': 2,
                'configured_timestamp': int(time.time()),
                'last_activity': int(time.time()) - (8 * 24 * 60 * 60),  # 8 days ago
                'warnings_sent': 0,
                'wipe_scheduled': False
            }
        }
        
        # Import auto_wipe module
        from auto_wipe import trigger_auto_wipe
        
        # Trigger auto-wipe
        config = security_engine.user_sessions[device_id]['auto_wipe_config']
        await trigger_auto_wipe(device_id, config)
        
        # Verify keys were destroyed
        session = security_engine.user_sessions.get(device_id, {})
        
        # Keys should be gone (crypto-erase ran)
        assert 'message_key_1' not in session
        assert 'vault_master_key' not in session
        
        print(f"✅ Auto-wipe integration test passed: Keys destroyed before wipe")
    
    @pytest.mark.asyncio
    async def test_emergency_revocation_integration(self):
        """Test that emergency revocation calls crypto-erase first"""
        omerta_id = "OID_TEST_123"
        device_id = f"device_for_{omerta_id}"
        
        # Setup device session
        security_engine.user_sessions[device_id] = {
            'identity_key_private': 'private_key_data',
            'message_key_1': 'msg_key_data'
        }
        
        # Import emergency_revocation module
        from emergency_revocation import execute_emergency_revocation
        
        # Create revocation data
        revocation_data = {
            'omerta_id': omerta_id,
            'emergency_contact': 'John Doe',
            'reason': 'Test emergency revocation',
            'signature': 'test_signature'
        }
        
        # Execute emergency revocation
        await execute_emergency_revocation('test_revocation_id', revocation_data)
        
        # Verify keys were destroyed
        session = security_engine.user_sessions.get(device_id, {})
        
        # Keys should be gone
        assert 'identity_key_private' not in session
        assert 'message_key_1' not in session
        
        print(f"✅ Emergency revocation integration test passed")


@pytest.mark.asyncio
async def run_all_tests():
    """Run all security enhancement tests"""
    print("\n" + "="*70)
    print("🧪 OMERTA SECURITY ENHANCEMENT TEST SUITE")
    print("="*70 + "\n")
    
    # Test Crypto-Erase Engine
    print("\n📦 Testing Crypto-Erase Engine...")
    crypto_tests = TestCryptoEraseEngine()
    await crypto_tests.test_crypto_erase_all_keys()
    await crypto_tests.test_crypto_erase_by_scope()
    await crypto_tests.test_secure_overwrite()
    
    # Test Message Integrity
    print("\n🛡️ Testing Message Integrity Verification...")
    integrity_tests = TestMessageIntegrity()
    await integrity_tests.test_valid_e2ee_message()
    await integrity_tests.test_unencrypted_message_detection()
    await integrity_tests.test_replay_attack_detection()
    await integrity_tests.test_tampering_detection()
    
    # Test Integration
    print("\n🔄 Testing System Integration...")
    integration_tests = TestIntegration()
    await integration_tests.test_auto_wipe_integration()
    await integration_tests.test_emergency_revocation_integration()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70 + "\n")
    
    # Summary
    print("📊 TEST SUMMARY:")
    print("  ✅ Crypto-Erase Engine: 3/3 tests passed")
    print("  ✅ Message Integrity: 4/4 tests passed")
    print("  ✅ System Integration: 2/2 tests passed")
    print("\n  🎉 Total: 9/9 tests passed (100%)\n")


if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
