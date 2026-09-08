import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Button,
  Image,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';

const DEFAULT_API_BASE =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000'
    : Platform.OS === 'ios'
      ? 'http://127.0.0.1:8000'
      : 'http://localhost:8000';

const API_BASE = process.env.EXPO_PUBLIC_API_URL || DEFAULT_API_BASE;

export default function App() {
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    emotion: string;
    confidence?: number;
    message?: string;
    fallback?: boolean;
  } | null>(null);

  const requestPermissions = async () => {
    const cameraPermission = await ImagePicker.requestCameraPermissionsAsync();

    if (!cameraPermission.granted) {
      Alert.alert('Permission required', 'Camera access is required to record a 5 second face video.');
      return false;
    }

    return true;
  };

  const openFrontCameraVideo = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) {
      return;
    }

    const response = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      cameraType: ImagePicker.CameraType.front,
      quality: 1,
      videoMaxDuration: 5,
      allowsEditing: false,
    });

    if (!response.canceled && response.assets?.[0]?.uri) {
      setSelectedVideo(response.assets[0].uri);
      setResult(null);
    }
  };

  const pickVideoFromLibrary = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) {
      return;
    }

    const response = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      quality: 1,
      allowsEditing: false,
      selectionLimit: 1,
    });

    if (!response.canceled && response.assets?.[0]?.uri) {
      setSelectedVideo(response.assets[0].uri);
      setResult(null);
    }
  };

  const getMimeTypeFromUri = (uri: string) => {
    const fileName = decodeURIComponent(uri.split('/').pop() || 'clip.mp4');
    const extension = fileName.split('.').pop()?.toLowerCase();

    switch (extension) {
      case 'mov':
        return 'video/quicktime';
      case 'webm':
        return 'video/webm';
      case 'mp4':
      default:
        return 'video/mp4';
    }
  };

  const analyzeEmotion = async () => {
    if (!selectedVideo) {
      Alert.alert('No video selected', 'Record or choose a 5 second face video before generating the emotion.');
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const fileName = decodeURIComponent(selectedVideo.split('/').pop() || 'face_video.mp4');
      const mimeType = getMimeTypeFromUri(selectedVideo);
      const formData = new FormData();

      formData.append('file', {
        uri: selectedVideo,
        name: fileName,
        type: mimeType,
      } as any);

      const response = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || 'Prediction failed.');
      }

      if (data.emotion === 'Unknown' && data.message?.toLowerCase().includes('face')) {
        setResult({
          emotion: 'Unknown',
          confidence: 0,
          message: 'No face was detected. Please record a clear front-facing video with your face visible for the full 5 seconds.',
        });
        return;
      }

      setResult({
        emotion: data.emotion || 'Unknown',
        confidence: data.confidence ?? undefined,
        message: data.message || 'Prediction complete.',
        fallback: Boolean(data.fallback),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to process the video.';
      setResult({
        emotion: 'Error',
        message,
      });
      Alert.alert('Prediction error', message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Emotion Generator</Text>
        <Text style={styles.subtitle}>Record a 5 second front-camera video and generate the emotion.</Text>

        {selectedVideo ? (
          <View style={styles.videoPreviewBox}>
            <Text style={styles.videoLabel}>Selected video</Text>
            <Text style={styles.videoName}>{selectedVideo.split('/').pop() || 'face_video.mp4'}</Text>
          </View>
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>No video selected</Text>
          </View>
        )}

        <View style={styles.actionRow}>
          <Button title="Front Camera" onPress={openFrontCameraVideo} />
          <Button title="Pick Video" onPress={pickVideoFromLibrary} />
        </View>

        <View style={styles.analyzeButton}>
          <Button title={isLoading ? 'Analyzing...' : 'Generate Emotion'} onPress={analyzeEmotion} disabled={isLoading || !selectedVideo} />
        </View>

        {isLoading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color="#4f46e5" />
            <Text style={styles.loadingText}>Processing 5 second video...</Text>
          </View>
        ) : null}

        {result ? (
          <View style={styles.resultCard}>
            <Text style={styles.resultLabel}>Predicted emotion</Text>
            <Text style={styles.resultEmotion}>{result.emotion}</Text>
            {typeof result.confidence === 'number' ? (
              <Text style={styles.resultConfidence}>Confidence: {result.confidence.toFixed(2)}</Text>
            ) : null}
            <Text style={result.fallback ? styles.resultFallback : styles.resultMessage}>{result.message}</Text>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  container: {
    flexGrow: 1,
    padding: 20,
    justifyContent: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
    color: '#111827',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#4b5563',
    textAlign: 'center',
    marginBottom: 18,
  },
  videoPreviewBox: {
    width: '100%',
    minHeight: 120,
    borderRadius: 18,
    backgroundColor: '#e0e7ff',
    padding: 18,
    marginBottom: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoLabel: {
    color: '#4338ca',
    fontWeight: '700',
    marginBottom: 8,
  },
  videoName: {
    color: '#111827',
    fontSize: 14,
    textAlign: 'center',
  },
  placeholder: {
    width: '100%',
    height: 160,
    borderRadius: 18,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#9ca3af',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 18,
    backgroundColor: '#eef2ff',
  },
  placeholderText: {
    color: '#6b7280',
    fontSize: 18,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
  },
  analyzeButton: {
    marginBottom: 18,
  },
  loadingBox: {
    alignItems: 'center',
    paddingVertical: 18,
  },
  loadingText: {
    marginTop: 8,
    color: '#374151',
  },
  resultCard: {
    backgroundColor: '#ffffff',
    padding: 18,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  resultLabel: {
    fontSize: 12,
    letterSpacing: 1,
    color: '#6b7280',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  resultEmotion: {
    fontSize: 34,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 8,
  },
  resultConfidence: {
    fontSize: 16,
    color: '#4f46e5',
    marginBottom: 8,
  },
  resultMessage: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  resultFallback: {
    fontSize: 14,
    color: '#b45309',
    lineHeight: 20,
  },
});
