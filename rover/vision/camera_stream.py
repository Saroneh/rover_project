"""
Camera streaming module for the rover project.
Handles Pi Camera capture and streaming via Flask with MJPEG support.
Designed to be a standalone module that can later integrate with AI detection.
"""

import os
import time
import logging
from datetime import datetime
from flask import Flask, Response, render_template, request, jsonify
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraStream:
    """Camera streaming class that handles Pi Camera operations and streaming."""
    
    def __init__(self, resolution=(640, 480), framerate=30):
        """
        Initialize the camera stream.
        
        Args:
            resolution (tuple): Camera resolution (width, height)
            framerate (int): Target frame rate
        """
        self.resolution = resolution
        self.framerate = framerate
        self.camera = None
        self.is_streaming = False
        self.clients = set()
        
        # Initialize camera
        self._setup_camera()
        
    def _setup_camera(self):
        """Initialize the Pi Camera with picamera2."""
        try:
            from picamera2 import Picamera2
            from picamera2.encoders import JpegEncoder
            from picamera2.outputs import FileOutput
            
            # Initialize camera
            self.camera = Picamera2()
            
            # Configure camera
            config = self.camera.create_preview_configuration(
                main={"size": self.resolution, "format": "RGB888"},
                controls={"FrameDurationLimits": (1000000 // self.framerate, 1000000 // self.framerate)}
            )
            self.camera.configure(config)
            
            # Start camera
            self.camera.start()
            logger.info(f"Camera initialized successfully at {self.resolution} resolution, {self.framerate} fps")
            
        except ImportError:
            logger.warning("picamera2 not available, using OpenCV fallback")
            self._setup_opencv_fallback()
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self._setup_opencv_fallback()
    
    def _setup_opencv_fallback(self):
        """Fallback to OpenCV for testing on non-Pi systems."""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                # Try different camera indices
                for i in range(4):
                    self.camera = cv2.VideoCapture(i)
                    if self.camera.isOpened():
                        break
                
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
                logger.info("OpenCV camera fallback initialized")
            else:
                logger.error("No camera available")
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenCV camera: {e}")
    
    def get_frame(self):
        """Capture a single frame from the camera."""
        if self.camera is None:
            return None
            
        try:
            if hasattr(self.camera, 'capture_array'):
                # picamera2
                frame = self.camera.capture_array()
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # OpenCV fallback
                ret, frame = self.camera.read()
                if not ret:
                    return None
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def generate_frames(self):
        """Generate MJPEG frames for streaming."""
        while self.is_streaming:
            frame = self.get_frame()
            if frame is not None:
                # Encode frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Send a blank frame if camera fails
                blank_frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                _, buffer = cv2.imencode('.jpg', blank_frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1.0 / self.framerate)
    
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
        if self.camera is not None:
            if hasattr(self.camera, 'close'):
                self.camera.close()
            else:
                self.camera.release()
        logger.info("Camera resources cleaned up")

# Flask application
app = Flask(__name__)
camera_stream = None

@app.route('/')
def index():
    """Main page with camera stream."""
    client_ip = request.remote_addr
    logger.info(f"Client {client_ip} accessed camera stream")
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    client_ip = request.remote_addr
    logger.info(f"Client {client_ip} started video stream")
    
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
            "framerate": camera_stream.framerate
        })
    return jsonify({"status": "error", "message": "Camera not initialized"})

def main():
    """Main function to run the camera stream server."""
    global camera_stream
    
    # Initialize camera
    camera_stream = CameraStream(resolution=(640, 480), framerate=30)
    
    try:
        # Start streaming
        camera_stream.start_streaming()
        
        # Run Flask app
        logger.info("Starting camera stream server on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down camera stream server...")
    finally:
        if camera_stream:
            camera_stream.stop_streaming()
            camera_stream.cleanup()

if __name__ == '__main__':
    main()
