import cv2
import time
import threading
import mss
import numpy as np
from flask import Response, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveMonitor:
    def __init__(self):
        self.camera = None
        self.screen_capture = None
        self.is_camera_running = False
        self.is_screen_running = False
        self.camera_lock = threading.Lock()
        self.screen_lock = threading.Lock()
        self.camera_enabled = False  # New flag to track if camera is enabled by user
        logger.info("LiveMonitor initialized")
        
    def start_camera_feed(self):
        """Initialize and start the webcam feed"""
        with self.camera_lock:
            if not self.is_camera_running and self.camera_enabled:  # Only start if enabled
                try:
                    logger.info("Attempting to start camera feed...")
                    self.camera = cv2.VideoCapture(0)
                    if not self.camera.isOpened():
                        logger.error("Error: Could not open webcam")
                        return False
                    # Set camera properties for better performance
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 20)
                    self.is_camera_running = True
                    logger.info("Camera feed started successfully")
                    return True
                except Exception as e:
                    logger.error(f"Error starting camera feed: {str(e)}")
                    if self.camera:
                        self.camera.release()
                    self.camera = None
                    return False
            return True
    def stop_camera_feed(self):
        """Stop the webcam feed"""
        with self.camera_lock:
            self.is_camera_running = False
            if self.camera:
                try:
                    # Release the camera multiple times to ensure it's freed
                    for _ in range(3):
                        try:
                            self.camera.release()
                            time.sleep(0.1)  # Small delay between attempts
                        except:
                            pass
                    
                    # Force OpenCV to release all captures
                    try:
                        cv2.destroyAllWindows()
                    except:
                        pass
                        
                    logger.info("Camera feed stopped")
                except Exception as e:
                    logger.error(f"Error releasing camera: {str(e)}")
                finally:
                    self.camera = None
                    self.is_camera_running = False  # Ensure flag is set to False
            
    def get_camera_frame(self):
        """Capture a frame from webcam"""
        if not self.camera or not self.camera_enabled:  # Don't capture if camera is disabled
            return None
            
        with self.camera_lock:
            try:
                success, frame = self.camera.read()
                if not success:
                    logger.warning("Failed to read camera frame")
                    return None
                
                # Compress frame
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ret:
                    logger.warning("Failed to compress camera frame")
                    return None
                
                return buffer.tobytes()
            except Exception as e:
                logger.error(f"Error capturing camera frame: {str(e)}")
                return None
        
    def get_screen_frame(self):
        """Capture a screenshot"""
        with self.screen_lock:
            try:
                if not self.screen_capture:
                    logger.info("Initializing screen capture...")
                    self.screen_capture = mss.mss()
                
                # Capture the screen using mss
                screen = self.screen_capture.grab(self.screen_capture.monitors[1])
                
                # Convert to numpy array and BGR format
                img = np.array(screen)
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Resize frame to reduce bandwidth
                height, width = frame.shape[:2]
                if width > 1280:  # Limit max width
                    scale = 1280 / width
                    new_width = 1280
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Compress frame
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ret:
                    logger.warning("Failed to compress screen frame")
                    return None
                
                return buffer.tobytes()
            except Exception as e:
                logger.error(f"Error capturing screen: {str(e)}")
                # Try to reinitialize screen capture on error
                try:
                    if self.screen_capture:
                        self.screen_capture.close()
                except:
                    pass
                self.screen_capture = None
                return None
            
    def generate_camera_frames(self):
        """Generator for camera frames"""
        logger.info("Starting camera frame generator")
        retry_count = 0
        try:
            while self.is_camera_running and self.camera_enabled:  # Check if camera is enabled
                try:
                    frame = self.get_camera_frame()
                    if frame is not None:
                        retry_count = 0  # Reset retry count on success
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    else:
                        retry_count += 1
                        if retry_count > 5:  # After 5 failures, try to restart camera
                            logger.warning("Attempting to restart camera feed...")
                            self.stop_camera_feed()
                            if self.start_camera_feed():
                                retry_count = 0
                            else:
                                time.sleep(5)  # Wait longer between retries
                    time.sleep(0.2)  # Reduced from 0.05 to 0.2 seconds (5 FPS instead of 20 FPS)
                except Exception as e:
                    logger.error(f"Error in camera frame generator: {str(e)}")
                    time.sleep(1)  # Wait on error
        finally:
            # Ensure camera is released when generator stops
            logger.info("Camera frame generator stopping - releasing resources")
            self.stop_camera_feed()
            logger.info("Camera frame generator stopped")
            
    def generate_screen_frames(self):
        """Generator for screen frames"""
        logger.info("Starting screen frame generator")
        retry_count = 0
        while self.is_screen_running:
            try:
                frame = self.get_screen_frame()
                if frame is not None:
                    retry_count = 0  # Reset retry count on success
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    retry_count += 1
                    if retry_count > 5:  # After 5 failures, try to reinitialize
                        logger.warning("Attempting to reinitialize screen capture...")
                        with self.screen_lock:
                            try:
                                if self.screen_capture:
                                    self.screen_capture.close()
                            except:
                                pass
                            self.screen_capture = None
                        retry_count = 0
                time.sleep(0.3)  # Reduced from 0.1 to 0.3 seconds (3 FPS instead of 10 FPS)
            except Exception as e:
                logger.error(f"Error in screen frame generator: {str(e)}")
                time.sleep(1)  # Wait on error
            
    def start_screen_feed(self):
        """Start screen capture feed"""
        with self.screen_lock:
            if not self.is_screen_running:
                try:
                    if not self.screen_capture:
                        self.screen_capture = mss.mss()
                    self.is_screen_running = True
                    logger.info("Screen feed started successfully")
                    return True
                except Exception as e:
                    logger.error(f"Error starting screen feed: {str(e)}")
                    return False
            return True
            
    def stop_screen_feed(self):
        """Stop screen capture feed"""
        with self.screen_lock:
            self.is_screen_running = False
            if self.screen_capture:
                try:
                    self.screen_capture.close()
                    logger.info("Screen feed stopped")
                except Exception as e:
                    logger.error(f"Error closing screen capture: {str(e)}")
                finally:
                    self.screen_capture = None

    def set_camera_enabled(self, enabled):
        """Enable or disable camera feed"""
        self.camera_enabled = enabled
        if enabled:
            return self.start_camera_feed()
        else:
            self.stop_camera_feed()
            return True
        
    def start(self):
        """Start all monitoring feeds"""
        logger.info("Starting live monitor...")
        screen_success = self.start_screen_feed()
        # Don't start camera by default, wait for user to enable it
        if screen_success:
            logger.info("Live monitor started successfully")
            return True
        else:
            logger.error("Failed to start live monitor - screen feed failed")
            return False
        
    def stop(self):
        """Stop all monitoring feeds"""
        logger.info("Stopping live monitor...")
        self.stop_camera_feed()
        self.stop_screen_feed()
        logger.info("Live monitor stopped") 