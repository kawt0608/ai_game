import RPi.GPIO as GPIO
from time import sleep
import json
from datetime import datetime

# =========================
# サーボモーター設定
# =========================
SERVO_PIN = 20
FREQUENCY = 50

# =========================
# 角度とDuty比の設定
# =========================
MIN_ANGLE = 0
MAX_ANGLE = 180

# 画像のサンプルコードに合わせる
# 0度   -> 12.5%
# 90度  -> 7.5%
# 180度 -> 2.5%
MIN_DUTY = 2.5
MAX_DUTY = 12.5

# True の場合: 0度 -> 12.5%, 180度 -> 2.5%
# Falseの場合: 0度 -> 2.5%, 180度 -> 12.5%
REVERSE_DIRECTION = True

# =========================
# 保存用データ
# =========================
records = []


def angle_to_duty(angle):
    """
    角度からDuty比を求める関数
    """

    if REVERSE_DIRECTION:
        # 0度 -> 12.5%
        # 180度 -> 2.5%
        duty = MAX_DUTY - (angle / 18)
    else:
        # 0度 -> 2.5%
        # 180度 -> 12.5%
        duty = MIN_DUTY + (angle / 18)

    return duty


def get_formula_text():
    """
    data.mdやdata.jsonに書くための換算式を返す
    """

    if REVERSE_DIRECTION:
        return "Duty比(%) = 12.5 - 角度 / 18"
    else:
        return "Duty比(%) = 2.5 + 角度 / 18"


def save_json():
    """
    data.jsonを作成する
    """

    data = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "servo_setting": {
            "servo_pin": SERVO_PIN,
            "frequency_hz": FREQUENCY,
            "min_angle": MIN_ANGLE,
            "max_angle": MAX_ANGLE,
            "min_duty_percent": MIN_DUTY,
            "max_duty_percent": MAX_DUTY,
            "reverse_direction": REVERSE_DIRECTION
        },
        "conversion_formula": get_formula_text(),
        "operation_check_angles": records
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_markdown():
    """
    data.mdを作成する
    """

    with open("data.md", "w", encoding="utf-8") as f:
        f.write("# Task1-4 サーボモーター角度制御\n\n")

        f.write("## 角度からDuty比への換算式\n\n")
        f.write("サーボモーターは50Hzで制御する。\n\n")
        f.write("周期は以下のようになる。\n\n")
        f.write("```text\n")
        f.write("1 / 50 = 0.02秒 = 20ms\n")
        f.write("```\n\n")

        f.write("0度から180度までの範囲を、Duty比2.5%から12.5%に対応させる。\n\n")

        if REVERSE_DIRECTION:
            f.write("今回のプログラムでは、画像のサンプルコードに合わせて以下の対応とした。\n\n")
            f.write("- 0度: 12.5%\n")
            f.write("- 90度: 7.5%\n")
            f.write("- 180度: 2.5%\n\n")
            f.write("したがって、換算式は以下のようになる。\n\n")
            f.write("```text\n")
            f.write("Duty比(%) = 12.5 - 角度 / 18\n")
            f.write("```\n\n")
        else:
            f.write("今回のプログラムでは、以下の対応とした。\n\n")
            f.write("- 0度: 2.5%\n")
            f.write("- 90度: 7.5%\n")
            f.write("- 180度: 12.5%\n\n")
            f.write("したがって、換算式は以下のようになる。\n\n")
            f.write("```text\n")
            f.write("Duty比(%) = 2.5 + 角度 / 18\n")
            f.write("```\n\n")

        f.write("## 動作確認に使用した角度のリスト\n\n")

        if len(records) == 0:
            f.write("まだ動作確認データはない。\n\n")
        else:
            f.write("| 番号 | 入力角度[度] | Duty比[%] | 実行時刻 |\n")
            f.write("|---:|---:|---:|---|\n")

            for i, record in enumerate(records, 1):
                f.write(
                    f"| {i} | {record['angle_degree']} | "
                    f"{record['duty_percent']} | {record['time']} |\n"
                )

            f.write("\n")

        f.write("## 各角度に対応するDuty比のリスト\n\n")

        f.write("| 角度[度] | Duty比[%] |\n")
        f.write("|---:|---:|\n")

        for angle in [0, 30, 45, 60, 90, 120, 135, 150, 180]:
            duty = round(angle_to_duty(angle), 2)
            f.write(f"| {angle} | {duty} |\n")


def save_files():
    """
    data.jsonとdata.mdを両方保存する
    """

    save_json()
    save_markdown()


# =========================
# GPIO初期化
# =========================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, FREQUENCY)
pwm.start(0)

# 最初に空のdata.jsonとdata.mdを作成
save_files()

try:
    print("サーボモーター角度制御プログラム")
    print("0から180の角度を入力してください")
    print("終了する場合は q を入力してください")
    print("--------------------------------")

    while True:
        input_text = input("角度を入力してください > ")

        if input_text == "q":
            break

        try:
            angle = float(input_text)
        except ValueError:
            print("数値を入力してください")
            continue

        if angle < MIN_ANGLE or angle > MAX_ANGLE:
            print("0度から180度の範囲で入力してください")
            continue

        duty = angle_to_duty(angle)
        duty = round(duty, 2)

        print("入力角度:", angle, "度")
        print("Duty比:", duty, "%")

        # サーボモーターを指定角度へ動かす
        pwm.ChangeDutyCycle(duty)
        sleep(1)

        # サーボの振動を抑えるためDutyを0にする
        pwm.ChangeDutyCycle(0)

        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "angle_degree": angle,
            "duty_percent": duty
        }

        records.append(record)

        save_files()

        print("data.json と data.md を更新しました")
        print("--------------------------------")

except KeyboardInterrupt:
    print("\nプログラムを終了します")

finally:
    save_files()
    pwm.stop()
    GPIO.cleanup()
    print("終了しました")
