import RPi.GPIO as GPIO
import time
import sys

# =========================
# ピン設定
# =========================
# GPIO.BCMなので、数字はGPIO番号です
# GPIO14 = 物理ピン8
# GPIO15 = 物理ピン10
TRIG_PIN = 14
ECHO_PIN = 15

SPEED_OF_SOUND = 34370  # cm/s

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

GPIO.output(TRIG_PIN, GPIO.LOW)
time.sleep(0.5)


def measure_distance():
    # TrigをLOWで安定させる
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.000002)

    # 10μsだけHIGHにして超音波を発射
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # EchoがHIGHになるまで待つ
    start_time = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        pulse_start = time.time()

        if pulse_start - start_time > 0.1:
            print("測定失敗: EchoがHIGHにならない")
            return None

    # EchoがLOWに戻るまで待つ
    start_time = time.time()
    pulse_end = pulse_start

    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        pulse_end = time.time()

        if pulse_end - start_time > 0.1:
            print("測定失敗: EchoがLOWに戻らない")
            return None

    # 距離計算
    duration = pulse_end - pulse_start
    distance = duration * SPEED_OF_SOUND / 2

    return distance


try:
    print("距離センサーテスト開始")
    print("Ctrl + C で終了")
    print("--------------------")

    while True:
        echo_state = GPIO.input(ECHO_PIN)
        print("Echo現在値:", echo_state)

        distance = measure_distance()

        if distance is not None:
            print("Distance: {:.1f} cm".format(distance))

        print("--------------------")
        time.sleep(1)

except KeyboardInterrupt:
    print("終了します")
    GPIO.cleanup()
    sys.exit()
