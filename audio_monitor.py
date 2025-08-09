import pyaudio
import numpy as np
import threading
import time
import logging
import wave
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioMonitor:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_thread = None
        self.chunk_size = 1024
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 44100
        self.frames = []
        self.current_device_index = None
        self.log_dir = "logs/audio"
        self.ensure_log_directory()

    def ensure_log_directory(self):
        """Create audio logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def get_available_devices(self):
        """Get list of available audio input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Only input devices
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'default_sample_rate': device_info['defaultSampleRate']
                    })
            except Exception as e:
                logger.error(f"Error getting device info for index {i}: {str(e)}")
        return devices

    def set_device(self, device_index):
        """Change audio input device"""
        try:
            was_recording = self.is_recording
            if was_recording:
                self.stop_recording()

            self.current_device_index = device_index
            
            if was_recording:
                self.start_recording()
            return True
        except Exception as e:
            logger.error(f"Error setting audio device {device_index}: {str(e)}")
            return False

    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            return

        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.current_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            self.frames = []
            self.is_recording = True
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            logger.info("Audio recording started")
            return True
        except Exception as e:
            logger.error(f"Error starting audio recording: {str(e)}")
            return False

    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.save_recording()
                logger.info("Audio recording stopped")
            except Exception as e:
                logger.error(f"Error stopping audio recording: {str(e)}")

    def _record_audio(self):
        """Background thread for recording audio"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                logger.error(f"Error reading audio stream: {str(e)}")
                time.sleep(0.1)

    def save_recording(self):
        """Save recorded audio to file"""
        if not self.frames:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.log_dir, f"audio_{timestamp}.wav")
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            logger.info(f"Audio saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving audio recording: {str(e)}")

    def get_audio_level(self):
        """Get current audio input level (0-100)"""
        if not self.stream or not self.is_recording:
            return 0
        
        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.float32)
            level = np.abs(audio_data).mean()
            # Convert to percentage (0-100)
            return min(100, int(level * 100))
        except Exception as e:
            logger.error(f"Error getting audio level: {str(e)}")
            return 0

    def start(self):
        """Start the audio monitor"""
        # Try to use default input device
        devices = self.get_available_devices()
        if devices:
            self.current_device_index = devices[0]['index']
            return self.start_recording()
        return False

    def stop(self):
        """Stop the audio monitor"""
        self.stop_recording()
        self.audio.terminate() 