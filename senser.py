{
  "created_at": "2026-06-19 10:30:00",
  "sensor_setting": {
    "trig_pin": 14,
    "echo_pin": 15,
    "detect_distance_cm": 50.0,
    "release_distance_cm": 70.0,
    "measure_interval_sec": 0.2import RPi.GPIO as GPIO
import time
import sys
import json
from datetime import datetime

# =========================
# GPIO設定
# =========================
# GPIO.BCMなので、数字はGPIO番号
# GPIO14 = 物理ピン8
# GPIO15 = 物理ピン10
TRIG_PIN = 14
ECHO_PIN = 15

SPEED_OF_SOUND = 34370  # 20℃での音速 cm/s

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# =========================
# 検知設定
# =========================
DETECT_DISTANCE = 50.0     # cm この距離以下なら物体検知
RELEASE_DISTANCE = 70.0    # cm この距離より遠くなったら検知終了
MEASURE_INTERVAL = 0.2     # 秒 測定間隔

# =========================
# 状態管理
# =========================
object_count = 0
current_object = None

# =========================
# 保存用データ
# =========================
data = {
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

    "sensor_setting": {
        "trig_pin": TRIG_PIN,
        "echo_pin": ECHO_PIN,
        "detect_distance_cm": DETECT_DISTANCE,
        "release_distance_cm": RELEASE_DISTANCE,
        "measure_interval_sec": MEASURE_INTERVAL
    },

    # センサー精度測定結果
    # 実験後に自分で実測値を入れる
    "calibration_results": [
        # 例:
        # {"actual_cm": 10, "measured_cm": 10.4},
        # {"actual_cm": 20, "measured_cm": 19.7},
        # {"actual_cm": 30, "measured_cm": 30.2}
    ],

    # 計測中すべての距離
    "all_measurements": [],

    # 物体ごとの距離データ
    "objects": []
}


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def measure_distance():
    """
    距離を測定する関数
    戻り値:
      距離[cm]
      測定失敗時は None
    """

    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.000002)

    # Trigを10μsだけHIGHにする
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # EchoがHIGHになるのを待つ
    timeout_start = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        pulse_start = time.time()

        if pulse_start - timeout_start > 0.1:
            print("測定失敗: EchoがHIGHにならない")
            return None

    # EchoがLOWに戻るのを待つ
    timeout_start = time.time()
    pulse_end = pulse_start

    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        pulse_end = time.time()

        if pulse_end - timeout_start > 0.1:
            print("測定失敗: EchoがLOWに戻らない")
            return None

    duration = pulse_end - pulse_start
    distance = duration * SPEED_OF_SOUND / 2

    return distance


def save_json():
    """
    data.json に保存する
    """

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def finish_current_object():
    """
    現在検知中の物体を終了処理する
    """

    global current_object

    if current_object is None:
        return

    current_object["end_time"] = now_text()

    samples = current_object["samples"]

    if len(samples) > 0:
        distances = [sample["distance_cm"] for sample in samples]

        current_object["sample_count"] = len(samples)
        current_object["min_distance_cm"] = min(distances)
        current_object["max_distance_cm"] = max(distances)
        current_object["average_distance_cm"] = round(
            sum(distances) / len(distances), 1
        )
    else:
        current_object["sample_count"] = 0
        current_object["min_distance_cm"] = None
        current_object["max_distance_cm"] = None
        current_object["average_distance_cm"] = None

    data["objects"].append(current_object)
    current_object = None


try:
    print("Task1-3 距離センサー計測開始")
    print("Ctrl + C で終了")
    print("--------------------------------")

    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.5)

    while True:
        distance = measure_distance()
        current_time = now_text()

        # 測定失敗時
        if distance is None:
            data["all_measurements"].append({
                "time": current_time,
                "distance_cm": None,
                "status": "failed",
                "object_id": None
            })

            save_json()
            time.sleep(MEASURE_INTERVAL)
            continue

        distance = round(distance, 1)

        # 現在の測定データを全体ログに保存
        measurement_log = {
            "time": current_time,
            "distance_cm": distance,
            "status": "success",
            "object_id": None
        }

        # =========================
        # 物体検知開始
        # =========================
        if current_object is None and distance <= DETECT_DISTANCE:
            object_count += 1

            current_object = {
                "object_id": object_count,
                "start_time": current_time,
                "end_time": None,
                "samples": []
            }

            print("物体検知開始: object_id =", object_count)

        # =========================
        # 物体検知中
        # =========================
        if current_object is not None:
            measurement_log["object_id"] = current_object["object_id"]

            # まだ物体が範囲内にある場合
            if distance <= RELEASE_DISTANCE:
                current_object["samples"].append({
                    "time": current_time,
                    "distance_cm": distance
                })

            # 物体が離れた場合
            else:
                print("物体検知終了: object_id =", current_object["object_id"])
                finish_current_object()

        data["all_measurements"].append(measurement_log)

        print(
            "Distance:",
            distance,
            "cm",
            " Object count:",
            object_count
        )

        save_json()

        time.sleep(MEASURE_INTERVAL)

except KeyboardInterrupt:
    print("\n計測を終了します")

    # 終了時に、検知中の物体があれば保存する
    if current_object is not None:
        finish_current_object()

    save_json()

    print("最終物体数:", object_count)
    print("data.json に保存しました")

    GPIO.cleanup()
    sys.exit()
  },
  "calibration_results": [],
  "all_measurements": [
    {
      "time": "2026-06-19 10:30:01.100",
      "distance_cm": 120.4,
      "status": "success",
      "object_id": null
    },
    {
      "time": "2026-06-19 10:30:01.300",
      "distance_cm": 45.2,
      "status": "success",
      "object_id": 1
    }
  ],
  "objects": [
    {
      "object_id": 1,
      "start_time": "2026-06-19 10:30:01.300",
      "end_time": "2026-06-19 10:30:02.100",
      "samples": [
        {
          "time": "2026-06-19 10:30:01.300",
          "distance_cm": 45.2
        },
        {
          "time": "2026-06-19 10:30:01.500",
          "distance_cm": 42.8
        },
        {
          "time": "2026-06-19 10:30:01.700",
          "distance_cm": 39.6
        }
      ],
      "sample_count": 3,
      "min_distance_cm": 39.6,
      "max_distance_cm": 45.2,
      "average_distance_cm": 42.5
    }
  ]
}
