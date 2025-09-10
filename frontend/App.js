import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, TextInput, Alert } from 'react-native';
import { useState, useEffect } from 'react';
import { useSecurityStore } from './src/state/security';
import threatDetector from './src/utils/threatDetection';
import autoRebootManager from './src/utils/autoReboot';
import VanishMessage from './src/components/VanishMessage';
import SecureChat from './src/components/SecureChat';
import DefconOnePanel from './src/components/DefconOnePanel';
import SteeloshShredder from './src/components/SteeloshShredder';
import ContactManager from './src/components/ContactManager';
import MatrixBackground from './src/components/MatrixBackground';
import RemoteKillSystem from './src/components/RemoteKillSystem';
import MessageExpirationSettings from './src/components/MessageExpirationSettings';
import FileSharing from './src/components/FileSharing';
import VoiceMessages from './src/components/VoiceMessages';

export default function App() {
  const [pin, setPin] = useState('');
  const [currentView, setCurrentView] = useState('auth'); // auth, main, demo, defcon
  const [threatStatus, setThreatStatus] = useState('normal');
  const [showDefconPanel, setShowDefconPanel] = useState(false);
  const [showSteeloshShredder, setShowSteeloshShredder] = useState(false);
  const [shredderTrigger, setShredderTrigger] = useState('manual');
  const [tapSequence, setTapSequence] = useState([]);
  const [lastTapTime, setLastTapTime] = useState(0);
  const [nextRebootTime, setNextRebootTime] = useState(null);
  const [rebootWarning, setRebootWarning] = useState(false);
  const [showContactManager, setShowContactManager] = useState(false);
  const [showRemoteKillSystem, setShowRemoteKillSystem] = useState(false);
  const [showMessageExpirationSettings, setShowMessageExpirationSettings] = useState(false);
  const [showFileSharing, setShowFileSharing] = useState(false);
  const [showVoiceMessages, setShowVoiceMessages] = useState(false);
  
  const { 
    isAuthenticated, 
    authenticate, 
    threatLevel,
    setThreatLevel,
    addThreat,
    startMonitoring,
    stopMonitoring,
    triggerPanicMode 
  } = useSecurityStore();

  // Initialize security systems
  useEffect(() => {
    // Initialize threat detection
    threatDetector.initialize().then(() => {
      threatDetector.onThreatDetected((analysis) => {
        console.log('🚨 Threat detected:', analysis);
        setThreatLevel(analysis.level);
        setThreatStatus(analysis.level);
        
        analysis.threats.forEach(threat => {
          addThreat(threat);
        });
        
        if (analysis.level === 'critical') {
          Alert.alert(
            '🚨 CRITICAL THREAT DETECTED',
            'Possible Pegasus/Graphite surveillance detected. OMERTÁ recommends immediate action.',
            [
              { 
                text: '🔥 STEELOS-Shredder', 
                style: 'destructive',
                onPress: () => {
                  setShredderTrigger('threat_detected');
                  setShowSteeloshShredder(true);
                }
              },
              { text: 'Activate DEFCON-1', onPress: () => setShowDefconPanel(true) },
              { text: 'Continue Monitoring', style: 'cancel' }
            ]
          );
        }
      });
    });

    // Initialize auto-reboot system
    autoRebootManager.initialize().then(() => {
      // Set up auto-reboot callbacks
      autoRebootManager.setCallbacks({
        onRebootScheduled: (time) => {
          setNextRebootTime(time);
          console.log(`🔄 Next reboot scheduled: ${time.toLocaleString()}`);
        },
        onRebootWarning: () => {
          setRebootWarning(true);
        },
        onRebootExecuted: () => {
          // Reset to authentication screen
          setCurrentView('auth');
          setIsAuthenticated(false);
          setRebootWarning(false);
        }
      });
    });

    return () => {
      threatDetector.stopMonitoring();
      autoRebootManager.stop();
    };
  }, []);

  const handleAuthentication = async () => {
    // Check for panic PIN first
    if (pin === '000000') {
      setShredderTrigger('panic_pin');
      setShowSteeloshShredder(true);
      setPin('');
      return;
    }
    
    const success = await authenticate(pin);
    if (success) {
      setCurrentView('main');
      startMonitoring();
      threatDetector.startMonitoring();
      
      // Enable clipboard restrictions on successful authentication
      clipboardSecurityManager.enterSecureArea('main_app');
      setClipboardRestricted(true);
      console.log('🔒 Entered secure OMERTÁ environment - clipboard restricted');
    } else {
      Alert.alert('Authentication Failed', 'Invalid PIN entered');
      setPin('');
    }
  };

  const handleTapSequence = () => {
    const now = Date.now();
    
    // Reset sequence if more than 2 seconds between taps
    if (now - lastTapTime > 2000) {
      setTapSequence([1]);
    } else {
      const newSequence = [...tapSequence, tapSequence.length + 1];
      
      // Check for 4-4-4-2-2 pattern completion
      if (newSequence.length === 4 && newSequence[3] !== 4) {
        setTapSequence([1]); // Reset if not 4
      } else if (newSequence.length === 8 && newSequence[7] !== 4) {
        setTapSequence([1]); // Reset if not 4
      } else if (newSequence.length === 12 && newSequence[11] !== 4) {
        setTapSequence([1]); // Reset if not 4
      } else if (newSequence.length === 14 && newSequence[13] !== 2) {
        setTapSequence([1]); // Reset if not 2
      } else if (newSequence.length === 16) {
        if (newSequence[15] === 2) {
          // Success! 4-4-4-2-2 sequence completed
          console.log('🚨 DEFCON-1 access sequence activated');
          setShowDefconPanel(true);
          setTapSequence([]);
        } else {
          setTapSequence([1]); // Reset
        }
      } else {
        setTapSequence(newSequence);
      }
    }
    
    setLastTapTime(now);
  };

  const handlePINInput = (digit) => {
    if (pin.length < 6) {
      setPin(pin + digit);
    }
  };

  const clearPIN = () => {
    setPin('');
  };

  // Authentication Screen
  if (!isAuthenticated) {
    return (
      <View style={styles.container}>
        <MatrixBackground intensity={0.2} color="#ef4444" />
        <Text style={styles.title}>🔒 OMERTÁ</Text>
        <Text style={styles.subtitle}>World's Most Secure Messaging</Text>
        <Text style={styles.tagline}>Making Pegasus Irrelevant</Text>
        
        <View style={styles.pinContainer}>
          <Text style={styles.pinLabel}>Enter Security PIN</Text>
          <Text style={styles.pinDisplay}>
            {pin.replace(/./g, '●')} {pin.length < 6 && '_'.repeat(6 - pin.length)}
          </Text>
          
          <View style={styles.keypad}>
            {[1,2,3,4,5,6,7,8,9,0].map(digit => (
              <TouchableOpacity 
                key={digit}
                style={styles.keypadButton}
                onPress={() => handlePINInput(digit.toString())}
              >
                <Text style={styles.keypadText}>{digit}</Text>
              </TouchableOpacity>
            ))}
          </View>
          
          <View style={styles.pinActions}>
            <TouchableOpacity style={styles.clearButton} onPress={clearPIN}>
              <Text style={styles.clearButtonText}>Clear</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.authButton, pin.length === 6 && styles.authButtonActive]}
              onPress={handleAuthentication}
              disabled={pin.length !== 6}
            >
              <Text style={styles.authButtonText}>Authenticate</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        <Text style={styles.footer}>Nuclear Reset Build v2.0</Text>
        <Text style={styles.hint}>PIN: 123456 | Panic: 000000</Text>
        <StatusBar style="light" />
      </View>
    );
  }

  // Main Application
  return (
    <View style={styles.mainContainer}>
      <MatrixBackground intensity={threatLevel === 'critical' ? 0.8 : 0.1} color="#ef4444" />
      <TouchableOpacity 
        style={[styles.header, threatLevel !== 'normal' && styles.threatHeader]}
        onPress={handleTapSequence}
        activeOpacity={1}
      >
        <Text style={styles.headerTitle}>🔒 OMERTÁ</Text>
        <Text style={styles.headerSubtitle}>NUCLEAR RESET BUILD</Text>
        {threatLevel !== 'normal' && (
          <Text style={styles.threatIndicator}>
            🚨 THREAT LEVEL: {threatLevel.toUpperCase()}
          </Text>
        )}
        {tapSequence.length > 0 && (
          <Text style={styles.tapSequenceIndicator}>
            Sequence: {tapSequence.join('-')} {tapSequence.length >= 12 ? '(Almost there...)' : ''}
          </Text>
        )}
      </TouchableOpacity>
      
      <ScrollView style={styles.content}>
        <View style={styles.statusPanel}>
          <Text style={styles.statusTitle}>🛡️ SECURITY STATUS</Text>
          <View style={styles.statusGrid}>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Vanish Protocol</Text>
              <Text style={styles.statusValue}>✅ ACTIVE</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Threat Detection</Text>
              <Text style={[styles.statusValue, { color: getThreatColor(threatLevel) }]}>
                {threatLevel.toUpperCase()}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>DEFCON Level</Text>
              <Text style={styles.statusValue}>5 - NORMAL</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>STEELOS-Shredder</Text>
              <Text style={styles.statusValue}>🔥 READY</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Auto-Reboot</Text>
              <Text style={styles.statusValue}>
                {nextRebootTime ? 
                  `⏰ ${nextRebootTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}` : 
                  '🔄 ACTIVE'
                }
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Next Schedule</Text>
              <Text style={styles.statusValue}>
                {rebootWarning ? '⚠️ WARNING' : '2AM/2PM'}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Msg Expiration</Text>
              <Text style={styles.statusValue}>
                {messageExpiryEnabled ? '⏰ ACTIVE' : '❌ DISABLED'}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Clipboard</Text>
              <Text style={styles.statusValue}>
                {clipboardRestricted ? '🚫 RESTRICTED' : '✅ NORMAL'}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Vault Security</Text>
              <Text style={styles.statusValue}>
                {fakeDialMode ? '🎭 FAKE MODE' : vaultUnlocked ? '🔓 UNLOCKED' : vaultConfigured ? '🔒 LOCKED' : '⚙️ SETUP'}
              </Text>
            </View>
          </View>
          
          {/* Message Expiry Settings Access */}
          <TouchableOpacity 
            style={styles.statusSettingsButton}
            onPress={() => setShowMessageExpirationSettings(true)}
          >
            <Text style={styles.statusSettingsText}>⏰ Message Expiry Settings</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity 
          style={styles.actionButton}
          onPress={() => setCurrentView('chat')}
        >
          <Text style={styles.actionButtonText}>💬 Open Secure Chat</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#28a745' }]}
          onPress={() => setShowContactManager(true)}
        >
          <Text style={styles.actionButtonText}>📇 Secure Contacts</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#ef4444' }]}
          onPress={() => setShowMessageExpirationSettings(true)}
        >
          <Text style={styles.actionButtonText}>⏰ Message Expiry Settings</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#9333ea' }]}
          onPress={() => setShowFileSharing(true)}
        >
          <Text style={styles.actionButtonText}>📁 File Sharing</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#059669' }]}
          onPress={() => setShowVoiceMessages(true)}
        >
          <Text style={styles.actionButtonText}>🎤 Voice Messages</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#ff4500' }]}
          onPress={() => setShowRemoteKillSystem(true)}
        >
          <Text style={styles.actionButtonText}>🎯 Remote Kill System</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#666' }]}
          onPress={() => setCurrentView('demo')}
        >
          <Text style={styles.actionButtonText}>🚀 Demo Vanish Protocol</Text>
        </TouchableOpacity>

        {currentView === 'chat' && (
          <View style={styles.chatSection}>
            <SecureChat />
          </View>
        )}

        {currentView === 'demo' && (
          <View style={styles.demoSection}>
            <Text style={styles.demoTitle}>🥇 VANISH PROTOCOL DEMO</Text>
            <Text style={styles.demoSubtitle}>Gold Standard - Safer than Signal</Text>
            
            <VanishMessage 
              messageId="demo1"
              initialContent="This message will self-destruct after reading. This is OMERTÁ-SECURE'S VANISH PROTOCOL - making message content unextractable even if Pegasus infects your device."
              ttl={60000}
            />
            
            <VanishMessage 
              messageId="demo2"
              initialContent="🔗 Hidden Link Test: https://secure-channel.omerta/classified-intel-xyz123 - Links are encrypted behind chat bubbles, invisible to surveillance."
              ttl={45000}
            />
          </View>
        )}

        <View style={styles.features}>
          <Text style={styles.featureTitle}>🚀 ACTIVE DEFENSES:</Text>
          <Text style={styles.feature}>🛡️ RAM-only message storage</Text>
          <Text style={styles.feature}>👁️ One-time read protection</Text>
          <Text style={styles.feature}>🔗 Encrypted hidden links</Text>
          <Text style={styles.feature}>📱 Screenshot resistance</Text>
          <Text style={styles.feature}>🔍 Real-time threat detection</Text>
          <Text style={styles.feature}>🏥 Behavioral anomaly analysis</Text>
          <Text style={styles.feature}>🚨 Emergency protocols</Text>
          <Text style={styles.feature}>⚛️ DEFCON-1 two-person integrity</Text>
        </View>

        <TouchableOpacity 
          style={[styles.panicButton, { marginBottom: 20 }]}
          onPress={() => {
            setShredderTrigger('emergency_nuke');
            setShowSteeloshShredder(true);
          }}
        >
          <Text style={styles.panicButtonText}>🔥 STEELOS-SHREDDER</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.defconButton, { marginBottom: 100 }]}
          onPress={() => setShowDefconPanel(true)}
        >
          <Text style={styles.defconButtonText}>🚨 DEFCON-1 PROTOCOL</Text>
          <Text style={styles.defconButtonSubtext}>
            Secret Access: Tap header 4-4-4-2-2 times
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* DEFCON-1 Panel */}
      <DefconOnePanel 
        visible={showDefconPanel}
        onClose={() => setShowDefconPanel(false)}
      />

      {/* STEELOS-Shredder Modal */}
      <SteeloshShredder
        visible={showSteeloshShredder}
        triggerType={shredderTrigger}
        onClose={() => setShowSteeloshShredder(false)}
      />

      {/* Contact Manager Modal */}
      <ContactManager
        visible={showContactManager}
        onClose={() => setShowContactManager(false)}
      />

      {/* Remote Kill System Modal */}
      <RemoteKillSystem
        visible={showRemoteKillSystem}
        onClose={() => setShowRemoteKillSystem(false)}
        targetDevice={{
          id: 'target_device_classified',
          oid: 'target_oid_redacted'
        }}
      />
      
      {/* Message Expiration Settings Modal */}
      <MessageExpirationSettings
        visible={showMessageExpirationSettings}
        onClose={() => setShowMessageExpirationSettings(false)}
        onExpirySelected={(minutes) => {
          console.log(`Message expiry set to: ${minutes ? minutes + ' minutes' : 'disabled'}`);
          Alert.alert('Settings Updated', minutes ? `Messages will expire after ${minutes} minutes` : 'Message expiration disabled');
        }}
        currentExpiryMinutes={null}
      />

      {/* Vault Double Security Setup Modal */}
      <VaultDoubleSecuritySetup
        visible={showVaultSetup}
        onClose={() => setShowVaultSetup(false)}
        onSetupComplete={() => {
          setVaultConfigured(true);
          setShowVaultSetup(false);
          Alert.alert('Setup Complete', 'Vault double security is now configured. You can now access your secure vault.');
        }}
      />

      {/* Vault Double Security Unlock Modal */}
      <VaultDoubleSecurityUnlock
        visible={showVaultUnlock}
        onClose={() => setShowVaultUnlock(false)}
        onUnlocked={() => {
          setVaultUnlocked(true);
          setFakeDialMode(false);
          console.log('✅ Vault unlocked successfully');
        }}
        onFakeDialActivated={() => {
          setFakeDialMode(true);
          setVaultUnlocked(false);
          console.log('🎭 Fake dial mode activated - showing decoy content');
        }}
      />
      
      {/* LiveKit Video Call Modal - Temporarily disabled
      <LiveKitVideoCall
        visible={showVideoCall}
        onClose={() => {
          setShowVideoCall(false);
          setVideoCallConfig(null);
        }}
        roomConfig={videoCallConfig}
        securitySettings={{
          enableFaceBlur: true,
          enableVoiceScramble: true
        }}
      />
      */}
      
      {/* Group Chat Manager Modal */}
      <GroupChatManager
        visible={showGroupChatManager}
        onClose={() => setShowGroupChatManager(false)}
      />
      
      {/* File Sharing Modal */}
      <FileSharing
        visible={showFileSharing}
        onClose={() => setShowFileSharing(false)}
      />

      {/* Voice Messages Modal */}
      <VoiceMessages
        visible={showVoiceMessages}
        onClose={() => setShowVoiceMessages(false)}
      />
      
      <StatusBar style="light" />
    </View>
  );
}

