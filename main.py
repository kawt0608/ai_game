import time

import spidev


VREF = 3.3
SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1_350_000


def read_adc(spi, channel):
    if channel < 0 or channel > 7:
        raise ValueError("channel must be 0-7")

    result = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((result[1] & 0x03) << 8) + result[2]


def adc_to_voltage(adc_value):
    return adc_value / 1024 * VREF


def main():
    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEVICE)
    spi.max_speed_hz = SPI_SPEED_HZ

    try:
        print("MCP3008 ADC読み取り開始（Ctrl+Cで終了）")
        print("CH0: CdSセル, CH1: 可変抵抗")
        print("-" * 50)

        while True:
            cds_adc = read_adc(spi, 0)
            cds_voltage = adc_to_voltage(cds_adc)

            variable_resistor_adc = read_adc(spi, 1)
            variable_resistor_voltage = adc_to_voltage(variable_resistor_adc)

            print(
                f"CH0 CdSセル: ADC={cds_adc:4d}, "
                f"電圧={cds_voltage:.3f} V"
            )
            print(
                f"CH1 可変抵抗: ADC={variable_resistor_adc:4d}, "
                f"電圧={variable_resistor_voltage:.3f} V"
            )
            print("-" * 50)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n読み取りを終了します。")
    finally:
        spi.close()


if __name__ == "__main__":
    main()
