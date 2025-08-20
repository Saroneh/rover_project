"""
Real GPIO controller for Raspberry Pi.
Controls actual motors and hardware on the Pi.
"""
import time
import logging

logger = logging.getLogger(__name__)

class RealGPIOController:
    """Real GPIO controller for Raspberry Pi motor control."""
    
    def __init__(self):
        self.mock_mode = False
        self.pin_states = {}
        self.pwm_objects = {}
        
        # Import RPi.GPIO only when running on Pi
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self._setup_gpio()
            logger.info("Real GPIO initialized successfully")
        except ImportError:
            logger.error("RPi.GPIO not available - are you on a Raspberry Pi?")
            raise ImportError("RPi.GPIO required for real GPIO control")
    
    def _setup_gpio(self):
        """Initialize GPIO system."""
        # Set GPIO mode to BCM (GPIO pin numbers)
        self.GPIO.setmode(self.GPIO.BCM)
        
        # Disable GPIO warnings
        self.GPIO.setwarnings(False)
        
        logger.info("GPIO system initialized in BCM mode")
    
    def setup_pin(self, pin_number, mode='OUT'):
        """Set up a GPIO pin."""
        try:
            if mode == 'OUT':
                self.GPIO.setup(pin_number, self.GPIO.OUT)
                # Initialize pin to LOW
                self.GPIO.output(pin_number, self.GPIO.LOW)
                self.pin_states[pin_number] = 0
                logger.info(f"Pin {pin_number} set up as OUTPUT")
            elif mode == 'PWM':
                # For PWM pins (motor speed control)
                self.GPIO.setup(pin_number, self.GPIO.OUT)
                pwm = self.GPIO.PWM(pin_number, 1000)  # 1kHz frequency
                pwm.start(0)  # Start with 0% duty cycle
                self.pwm_objects[pin_number] = pwm
                self.pin_states[pin_number] = 0
                logger.info(f"Pin {pin_number} set up as PWM")
        except Exception as e:
            logger.error(f"Failed to setup pin {pin_number}: {e}")
            raise
    
    def set_pin(self, pin_number, value):
        """Set a GPIO pin high or low."""
        try:
            if pin_number in self.pwm_objects:
                # PWM pin - set duty cycle (0-100)
                pwm_value = max(0, min(100, int(value)))
                self.pwm_objects[pin_number].ChangeDutyCycle(pwm_value)
                self.pin_states[pin_number] = pwm_value
                logger.debug(f"PWM pin {pin_number} set to {pwm_value}%")
            else:
                # Digital pin - set high or low
                if value > 0:
                    self.GPIO.output(pin_number, self.GPIO.HIGH)
                    self.pin_states[pin_number] = 1
                else:
                    self.GPIO.output(pin_number, self.GPIO.LOW)
                    self.pin_states[pin_number] = 0
                logger.debug(f"Digital pin {pin_number} set to {value}")
        except Exception as e:
            logger.error(f"Failed to set pin {pin_number} to {value}: {e}")
            raise
    
    def get_pin_state(self, pin_number):
        """Get the current state of a GPIO pin."""
        try:
            if pin_number in self.pwm_objects:
                return self.pin_states.get(pin_number, 0)
            else:
                return self.GPIO.input(pin_number)
        except Exception as e:
            logger.error(f"Failed to get pin {pin_number} state: {e}")
            return 0
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            # Stop all PWM objects
            for pin, pwm in self.pwm_objects.items():
                pwm.stop()
                logger.info(f"PWM stopped on pin {pin}")
            
            # Clean up GPIO
            self.GPIO.cleanup()
            self.pin_states.clear()
            self.pwm_objects.clear()
            logger.info("GPIO resources cleaned up")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
