# Camera Module for Rover Project

This module provides camera streaming capabilities for the rover project, designed to work with both Raspberry Pi Camera and USB webcams.

## Features

- **Pi Camera Support**: Native support for Raspberry Pi Camera Module V2.1 using `picamera2`
- **USB Camera Fallback**: OpenCV fallback for USB webcams and testing on non-Pi systems
- **MJPEG Streaming**: Real-time video streaming over HTTP
- **Configurable Resolution**: Adjustable resolution and frame rate
- **Network Access**: Stream accessible from any device on the local network

## Hardware Requirements

- **Primary**: Raspberry Pi Camera Module V2.1
- **Fallback**: USB webcam (for testing on non-Pi systems)
- **Network**: Wi-Fi or Ethernet connection

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Enable Pi Camera** (if using Raspberry Pi):
   ```bash
   sudo raspi-config
   # Navigate to Interface Options > Camera > Enable
   ```

## Usage

### Standalone Camera Module

Run the camera module independently:
```bash
cd rover/vision
python3 camera_stream.py
```

### Unified Interface

Run the complete rover system with camera and motor control:
```bash
cd rover/web
python3 -m rover.web.unified_app
```

## API Endpoints

### Camera Endpoints

- `GET /camera/video_feed` - MJPEG video stream
- `GET /camera/status` - Camera status information
- `POST /camera/start` - Start camera streaming
- `POST /camera/stop` - Stop camera streaming

### Motor Control Endpoints

- `POST /motor/forward` - Move forward
- `POST /motor/backward` - Move backward
- `POST /motor/left` - Turn left
- `POST /motor/right` - Turn right
- `POST /motor/stop` - Stop movement
- `POST /motor/forward_timed` - Timed forward movement

### System Endpoints

- `GET /api/status` - Overall system status
- `GET /` - Main web interface

## Configuration

### Camera Settings

Default configuration in `CameraStream` class:
- **Resolution**: 640x480
- **Frame Rate**: 30 fps
- **JPEG Quality**: 80%

To modify these settings, edit the `CameraStream` initialization in the code.

### Network Access

The camera stream is accessible at:
```
http://[RASPBERRY_PI_IP]:5000
```

Make sure your device is on the same local network as the Raspberry Pi.

## Testing

### On Raspberry Pi
1. Connect Pi Camera Module
2. Run the unified app
3. Access from any device on the network

### On Development Machine
1. Connect USB webcam
2. Run with OpenCV fallback
3. Test camera functionality locally

## Future Enhancements

- **AI Integration**: Ready for YOLO/OpenCV object detection
- **WebSocket Support**: Real-time communication for AI results
- **Cloud Streaming**: Easy transition to remote streaming
- **Multiple Cameras**: Support for multiple camera inputs

## Troubleshooting

### Camera Not Working
1. Check camera connections
2. Verify camera is enabled in `raspi-config`
3. Check for USB camera availability
4. Review error logs in terminal

### Stream Not Loading
1. Verify network connectivity
2. Check firewall settings
3. Ensure port 5000 is accessible
4. Check browser compatibility

### Performance Issues
1. Reduce resolution/frame rate
2. Check network bandwidth
3. Monitor Pi CPU usage
4. Consider using wired connection

## Architecture Notes

This module is designed to be:
- **Standalone**: Can run independently for testing
- **Integratable**: Easy to combine with other rover modules
- **Extensible**: Ready for AI and advanced features
- **Hardware Agnostic**: Works with Pi Camera and USB cameras
