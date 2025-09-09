import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput,
  Modal,
  Alert,
  Animated
} from 'react-native';
import vaultDoubleSecurityManager from '../utils/vaultDoubleSecurity';

export default function VaultDoubleSecurityUnlock({ 
  visible, 
  onClose, 
  onUnlocked, 
  onFakeDialActivated 
}) {
  const [currentStep, setCurrentStep] = useState(1); // 1: passphrase, 2: PIN
  const [passphrase, setPassphrase] = useState('');
  const [pin, setPin] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [attemptsRemaining, setAttemptsRemaining] = useState(3);
  const [lockoutTime, setLockoutTime] = useState(0);
  const [securityStatus, setSecurityStatus] = useState({});
  const [shakeAnimation] = useState(new Animated.Value(0));
  const [unlockProgress] = useState(new Animated.Value(0));

  useEffect(() => {
    if (visible) {
      initializeUnlock();
    }
  }, [visible]);

  useEffect(() => {
    let interval;
    if (lockoutTime > 0) {
      interval = setInterval(() => {
        const remaining = Math.max(0, lockoutTime - Date.now());
        if (remaining === 0) {
          setLockoutTime(0);
          clearInterval(interval);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [lockoutTime]);

  const initializeUnlock = async () => {
    const result = await vaultDoubleSecurityManager.initialize();
    const status = vaultDoubleSecurityManager.getStatus();
    
    setSecurityStatus(status);
    setAttemptsRemaining(status.maxAttempts - status.bruteForceAttempts);
    
    if (result.locked && result.timeRemaining) {
      setLockoutTime(Date.now() + result.timeRemaining);
    }
  };

  const triggerShakeAnimation = () => {
    Animated.sequence([
      Animated.timing(shakeAnimation, { toValue: 10, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: -10, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: 10, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: 0, duration: 100, useNativeDriver: true }),
    ]).start();
  };

  const updateUnlockProgress = (progress) => {
    Animated.timing(unlockProgress, {
      toValue: progress,
      duration: 300,
      useNativeDriver: false,
    }).start();
  };

  const handlePassphraseSubmit = async () => {
    if (!passphrase.trim()) {
      Alert.alert('Error', 'Please enter your passphrase');
      return;
    }

    setIsVerifying(true);
    
    try {
      // First check for fake dial
      const fakeDialResult = await vaultDoubleSecurityManager.verifyFakeDial(passphrase);
      if (fakeDialResult.success && fakeDialResult.fakeMode) {
        console.log('🎭 Fake dial activated');
        onFakeDialActivated();
        onClose();
        return;
      }

      // Then check real passphrase
      const result = await vaultDoubleSecurityManager.verifyPassphrase(passphrase);
      
      if (result.success) {
        setCurrentStep(2);
        updateUnlockProgress(0.5);
        Alert.alert('Step 1 Complete', 'Passphrase verified. Enter your PIN.');
      } else {
        handleFailedAttempt(result);
      }
    } catch (error) {
      Alert.alert('Error', 'Passphrase verification failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const handlePINSubmit = async () => {
    if (pin.length !== 6) {
      Alert.alert('Error', 'Please enter your 6-digit PIN');
      return;
    }

    setIsVerifying(true);
    
    try {
      const result = await vaultDoubleSecurityManager.verifyPIN(pin);
      
      if (result.success && result.vaultUnlocked) {
        updateUnlockProgress(1.0);
        
        // Success animation
        setTimeout(() => {
          Alert.alert('Vault Unlocked', 'Welcome to your secure vault!', [
            { text: 'Continue', onPress: () => {
              onUnlocked();
              onClose();
              resetForm();
            }}
          ]);
        }, 500);
      } else {
        handleFailedAttempt(result);
      }
    } catch (error) {
      Alert.alert('Error', 'PIN verification failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFailedAttempt = (result) => {
    triggerShakeAnimation();
    
    if (result.locked && result.bruteForce) {
      setLockoutTime(Date.now() + result.timeRemaining);
      Alert.alert(
        '🚨 Security Lockout',
        'Too many failed attempts. Vault is locked for 5 minutes for your protection.',
        [{ text: 'OK', onPress: () => onClose() }]
      );
    } else if (result.locked) {
      const minutes = Math.ceil(result.timeRemaining / 60000);
      Alert.alert(
        '⏰ Vault Locked',
        `Vault is locked. Try again in ${minutes} minutes.`,
        [{ text: 'OK', onPress: () => onClose() }]
      );
    } else {
      setAttemptsRemaining(result.attemptsRemaining || 0);
      Alert.alert(
        'Access Denied',
        `${result.error}\n\nAttempts remaining: ${result.attemptsRemaining || 0}`,
        [{ text: 'Try Again' }]
      );
    }
    
    // Clear input on failed attempt
    if (currentStep === 1) {
      setPassphrase('');
    } else {
      setPin('');
    }
  };

  const resetForm = () => {
    setCurrentStep(1);
    setPassphrase('');
    setPin('');
    updateUnlockProgress(0);
  };

  const formatTimeRemaining = () => {
    if (lockoutTime <= Date.now()) return '';
    
    const remaining = Math.ceil((lockoutTime - Date.now()) / 1000);
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const isLocked = lockoutTime > Date.now();

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <Animated.View 
          style={[
            styles.container,
            { transform: [{ translateX: shakeAnimation }] }
          ]}
        >
          <View style={styles.header}>
            <Text style={styles.title}>🔐 VAULT ACCESS</Text>
            <Text style={styles.subtitle}>
              {currentStep === 1 ? 'Enter Master Passphrase' : 'Enter Security PIN'}
            </Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Progress Bar */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <Animated.View 
                style={[
                  styles.progressFill,
                  {
                    width: unlockProgress.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['0%', '100%']
                    })
                  }
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              Step {currentStep} of 2 - {currentStep === 1 ? 'Passphrase' : 'PIN'}
            </Text>
          </View>

          <View style={styles.content}>
            {isLocked ? (
              <View style={styles.lockoutContainer}>
                <Text style={styles.lockoutTitle}>🔒 VAULT LOCKED</Text>
                <Text style={styles.lockoutMessage}>
                  Security lockout active for your protection.
                </Text>
                <Text style={styles.lockoutTimer}>
                  Time remaining: {formatTimeRemaining()}
                </Text>
                <TouchableOpacity 
                  style={styles.lockoutButton}
                  onPress={onClose}
                >
                  <Text style={styles.lockoutButtonText}>Close</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                {currentStep === 1 ? (
                  <View style={styles.stepContainer}>
                    <Text style={styles.stepInstruction}>
                      Enter your master passphrase to proceed:
                    </Text>
                    
                    <TextInput
                      style={styles.passphraseInput}
                      value={passphrase}
                      onChangeText={setPassphrase}
                      placeholder="Master passphrase..."
                      placeholderTextColor="#666"
                      secureTextEntry
                      autoCapitalize="none"
                      editable={!isVerifying}
                      onSubmitEditing={handlePassphraseSubmit}
                    />

                    <TouchableOpacity 
                      style={[
                        styles.submitButton,
                        (!passphrase || isVerifying) && styles.disabledButton
                      ]}
                      onPress={handlePassphraseSubmit}
                      disabled={!passphrase || isVerifying}
                    >
                      <Text style={styles.submitButtonText}>
                        {isVerifying ? 'Verifying...' : 'Next: Enter PIN'}
                      </Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.stepContainer}>
                    <Text style={styles.stepInstruction}>
                      Enter your 6-digit security PIN:
                    </Text>
                    
                    <TextInput
                      style={styles.pinInput}
                      value={pin}
                      onChangeText={(text) => setPin(text.replace(/[^0-9]/g, '').slice(0, 6))}
                      placeholder="••••••"
                      placeholderTextColor="#666"
                      secureTextEntry
                      keyboardType="numeric"
                      maxLength={6}
                      editable={!isVerifying}
                      onSubmitEditing={handlePINSubmit}
                    />

                    <View style={styles.pinDots}>
                      {[0, 1, 2, 3, 4, 5].map((index) => (
                        <View
                          key={index}
                          style={[
                            styles.pinDot,
                            index < pin.length && styles.pinDotFilled
                          ]}
                        />
                      ))}
                    </View>

                    <TouchableOpacity 
                      style={[
                        styles.submitButton,
                        (pin.length !== 6 || isVerifying) && styles.disabledButton
                      ]}
                      onPress={handlePINSubmit}
                      disabled={pin.length !== 6 || isVerifying}
                    >
                      <Text style={styles.submitButtonText}>
                        {isVerifying ? 'Unlocking...' : 'Unlock Vault'}
                      </Text>
                    </TouchableOpacity>
                  </View>
                )}

                {/* Security Status */}
                <View style={styles.securityStatus}>
                  <Text style={styles.securityStatusTitle}>🛡️ Security Status</Text>
                  <Text style={styles.securityStatusText}>
                    Attempts remaining: {attemptsRemaining}/3
                  </Text>
                  <Text style={styles.securityStatusText}>
                    Brute force protection: Active
                  </Text>
                </View>

                {/* Fake Dial Hint */}
                <View style={styles.hintBox}>
                  <Text style={styles.hintText}>
                    💡 Tip: If under coercion, use your fake passphrase to show decoy content
                  </Text>
                </View>
              </>
            )}
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    justifyContent: 'center',
    padding: 20,
  },
  container: {
    backgroundColor: '#111',
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#ef4444',
    maxHeight: '90%',
  },
  header: {
    backgroundColor: '#ef4444',
    padding: 20,
    borderTopLeftRadius: 13,
    borderTopRightRadius: 13,
    alignItems: 'center',
    position: 'relative',
  },
  title: {
    color: '#fff',
    fontSize: 22,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  subtitle: {
    color: '#fff',
    fontSize: 14,
    marginTop: 5,
  },
  closeButton: {
    position: 'absolute',
    right: 15,
    top: 15,
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressContainer: {
    padding: 20,
    alignItems: 'center',
  },
  progressBar: {
    width: '100%',
    height: 6,
    backgroundColor: '#333',
    borderRadius: 3,
    marginBottom: 10,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#ef4444',
    borderRadius: 3,
  },
  progressText: {
    color: '#fff',
    fontSize: 12,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  stepContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  stepInstruction: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 25,
  },
  passphraseInput: {
    backgroundColor: '#222',
    color: '#fff',
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 15,
    fontSize: 16,
    width: '100%',
    marginBottom: 25,
    borderWidth: 2,
    borderColor: '#444',
    textAlign: 'center',
  },
  pinInput: {
    backgroundColor: '#222',
    color: '#fff',
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 15,
    fontSize: 28,
    width: '80%',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#444',
    textAlign: 'center',
    letterSpacing: 12,
    fontFamily: 'monospace',
  },
  pinDots: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 25,
  },
  pinDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#333',
    marginHorizontal: 8,
    borderWidth: 2,
    borderColor: '#666',
  },
  pinDotFilled: {
    backgroundColor: '#ef4444',
    borderColor: '#ef4444',
  },
  submitButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 25,
    alignItems: 'center',
    width: '100%',
  },
  disabledButton: {
    backgroundColor: '#333',
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  securityStatus: {
    backgroundColor: '#1a1a1a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#333',
  },
  securityStatusTitle: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  securityStatusText: {
    color: '#ccc',
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 3,
  },
  hintBox: {
    backgroundColor: '#0a1a0a',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#00aa00',
  },
  hintText: {
    color: '#00ff00',
    fontSize: 11,
    textAlign: 'center',
  },
  lockoutContainer: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  lockoutTitle: {
    color: '#ff4444',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  lockoutMessage: {
    color: '#ccc',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  lockoutTimer: {
    color: '#ff4444',
    fontSize: 32,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginBottom: 30,
  },
  lockoutButton: {
    backgroundColor: '#666',
    paddingVertical: 12,
    paddingHorizontal: 30,
    borderRadius: 20,
  },
  lockoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});