# 🚗 Motor Wiring Guide for Raspberry Pi Rover - MD10C R3 Cytron

## **Required Components:**
- 2x DC Motors (for left and right wheels)
- 2x MD10C R3 Cytron Motor Driver Boards (one per motor)
- 1x Raspberry Pi (any model with GPIO)
- 1x Power Supply (12V recommended for motors)
- Jumper wires
- Breadboard (optional, for testing)

## **MD10C R3 Cytron Pinout:**
Each MD10C R3 has 3 control pins:
- **DIR** (Direction) - HIGH = forward, LOW = backward
- **PWM** (Speed) - 0-100% duty cycle for speed control
- **GND** (Ground) - Common ground connection

## **GPIO Pin Assignment:**

### **Left Motor (MD10C R3 #1):**
- **Direction**: GPIO 17 (Pin 11) → DIR pin
- **Speed**: GPIO 22 (Pin 15) → PWM pin
- **Ground**: Pi GND → GND pin

### **Right Motor (MD10C R3 #2):**
- **Direction**: GPIO 23 (Pin 16) → DIR pin  
- **Speed**: GPIO 25 (Pin 22) → PWM pin
- **Ground**: Pi GND → GND pin

## **Wiring Diagram:**

```
Raspberry Pi GPIO    Left MD10C R3    Left Motor
─────────────────    ────────────    ──────────
GPIO 17 (Pin 11) ──→ DIR ────────── Motor Direction
GPIO 22 (Pin 15) ──→ PWM ────────── Motor Speed
Pi GND ────────────→ GND ────────── Common Ground

Raspberry Pi GPIO    Right MD10C R3   Right Motor  
─────────────────    ─────────────    ───────────
GPIO 23 (Pin 16) ──→ DIR ────────── Motor Direction
GPIO 25 (Pin 22) ──→ PWM ────────── Motor Speed
Pi GND ────────────→ GND ────────── Common Ground

Power Supply:
VCC (12V) ─────────→ MD10C R3 #1 VIN
VCC (12V) ─────────→ MD10C R3 #2 VIN
GND ───────────────→ MD10C R3 #1 GND
GND ───────────────→ MD10C R3 #2 GND
```

## **MD10C R3 Setup:**

1. **Power Connections:**
   - Connect 12V power supply to VIN on both drivers
   - Connect power supply GND to GND on both drivers
   - **NO need to connect Pi 5V** - MD10C R3 has internal logic level conversion

2. **Motor Connections:**
   - Left motor to OUT1 and OUT2 on first MD10C R3
   - Right motor to OUT1 and OUT2 on second MD10C R3

3. **Control Connections:**
   - GPIO direction pins to DIR pins
   - GPIO PWM pins to PWM pins
   - Pi GND to GND pins on both drivers

## **Advantages of MD10C R3 over L298N:**

✅ **Simpler wiring** - Only 3 control pins per motor  
✅ **Better efficiency** - Less heat generation  
✅ **Built-in protection** - Overcurrent, overvoltage protection  
✅ **Logic level conversion** - Works directly with Pi's 3.3V GPIO  
✅ **Higher current rating** - Can handle more powerful motors  
✅ **Cleaner signals** - Better PWM control  

## **Testing Your Setup:**

### **1. Install Dependencies:**
```bash
# On your Raspberry Pi
pip3 install -r requirements_pi.txt
```

### **2. Test GPIO Access:**
```bash
# Check if you can access GPIO
sudo python3 -c "import RPi.GPIO as GPIO; print('GPIO access OK')"
```

### **3. Test Individual Motors:**
```bash
# Test left motor
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # DIR
GPIO.setup(22, GPIO.OUT)  # PWM
GPIO.output(17, GPIO.HIGH)  # Forward
GPIO.output(22, GPIO.HIGH)  # Full speed
print('Left motor should move forward')
input('Press Enter to stop...')
GPIO.output(22, GPIO.LOW)   # Stop
GPIO.cleanup()
"
```

### **4. Run Motor Test:**
```bash
# Test full motor controller
python3 -m rover.tests.test_motor_controller
```

### **5. Run Full System:**
```bash
# Start the unified web interface
python3 -m rover.web.unified_app
```

## **Troubleshooting:**

### **"GPIO Access Denied" Error:**
```bash
# Add your user to the gpio group
sudo usermod -a -G gpio $USER

# Or run with sudo (not recommended for production)
sudo python3 -m rover.web.unified_app
```

### **Motors Not Moving:**
1. Check power supply voltage (should be 12V)
2. Verify DIR and PWM connections
3. Check GPIO pin assignments
4. Ensure motors are properly connected to OUT1/OUT2

### **Motors Moving Wrong Direction:**
1. Swap motor wires (red/black) on OUT1/OUT2
2. Or swap DIR pin connections
3. Or modify the code to invert direction logic

### **PWM Not Working:**
1. Check PWM pin connections
2. Verify PWM pin setup in code
3. Test with simple on/off first (DIR only)

## **Safety Notes:**

⚠️ **Important Safety Warnings:**
- **Always disconnect power** before wiring
- **Double-check connections** before powering on
- **Start with low speeds** to test
- **Keep hands clear** of moving parts during testing
- **Use appropriate power supply** for your motors
- **MD10C R3 can handle up to 10A per channel**

## **Next Steps:**

1. **Wire your motors** following the MD10C R3 diagram above
2. **Install the Pi requirements** on your Raspberry Pi
3. **Test basic motor control** with the test script
4. **Run the full web interface** to control from browser
5. **Calibrate motor speeds** and directions as needed

## **Need Help?**

If you encounter issues:
1. Check the console output for error messages
2. Verify all connections match the diagram
3. Test GPIO pins individually with simple scripts
4. Check MD10C R3 documentation for your specific model

Happy building with your MD10C R3 drivers! 🤖🚗
