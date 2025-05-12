"""
GPIO Mock implementation for development environment.
Uses gpiozero's mock pins for testing and development on non-Pi systems.
"""
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

# Set up mock GPIO for development
Device.pin_factory = MockFactory()

class GPIOController:
    def __init__(self):
        self.mock_mode = not self._is_running_on_pi()
        if self.mock_mode:
            print("Running in GPIO Mock mode")
        else:
            print("Running on Raspberry Pi with real GPIO")
        self.pin_states = {}  # Track pin states

    def _is_running_on_pi(self):
        """Check if we're running on a Raspberry Pi."""
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as f:
                return 'raspberry pi' in f.read().lower()
        except:
            return False

    def setup_pin(self, pin_number, mode='OUT'):
        """Set up a GPIO pin."""
        # In mock mode, this is handled by gpiozero
        self.pin_states[pin_number] = 0  # Initialize pin state to 0
        print(f"Setting up pin {pin_number} as {mode}")

    def set_pin(self, pin_number, value):
        """Set a GPIO pin high or low."""
        # In mock mode, this is handled by gpiozero
        self.pin_states[pin_number] = value
        print(f"Setting pin {pin_number} to {value}")

    def get_pin_state(self, pin_number):
        """Get the current state of a GPIO pin."""
        return self.pin_states.get(pin_number, 0)

    def cleanup(self):
        """Clean up GPIO resources."""
        # In mock mode, this is handled by gpiozero
        self.pin_states.clear()
        print("GPIO resources cleaned up")
