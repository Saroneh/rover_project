"""
Simple camera streaming module for the rover project.
This version avoids common picamera2 issues by using a more basic approach.
"""

import os
import time
import logging
from flask import Flask, Response, render_template, request, jsonify
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCameraStream:
    """Simple camera streaming class that avoids picamera2 issues."""
    
    def __init__(self, resolution=(640, 480), framerate=30):
        self.resolution = resolution
        self.framerate = framerate
        self.camera = None
        self.is_streaming = False
        self.camera_type = None
        
        # Initialize camera
        self._setup_camera()
        
    def _setup_camera(self):
        """Try different camera methods in order of preference."""
        
        # Method 1: Try OpenCV first (most reliable)
        if self._try_opencv():
            return
            
        # Method 2: Try basic picamera2 (minimal configuration)
        if self._try_basic_picamera2():
            return
            
        # Method 3: Try legacy picamera (if available)
        if self._try_legacy_picamera():
            return
            
        logger.error("No camera method available")
        self.camera_type = None
    
    def _try_opencv(self):
        """Try OpenCV camera capture."""
        try:
            # Try camera index 0 first
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                # Try different camera indices
                for i in range(4):
                    self.camera = cv2.VideoCapture(i)
                    if self.camera.isOpened():
                        break
            
            if self.camera.isOpened():
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
                
                # Test capture
                ret, test_frame = self.camera.read()
                if ret and test_frame is not None:
                    self.camera_type = 'opencv'
                    logger.info("OpenCV camera initialized successfully")
                    return True
                    
            self.camera.release()
            return False
            
        except Exception as e:
            logger.warning(f"OpenCV camera failed: {e}")
            return False
    
    def _try_basic_picamera2(self):
        """Try basic picamera2 with minimal configuration."""
        try:
            # Import with error handling
            import sys
            sys.path.append('/usr/lib/python3/dist-packages')
            
            from picamera2 import Picamera2
            
            # Create camera instance
            self.camera = Picamera2()
            
            # Use minimal configuration to avoid allocator issues
            config = self.camera.create_preview_configuration(
                main={"size": self.resolution}
            )
            
            # Apply and start
            self.camera.configure(config)
            self.camera.start()
            
            # Wait for stabilization
            time.sleep(3)
            
            # Test capture
            try:
                frame = self.camera.capture_array()
                if frame is not None and frame.size > 0:
                    self.camera_type = 'picamera2'
                    logger.info("Basic picamera2 initialized successfully")
                    return True
            except Exception as e:
                logger.warning(f"picamera2 capture test failed: {e}")
                
            # Cleanup on failure
            self.camera.stop()
            self.camera = None
            return False
            
        except Exception as e:
            logger.warning(f"Basic picamera2 failed: {e}")
            return False
    
    def _try_legacy_picamera(self):
        """Try legacy picamera (if available)."""
        try:
            import picamera
            
            self.camera = picamera.PiCamera()
            self.camera.resolution = self.resolution
            self.camera.framerate = self.framerate
            
            # Test capture
            time.sleep(2)
            
            self.camera_type = 'legacy_picamera'
            logger.info("Legacy picamera initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Legacy picamera failed: {e}")
            return False
    
    def get_frame(self):
        """Capture a single frame from the camera."""
        if self.camera is None or self.camera_type is None:
            return None
            
        try:
            if self.camera_type == 'opencv':
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    return None
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            elif self.camera_type == 'picamera2':
                frame = self.camera.capture_array()
                if frame is None or frame.size == 0:
                    return None
                # picamera2 returns BGR by default
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            elif self.camera_type == 'legacy_picamera':
                # Legacy picamera returns RGB
                frame = np.empty((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                self.camera.capture(frame, format='rgb')
                
            else:
                return None
                
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def generate_frames(self):
        """Generate MJPEG frames for streaming."""
        frame_count = 0
        consecutive_errors = 0
        
        while self.is_streaming:
            try:
                frame = self.get_frame()
                frame_count += 1
                
                if frame is not None:
                    consecutive_errors = 0
                    # Encode frame to JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    consecutive_errors += 1
                    # Send blank frame
                    blank_frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                    cv2.putText(blank_frame, f'No Frame - Count: {frame_count}', (50, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    _, buffer = cv2.imencode('.jpg', blank_frame)
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Adaptive delay based on errors
                if consecutive_errors > 5:
                    time.sleep(0.5)  # Slower on many errors
                else:
                    time.sleep(1.0 / self.framerate)
                    
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Frame generation error: {e}")
                
                # Send error frame
                error_frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                cv2.putText(error_frame, f'Error: {str(e)[:25]}', (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                _, buffer = cv2.imencode('.jpg', error_frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(1.0)  # Longer delay on error
    
    def start_streaming(self):
        """Start the camera stream."""
        self.is_streaming = True
        logger.info("Camera streaming started")
    
    def stop_streaming(self):
        """Stop the camera stream."""
        self.is_streaming = False
        logger.info("Camera streaming stopped")
    
    def cleanup(self):
        """Clean up camera resources."""
        try:
            if self.camera is not None:
                if hasattr(self.camera, 'close'):
                    self.camera.close()
                elif hasattr(self.camera, 'release'):
                    self.camera.release()
                elif hasattr(self.camera, 'stop'):
                    self.camera.stop()
            logger.info("Camera resources cleaned up")
        except Exception as e:
            logger.error(f"Error during camera cleanup: {e}")

# Flask application
app = Flask(__name__)
camera_stream = None

@app.route('/')
def index():
    """Main page with camera stream."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(camera_stream.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_stream')
def start_stream():
    """Start the camera stream."""
    if camera_stream:
        camera_stream.start_streaming()
        return jsonify({"status": "success", "message": "Stream started"})
    return jsonify({"status": "error", "message": "Camera not initialized"})

@app.route('/stop_stream')
def stop_stream():
    """Stop the camera stream."""
    if camera_stream:
        camera_stream.stop_streaming()
        return jsonify({"status": "success", "message": "Stream stopped"})
    return jsonify({"status": "error", "message": "Camera not initialized"})

@app.route('/status')
def status():
    """Get camera status."""
    if camera_stream:
        return jsonify({
            "status": "success",
            "is_streaming": camera_stream.is_streaming,
            "resolution": camera_stream.resolution,
            "framerate": camera_stream.framerate,
            "camera_type": camera_stream.camera_type
        })
    return jsonify({"status": "error", "message": "Camera not initialized"})

def main():
    """Main function to run the camera stream server."""
    global camera_stream
    
    # Initialize camera
    camera_stream = SimpleCameraStream(resolution=(640, 480), framerate=30)
    
    try:
        # Start streaming
        camera_stream.start_streaming()
        
        # Run Flask app
        logger.info("Starting simple camera stream server on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down camera stream server...")
    finally:
        if camera_stream:
            camera_stream.stop_streaming()
            camera_stream.cleanup()

if __name__ == '__main__':
    main()
