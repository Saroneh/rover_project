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
# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from rover.utils.gpio_factory import create_gpio_controller
from rover.core.motor_controller import MotorController

# Import the working camera stream
try:
    from rover.vision.camera_stream_working import CameraStream
    logger.info("Using working camera stream from rover.vision.camera_stream_working")
except ImportError:
    # Fallback to simple camera if main one fails
    try:
        from rover.vision.camera_stream_simple import SimpleCameraStream as CameraStream
        logger.info("Using simple camera stream as fallback")
    except ImportError:
        logger.error("No camera stream module available")
        CameraStream = None

# Initialize Flask app
app = Flask(__name__)

# Initialize system components
gpio = create_gpio_controller()
motor_controller = MotorController(gpio)
camera_stream = None

# Initialize camera stream
def init_camera():
    """Initialize camera stream when needed."""
    global camera_stream
    if camera_stream is None and CameraStream is not None:
        camera_stream = CameraStream(resolution=(640, 480), framerate=30)
        logger.info(f"Camera initialized: {camera_stream.camera_type}")
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
            "framerate": camera.framerate,
            "camera_type": camera.camera_type
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
            "framerate": camera.framerate if camera else None,
            "camera_type": camera.camera_type if camera else None
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