function getThreatColor(level) {
  switch(level) {
    case 'critical': return '#ff0000';
    case 'high': return '#ff4444';
    case 'medium': return '#ff8800';
    case 'low': return '#ffaa00';
    default: return '#00ff00';
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#ef4444',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 5,
  },
  tagline: {
    fontSize: 16,
    color: '#ef4444',
    textAlign: 'center',
    marginBottom: 30,
    fontStyle: 'italic',
  },
  pinContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  pinLabel: {
    color: '#fff',
    fontSize: 18,
    marginBottom: 10,
  },
  pinDisplay: {
    color: '#ef4444',
    fontSize: 24,
    fontFamily: 'monospace',
    marginBottom: 20,
    letterSpacing: 10,
  },
  keypad: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    width: 240,
    marginBottom: 20,
  },
  keypadButton: {
    backgroundColor: '#222',
    width: 60,
    height: 60,
    margin: 5,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#444',
  },
  keypadText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  pinActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: 200,
  },
  clearButton: {
    backgroundColor: '#666',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  clearButtonText: {
    color: '#fff',
    fontSize: 16,
  },
  authButton: {
    backgroundColor: '#333',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  authButtonActive: {
    backgroundColor: '#ef4444',
  },
  authButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    color: '#666',
    fontSize: 12,
    position: 'absolute',
    bottom: 40,
  },
  hint: {
    color: '#444',
    fontSize: 10,
    position: 'absolute',
    bottom: 20,
  },
  mainContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    backgroundColor: '#111',
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: '#ef4444',
  },
  threatHeader: {
    backgroundColor: '#2a0a0a',
    borderBottomColor: '#ff0000',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ef4444',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#fff',
    letterSpacing: 2,
  },
  threatIndicator: {
    color: '#ff0000',
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 5,
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  statusPanel: {
    backgroundColor: '#111',
    margin: 20,
    borderRadius: 15,
    padding: 20,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  statusTitle: {
    color: '#ef4444',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 15,
  },
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statusItem: {
    width: '48%',
    marginBottom: 10,
  },
  statusLabel: {
    color: '#888',
    fontSize: 12,
    marginBottom: 2,
  },
  statusValue: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  statusSettingsButton: {
    backgroundColor: '#333',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 10,
    marginTop: 10,
    alignItems: 'center',
  },
  statusSettingsText: {
    color: '#ef4444',
    fontSize: 12,
    fontWeight: 'bold',
  },
  chatSection: {
    flex: 1,
    margin: 10,
    backgroundColor: '#000',
    borderRadius: 15,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  demoSection: {
    margin: 20,
  },
  demoTitle: {
    color: '#ffd700',
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 5,
  },
  demoSubtitle: {
    color: '#ef4444',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
  },
  features: {
    backgroundColor: '#111',
    margin: 20,
    padding: 20,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  featureTitle: {
    fontSize: 18,
    color: '#ef4444',
    fontWeight: 'bold',
    marginBottom: 15,
  },
  feature: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 8,
    paddingLeft: 10,
  },
  actionButton: {
    backgroundColor: '#ef4444',
    margin: 20,
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  panicButton: {
    backgroundColor: '#800000',
    margin: 20,
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#ff0000',
  },
  panicButtonText: {
    color: '#ff0000',
    fontSize: 18,
    fontWeight: 'bold',
  },
  defconButton: {
    backgroundColor: '#1a0a0a',
    margin: 20,
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#ef4444',
  },
  defconButtonText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: 'bold',
  },
  defconButtonSubtext: {
    color: '#666',
    fontSize: 10,
    marginTop: 5,
  },
  tapSequenceIndicator: {
    color: '#ef4444',
    fontSize: 10,
    marginTop: 5,
    textAlign: 'center',
  },
});
