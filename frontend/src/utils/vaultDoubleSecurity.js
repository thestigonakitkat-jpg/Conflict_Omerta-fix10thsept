import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Crypto from 'expo-crypto';

// OMERTÁ Vault Double Protection System - Passphrase + PIN + Fake Dial
class VaultDoubleSecurityManager {
  constructor() {
    this.vaultUnlocked = false;
    this.passphraseVerified = false;
    this.pinVerified = false;
    this.fakeDialActive = false;
    this.bruteForceAttempts = 0;
    this.lockoutTime = 0;
    this.maxAttempts = 3;
    this.lockoutDuration = 300000; // 5 minutes
    this.callbacks = {};
  }

  // Initialize vault security system
  async initialize() {
    try {
      console.log('🔐 Initializing OMERTÁ Vault Double Security...');
      
      // Load security settings
      await this.loadSecurityState();
      
      // Check if still in lockout period
      if (this.lockoutTime > Date.now()) {
        console.log('⚠️ Vault still in lockout period');
        return { locked: true, timeRemaining: this.lockoutTime - Date.now() };
      }
      
      console.log('✅ Vault Double Security initialized');
      return { locked: false, initialized: true };
    } catch (error) {
      console.error('❌ Vault security initialization failed:', error);
      return { locked: true, error: error.message };
    }
  }

  // Load security state from storage
  async loadSecurityState() {
    try {
      const state = await AsyncStorage.getItem('@omerta_vault_security_state');
      if (state) {
        const parsed = JSON.parse(state);
        this.bruteForceAttempts = parsed.bruteForceAttempts || 0;
        this.lockoutTime = parsed.lockoutTime || 0;
      }
    } catch (error) {
      console.error('Failed to load vault security state:', error);
    }
  }

  // Save security state to storage
  async saveSecurityState() {
    try {
      const state = {
        bruteForceAttempts: this.bruteForceAttempts,
        lockoutTime: this.lockoutTime,
        lastAccess: Date.now()
      };
      await AsyncStorage.setItem('@omerta_vault_security_state', JSON.stringify(state));
    } catch (error) {
      console.error('Failed to save vault security state:', error);
    }
  }

  // Set up vault passphrase (first time setup)
  async setupPassphrase(passphrase) {
    try {
      if (passphrase.length < 12) {
        throw new Error('Passphrase must be at least 12 characters');
      }

      // Generate salt and hash passphrase
      const salt = await Crypto.getRandomBytesAsync(32);
      const passphraseHash = await this.hashPassphrase(passphrase, salt);
      
      // Store encrypted passphrase data
      const passphraseData = {
        hash: passphraseHash,
        salt: Array.from(salt),
        created: Date.now(),
        strength: this.calculatePassphraseStrength(passphrase)
      };

      await AsyncStorage.setItem('@omerta_vault_passphrase', JSON.stringify(passphraseData));
      
      console.log('🔐 Vault passphrase configured successfully');
      return { success: true, strength: passphraseData.strength };
    } catch (error) {
      console.error('Failed to setup vault passphrase:', error);
      throw error;
    }
  }

