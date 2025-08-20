"""
Motor controller implementation for the rover.
Supports both real GPIO and mock GPIO for development.
"""
from typing import Tuple
import time
import logging

logger = logging.getLogger(__name__)

class MotorController:
    def __init__(self, gpio_controller):
        """
        Initialize the motor controller.
        
        Args:
            gpio_controller: GPIO controller instance (real or mock)
        """
        self.gpio = gpio_controller
        
        # Motor pin configuration
        self.left_motor_pins = {
            'forward': 17,  # GPIO pin for left motor forward
            'backward': 18, # GPIO pin for left motor backward
            'enable': 22    # GPIO pin for left motor enable (PWM)
        }
        
        self.right_motor_pins = {
            'forward': 23,  # GPIO pin for right motor forward
            'backward': 24, # GPIO pin for right motor backward
            'enable': 25    # GPIO pin for right motor enable (PWM)
        }
        
        # Setup GPIO pins
        self._setup_pins()
        
    def _setup_pins(self):
        """Setup all GPIO pins for motor control."""
        try:
            # Setup left motor pins
            self.gpio.setup_pin(self.left_motor_pins['forward'], 'OUT')
            self.gpio.setup_pin(self.left_motor_pins['backward'], 'OUT')
            self.gpio.setup_pin(self.left_motor_pins['enable'], 'PWM')
            
            # Setup right motor pins
            self.gpio.setup_pin(self.right_motor_pins['forward'], 'OUT')
            self.gpio.setup_pin(self.right_motor_pins['backward'], 'OUT')
            self.gpio.setup_pin(self.right_motor_pins['enable'], 'PWM')
            
            logger.info("Motor pins configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup motor pins: {e}")
            raise
        
    def move_forward(self, speed: float = 1.0):
        """Move the rover forward at specified speed (0.0 to 1.0)."""
        logger.info(f"Moving forward at speed {speed}")
        self._set_motor_direction(self.left_motor_pins, 'forward')
        self._set_motor_direction(self.right_motor_pins, 'forward')
        self._set_motor_speed(speed)

    def move_forward_in_seconds(self, speed: float = 1.0, seconds: float = 5.0):
        """
        Move the rover forward at specified speed (0.0 to 1.0) for a given number of seconds.
        This method blocks for the duration.
        """
        logger.info(f"Moving forward at speed {speed} for {seconds} seconds.")
        self._set_motor_direction(self.left_motor_pins, 'forward')
        self._set_motor_direction(self.right_motor_pins, 'forward')
        self._set_motor_speed(speed)
        time.sleep(seconds)
        self.stop()
        logger.info("Stopped moving forward.")

    def move_backward(self, speed: float = 1.0):
        """Move the rover backward at specified speed (0.0 to 1.0)."""
        logger.info(f"Moving backward at speed {speed}")
        self._set_motor_direction(self.left_motor_pins, 'backward')
        self._set_motor_direction(self.right_motor_pins, 'backward')
        self._set_motor_speed(speed)
        
    def turn_left(self, speed: float = 1.0):
        """Turn the rover left at specified speed (0.0 to 1.0)."""
        logger.info(f"Turning left at speed {speed}")
        self._set_motor_direction(self.left_motor_pins, 'backward')
        self._set_motor_direction(self.right_motor_pins, 'forward')
        self._set_motor_speed(speed)
        
    def turn_right(self, speed: float = 1.0):
        """Turn the rover right at specified speed (0.0 to 1.0)."""
        logger.info(f"Turning right at speed {speed}")
        self._set_motor_direction(self.left_motor_pins, 'forward')
        self._set_motor_direction(self.right_motor_pins, 'backward')
        self._set_motor_speed(speed)
        
    def stop(self):
        """Stop all motors."""
        logger.info("Stopping all motors")
        self._set_motor_speed(0.0)
        
    def _set_motor_direction(self, motor_pins: dict, direction: str):
        """Set motor direction (forward or backward)."""
        try:
            if direction == 'forward':
                self.gpio.set_pin(motor_pins['forward'], 1)
                self.gpio.set_pin(motor_pins['backward'], 0)
                logger.debug(f"Motor direction set to forward")
            elif direction == 'backward':
                self.gpio.set_pin(motor_pins['forward'], 0)
                self.gpio.set_pin(motor_pins['backward'], 1)
                logger.debug(f"Motor direction set to backward")
        except Exception as e:
            logger.error(f"Failed to set motor direction: {e}")
            raise
            
    def _set_motor_speed(self, speed: float):
        """Set motor speed (0.0 to 1.0)."""
        try:
            # Convert speed to PWM value (0-100)
            pwm_value = int(speed * 100)
            logger.debug(f"Setting motor speed to {pwm_value}%")
            
            # Set PWM for both motors
            self.gpio.set_pin(self.left_motor_pins['enable'], pwm_value)
            self.gpio.set_pin(self.right_motor_pins['enable'], pwm_value)
            
        except Exception as e:
            logger.error(f"Failed to set motor speed: {e}")
            raise
        
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            # Stop motors first
            self.stop()
            time.sleep(0.1)  # Brief delay to ensure motors stop
            
            # Clean up GPIO
            self.gpio.cleanup()
            logger.info("Motor controller cleaned up")
        except Exception as e:
            logger.error(f"Error during motor controller cleanup: {e}")
