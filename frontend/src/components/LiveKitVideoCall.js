import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Modal,
  Alert,
  Dimensions,
  Switch
} from 'react-native';
import { 
  Room, 
  RoomEvent, 
  Track, 
  TrackPublication,
  RemoteParticipant,
  LocalParticipant,
  VideoView,
  AudioView
} from '@livekit/react-native';
import omertaAPI from '../utils/api';

const { width, height } = Dimensions.get('window');

export default function LiveKitVideoCall({ 
  visible, 
  onClose, 
  roomConfig = null,
  securitySettings = {}
}) {
  const [room, setRoom] = useState(null);
  const [token, setToken] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState(new Map());
  const [localParticipant, setLocalParticipant] = useState(null);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [faceBlurEnabled, setFaceBlurEnabled] = useState(securitySettings.enableFaceBlur || false);
  const [voiceScramblingEnabled, setVoiceScramblingEnabled] = useState(securitySettings.enableVoiceScramble || false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [callDuration, setCallDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const roomRef = useRef(null);
  const callStartTime = useRef(null);
  const durationInterval = useRef(null);

  useEffect(() => {
    if (visible && roomConfig) {
      initializeCall();
    }
    
    return () => {
      cleanup();
    };
  }, [visible, roomConfig]);

  useEffect(() => {
    // Call duration timer
    if (isConnected && callStartTime.current) {
      durationInterval.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime.current) / 1000);
        setCallDuration(elapsed);
      }, 1000);
    } else {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
        durationInterval.current = null;
      }
    }

    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
    };
  }, [isConnected]);

  const initializeCall = async () => {
    try {
      setIsLoading(true);
      setConnectionStatus('connecting');

      // Get access token from backend
      const tokenResponse = await getAccessToken();
      if (!tokenResponse || !tokenResponse.token) {
        throw new Error('Failed to get access token');
      }

      setToken(tokenResponse.token);

      // Create and configure room
      const newRoom = new Room({
        // Audio processing options
        audioCaptureOptions: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          voiceActivityDetection: true
        },
        // Video processing options
        videoCaptureOptions: {
          resolution: {
            width: 1280,
            height: 720
          },
          frameRate: 30
        },
        // Adaptive streaming
        adaptiveStream: true,
        dynacast: true
      });

      // Set up room event listeners
      setupRoomEventListeners(newRoom);

      // Connect to room
      await newRoom.connect(tokenResponse.ws_url, tokenResponse.token);

      setRoom(newRoom);
      roomRef.current = newRoom;
      setIsConnected(true);
      setConnectionStatus('connected');
      callStartTime.current = Date.now();

    } catch (error) {
      console.error('Failed to initialize call:', error);
      setConnectionStatus('failed');
      Alert.alert('Connection Failed', `Unable to join call: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getAccessToken = async () => {
    try {
      if (roomConfig && roomConfig.isCreator) {
        // Create new room
        const response = await omertaAPI.makeRequest('/livekit/room/create', {
          method: 'POST',
          body: JSON.stringify({
            room_name: roomConfig.roomName || 'Secure Call',
            creator_id: roomConfig.userId,
            max_participants: roomConfig.maxParticipants || 10,
            enable_face_blur: faceBlurEnabled,
            enable_voice_scramble: voiceScramblingEnabled,
            session_timeout: 3600
          })
        });

        return response;
      } else {
        // Join existing room
        const response = await omertaAPI.makeRequest('/livekit/room/join', {
          method: 'POST',
          body: JSON.stringify({
            room_id: roomConfig.roomId,
            participant_id: roomConfig.userId,
            permissions: {
              canPublish: true,
              canSubscribe: true,
              canPublishData: false
            }
          })
        });

        return response;
      }
    } catch (error) {
      console.error('Failed to get access token:', error);
      throw error;
    }
  };

  const setupRoomEventListeners = (room) => {
    // Connection events
    room.on(RoomEvent.Connected, () => {
      console.log('Connected to room');
      setIsConnected(true);
      setConnectionStatus('connected');
      setLocalParticipant(room.localParticipant);
    });

    room.on(RoomEvent.Disconnected, (reason) => {
      console.log('Disconnected from room:', reason);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      cleanup();
    });

    room.on(RoomEvent.Reconnecting, () => {
      console.log('Reconnecting to room...');
      setConnectionStatus('reconnecting');
    });

    room.on(RoomEvent.Reconnected, () => {
      console.log('Reconnected to room');
      setConnectionStatus('connected');
    });

    // Participant events
    room.on(RoomEvent.ParticipantConnected, (participant) => {
      console.log('Participant connected:', participant.identity);
      setParticipants(prev => new Map(prev.set(participant.sid, participant)));
    });

    room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      console.log('Participant disconnected:', participant.identity);
      setParticipants(prev => {
        const updated = new Map(prev);
        updated.delete(participant.sid);
        return updated;
      });
    });

    // Track events
    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log('Track subscribed:', track.kind, participant.identity);
    });

    room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      console.log('Track unsubscribed:', track.kind, participant.identity);
    });

    // Error handling
    room.on(RoomEvent.MediaDevicesError, (error) => {
      console.error('Media devices error:', error);
      Alert.alert('Media Error', 'Failed to access camera or microphone');
    });

    room.on(RoomEvent.ConnectionQualityChanged, (quality, participant) => {
      console.log('Connection quality changed:', quality, participant?.identity);
    });
  };

  const toggleAudio = async () => {
    if (!room || !localParticipant) return;

    try {
      await localParticipant.setMicrophoneEnabled(!isAudioEnabled);
      setIsAudioEnabled(!isAudioEnabled);
    } catch (error) {
      console.error('Failed to toggle audio:', error);
      Alert.alert('Audio Error', 'Failed to toggle microphone');
    }
  };

  const toggleVideo = async () => {
    if (!room || !localParticipant) return;

    try {
      await localParticipant.setCameraEnabled(!isVideoEnabled);
      setIsVideoEnabled(!isVideoEnabled);
    } catch (error) {
      console.error('Failed to toggle video:', error);
      Alert.alert('Video Error', 'Failed to toggle camera');
    }
  };

  const toggleFaceBlur = async () => {
    try {
      // Send security setting update to server
      await omertaAPI.makeRequest('/livekit/security/update', {
        method: 'POST',
        body: JSON.stringify({
          room_id: roomConfig.roomId,
          participant_id: roomConfig.userId,
          face_blur_enabled: !faceBlurEnabled
        })
      });

      setFaceBlurEnabled(!faceBlurEnabled);
    } catch (error) {
      console.error('Failed to toggle face blur:', error);
      Alert.alert('Security Error', 'Failed to update face blur setting');
    }
  };

  const toggleVoiceScrambling = async () => {
    try {
      // Send security setting update to server
      await omertaAPI.makeRequest('/livekit/security/update', {
        method: 'POST',
        body: JSON.stringify({
          room_id: roomConfig.roomId,
          participant_id: roomConfig.userId,
          voice_scramble_enabled: !voiceScramblingEnabled
        })
      });

      setVoiceScramblingEnabled(!voiceScramblingEnabled);
    } catch (error) {
      console.error('Failed to toggle voice scrambling:', error);
      Alert.alert('Security Error', 'Failed to update voice scrambling setting');
    }
  };

  const endCall = async () => {
    try {
      if (room) {
        await room.disconnect();
      }
      cleanup();
      onClose();
    } catch (error) {
      console.error('Failed to end call:', error);
      cleanup();
      onClose();
    }
  };

  const cleanup = () => {
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
    
    if (roomRef.current) {
      roomRef.current.disconnect();
      roomRef.current = null;
    }
    
    setRoom(null);
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setParticipants(new Map());
    setLocalParticipant(null);
    setCallDuration(0);
    callStartTime.current = null;
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return '#00ff00';
      case 'connecting': return '#ffaa00';
      case 'reconnecting': return '#ff8800';
      case 'failed': return '#ff4444';
      default: return '#666';
    }
  };

  const renderParticipantVideo = (participant, isLocal = false) => {
    const videoTrack = participant.videoTracks.values().next().value?.track;
    const audioTrack = participant.audioTracks.values().next().value?.track;

    return (
      <View key={participant.sid || 'local'} style={styles.participantContainer}>
        <View style={styles.videoContainer}>
          {videoTrack && (
            <VideoView
              style={styles.videoView}
              track={videoTrack}
              objectFit="cover"
            />
          )}
          {audioTrack && (
            <AudioView
              track={audioTrack}
              enabled={true}
            />
          )}
          
          {/* Participant overlay */}
          <View style={styles.participantOverlay}>
            <Text style={styles.participantName}>
              {isLocal ? 'You' : participant.identity}
            </Text>
            
            {/* Security indicators */}
            <View style={styles.securityIndicators}>
              {faceBlurEnabled && isLocal && (
                <View style={styles.securityBadge}>
                  <Text style={styles.securityBadgeText}>🎭</Text>
                </View>
              )}
              {voiceScramblingEnabled && isLocal && (
                <View style={styles.securityBadge}>
                  <Text style={styles.securityBadgeText}>🔊</Text>
                </View>
              )}
            </View>
            
            {/* Audio indicator */}
            <View style={styles.audioIndicator}>
              <Text style={styles.audioIndicatorText}>
                {participant.isMuted ? '🔇' : '🔊'}
              </Text>
            </View>
          </View>
        </View>
      </View>
    );
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" statusBarTranslucent>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={[styles.statusIndicator, { backgroundColor: getConnectionStatusColor() }]} />
            <Text style={styles.statusText}>{connectionStatus.toUpperCase()}</Text>
          </View>
          
          <View style={styles.headerCenter}>
            <Text style={styles.roomTitle}>
              {roomConfig?.roomName || 'Secure Call'}
            </Text>
            {isConnected && (
              <Text style={styles.callDuration}>
                {formatDuration(callDuration)}
              </Text>
            )}
          </View>
          
          <TouchableOpacity style={styles.headerRight} onPress={endCall}>
            <Text style={styles.endCallText}>End</Text>
          </TouchableOpacity>
        </View>

        {/* Video Area */}
        <View style={styles.videoArea}>
          {isLoading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Connecting to secure call...</Text>
            </View>
          ) : connectionStatus === 'failed' ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>Connection Failed</Text>
              <TouchableOpacity style={styles.retryButton} onPress={initializeCall}>
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.participantsGrid}>
              {/* Local participant (self) */}
              {localParticipant && renderParticipantVideo(localParticipant, true)}
              
              {/* Remote participants */}
              {Array.from(participants.values()).map(participant => 
                renderParticipantVideo(participant, false)
              )}
            </View>
          )}
        </View>

        {/* Security Controls */}
        <View style={styles.securityControls}>
          <Text style={styles.securityTitle}>🔒 Security Settings</Text>
          
          <View style={styles.securityRow}>
            <Text style={styles.securityLabel}>Face Blur</Text>
            <Switch
              value={faceBlurEnabled}
              onValueChange={toggleFaceBlur}
              trackColor={{ false: '#666', true: '#ef4444' }}
              thumbColor={faceBlurEnabled ? '#fff' : '#ccc'}
              disabled={!isConnected}
            />
          </View>
          
          <View style={styles.securityRow}>
            <Text style={styles.securityLabel}>Voice Scrambling</Text>
            <Switch
              value={voiceScramblingEnabled}
              onValueChange={toggleVoiceScrambling}
              trackColor={{ false: '#666', true: '#ef4444' }}
              thumbColor={voiceScramblingEnabled ? '#fff' : '#ccc'}
              disabled={!isConnected}
            />
          </View>
        </View>

        {/* Call Controls */}
        <View style={styles.controlsContainer}>
          <TouchableOpacity
            style={[styles.controlButton, !isAudioEnabled && styles.disabledControl]}
            onPress={toggleAudio}
            disabled={!isConnected}
          >
            <Text style={styles.controlButtonText}>
              {isAudioEnabled ? '🎤' : '🔇'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.controlButton, !isVideoEnabled && styles.disabledControl]}
            onPress={toggleVideo}
            disabled={!isConnected}
          >
            <Text style={styles.controlButtonText}>
              {isVideoEnabled ? '📹' : '📵'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.endCallButton}
            onPress={endCall}
          >
            <Text style={styles.endCallButtonText}>📞</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 15,
    backgroundColor: '#111',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  headerCenter: {
    flex: 2,
    alignItems: 'center',
  },
  roomTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  callDuration: {
    color: '#ef4444',
    fontSize: 12,
    marginTop: 2,
    fontFamily: 'monospace',
  },
  headerRight: {
    flex: 1,
    alignItems: 'flex-end',
  },
  endCallText: {
    color: '#ff4444',
    fontSize: 16,
    fontWeight: 'bold',
  },
  videoArea: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: '#ff4444',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 30,
    paddingVertical: 10,
    borderRadius: 20,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  participantsGrid: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  participantContainer: {
    width: width / 2 - 15,
    height: height / 3,
    margin: 5,
  },
  videoContainer: {
    flex: 1,
    borderRadius: 10,
    overflow: 'hidden',
    backgroundColor: '#222',
    position: 'relative',
  },
  videoView: {
    flex: 1,
  },
  participantOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  participantName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  securityIndicators: {
    flexDirection: 'row',
  },
  securityBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.8)',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 5,
  },
  securityBadgeText: {
    fontSize: 12,
  },
  audioIndicator: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  audioIndicatorText: {
    fontSize: 12,
  },
  securityControls: {
    backgroundColor: '#111',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  securityTitle: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  securityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  securityLabel: {
    color: '#fff',
    fontSize: 14,
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 40,
    backgroundColor: '#111',
  },
  controlButton: {
    backgroundColor: '#333',
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 15,
    borderWidth: 2,
    borderColor: '#555',
  },
  disabledControl: {
    backgroundColor: '#666',
    borderColor: '#888',
  },
  controlButtonText: {
    fontSize: 24,
  },
  endCallButton: {
    backgroundColor: '#ff4444',
    width: 70,
    height: 70,
    borderRadius: 35,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 15,
    borderWidth: 2,
    borderColor: '#fff',
  },
  endCallButtonText: {
    fontSize: 30,
    transform: [{ rotate: '135deg' }],
  },
});