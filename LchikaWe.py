"""Task 3-1: control two LEDs independently from a Flask web page."""

from __future__ import annotations

import atexit
from dataclasses import dataclass

from flask import Flask, redirect, render_template, request, url_for


try:
    import RPi.GPIO as GPIO  # type: ignore[import-not-found]
except (ImportError, RuntimeError):
    GPIO = None


@dataclass
class Led:
    name: str
    pin: int
    is_on: bool = False


class LedController:
    """Keep the page usable on a PC while driving real GPIO on a Raspberry Pi."""

    def __init__(self) -> None:
        self.leds = {
            "led1": Led("LED 1", 16),
            "led2": Led("LED 2", 20),
        }
        self.using_gpio = GPIO is not None

        if self.using_gpio:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for led in self.leds.values():
                GPIO.setup(led.pin, GPIO.OUT, initial=GPIO.LOW)

    def set_state(self, led_id: str, turn_on: bool) -> None:
        led = self.leds[led_id]
        led.is_on = turn_on
        if self.using_gpio:
            GPIO.output(led.pin, GPIO.HIGH if turn_on else GPIO.LOW)

    def cleanup(self) -> None:
        if self.using_gpio:
            GPIO.cleanup([led.pin for led in self.leds.values()])


app = Flask(__name__)
controller = LedController()
atexit.register(controller.cleanup)


@app.get("/")
def index():
    return render_template(
        "index.html",
        leds=controller.leds,
        using_gpio=controller.using_gpio,
    )


@app.post("/led/<led_id>")
def change_led(led_id: str):
    if led_id not in controller.leds:
        return "Unknown LED", 404

    action = request.form.get("action")
    if action not in {"on", "off"}:
        return "Invalid action", 400

    controller.set_state(led_id, action == "on")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
