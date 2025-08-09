import cv2
import os
import threading
from datetime import datetime
import time
import logging

class WebcamCapture:
    def __init__(self):
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.cap = None
        
    def start(self):
        """Start the webcam capture thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            self.logger.info("Webcam capture started")
            return True
        return False
        
    def stop(self):
        """Stop the webcam capture thread"""
        if self.running:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
            if self.cap:
                self.cap.release()
                self.cap = None
            self.logger.info("Webcam capture stopped")
            return True
        return False
            
    def _run(self):
        """Main webcam capture loop"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.logger.error("Could not open webcam")
                self.running = False
                return
                
            while self.running:
                try:
                    # Capture frame
                    ret, frame = self.cap.read()
                    if ret:
                        # Save image
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        filename = f"capture_{timestamp}.jpg"
                        filepath = os.path.join("WebcamLogs", filename)
                        
                        # Ensure directory exists
                        os.makedirs("WebcamLogs", exist_ok=True)
                        
                        # Save frame
                        cv2.imwrite(filepath, frame)
                        self.logger.info(f"Webcam capture saved: {filename}")
                        
                    # Wait for 5 minutes
                    time.sleep(300)
                    
                except Exception as e:
                    self.logger.error(f"Error capturing webcam: {str(e)}")
                    time.sleep(60)  # Wait a minute before retrying
                    
        except Exception as e:
            self.logger.error(f"Fatal error in webcam capture: {str(e)}")
            self.running = False
            
        finally:
            if self.cap:
                self.cap.release()
                self.cap = None
