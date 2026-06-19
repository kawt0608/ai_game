import RPi.GPIO as GPIO
import time
import sys
import json
from datetime import datetime

# =========================
# GPIO設定
# =========================
trig_pin = 14      # GPIO14
echo_pin = 15      # GPIO15

speed_of_sound = 34370  # 20℃での音速 cm/s

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(trig_pin, GPIO.OUT)
GPIO.setup(echo_pin, GPIO.IN)

# =========================
# 人数カウント設定
# =========================
GATE_DISTANCE = 50.0      # cm この距離より近ければ「通過中」と判定
RELEASE_DISTANCE = 70.0   # cm この距離より離れたら次の人を検出可能にする
MEASURE_INTERVAL = 0.2    # 秒 測定間隔

count = 0
person_detected = False

# =========================
# 保存用データ
# =========================
data = {
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "sensor_setting": {
        "trig_pin": trig_pin,
        "echo_pin": echo_pin,
        "gate_distance_cm": GATE_DISTANCE,
        "release_distance_cm": RELEASE_DISTANCE
    },
    "calibration_results": [
        # 実験後に実測値と測定値を記録する
        # 例:
        # {"actual_cm": 10, "measured_cm": 10.4},
        # {"actual_cm": 20, "measured_cm": 19.8},
        # {"actual_cm": 30, "measured_cm": 30.7}
    ],
    "count_log": []
}


def measure_distance():
    """
    超音波距離センサーで距離を測定する関数
    戻り値: 距離[cm]
    """

    GPIO.output(trig_pin, GPIO.LOW)
    time.sleep(0.000002)

    # Trigピンを10μsだけHIGHにする
    GPIO.output(trig_pin, GPIO.HIGH)
    time.sleep(0.000010)
    GPIO.output(trig_pin, GPIO.LOW)

    timeout = time.time() + 0.05

    # EchoがHIGHになるまで待つ
    while GPIO.input(echo_pin) == GPIO.LOW:
        t1 = time.time()
        if time.time() > timeout:
            return None

    timeout = time.time() + 0.05

    # EchoがLOWになるまで待つ
    while GPIO.input(echo_pin) == GPIO.HIGH:
        t2 = time.time()
        if time.time() > timeout:
            return None

    # 距離 = 時間 × 音速 ÷ 2
    distance = (t2 - t1) * speed_of_sound / 2

    return distance


def save_data():
    """
    data.json と data.md を保存する関数
    """

    # JSON保存
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Markdown保存
    with open("data.md", "w", encoding="utf-8") as f:
        f.write("# Task1-3 距離センサーによるゲート通過人数計測\n\n")

        f.write("## センサー設定\n\n")
        f.write(f"- Trigピン: GPIO{trig_pin}\n")
        f.write(f"- Echoピン: GPIO{echo_pin}\n")
        f.write(f"- 通過判定距離: {GATE_DISTANCE} cm\n")
        f.write(f"- 解除判定距離: {RELEASE_DISTANCE} cm\n\n")

        f.write("## センサー精度測定結果\n\n")
        f.write("| 実際の距離[cm] | 測定値[cm] |\n")
        f.write("|---:|---:|\n")

        if len(data["calibration_results"]) == 0:
            f.write("| 未記録 | 未記録 |\n")
        else:
            for result in data["calibration_results"]:
                f.write(
                    f"| {result['actual_cm']} | {result['measured_cm']} |\n"
                )

        f.write("\n## ゲート通過人数の計測結果\n\n")
        f.write(f"- 通過人数: {count}人\n\n")

        f.write("## 計測ログ\n\n")
        f.write("| 時刻 | 距離[cm] | 通過人数 |\n")
        f.write("|---|---:|---:|\n")

        for log in data["count_log"]:
            f.write(
                f"| {log['time']} | {log['distance_cm']} | {log['count']} |\n"
            )


try:
    print("距離センサーによる人数カウントを開始します")
    print("Ctrl + C で終了します")

    while True:
        distance = measure_distance()

        if distance is None:
            print("測定失敗")
            time.sleep(MEASURE_INTERVAL)
            continue

        distance_format = "{:.1f}".format(distance)
        print("Distance:", distance_format, "cm", " Count:", count)

        # 人がゲート内に入った瞬間
        if distance < GATE_DISTANCE and person_detected is False:
            count += 1
            person_detected = True

            now = datetime.now().strftime("%H:%M:%S")

            data["count_log"].append({
                "time": now,
                "distance_cm": float(distance_format),
                "count": count
            })

            print("人を検出しました。現在の人数:", count)

        # 人がゲートから離れたら、次の人を検出可能にする
        if distance > RELEASE_DISTANCE:
            person_detected = False

        save_data()

        time.sleep(MEASURE_INTERVAL)

except KeyboardInterrupt:
    print("\n計測を終了します")
    print("最終通過人数:", count)

    save_data()

    GPIO.cleanup()
    sys.exit()
