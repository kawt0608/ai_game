from flask import Flask, render_template
from RPi import GPIO

app = Flask(__name__)

LED1_PIN = 16
LED2_PIN = 20


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED1_PIN, GPIO.OUT)
    GPIO.setup(LED2_PIN, GPIO.OUT)


def get_led_state(pin):
    return "ON" if GPIO.input(pin) == GPIO.HIGH else "OFF"


@app.route("/")
def index():
    return render_template(
        "index.html",
        led1=get_led_state(LED1_PIN),
        led2=get_led_state(LED2_PIN)
    )


@app.route("/led1/on")
def led1_on():
    GPIO.output(LED1_PIN, GPIO.HIGH)
    return index()


@app.route("/led1/off")
def led1_off():
    GPIO.output(LED1_PIN, GPIO.LOW)
    return index()


@app.route("/led2/on")
def led2_on():
    GPIO.output(LED2_PIN, GPIO.HIGH)
    return index()


@app.route("/led2/off")
def led2_off():
    GPIO.output(LED2_PIN, GPIO.LOW)
    return index()


if __name__ == "__main__":
    try:
        setup_gpio()
        app.run(host="0.0.0.0", port=5000)
    finally:
        GPIO.cleanup()
