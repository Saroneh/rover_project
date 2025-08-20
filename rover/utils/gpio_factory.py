"""
Smart GPIO factory that automatically chooses between mock and real GPIO.
Detects the environment and provides the appropriate GPIO controller.
"""
import logging
import os

logger = logging.getLogger(__name__)

def create_gpio_controller():
    """
    Create the appropriate GPIO controller based on the environment.
    
    Returns:
        GPIO controller instance (mock or real)
    """
    # Check if we're on a Raspberry Pi
    if _is_running_on_pi():
        try:
            # Try to import and use real GPIO
            from .gpio_real import RealGPIOController
            logger.info("Creating real GPIO controller for Raspberry Pi")
            return RealGPIOController()
        except ImportError as e:
            logger.warning(f"Real GPIO not available: {e}")
            logger.info("Falling back to mock GPIO")
            return _create_mock_gpio()
        except Exception as e:
            logger.error(f"Failed to initialize real GPIO: {e}")
            logger.info("Falling back to mock GPIO")
            return _create_mock_gpio()
    else:
        # Not on Pi, use mock GPIO
        logger.info("Creating mock GPIO controller for development")
        return _create_mock_gpio()

def _is_running_on_pi():
    """Check if we're running on a Raspberry Pi."""
    try:
        # Method 1: Check device tree
        with open('/sys/firmware/devicetree/base/model', 'r') as f:
            return 'raspberry pi' in f.read().lower()
    except:
        pass
    
    try:
        # Method 2: Check CPU info
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = f.read()
            return 'raspberry' in cpu_info.lower() or 'bcm' in cpu_info.lower()
    except:
        pass
    
    try:
        # Method 3: Check environment variable
        if os.environ.get('RASPBERRY_PI'):
            return True
    except:
        pass
    
    # Method 4: Check if RPi.GPIO is available
    try:
        import RPi.GPIO
        return True
    except ImportError:
        pass
    
    return False

def _create_mock_gpio():
    """Create a mock GPIO controller."""
    try:
        from .gpio_mock import GPIOController
        return GPIOController()
    except ImportError as e:
        logger.error(f"Mock GPIO not available: {e}")
        raise ImportError("No GPIO controller available")

# Convenience function for direct import
def get_gpio():
    """Get the appropriate GPIO controller."""
    return create_gpio_controller()
