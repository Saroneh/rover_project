# rover/web/app.py

from flask import Flask, redirect, url_for
from rover.utils.gpio_mock import GPIOController
from rover.core.motor_controller import MotorController

app = Flask(__name__)

# Initialize the GPIO and MotorController
gpio = GPIOController()
motor_controller = MotorController(gpio)

@app.route('/')
def index():
    # Simple HTML page with control buttons
    return '''
        <h1>Rover Manual Control</h1>
        <form action="/forward" method="post"><button>Forward</button></form>
        <form action="/forward_in_seconds" method="post"><button>Forward in seconds</button></form>
        <form action="/backward" method="post"><button>Backward</button></form>
        <form action="/left" method="post"><button>Left</button></form>
        <form action="/right" method="post"><button>Right</button></form>
        <form action="/stop" method="post"><button>Stop</button></form>
    '''

@app.route('/forward', methods=['POST'])
def forward():
    motor_controller.move_forward(0.5)
    return redirect(url_for('index'))

@app.route('/forward_in_seconds', methods=['POST'])
def forward_in_seconds():
    motor_controller.move_forward_in_seconds(0.5, 5)
    return redirect(url_for('index'))

@app.route('/backward', methods=['POST'])
def backward():
    motor_controller.move_backward(0.5)
    return redirect(url_for('index'))

@app.route('/left', methods=['POST'])
def left():
    motor_controller.turn_left(0.5)
    return redirect(url_for('index'))

@app.route('/right', methods=['POST'])
def right():
    motor_controller.turn_right(0.5)
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    motor_controller.stop()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)