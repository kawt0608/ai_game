import spidev
import time

# SPI設定
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000


def read_adc(channel):
    """MCP3008からアナログ値を読み取る"""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


try:
    print("読み取り開始（Ctrl+Cで終了）")
    print("=" * 50)

    while True:
        # CH0を読み取り
        adc_cds = read_adc(0)
        voltage_cds = (adc_cds / 1024.0) * 3.3

        # CH1を読み取り
        adc_pot = read_adc(1)
        voltage_pot = (adc_pot / 1024.0) * 3.3

        # 結果を表示
        print(
            f"CH0: ADC={adc_cds:4d}, {voltage_cds:.3f}V | "
            f"CH1: ADC={adc_pot:4d}, {voltage_pot:.3f}V"
        )

        time.sleep(1)  # 1秒待機

except KeyboardInterrupt:
    print("\nプログラム終了")

finally:
    spi.close()
