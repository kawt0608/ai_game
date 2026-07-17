"""Task 3-2: show the measurement time, temperature, and humidity."""

from __future__ import annotations

from datetime import datetime

from flask import Flask, render_template


try:
    import SDL_Pi_HDC1080  # type: ignore[import-not-found]
except (ImportError, RuntimeError):
    SDL_Pi_HDC1080 = None


class SensorReader:
    def __init__(self) -> None:
        self.using_sensor = SDL_Pi_HDC1080 is not None
        self.sensor = (
            SDL_Pi_HDC1080.SDL_Pi_HDC1080()
            if self.using_sensor
            else None
        )

    def read(self) -> tuple[float, float]:
        if self.sensor is None:
            # PC上でも画面とPOST処理を確認できるサンプル値
            return 23.5, 45.2
        return self.sensor.readTemperature(), self.sensor.readHumidity()


app = Flask(__name__)
reader = SensorReader()


@app.get("/")
def index():
    return render_template("index.html", measurement=None, using_sensor=reader.using_sensor)


@app.post("/measure")
def measure():
    temperature, humidity = reader.read()
    measurement = {
        "measured_at": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
    }
    return render_template(
        "index.html",
        measurement=measurement,
        using_sensor=reader.using_sensor,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
