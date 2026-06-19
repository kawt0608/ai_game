import RPi.GPIO as GPIO
import time
import json
from datetime import datetime

# =========================
# GPIO設定
# =========================
# GPIO.BCMなので、数字はGPIO番号です
# GPIO14 = 物理ピン8
# GPIO15 = 物理ピン10
#
# 測定失敗が続く場合は、
# TRIG_PIN と ECHO_PIN を入れ替えて試してください。
TRIG_PIN = 14
ECHO_PIN = 15

SPEED_OF_SOUND = 34370  # 20℃での音速 cm/s

# =========================
# 検知設定
# =========================
DETECT_DISTANCE = 50.0      # cm この距離以下で物体検知開始
RELEASE_DISTANCE = 70.0     # cm この距離より遠くなったら検知終了
MEASURE_INTERVAL = 0.2      # 秒 測定間隔

MAX_SAMPLES_PER_OBJECT = 5  # 各物体ごとの距離測定回数

# =========================
# GPIO初期化
# =========================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

GPIO.output(TRIG_PIN, GPIO.LOW)
time.sleep(0.5)

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
        "measure_interval_sec": MEASURE_INTERVAL,
        "max_samples_per_object": MAX_SAMPLES_PER_OBJECT
    },

    # センサー精度測定結果
    # 必要に応じて、実験後に手動で書き込む
    "calibration_results": [
        # 例:
        # {"actual_cm": 10, "measured_cm": 10.4},
        # {"actual_cm": 20, "measured_cm": 19.8},
        # {"actual_cm": 30, "measured_cm": 30.5}
    ],

    # 物体ごとの測定結果
    "objects": []
}


def now_text():
    """
    現在時刻を文字列で返す
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def measure_distance():
    """
    超音波距離センサーで距離を測定する関数
    戻り値:
        距離[cm]
        測定失敗時は None
    """

    # Trigを安定させる
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.000002)

    # Trigを10μsだけHIGHにする
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # EchoがHIGHになるまで待つ
    wait_start = time.time()

    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        if time.time() - wait_start > 0.1:
            print("測定失敗: EchoがHIGHにならない")
            return None

    pulse_start = time.time()

    # EchoがLOWに戻るまで待つ
    wait_start = time.time()

    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        if time.time() - wait_start > 0.1:
            print("測定失敗: EchoがLOWに戻らない")
            return None

    pulse_end = time.time()

    # 距離計算
    duration = pulse_end - pulse_start
    distance = duration * SPEED_OF_SOUND / 2

    return distance


def save_json():
    """
    data.json に保存する
    """
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_sample_to_current_object(distance, current_time):
    """
    現在検知中の物体に距離データを追加する
    ただし、各物体ごとに最大5回まで
    """

    global current_object

    if current_object is None:
        return

    samples = current_object["samples"]

    if len(samples) < MAX_SAMPLES_PER_OBJECT:
        samples.append({
            "sample_number": len(samples) + 1,
            "time": current_time,
            "distance_cm": distance
        })


def finish_current_object(end_reason):
    """
    現在検知中の物体を終了し、統計情報を追加して保存する
    """

    global current_object

    if current_object is None:
        return

    current_object["end_time"] = now_text()
    current_object["end_reason"] = end_reason

    samples = current_object["samples"]

    if len(samples) > 0:
        distances = [sample["distance_cm"] for sample in samples]

        current_object["sample_count"] = len(samples)
        current_object["min_distance_cm"] = min(distances)
        current_object["max_distance_cm"] = max(distances)
        current_object["average_distance_cm"] = round(
            sum(distances) / len(distances),
            1
        )
    else:
        current_object["sample_count"] = 0
        current_object["min_distance_cm"] = None
        current_object["max_distance_cm"] = None
        current_object["average_distance_cm"] = None

    data["objects"].append(current_object)

    current_object = None

    save_json()


try:
    print("Task1-3 距離センサー計測開始")
    print("Ctrl + C で終了")
    print("--------------------------------")

    while True:
        distance = measure_distance()
        current_time = now_text()

        # 測定失敗時
        if distance is None:
            time.sleep(MEASURE_INTERVAL)
            continue

        distance = round(distance, 1)

        print("Distance:", distance, "cm")

        # =========================
        # 物体をまだ検知していない状態
        # =========================
        if current_object is None:

            # 物体検知開始
            if distance <= DETECT_DISTANCE:
                object_count += 1

                current_object = {
                    "object_id": object_count,
                    "start_time": current_time,
                    "end_time": None,
                    "end_reason": None,
                    "samples": []
                }

                print("物体検知開始: object_id =", object_count)

                # 1回目の距離データを保存
                add_sample_to_current_object(distance, current_time)

        # =========================
        # 物体を検知中の状態
        # =========================
        else:

            # まだ物体が検知範囲内にいる
            if distance <= RELEASE_DISTANCE:
                add_sample_to_current_object(distance, current_time)

                print(
                    "検知中: object_id =",
                    current_object["object_id"],
                    " sample_count =",
                    len(current_object["samples"])
                )

            # 物体が離れた
            else:
                print("物体検知終了: object_id =", current_object["object_id"])
                finish_current_object("released")

        save_json()

        time.sleep(MEASURE_INTERVAL)

except KeyboardInterrupt:
    print("\n計測を終了します")

    # Ctrl+Cで終了したとき、検知中の物体があれば保存する
    if current_object is not None:
        finish_current_object("stopped_by_user")

    save_json()

    print("最終物体数:", object_count)
    print("data.json に保存しました")

finally:
    GPIO.cleanup()
