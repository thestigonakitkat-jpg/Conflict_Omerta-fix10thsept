import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Modal,
  Slider,
  Switch,
  Alert
} from 'react-native';
import messageExpirationManager from '../utils/messageExpiration';

export default function MessageExpirationSettings({ 
  visible, 
  onClose, 
  onExpirySelected,
  currentExpiryMinutes = null
}) {
  const [selectedIndex, setSelectedIndex] = useState(5); // Default to 1 hour
  const [isEnabled, setIsEnabled] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [sliderOptions, setSliderOptions] = useState([]);

  useEffect(() => {
    // Load slider options from the manager
    const options = messageExpirationManager.getSliderOptions();
    setSliderOptions(options);
    
    // Set current expiry if provided
    if (currentExpiryMinutes) {
      const index = options.findIndex(opt => opt.minutes === currentExpiryMinutes);
      if (index !== -1) {
        setSelectedIndex(index);
      }
    }
  }, [currentExpiryMinutes]);

  const handleConfirm = () => {
    if (!isEnabled) {
      onExpirySelected(null);
    } else {
      const selectedOption = sliderOptions[selectedIndex];
      onExpirySelected(selectedOption.minutes);
    }
    onClose();
  };

  const setDefaultExpiry = async () => {
    try {
      const selectedOption = sliderOptions[selectedIndex];
      await messageExpirationManager.setDefaultExpiry(selectedOption.minutes / (7 * 24 * 60)); // Convert to weeks
      Alert.alert(
        '✅ Default Set',
        `Default message expiry set to ${selectedOption.label}`,
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to set default expiry');
    }
  };

  const forceCleanup = async () => {
    try {
      const result = await messageExpirationManager.forceCleanup();
      Alert.alert(
        '🧹 Cleanup Complete',
        `Expired ${result.expired} messages. ${result.active} messages remaining.`,
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to run cleanup');
    }
  };

  const getTimeDescription = () => {
    if (!isEnabled) return 'Never expire (Default: 6 weeks)';
    if (selectedIndex >= 0 && selectedIndex < sliderOptions.length) {
      return sliderOptions[selectedIndex].label;
    }
    return '1 hour';
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>⏰ MESSAGE EXPIRATION</Text>
            <Text style={styles.subtitle}>Auto-Purge Security System</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.content}>
            {/* Enable/Disable Toggle */}
            <View style={styles.toggleContainer}>
              <Text style={styles.toggleLabel}>Enable Message Expiration</Text>
              <Switch
                value={isEnabled}
                onValueChange={setIsEnabled}
                trackColor={{ false: '#666', true: '#ef4444' }}
                thumbColor={isEnabled ? '#fff' : '#ccc'}
              />
            </View>

            {isEnabled && (
              <>
                {/* Current Selection */}
                <View style={styles.selectionContainer}>
                  <Text style={styles.selectionLabel}>Current Setting:</Text>
                  <Text style={styles.selectionValue}>{getTimeDescription()}</Text>
                </View>

                {/* Slider */}
                <View style={styles.sliderContainer}>
                  <Text style={styles.sliderLabel}>Expiry Time (1 minute to 1 week)</Text>
                  <Slider
                    style={styles.slider}
                    minimumValue={0}
                    maximumValue={sliderOptions.length - 1}
                    value={selectedIndex}
                    onValueChange={(value) => setSelectedIndex(Math.round(value))}
                    step={1}
                    minimumTrackTintColor="#ef4444"
                    maximumTrackTintColor="#666"
                    thumbStyle={{ backgroundColor: '#ef4444' }}
                  />
                  
                  <View style={styles.sliderLabels}>
                    <Text style={styles.sliderLabelText}>1m</Text>
                    <Text style={styles.sliderLabelText}>1w</Text>
                  </View>
                </View>

                {/* Quick Options */}
                <View style={styles.quickOptions}>
                  <Text style={styles.quickOptionsTitle}>Quick Select:</Text>
                  <View style={styles.quickButtonsRow}>
                    <TouchableOpacity 
                      style={[styles.quickButton, selectedIndex === 0 && styles.quickButtonActive]}
                      onPress={() => setSelectedIndex(0)}
                    >
                      <Text style={styles.quickButtonText}>1m</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.quickButton, selectedIndex === 2 && styles.quickButtonActive]}
                      onPress={() => setSelectedIndex(2)}
                    >
                      <Text style={styles.quickButtonText}>15m</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.quickButton, selectedIndex === 5 && styles.quickButtonActive]}
                      onPress={() => setSelectedIndex(5)}
                    >
                      <Text style={styles.quickButtonText}>1h</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.quickButton, selectedIndex === 8 && styles.quickButtonActive]}
                      onPress={() => setSelectedIndex(8)}
                    >
                      <Text style={styles.quickButtonText}>1d</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.quickButton, selectedIndex === 10 && styles.quickButtonActive]}
                      onPress={() => setSelectedIndex(10)}
                    >
                      <Text style={styles.quickButtonText}>1w</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </>
            )}

            {/* Advanced Options */}
            <TouchableOpacity 
              style={styles.advancedToggle}
              onPress={() => setShowAdvanced(!showAdvanced)}
            >
              <Text style={styles.advancedToggleText}>
                {showAdvanced ? '▼' : '▶'} Advanced Options
              </Text>
            </TouchableOpacity>

            {showAdvanced && (
              <View style={styles.advancedOptions}>
                <TouchableOpacity style={styles.advancedButton} onPress={setDefaultExpiry}>
                  <Text style={styles.advancedButtonText}>Set as Default</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.advancedButton} onPress={forceCleanup}>
                  <Text style={styles.advancedButtonText}>🧹 Force Cleanup Now</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Security Notice */}
            <View style={styles.securityNotice}>
              <Text style={styles.securityNoticeTitle}>🛡️ SECURITY NOTICE</Text>
              <Text style={styles.securityNoticeText}>
                Messages expire automatically for your protection. Default expiry is 6 weeks. 
                Very short expiry times (1-5 minutes) provide maximum security but may impact usability.
              </Text>
            </View>

            {/* Confirm Button */}
            <TouchableOpacity style={styles.confirmButton} onPress={handleConfirm}>
              <Text style={styles.confirmButtonText}>
                {isEnabled ? `✅ Set to ${getTimeDescription()}` : '❌ Disable Expiration'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
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
  content: {
    padding: 20,
  },
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  toggleLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  selectionContainer: {
    backgroundColor: '#1a1a1a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    alignItems: 'center',
  },
  selectionLabel: {
    color: '#666',
    fontSize: 12,
    marginBottom: 5,
  },
  selectionValue: {
    color: '#ef4444',
    fontSize: 18,
    fontWeight: 'bold',
  },
  sliderContainer: {
    marginBottom: 20,
  },
  sliderLabel: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 10,
    textAlign: 'center',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
  },
  sliderLabelText: {
    color: '#666',
    fontSize: 12,
  },
  quickOptions: {
    marginBottom: 20,
  },
  quickOptionsTitle: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 10,
    textAlign: 'center',
  },
  quickButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  quickButton: {
    backgroundColor: '#333',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: '#666',
  },
  quickButtonActive: {
    backgroundColor: '#ef4444',
    borderColor: '#fff',
  },
  quickButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  advancedToggle: {
    alignItems: 'center',
    paddingVertical: 10,
    marginBottom: 10,
  },
  advancedToggleText: {
    color: '#666',
    fontSize: 14,
  },
  advancedOptions: {
    backgroundColor: '#1a1a1a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  advancedButton: {
    backgroundColor: '#333',
    paddingVertical: 10,
    borderRadius: 10,
    marginBottom: 10,
    alignItems: 'center',
  },
  advancedButtonText: {
    color: '#fff',
    fontSize: 14,
  },
  securityNotice: {
    backgroundColor: '#1a0a0a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  securityNoticeTitle: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  securityNoticeText: {
    color: '#ccc',
    fontSize: 12,
    lineHeight: 16,
  },
  confirmButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});