  // Hash passphrase with salt
  async hashPassphrase(passphrase, salt) {
    const encoder = new TextEncoder();
    const data = encoder.encode(passphrase + Array.from(salt).join(''));
    const hashBuffer = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      data
    );
    return hashBuffer;
  }

  // Calculate passphrase strength
  calculatePassphraseStrength(passphrase) {
    let score = 0;
    
    // Length bonus
    score += Math.min(passphrase.length * 2, 50);
    
    // Character variety
    if (/[a-z]/.test(passphrase)) score += 5;
    if (/[A-Z]/.test(passphrase)) score += 5;
    if (/[0-9]/.test(passphrase)) score += 5;
    if (/[^a-zA-Z0-9]/.test(passphrase)) score += 10;
    
    // Word count bonus (for passphrases)
    const words = passphrase.split(/\s+/).length;
    if (words >= 4) score += 15;
    if (words >= 6) score += 10;
    
    return Math.min(score, 100);
  }

  // Verify passphrase (Step 1 of double security)
  async verifyPassphrase(inputPassphrase) {
    try {
      // Check lockout first
      const lockoutCheck = await this.checkLockout();
      if (lockoutCheck.locked) {
        return lockoutCheck;
      }

      const storedData = await AsyncStorage.getItem('@omerta_vault_passphrase');
      if (!storedData) {
        throw new Error('No vault passphrase configured');
      }

      const passphraseData = JSON.parse(storedData);
      const salt = new Uint8Array(passphraseData.salt);
      const inputHash = await this.hashPassphrase(inputPassphrase, salt);

      if (inputHash === passphraseData.hash) {
        this.passphraseVerified = true;
        console.log('✅ Vault passphrase verified - Step 1 complete');
        return { 
          success: true, 
          step: 1, 
          message: 'Passphrase verified. Enter PIN to continue.' 
        };
      } else {
        return await this.handleFailedAttempt('Invalid passphrase');
      }
    } catch (error) {
      console.error('Passphrase verification failed:', error);
      return await this.handleFailedAttempt('Passphrase verification error');
    }
  }

  // Set up vault PIN (configured after passphrase)
  async setupVaultPIN(pin) {
    try {
      if (!this.passphraseVerified) {
        throw new Error('Passphrase must be verified first');
      }

      if (pin.length !== 6 || !/^\d{6}$/.test(pin)) {
        throw new Error('PIN must be exactly 6 digits');
      }

      // Generate salt and hash PIN
      const salt = await Crypto.getRandomBytesAsync(16);
      const pinHash = await this.hashPIN(pin, salt);

      const pinData = {
        hash: pinHash,
        salt: Array.from(salt),
        created: Date.now()
      };

      await AsyncStorage.setItem('@omerta_vault_pin', JSON.stringify(pinData));
      
      console.log('🔢 Vault PIN configured successfully');
      return { success: true };
    } catch (error) {
      console.error('Failed to setup vault PIN:', error);
      throw error;
    }
  }

  // Hash PIN with salt
  async hashPIN(pin, salt) {
    const data = pin + Array.from(salt).join('');
    const hashBuffer = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      data
    );
    return hashBuffer;
  }

  // Verify PIN (Step 2 of double security)
  async verifyPIN(inputPIN) {
    try {
      if (!this.passphraseVerified) {
        return { 
          success: false, 
          error: 'Passphrase must be verified first',
          step: 1 
        };
      }

      // Check lockout
      const lockoutCheck = await this.checkLockout();
      if (lockoutCheck.locked) {
        return lockoutCheck;
      }

      const storedData = await AsyncStorage.getItem('@omerta_vault_pin');
      if (!storedData) {
        throw new Error('No vault PIN configured');
      }

      const pinData = JSON.parse(storedData);
      const salt = new Uint8Array(pinData.salt);
      const inputHash = await this.hashPIN(inputPIN, salt);

      if (inputHash === pinData.hash) {
        this.pinVerified = true;
        this.vaultUnlocked = true;
        await this.resetAttempts();
        
        console.log('✅ Vault PIN verified - Vault UNLOCKED');
        
        // Callback for successful unlock
        if (this.callbacks.onVaultUnlocked) {
          this.callbacks.onVaultUnlocked();
        }
        
        return { 
          success: true, 
          step: 2, 
          vaultUnlocked: true,
          message: 'Vault unlocked successfully!' 
        };
      } else {
        return await this.handleFailedAttempt('Invalid PIN');
      }
    } catch (error) {
      console.error('PIN verification failed:', error);
      return await this.handleFailedAttempt('PIN verification error');
    }
  }

  // Fake dial verification system
  async setupFakeDial(fakePassphrase, realPassphrase) {
    try {
      const fakeData = {
        fakeHash: await this.hashPassphrase(fakePassphrase, new Uint8Array(16)),
        realHash: await this.hashPassphrase(realPassphrase, new Uint8Array(16)),
        created: Date.now()
      };

      await AsyncStorage.setItem('@omerta_fake_dial', JSON.stringify(fakeData));
      
      console.log('🎭 Fake dial configured successfully');
      return { success: true };
    } catch (error) {
      console.error('Failed to setup fake dial:', error);
      throw error;
    }
  }

  // Verify fake dial (shows fake vault content)
  async verifyFakeDial(inputPassphrase) {
    try {
      const storedData = await AsyncStorage.getItem('@omerta_fake_dial');
      if (!storedData) {
        return { success: false, error: 'Fake dial not configured' };
      }

      const dialData = JSON.parse(storedData);
      const inputHash = await this.hashPassphrase(inputPassphrase, new Uint8Array(16));

      if (inputHash === dialData.fakeHash) {
        this.fakeDialActive = true;
        console.log('🎭 Fake dial activated - showing decoy content');
        
        if (this.callbacks.onFakeDialActivated) {
          this.callbacks.onFakeDialActivated();
        }
        
        return { 
          success: true, 
          fakeMode: true,
          message: 'Vault accessed (fake mode)' 
        };
      }
      
      return { success: false, error: 'Invalid fake dial passphrase' };
    } catch (error) {
      console.error('Fake dial verification failed:', error);
      return { success: false, error: 'Fake dial error' };
    }
  }

  // Handle failed authentication attempts
  async handleFailedAttempt(error) {
    this.bruteForceAttempts++;
    await this.saveSecurityState();

    console.log(`⚠️ Vault security attempt ${this.bruteForceAttempts}/${this.maxAttempts} failed: ${error}`);

    if (this.bruteForceAttempts >= this.maxAttempts) {
      this.lockoutTime = Date.now() + this.lockoutDuration;
      await this.saveSecurityState();
      
      // Trigger security alert
      if (this.callbacks.onBruteForceDetected) {
        this.callbacks.onBruteForceDetected({
          attempts: this.bruteForceAttempts,
          lockoutDuration: this.lockoutDuration
        });
      }
      
      console.log('🚨 BRUTE FORCE DETECTED - Vault locked for 5 minutes');
      
      return {
        success: false,
        locked: true,
        error: 'Too many failed attempts. Vault locked for 5 minutes.',
        timeRemaining: this.lockoutDuration,
        bruteForce: true
      };
    }

    return {
      success: false,
      error: error,
      attemptsRemaining: this.maxAttempts - this.bruteForceAttempts
    };
  }

  // Check if vault is in lockout period
  async checkLockout() {
    if (this.lockoutTime > Date.now()) {
      const timeRemaining = this.lockoutTime - Date.now();
      return {
        locked: true,
        timeRemaining: timeRemaining,
        message: `Vault locked. Try again in ${Math.ceil(timeRemaining / 60000)} minutes.`
      };
    }
    return { locked: false };
  }

  // Reset failed attempts
  async resetAttempts() {
    this.bruteForceAttempts = 0;
    this.lockoutTime = 0;
    await this.saveSecurityState();
  }

  // Lock vault
  lockVault() {
    this.vaultUnlocked = false;
    this.passphraseVerified = false;
    this.pinVerified = false;
    this.fakeDialActive = false;
    console.log('🔒 Vault locked');
    
    if (this.callbacks.onVaultLocked) {
      this.callbacks.onVaultLocked();
    }
  }

  // Get vault status
  getStatus() {
    return {
      vaultUnlocked: this.vaultUnlocked,
      passphraseVerified: this.passphraseVerified,
      pinVerified: this.pinVerified,
      fakeDialActive: this.fakeDialActive,
      bruteForceAttempts: this.bruteForceAttempts,
      maxAttempts: this.maxAttempts,
      lockoutTime: this.lockoutTime,
      isLocked: this.lockoutTime > Date.now()
    };
  }

  // Set callbacks
  setCallbacks(callbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  // Emergency vault destruction (for STEELOS integration)
  async emergencyVaultDestruction() {
    try {
      console.log('💀 EMERGENCY VAULT DESTRUCTION INITIATED');
      
      // Clear all vault data
      await AsyncStorage.removeItem('@omerta_vault_passphrase');
      await AsyncStorage.removeItem('@omerta_vault_pin');
      await AsyncStorage.removeItem('@omerta_fake_dial');
      await AsyncStorage.removeItem('@omerta_vault_security_state');
      await AsyncStorage.removeItem('@omerta_vault_data');
      
      // Reset all states
      this.vaultUnlocked = false;
      this.passphraseVerified = false;
      this.pinVerified = false;
      this.fakeDialActive = false;
      this.bruteForceAttempts = 0;
      this.lockoutTime = 0;
      
      if (this.callbacks.onEmergencyDestruction) {
        this.callbacks.onEmergencyDestruction();
      }
      
      console.log('💀 Vault completely destroyed');
      return { success: true, message: 'Vault destroyed' };
    } catch (error) {
      console.error('Emergency destruction failed:', error);
      return { success: false, error: error.message };
    }
  }

  // Generate fake vault data (for fake dial mode)
  generateFakeVaultData() {
    return {
      contacts: [
        { name: 'John Smith', oid: 'fake_oid_001', verified: false },
        { name: 'Sarah Johnson', oid: 'fake_oid_002', verified: false }
      ],
      notes: [
        { id: 'fake_note_001', title: 'Shopping List', content: 'Milk, Bread, Eggs' },
        { id: 'fake_note_002', title: 'Meeting Notes', content: 'Team meeting at 3pm' }
      ],
      messages: [
        { id: 'fake_msg_001', from: 'John', content: 'Hey, how are you?', timestamp: Date.now() - 3600000 }
      ]
    };
  }
}

// Export singleton instance
export const vaultDoubleSecurityManager = new VaultDoubleSecurityManager();
export default vaultDoubleSecurityManager;