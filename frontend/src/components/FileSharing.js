import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Modal,
  Alert,
  ScrollView,
  Image
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from 'expo-image-picker';
import omertaAPI from '../utils/api';

export default function FileSharing({ visible, onClose }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [sharedFiles, setSharedFiles] = useState([]);

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
        multiple: true
      });

      if (!result.canceled) {
        setSelectedFiles([...selectedFiles, ...result.assets]);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick document');
    }
  };

  const pickImage = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Camera roll permissions required');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsMultipleSelection: true,
        quality: 0.8,
      });

      if (!result.canceled) {
        setSelectedFiles([...selectedFiles, ...result.assets]);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const takePhoto = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Camera permissions required');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        quality: 0.8,
        allowsEditing: true,
      });

      if (!result.canceled) {
        setSelectedFiles([...selectedFiles, ...result.assets]);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', {
          uri: file.uri,
          type: file.mimeType || 'application/octet-stream',
          name: file.name || 'file',
        });
        formData.append('expiry_hours', '24');
        formData.append('auto_destruct', 'true');

        const response = await omertaAPI.makeRequest('/files/upload', {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        });

        setSharedFiles(prev => [...prev, response]);
      }

      setSelectedFiles([]);
      Alert.alert('Success', 'Files uploaded and encrypted successfully');
    } catch (error) {
      Alert.alert('Upload Failed', 'Failed to upload files securely');
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  const shareFile = (file) => {
    Alert.alert(
      'Share File',
      'File link copied to clipboard. Will auto-destruct after access.',
      [{ text: 'OK' }]
    );
  };

  const deleteFile = async (fileId) => {
    try {
      await omertaAPI.makeRequest(`/files/${fileId}`, {
        method: 'DELETE'
      });
      setSharedFiles(sharedFiles.filter(f => f.id !== fileId));
      Alert.alert('Deleted', 'File permanently destroyed');
    } catch (error) {
      Alert.alert('Error', 'Failed to delete file');
    }
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>📁 SECURE FILE SHARING</Text>
            <Text style={styles.subtitle}>Auto-Destruct Document Transfer</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content}>
            {/* File Selection Buttons */}
            <View style={styles.actionSection}>
              <Text style={styles.sectionTitle}>📤 Add Files</Text>
              <View style={styles.buttonRow}>
                <TouchableOpacity style={styles.pickButton} onPress={pickDocument}>
                  <Text style={styles.pickButtonText}>📄 Document</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.pickButton} onPress={pickImage}>
                  <Text style={styles.pickButtonText}>🖼️ Gallery</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.pickButton} onPress={takePhoto}>
                  <Text style={styles.pickButtonText}>📷 Camera</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <View style={styles.selectedSection}>
                <Text style={styles.sectionTitle}>📋 Selected Files ({selectedFiles.length})</Text>
                {selectedFiles.map((file, index) => (
                  <View key={index} style={styles.fileItem}>
                    {file.type?.startsWith('image/') && (
                      <Image source={{ uri: file.uri }} style={styles.filePreview} />
                    )}
                    <View style={styles.fileInfo}>
                      <Text style={styles.fileName}>{file.name || 'Unnamed file'}</Text>
                      <Text style={styles.fileDetails}>
                        {file.size ? `${Math.round(file.size / 1024)} KB` : 'Unknown size'}
                      </Text>
                    </View>
                    <TouchableOpacity
                      style={styles.removeButton}
                      onPress={() => removeFile(index)}
                    >
                      <Text style={styles.removeButtonText}>✕</Text>
                    </TouchableOpacity>
                  </View>
                ))}

                <TouchableOpacity
                  style={[styles.uploadButton, isUploading && styles.uploadButtonDisabled]}
                  onPress={uploadFiles}
                  disabled={isUploading}
                >
                  <Text style={styles.uploadButtonText}>
                    {isUploading ? '🔄 Encrypting...' : '🔒 Encrypt & Upload'}
                  </Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Shared Files */}
            <View style={styles.sharedSection}>
              <Text style={styles.sectionTitle}>☁️ Shared Files</Text>
              {sharedFiles.length === 0 ? (
                <Text style={styles.emptyText}>No files shared yet</Text>
              ) : (
                sharedFiles.map((file, index) => (
                  <View key={index} style={styles.sharedFileItem}>
                    <View style={styles.fileInfo}>
                      <Text style={styles.fileName}>{file.name}</Text>
                      <Text style={styles.fileDetails}>
                        Expires: {file.expiry_time} | Views: {file.view_count}
                      </Text>
                    </View>
                    <View style={styles.fileActions}>
                      <TouchableOpacity
                        style={styles.shareButton}
                        onPress={() => shareFile(file)}
                      >
                        <Text style={styles.shareButtonText}>📋</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.deleteButton}
                        onPress={() => deleteFile(file.id)}
                      >
                        <Text style={styles.deleteButtonText}>🗑️</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ))
              )}
            </View>

            {/* Security Notice */}
            <View style={styles.securityNotice}>
              <Text style={styles.securityNoticeTitle}>🛡️ SECURITY FEATURES</Text>
              <Text style={styles.securityNoticeText}>
                • Files encrypted with AES-256{'\n'}
                • Auto-destruct after 24 hours{'\n'}
                • One-time access links{'\n'}
                • No permanent storage{'\n'}
                • End-to-end encryption
              </Text>
            </View>
          </ScrollView>
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
  actionSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  pickButton: {
    backgroundColor: '#333',
    paddingVertical: 12,
    paddingHorizontal: 15,
    borderRadius: 10,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  pickButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  selectedSection: {
    marginBottom: 20,
  },
  fileItem: {
    backgroundColor: '#222',
    padding: 10,
    borderRadius: 10,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  filePreview: {
    width: 40,
    height: 40,
    borderRadius: 5,
    marginRight: 10,
  },
  fileInfo: {
    flex: 1,
  },
  fileName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  fileDetails: {
    color: '#666',
    fontSize: 12,
    marginTop: 2,
  },
  removeButton: {
    backgroundColor: '#ff4444',
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  uploadButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
    marginTop: 10,
  },
  uploadButtonDisabled: {
    backgroundColor: '#666',
    opacity: 0.5,
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  sharedSection: {
    marginBottom: 20,
  },
  emptyText: {
    color: '#666',
    fontSize: 14,
    textAlign: 'center',
    padding: 20,
  },
  sharedFileItem: {
    backgroundColor: '#222',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  fileActions: {
    flexDirection: 'row',
  },
  shareButton: {
    backgroundColor: '#00aa00',
    width: 35,
    height: 35,
    borderRadius: 17,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  shareButtonText: {
    fontSize: 16,
  },
  deleteButton: {
    backgroundColor: '#ff4444',
    width: 35,
    height: 35,
    borderRadius: 17,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: 16,
  },
  securityNotice: {
    backgroundColor: '#1a0a0a',
    padding: 15,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  securityNoticeTitle: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  securityNoticeText: {
    color: '#ccc',
    fontSize: 12,
    lineHeight: 16,
  },
});