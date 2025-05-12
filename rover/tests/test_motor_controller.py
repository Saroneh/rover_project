"""
Test script for the motor controller using mock GPIO.
"""
import time
from rover.utils.gpio_mock import GPIOController
from rover.core.motor_controller import MotorController

def print_pin_states(motor_controller):
    """Print the current state of all motor pins."""
    print("\nCurrent Pin States:")
    print("Left Motor:")
    print(f"  Forward: {motor_controller.gpio.get_pin_state(motor_controller.left_motor_pins['forward'])}")
    print(f"  Backward: {motor_controller.gpio.get_pin_state(motor_controller.left_motor_pins['backward'])}")
    print(f"  Enable: {motor_controller.gpio.get_pin_state(motor_controller.left_motor_pins['enable'])}")
    print("Right Motor:")
    print(f"  Forward: {motor_controller.gpio.get_pin_state(motor_controller.right_motor_pins['forward'])}")
    print(f"  Backward: {motor_controller.gpio.get_pin_state(motor_controller.right_motor_pins['backward'])}")
    print(f"  Enable: {motor_controller.gpio.get_pin_state(motor_controller.right_motor_pins['enable'])}")

def test_motor_controller():
    print("Initializing GPIO controller...")
    gpio = GPIOController()
    
    print("Initializing motor controller...")
    motor_controller = MotorController(gpio)
    
    try:
        # Test forward movement
        print("\n1. Testing forward movement...")
        motor_controller.move_forward(0.5)  # 50% speed
        print_pin_states(motor_controller)
        time.sleep(2)

        # Test forward movement in seconds 
        print("\n2. Testing forward movement in seconds...")
        motor_controller.move_forward_in_seconds(0.5, 2)
        print_pin_states(motor_controller)
        time.sleep(2)

        # Test backward movement
        print("\n3. Testing backward movement...")
        motor_controller.move_backward(0.5)
        print_pin_states(motor_controller)
        time.sleep(2)
        
        # Test turning left
        print("\n4. Testing left turn...")
        motor_controller.turn_left(0.5)
        print_pin_states(motor_controller)
        time.sleep(2)
        
        # Test turning right
        print("\n4. Testing right turn...")
        motor_controller.turn_right(0.5)
        print_pin_states(motor_controller)
        time.sleep(2)
        
        # Test stop
        print("\n5. Testing stop...")
        motor_controller.stop()
        print_pin_states(motor_controller)
        time.sleep(1)
        
    finally:
        # Clean up
        print("\nCleaning up GPIO resources...")
        motor_controller.cleanup()
        print("Test completed!")

if __name__ == "__main__":
    test_motor_controller() 