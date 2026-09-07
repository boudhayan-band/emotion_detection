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

const API_BASE =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000'
    : Platform.OS === 'ios'
      ? 'http://127.0.0.1:8000'
      : 'http://localhost:8000';

export default function App() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    emotion: string;
    confidence?: number;
    message?: string;
    fallback?: boolean;
  } | null>(null);

  const requestPermissions = async () => {
    const mediaPermission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    const cameraPermission = await ImagePicker.requestCameraPermissionsAsync();

    if (!mediaPermission.granted && !cameraPermission.granted) {
      Alert.alert('Permission required', 'Camera or photo library access is required to analyze a face image.');
      return false;
    }

    return true;
  };

  const openImagePicker = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) {
      return;
    }

    const response = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 1,
      allowsEditing: true,
    });

    if (!response.canceled && response.assets?.[0]?.uri) {
      setSelectedImage(response.assets[0].uri);
      setResult(null);
    }
  };

  const openCamera = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) {
      return;
    }

    const response = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 1,
    });

    if (!response.canceled && response.assets?.[0]?.uri) {
      setSelectedImage(response.assets[0].uri);
      setResult(null);
    }
  };

  const analyzeEmotion = async () => {
    if (!selectedImage) {
      Alert.alert('No image selected', 'Choose or capture a face image before predicting the emotion.');
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const filename = selectedImage.split('/').pop() || 'photo.jpg';
      const formData = new FormData();
      formData.append('file', {
        uri: selectedImage,
        name: filename,
        type: 'image/jpeg',
      } as any);

      const response = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || 'Prediction failed.');
      }

      setResult({
        emotion: data.emotion || 'Unknown',
        confidence: data.confidence ?? undefined,
        message: data.message || 'Prediction complete.',
        fallback: Boolean(data.fallback),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to process the image.';
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
        <Text style={styles.subtitle}>Select a face image to detect the emotion.</Text>

        {selectedImage ? (
          <Image source={{ uri: selectedImage }} style={styles.previewImage} resizeMode="cover" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>No image selected</Text>
          </View>
        )}

        <View style={styles.actionRow}>
          <Button title="Choose Photo" onPress={openImagePicker} />
          <Button title="Take Photo" onPress={openCamera} />
        </View>

        <View style={styles.analyzeButton}>
          <Button title={isLoading ? 'Analyzing...' : 'Generate Emotion'} onPress={analyzeEmotion} disabled={isLoading || !selectedImage} />
        </View>

        {isLoading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color="#4f46e5" />
            <Text style={styles.loadingText}>Analyzing image...</Text>
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
  previewImage: {
    width: '100%',
    height: 320,
    borderRadius: 18,
    backgroundColor: '#dfe7f5',
    marginBottom: 18,
  },
  placeholder: {
    width: '100%',
    height: 320,
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
