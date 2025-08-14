"""
Unified Flask application for the rover project.
Combines camera streaming and motor control in one interface.
Each system maintains separate endpoints for clean API design.
"""

import os
import time
import logging
from datetime import datetime
from flask import Flask, Response, render_template, request, redirect, url_for, jsonify
from rover.utils.gpio_mock import GPIOController
from rover.core.motor_controller import MotorController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize system components
gpio = GPIOController()
motor_controller = MotorController(gpio)
camera_stream = None

# Camera streaming class (will be initialized when needed)
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
        
        # Initialize camera
        self._setup_camera()
        
    def _setup_camera(self):
        """Initialize the Pi Camera with picamera2."""
        try:
            from picamera2 import Picamera2
            
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
            import cv2
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
                import cv2
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # OpenCV fallback
                import cv2
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
                import cv2
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Send a blank frame if camera fails
                import numpy as np
                blank_frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                import cv2
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

# Initialize camera stream
def init_camera():
    """Initialize camera stream when needed."""
    global camera_stream
    if camera_stream is None:
        camera_stream = CameraStream(resolution=(640, 480), framerate=30)
    return camera_stream

# ============================================================================
# UI ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main interface with camera stream and motor controls."""
    client_ip = request.remote_addr
    logger.info(f"Client {client_ip} accessed main interface")
    return render_template('unified_interface.html')

# ============================================================================
# CAMERA ENDPOINTS
# ============================================================================

@app.route('/camera/video_feed')
def video_feed():
    """Video streaming route."""
    client_ip = request.remote_addr
    logger.info(f"Client {client_ip} started video stream")
    
    camera = init_camera()
    if camera:
        camera.start_streaming()
        return Response(camera.generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Camera not available", 500

@app.route('/camera/status')
def camera_status():
    """Get camera status."""
    camera = init_camera()
    if camera:
        return jsonify({
            "status": "success",
            "is_streaming": camera.is_streaming,
            "resolution": camera.resolution,
            "framerate": camera.framerate
        })
    return jsonify({"status": "error", "message": "Camera not available"})

@app.route('/camera/start', methods=['POST'])
def camera_start():
    """Start the camera stream."""
    camera = init_camera()
    if camera:
        camera.start_streaming()
        return jsonify({"status": "success", "message": "Camera stream started"})
    return jsonify({"status": "error", "message": "Camera not available"})

@app.route('/camera/stop', methods=['POST'])
def camera_stop():
    """Stop the camera stream."""
    camera = init_camera()
    if camera:
        camera.stop_streaming()
        return jsonify({"status": "success", "message": "Camera stream stopped"})
    return jsonify({"status": "error", "message": "Camera not available"})

# ============================================================================
# MOTOR CONTROL ENDPOINTS
# ============================================================================

@app.route('/motor/forward', methods=['POST'])
def motor_forward():
    """Move rover forward."""
    speed = float(request.form.get('speed', 0.5))
    motor_controller.move_forward(speed)
    logger.info(f"Motor command: forward at speed {speed}")
    return jsonify({"status": "success", "action": "forward", "speed": speed})

@app.route('/motor/backward', methods=['POST'])
def motor_backward():
    """Move rover backward."""
    speed = float(request.form.get('speed', 0.5))
    motor_controller.move_backward(speed)
    logger.info(f"Motor command: backward at speed {speed}")
    return jsonify({"status": "success", "action": "backward", "speed": speed})

@app.route('/motor/left', methods=['POST'])
def motor_left():
    """Turn rover left."""
    speed = float(request.form.get('speed', 0.5))
    motor_controller.turn_left(speed)
    logger.info(f"Motor command: left turn at speed {speed}")
    return jsonify({"status": "success", "action": "left", "speed": speed})

@app.route('/motor/right', methods=['POST'])
def motor_right():
    """Turn rover right."""
    speed = float(request.form.get('speed', 0.5))
    motor_controller.turn_right(speed)
    logger.info(f"Motor command: right turn at speed {speed}")
    return jsonify({"status": "success", "action": "right", "speed": speed})

@app.route('/motor/stop', methods=['POST'])
def motor_stop():
    """Stop rover."""
    motor_controller.stop()
    logger.info("Motor command: stop")
    return jsonify({"status": "success", "action": "stop"})

@app.route('/motor/forward_timed', methods=['POST'])
def motor_forward_timed():
    """Move rover forward for specified duration."""
    speed = float(request.form.get('speed', 0.5))
    duration = float(request.form.get('duration', 2.0))
    motor_controller.move_forward_in_seconds(speed, duration)
    logger.info(f"Motor command: forward for {duration}s at speed {speed}")
    return jsonify({"status": "success", "action": "forward_timed", "speed": speed, "duration": duration})

# ============================================================================
# SYSTEM STATUS ENDPOINTS
# ============================================================================

@app.route('/api/status')
def system_status():
    """Get overall system status."""
    camera = init_camera()
    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "camera": {
            "is_streaming": camera.is_streaming if camera else False,
            "resolution": camera.resolution if camera else None,
            "framerate": camera.framerate if camera else None
        },
        "motor": {
            "status": "ready",
            "gpio_mode": "mock" if gpio.mock_mode else "real"
        }
    })

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main function to run the unified rover server."""
    try:
        logger.info("Starting unified rover server on http://0.0.0.0:5000")
        logger.info("Camera and motor control endpoints available")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down rover server...")
    finally:
        # Cleanup
        if camera_stream:
            camera_stream.stop_streaming()
            camera_stream.cleanup()
        motor_controller.cleanup()

if __name__ == '__main__':
    main()
