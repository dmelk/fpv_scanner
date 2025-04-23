
import time
import sys


def main(rssi):
    ADC_DIR = "/sys/bus/iio/devices/iio:device0"
    rssi_file = f"{ADC_DIR}/in_voltage{rssi}_raw"
    with open(rssi_file, "r") as file:
        value = float(file.read().strip())
        file.close()
    print(f"rssi: {value}")
    time.sleep(0.5)
    main(rssi)

if __name__ == "__main__":
    # read rssi from command line
    if len(sys.argv) > 1:
        rssi = int(sys.argv[1])
    else:
        rssi = 1
    main(rssi)

