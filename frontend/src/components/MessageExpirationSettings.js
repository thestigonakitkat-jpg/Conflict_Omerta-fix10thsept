import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Modal,
  Alert
} from 'react-native';

export default function MessageExpirationSettings({ 
  visible, 
  onClose, 
  onExpirySelected,
  currentExpiryMinutes = null
}) {
  const [selectedMinutes, setSelectedMinutes] = useState(60); // Default 1 hour

  const timeOptions = [
    { minutes: 1, label: '1 minute' },
    { minutes: 5, label: '5 minutes' },
    { minutes: 15, label: '15 minutes' },
    { minutes: 60, label: '1 hour' },
    { minutes: 240, label: '4 hours' },
    { minutes: 1440, label: '1 day' },
    { minutes: 10080, label: '1 week' }
  ];

  const handleConfirm = () => {
    onExpirySelected(selectedMinutes);
    onClose();
  };

  const handleDisable = () => {
    onExpirySelected(null);
    onClose();
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>⏰ MESSAGE EXPIRATION</Text>
            <Text style={styles.subtitle}>Auto-Delete Security</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.content}>
            <Text style={styles.description}>
              Choose how long messages should remain before auto-deletion:
            </Text>

            <View style={styles.optionsContainer}>
              {timeOptions.map((option) => (
                <TouchableOpacity
                  key={option.minutes}
                  style={[
                    styles.optionButton,
                    selectedMinutes === option.minutes && styles.selectedOption
                  ]}
                  onPress={() => setSelectedMinutes(option.minutes)}
                >
                  <Text style={[
                    styles.optionText,
                    selectedMinutes === option.minutes && styles.selectedOptionText
                  ]}>
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.buttonsContainer}>
              <TouchableOpacity 
                style={[styles.actionButton, styles.disableButton]}
                onPress={handleDisable}
              >
                <Text style={styles.buttonText}>❌ Disable Expiration</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={styles.actionButton}
                onPress={handleConfirm}
              >
                <Text style={styles.buttonText}>
                  ✅ Set to {timeOptions.find(opt => opt.minutes === selectedMinutes)?.label}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.securityNotice}>
              <Text style={styles.securityNoticeTitle}>🛡️ SECURITY INFO</Text>
              <Text style={styles.securityNoticeText}>
                Messages will be automatically deleted after the selected time for your security.
              </Text>
            </View>
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