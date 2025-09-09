import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Modal,
  ScrollView,
  TextInput,
  Alert,
  FlatList
} from 'react-native';
import omertaAPI from '../utils/api';

export default function GroupChatManager({ visible, onClose }) {
  const [groupChats, setGroupChats] = useState([]);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [selectedParticipants, setSelectedParticipants] = useState([]);
  const [availableContacts, setAvailableContacts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeChat, setActiveChat] = useState(null);

  useEffect(() => {
    if (visible) {
      loadGroupChats();
      loadAvailableContacts();
    }
  }, [visible]);

  const loadGroupChats = async () => {
    try {
      setIsLoading(true);
      const response = await omertaAPI.makeRequest('/group-chats/list', {
        method: 'GET'
      });
      setGroupChats(response.groups || []);
    } catch (error) {
      console.error('Failed to load group chats:', error);
      Alert.alert('Error', 'Failed to load group chats');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAvailableContacts = async () => {
    try {
      const response = await omertaAPI.makeRequest('/contacts/list', {
        method: 'GET'
      });
      setAvailableContacts(response.contacts || []);
    } catch (error) {
      console.error('Failed to load contacts:', error);
    }
  };

  const createGroupChat = async () => {
    if (!newGroupName.trim()) {
      Alert.alert('Error', 'Please enter a group name');
      return;
    }
    
    if (selectedParticipants.length === 0) {
      Alert.alert('Error', 'Please select at least one participant');
      return;
    }

    try {
      setIsLoading(true);
      
      const response = await omertaAPI.makeRequest('/group-chats/create', {
        method: 'POST',
        body: JSON.stringify({
          group_name: newGroupName,
          participants: selectedParticipants,
          security_settings: {
            vanish_protocol_enabled: true,
            message_expiry_default: 3600, // 1 hour
            encryption_level: 'maximum',
            allow_screenshots: false
          }
        })
      });

      setGroupChats([...groupChats, response.group]);
      setShowCreateGroup(false);
      setNewGroupName('');
      setSelectedParticipants([]);
      
      Alert.alert('Success', 'Group chat created successfully!');
      
    } catch (error) {
      console.error('Failed to create group chat:', error);
      Alert.alert('Error', 'Failed to create group chat');
    } finally {
      setIsLoading(false);
    }
  };

  const joinGroupChat = (group) => {
    setActiveChat(group);
    // Here you would navigate to the actual chat interface
    // For now, we'll just show an alert
    Alert.alert(
      'Join Group Chat',
      `Joining ${group.name} with ${group.participant_count} members and Vanish Protocol active.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Join', onPress: () => console.log('Joining group chat:', group.id) }
      ]
    );
  };

  const toggleParticipantSelection = (contact) => {
    if (selectedParticipants.includes(contact.id)) {
      setSelectedParticipants(selectedParticipants.filter(id => id !== contact.id));
    } else {
      setSelectedParticipants([...selectedParticipants, contact.id]);
    }
  };

  const renderGroupChatItem = ({ item }) => (
    <TouchableOpacity
      style={styles.groupChatItem}
      onPress={() => joinGroupChat(item)}
    >
      <View style={styles.groupChatHeader}>
        <View style={styles.groupChatIcon}>
          <Text style={styles.groupChatIconText}>
            {item.name.charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.groupChatInfo}>
          <Text style={styles.groupChatName}>{item.name}</Text>
          <Text style={styles.groupChatDetails}>
            {item.participant_count} members • {item.last_activity || 'No recent activity'}
          </Text>
        </View>
      </View>
      
      <View style={styles.groupChatMeta}>
        <View style={styles.securityBadges}>
          {item.vanish_protocol && (
            <View style={styles.securityBadge}>
              <Text style={styles.securityBadgeText}>👻</Text>
            </View>
          )}
          {item.encrypted && (
            <View style={styles.securityBadge}>
              <Text style={styles.securityBadgeText}>🔒</Text>
            </View>
          )}
        </View>
        
        {item.unread_count > 0 && (
          <View style={styles.unreadBadge}>
            <Text style={styles.unreadBadgeText}>{item.unread_count}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderContactItem = ({ item }) => (
    <TouchableOpacity
      style={[
        styles.contactItem,
        selectedParticipants.includes(item.id) && styles.selectedContact
      ]}
      onPress={() => toggleParticipantSelection(item)}
    >
      <View style={styles.contactInfo}>
        <View style={styles.contactAvatar}>
          <Text style={styles.contactAvatarText}>
            {item.name.charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.contactDetails}>
          <Text style={styles.contactName}>{item.name}</Text>
          <Text style={styles.contactStatus}>
            {item.verified ? '✅ Verified' : '⚠️ Unverified'}
          </Text>
        </View>
      </View>
      
      <View style={styles.selectionIndicator}>
        <Text style={styles.selectionIndicatorText}>
          {selectedParticipants.includes(item.id) ? '✓' : '○'}
        </Text>
      </View>
    </TouchableOpacity>
  );

  const renderCreateGroupModal = () => (
    <Modal visible={showCreateGroup} animationType="slide" transparent>
      <View style={styles.createGroupOverlay}>
        <View style={styles.createGroupContainer}>
          <View style={styles.createGroupHeader}>
            <Text style={styles.createGroupTitle}>Create Secure Group</Text>
            <TouchableOpacity
              style={styles.createGroupClose}
              onPress={() => {
                setShowCreateGroup(false);
                setNewGroupName('');
                setSelectedParticipants([]);
              }}
            >
              <Text style={styles.createGroupCloseText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.createGroupContent}>
            {/* Group Name */}
            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>Group Name</Text>
              <TextInput
                style={styles.textInput}
                value={newGroupName}
                onChangeText={setNewGroupName}
                placeholder="Enter group name..."
                placeholderTextColor="#666"
                maxLength={50}
              />
            </View>

            {/* Security Notice */}
            <View style={styles.securityNotice}>
              <Text style={styles.securityNoticeTitle}>🛡️ Security Features</Text>
              <Text style={styles.securityNoticeText}>
                • Vanish Protocol: Messages auto-destruct{'\n'}
                • E2EE: End-to-end encryption{'\n'}
                • No screenshots allowed{'\n'}
                • Perfect forward secrecy
              </Text>
            </View>

            {/* Participant Selection */}
            <View style={styles.participantSection}>
              <Text style={styles.inputLabel}>
                Select Participants ({selectedParticipants.length})
              </Text>
              
              {availableContacts.length === 0 ? (
                <View style={styles.noContactsContainer}>
                  <Text style={styles.noContactsText}>
                    No contacts available. Add contacts first.
                  </Text>
                </View>
              ) : (
                <FlatList
                  data={availableContacts}
                  keyExtractor={(item) => item.id}
                  renderItem={renderContactItem}
                  style={styles.contactsList}
                  maxHeight={200}
                />
              )}
            </View>

            {/* Create Button */}
            <TouchableOpacity
              style={[
                styles.createButton,
                (!newGroupName.trim() || selectedParticipants.length === 0) && styles.createButtonDisabled
              ]}
              onPress={createGroupChat}
              disabled={!newGroupName.trim() || selectedParticipants.length === 0 || isLoading}
            >
              <Text style={styles.createButtonText}>
                {isLoading ? 'Creating...' : 'Create Secure Group'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>👥 GROUP CHATS</Text>
            <Text style={styles.subtitle}>Secure Multi-Party Messaging</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.content}>
            {/* Action Buttons */}
            <View style={styles.actionButtonsContainer}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => setShowCreateGroup(true)}
              >
                <Text style={styles.actionButtonText}>➕ Create Group</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionButton, styles.refreshButton]}
                onPress={loadGroupChats}
              >
                <Text style={styles.actionButtonText}>🔄 Refresh</Text>
              </TouchableOpacity>
            </View>

            {/* Group Chats List */}
            <View style={styles.groupChatsSection}>
              <Text style={styles.sectionTitle}>Active Groups</Text>
              
              {isLoading ? (
                <View style={styles.loadingContainer}>
                  <Text style={styles.loadingText}>Loading groups...</Text>
                </View>
              ) : groupChats.length === 0 ? (
                <View style={styles.emptyContainer}>
                  <Text style={styles.emptyText}>No group chats yet</Text>
                  <Text style={styles.emptySubtext}>
                    Create your first secure group to start messaging
                  </Text>
                </View>
              ) : (
                <FlatList
                  data={groupChats}
                  keyExtractor={(item) => item.id}
                  renderItem={renderGroupChatItem}
                  style={styles.groupChatsList}
                  showsVerticalScrollIndicator={false}
                />
              )}
            </View>

            {/* Stats */}
            <View style={styles.statsContainer}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{groupChats.length}</Text>
                <Text style={styles.statLabel}>Active Groups</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>
                  {groupChats.reduce((sum, group) => sum + (group.participant_count || 0), 0)}
                </Text>
                <Text style={styles.statLabel}>Total Members</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>100%</Text>
                <Text style={styles.statLabel}>Encrypted</Text>
              </View>
            </View>
          </View>
        </View>
      </View>

      {/* Create Group Modal */}
      {renderCreateGroupModal()}
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
    flex: 1,
    padding: 20,
  },
  actionButtonsContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  actionButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 20,
    marginRight: 10,
    flex: 1,
    alignItems: 'center',
  },
  refreshButton: {
    backgroundColor: '#666',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  groupChatsSection: {
    flex: 1,
    marginBottom: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#666',
    fontSize: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    color: '#666',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  emptySubtext: {
    color: '#666',
    fontSize: 14,
    textAlign: 'center',
  },
  groupChatsList: {
    flex: 1,
  },
  groupChatItem: {
    backgroundColor: '#222',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#333',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  groupChatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  groupChatIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  groupChatIconText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  groupChatInfo: {
    flex: 1,
  },
  groupChatName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  groupChatDetails: {
    color: '#666',
    fontSize: 12,
  },
  groupChatMeta: {
    alignItems: 'flex-end',
  },
  securityBadges: {
    flexDirection: 'row',
    marginBottom: 5,
  },
  securityBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.3)',
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 5,
  },
  securityBadgeText: {
    fontSize: 12,
  },
  unreadBadge: {
    backgroundColor: '#ef4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  unreadBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#1a1a1a',
    padding: 15,
    borderRadius: 10,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    color: '#ef4444',
    fontSize: 20,
    fontWeight: 'bold',
  },
  statLabel: {
    color: '#666',
    fontSize: 12,
    marginTop: 5,
  },
  // Create Group Modal Styles
  createGroupOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    justifyContent: 'center',
    padding: 20,
  },
  createGroupContainer: {
    backgroundColor: '#111',
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#ef4444',
    maxHeight: '90%',
  },
  createGroupHeader: {
    backgroundColor: '#ef4444',
    padding: 20,
    borderTopLeftRadius: 13,
    borderTopRightRadius: 13,
    alignItems: 'center',
    position: 'relative',
  },
  createGroupTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  createGroupClose: {
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
  createGroupCloseText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  createGroupContent: {
    flex: 1,
    padding: 20,
  },
  inputSection: {
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
    marginBottom: 8,
  },
  securityNoticeText: {
    color: '#ccc',
    fontSize: 12,
    lineHeight: 16,
  },
  participantSection: {
    marginBottom: 20,
  },
  noContactsContainer: {
    backgroundColor: '#222',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
  },
  noContactsText: {
    color: '#666',
    fontSize: 14,
  },
  contactsList: {
    backgroundColor: '#222',
    borderRadius: 10,
    padding: 10,
  },
  contactItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 5,
  },
  selectedContact: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  contactInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  contactAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  contactAvatarText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  contactDetails: {
    flex: 1,
  },
  contactName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  contactStatus: {
    color: '#666',
    fontSize: 12,
    marginTop: 2,
  },
  selectionIndicator: {
    width: 30,
    height: 30,
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectionIndicatorText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: 'bold',
  },
  createButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
    marginTop: 10,
  },
  createButtonDisabled: {
    backgroundColor: '#333',
    opacity: 0.5,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});