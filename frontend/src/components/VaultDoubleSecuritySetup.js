import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput,
  Modal,
  Alert,
  ScrollView,
  Switch
} from 'react-native';
import vaultDoubleSecurityManager from '../utils/vaultDoubleSecurity';

export default function VaultDoubleSecuritySetup({ visible, onClose, onSetupComplete }) {
  const [currentStep, setCurrentStep] = useState(1); // 1: passphrase, 2: PIN, 3: fake dial, 4: complete
  const [passphrase, setPassphrase] = useState('');
  const [confirmPassphrase, setConfirmPassphrase] = useState('');
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [fakePassphrase, setFakePassphrase] = useState('');
  const [enableFakeDial, setEnableFakeDial] = useState(true);
  const [passphraseStrength, setPassphraseStrength] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (passphrase.length > 0) {
      // Calculate strength as user types
      const strength = calculateStrength(passphrase);
      setPassphraseStrength(strength);
    }
  }, [passphrase]);

  const calculateStrength = (phrase) => {
    let score = 0;
    score += Math.min(phrase.length * 2, 50);
    if (/[a-z]/.test(phrase)) score += 5;
    if (/[A-Z]/.test(phrase)) score += 5;
    if (/[0-9]/.test(phrase)) score += 5;
    if (/[^a-zA-Z0-9]/.test(phrase)) score += 10;
    const words = phrase.split(/\s+/).length;
    if (words >= 4) score += 15;
    if (words >= 6) score += 10;
    return Math.min(score, 100);
  };

  const getStrengthColor = () => {
    if (passphraseStrength < 30) return '#ff4444';
    if (passphraseStrength < 60) return '#ffaa00';
    if (passphraseStrength < 80) return '#ffdd00';
    return '#00ff00';
  };

  const getStrengthText = () => {
    if (passphraseStrength < 30) return 'Weak';
    if (passphraseStrength < 60) return 'Fair';
    if (passphraseStrength < 80) return 'Good';
    return 'Excellent';
  };

  const handlePassphraseSetup = async () => {
    if (passphrase.length < 12) {
      Alert.alert('Error', 'Passphrase must be at least 12 characters long');
      return;
    }
    
    if (passphrase !== confirmPassphrase) {
      Alert.alert('Error', 'Passphrases do not match');
      return;
    }

    if (passphraseStrength < 50) {
      Alert.alert(
        'Weak Passphrase',
        'Your passphrase is weak. Consider adding more words, numbers, or special characters.',
        [
          { text: 'Use Anyway', onPress: () => proceedWithPassphrase() },
          { text: 'Improve It', style: 'cancel' }
        ]
      );
      return;
    }

    await proceedWithPassphrase();
  };

  const proceedWithPassphrase = async () => {
    setIsLoading(true);
    try {
      const result = await vaultDoubleSecurityManager.setupPassphrase(passphrase);
      if (result.success) {
        setCurrentStep(2);
        Alert.alert('Success', 'Passphrase configured successfully. Now set up your 6-digit PIN.');
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePINSetup = async () => {
    if (pin.length !== 6 || !/^\d{6}$/.test(pin)) {
      Alert.alert('Error', 'PIN must be exactly 6 digits');
      return;
    }
    
    if (pin !== confirmPin) {
      Alert.alert('Error', 'PINs do not match');
      return;
    }

    // Check for weak PINs
    const weakPatterns = [
      '123456', '654321', '111111', '222222', '333333', '444444', '555555',
      '666666', '777777', '888888', '999999', '000000', '121212', '010101'
    ];

    if (weakPatterns.includes(pin)) {
      Alert.alert(
        'Weak PIN',
        'This PIN is too predictable. Please choose a more secure combination.',
        [{ text: 'OK' }]
      );
      return;
    }

    setIsLoading(true);
    try {
      const result = await vaultDoubleSecurityManager.setupVaultPIN(pin);
      if (result.success) {
        if (enableFakeDial) {
          setCurrentStep(3);
          Alert.alert('Success', 'PIN configured successfully. Now set up fake dial protection (optional).');
        } else {
          setCurrentStep(4);
          onSetupComplete();
        }
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFakeDialSetup = async () => {
    if (fakePassphrase.length < 8) {
      Alert.alert('Error', 'Fake passphrase must be at least 8 characters long');
      return;
    }

    if (fakePassphrase === passphrase) {
      Alert.alert('Error', 'Fake passphrase must be different from your real passphrase');
      return;
    }

    setIsLoading(true);
    try {
      const result = await vaultDoubleSecurityManager.setupFakeDial(fakePassphrase, passphrase);
      if (result.success) {
        setCurrentStep(4);
        Alert.alert('Success', 'Fake dial configured successfully. Setup complete!');
        onSetupComplete();
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const skipFakeDial = () => {
    setCurrentStep(4);
    Alert.alert('Setup Complete', 'Vault double security has been configured successfully!');
    onSetupComplete();
  };

  const renderPassphraseStep = () => (
    <ScrollView style={styles.stepContainer}>
      <Text style={styles.stepTitle}>🔐 Step 1: Master Passphrase</Text>
      <Text style={styles.stepDescription}>
        Create a strong passphrase (12+ characters). Use multiple words, numbers, and symbols.
      </Text>

      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Master Passphrase</Text>
        <TextInput
          style={styles.textInput}
          value={passphrase}
          onChangeText={setPassphrase}
          placeholder="Enter your master passphrase..."
          placeholderTextColor="#666"
          secureTextEntry
          autoCapitalize="none"
        />
        
        {passphrase.length > 0 && (
          <View style={styles.strengthContainer}>
            <View style={styles.strengthBar}>
              <View 
                style={[
                  styles.strengthFill, 
                  { 
                    width: `${passphraseStrength}%`, 
                    backgroundColor: getStrengthColor() 
                  }
                ]} 
              />
            </View>
            <Text style={[styles.strengthText, { color: getStrengthColor() }]}>
              {getStrengthText()} ({passphraseStrength}%)
            </Text>
          </View>
        )}
      </View>

      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Confirm Passphrase</Text>
        <TextInput
          style={styles.textInput}
          value={confirmPassphrase}
          onChangeText={setConfirmPassphrase}
          placeholder="Confirm your passphrase..."
          placeholderTextColor="#666"
          secureTextEntry
          autoCapitalize="none"
        />
      </View>

      <View style={styles.securityTips}>
        <Text style={styles.tipsTitle}>💡 Security Tips:</Text>
        <Text style={styles.tipText}>• Use 4-6 random words with spaces</Text>
        <Text style={styles.tipText}>• Add numbers and special characters</Text>
        <Text style={styles.tipText}>• Avoid personal information</Text>
        <Text style={styles.tipText}>• Example: "Mountain Blue 7891 Coffee!"</Text>
      </View>

      <TouchableOpacity 
        style={[styles.actionButton, (!passphrase || !confirmPassphrase) && styles.disabledButton]}
        onPress={handlePassphraseSetup}
        disabled={!passphrase || !confirmPassphrase || isLoading}
      >
        <Text style={styles.actionButtonText}>
          {isLoading ? 'Setting up...' : 'Next: Configure PIN'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderPINStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>🔢 Step 2: Security PIN</Text>
      <Text style={styles.stepDescription}>
        Choose a 6-digit PIN for quick access. Avoid predictable patterns.
      </Text>

      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>6-Digit PIN</Text>
        <TextInput
          style={[styles.textInput, styles.pinInput]}
          value={pin}
          onChangeText={(text) => setPin(text.replace(/[^0-9]/g, '').slice(0, 6))}
          placeholder="••••••"
          placeholderTextColor="#666"
          secureTextEntry
          keyboardType="numeric"
          maxLength={6}
        />
      </View>

      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Confirm PIN</Text>
        <TextInput
          style={[styles.textInput, styles.pinInput]}
          value={confirmPin}
          onChangeText={(text) => setConfirmPin(text.replace(/[^0-9]/g, '').slice(0, 6))}
          placeholder="••••••"
          placeholderTextColor="#666"
          secureTextEntry
          keyboardType="numeric"
          maxLength={6}
        />
      </View>

      <View style={styles.warningBox}>
        <Text style={styles.warningTitle}>⚠️ Avoid These PINs:</Text>
        <Text style={styles.warningText}>123456, 111111, 000000, birthdates, repeated digits</Text>
      </View>

      <TouchableOpacity 
        style={[styles.actionButton, (pin.length !== 6 || confirmPin.length !== 6) && styles.disabledButton]}
        onPress={handlePINSetup}
        disabled={pin.length !== 6 || confirmPin.length !== 6 || isLoading}
      >
        <Text style={styles.actionButtonText}>
          {isLoading ? 'Setting up...' : 'Next: Fake Dial (Optional)'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderFakeDialStep = () => (
    <ScrollView style={styles.stepContainer}>
      <Text style={styles.stepTitle}>🎭 Step 3: Fake Dial Protection</Text>
      <Text style={styles.stepDescription}>
        Create a fake passphrase that shows decoy content when someone forces you to unlock.
      </Text>

      <View style={styles.toggleContainer}>
        <Text style={styles.toggleLabel}>Enable Fake Dial Protection</Text>
        <Switch
          value={enableFakeDial}
          onValueChange={setEnableFakeDial}
          trackColor={{ false: '#666', true: '#ef4444' }}
          thumbColor={enableFakeDial ? '#fff' : '#ccc'}
        />
      </View>

      {enableFakeDial && (
        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Fake Passphrase</Text>
          <TextInput
            style={styles.textInput}
            value={fakePassphrase}
            onChangeText={setFakePassphrase}
            placeholder="Enter fake passphrase (shows decoy data)..."
            placeholderTextColor="#666"
            secureTextEntry
            autoCapitalize="none"
          />
        </View>
      )}

      <View style={styles.infoBox}>
        <Text style={styles.infoTitle}>🛡️ How Fake Dial Works:</Text>
        <Text style={styles.infoText}>
          • Real passphrase: Shows your actual vault data{'\n'}
          • Fake passphrase: Shows harmless decoy content{'\n'}
          • Protects you from coercion attacks{'\n'}
          • Both look completely authentic
        </Text>
      </View>

      <View style={styles.buttonRow}>
        <TouchableOpacity 
          style={[styles.actionButton, styles.skipButton]}
          onPress={skipFakeDial}
        >
          <Text style={styles.skipButtonText}>Skip This Step</Text>
        </TouchableOpacity>

        {enableFakeDial && (
          <TouchableOpacity 
            style={[styles.actionButton, !fakePassphrase && styles.disabledButton]}
            onPress={handleFakeDialSetup}
            disabled={!fakePassphrase || isLoading}
          >
            <Text style={styles.actionButtonText}>
              {isLoading ? 'Setting up...' : 'Complete Setup'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );

  const renderCompleteStep = () => (
    <View style={styles.completeContainer}>
      <Text style={styles.completeTitle}>✅ Setup Complete!</Text>
      <Text style={styles.completeDescription}>
        Your vault double security is now configured and ready to use.
      </Text>

      <View style={styles.summaryBox}>
        <Text style={styles.summaryTitle}>🔒 Security Summary:</Text>
        <Text style={styles.summaryItem}>✅ Master passphrase configured</Text>
        <Text style={styles.summaryItem}>✅ 6-digit PIN configured</Text>
        <Text style={styles.summaryItem}>
          {enableFakeDial ? '✅ Fake dial protection enabled' : '❌ Fake dial protection disabled'}
        </Text>
        <Text style={styles.summaryItem}>✅ Brute force protection active</Text>
      </View>

      <TouchableOpacity 
        style={styles.actionButton}
        onPress={onClose}
      >
        <Text style={styles.actionButtonText}>Start Using Vault</Text>
      </TouchableOpacity>
    </View>
  );

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>🔐 VAULT DOUBLE SECURITY</Text>
            <Text style={styles.subtitle}>Military-Grade Protection Setup</Text>
            {currentStep < 4 && (
              <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill, 
                  { width: `${(currentStep / 4) * 100}%` }
                ]} 
              />
            </View>
            <Text style={styles.progressText}>Step {currentStep} of 4</Text>
          </View>

          <View style={styles.content}>
            {currentStep === 1 && renderPassphraseStep()}
            {currentStep === 2 && renderPINStep()}
            {currentStep === 3 && renderFakeDialStep()}
            {currentStep === 4 && renderCompleteStep()}
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    justifyContent: 'center',
    padding: 15,
  },
  container: {
    backgroundColor: '#111',
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#ef4444',
    maxHeight: '95%',
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
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  subtitle: {
    color: '#fff',
    fontSize: 12,
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
    flex: 1,
  },
  stepTitle: {
    color: '#ef4444',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  stepDescription: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 20,
    lineHeight: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#222',
    color: '#fff',
    borderRadius: 10,
    paddingHorizontal: 15,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#444',
  },
  pinInput: {
    textAlign: 'center',
    fontSize: 24,
    letterSpacing: 8,
    fontFamily: 'monospace',
  },
  strengthContainer: {
    marginTop: 10,
  },
  strengthBar: {
    height: 4,
    backgroundColor: '#333',
    borderRadius: 2,
    overflow: 'hidden',
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthText: {
    fontSize: 12,
    marginTop: 5,
    textAlign: 'right',
  },
  securityTips: {
    backgroundColor: '#1a1a1a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  tipsTitle: {
    color: '#ffaa00',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  tipText: {
    color: '#ccc',
    fontSize: 12,
    marginBottom: 4,
  },
  warningBox: {
    backgroundColor: '#2a1a0a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#ff8800',
  },
  warningTitle: {
    color: '#ff8800',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  warningText: {
    color: '#ccc',
    fontSize: 12,
  },
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    padding: 15,
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
  },
  toggleLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  infoBox: {
    backgroundColor: '#0a1a0a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#00aa00',
  },
  infoTitle: {
    color: '#00ff00',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  infoText: {
    color: '#ccc',
    fontSize: 12,
    lineHeight: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 15,
    paddingHorizontal: 25,
    borderRadius: 25,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 5,
  },
  skipButton: {
    backgroundColor: '#666',
  },
  disabledButton: {
    backgroundColor: '#333',
    opacity: 0.5,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  skipButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  completeContainer: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  completeTitle: {
    color: '#00ff00',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  completeDescription: {
    color: '#ccc',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 22,
  },
  summaryBox: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    borderRadius: 15,
    marginBottom: 30,
    width: '100%',
    borderWidth: 1,
    borderColor: '#00aa00',
  },
  summaryTitle: {
    color: '#00ff00',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  summaryItem: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 8,
    paddingLeft: 10,
  },
});