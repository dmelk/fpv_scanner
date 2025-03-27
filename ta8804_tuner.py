import smbus
from abstarct_tuner import AbstractTuner

class Ta8804Tuner(AbstractTuner):
    min_frequency = 900
    max_frequency = 1500
    current_frequency = min_frequency
    frequency_step = 10
    i2c_bus = None
    rssi_file = None
    i2c_address = 0x60

    skip_table = []

    ADC_DIR = "/sys/bus/iio/devices/iio:device0"

    def __init__(self, i2c, rssi, rssi_threshold, min_frequency, max_frequency):
        self.i2c = i2c
        self.rssi_file = f"{self.ADC_DIR}/in_voltage{rssi}_raw"

        self.rssi_threshold = rssi_threshold

        self.skip_table = []
        self.i2c_bus = smbus.SMBus(i2c)

        self.min_frequency = min_frequency
        self.max_frequency = max_frequency
        self.current_frequency = self.min_frequency
        self.set_frequency(self.current_frequency)

    def next(self):
        self.current_frequency += self.frequency_step
        if self.current_frequency > self.max_frequency:
            self.current_frequency = self.min_frequency
        if self.current_frequency in self.skip_table:
            self.next()
            return
        self.set_frequency(self.current_frequency)

    def prev(self):
        self.current_frequency -= self.frequency_step
        if self.current_frequency < self.min_frequency:
            self.current_frequency = self.max_frequency
        if self.current_frequency in self.skip_table:
            self.prev()
            return
        self.set_frequency(self.current_frequency)

    def is_signal_strong(self):
        with open(self.rssi_file, "r") as file:
            value = float(file.read().strip())
            file.close()
            return value > self.rssi_threshold

    def get_frequency(self):
        return self.current_frequency

    def get_frequency_idx(self):
        return self.current_frequency

    def skip_frequency(self, frequency_idx):
        if frequency_idx not in self.skip_table:
            self.skip_table.append(frequency_idx)

    def clear_skip(self, frequency_idx, all_values = False):
        if all_values:
            self.skip_table = []
        else:
            if frequency_idx in self.skip_table:
                self.skip_table.remove(frequency_idx)

    def get_config(self):
        return {
            "frequency": self.get_frequency(),
            "frequency_idx": self.get_frequency_idx(),
            "rssi_threshold": self.rssi_threshold,
            "min_frequency": self.min_frequency,
            "max_frequency": self.max_frequency,
            "skip_table": self.skip_table
        }        

    def set_frequency(self, frequency):
        delitel = frequency * 8 + 3836
        delitelH = ( delitel >> 8 ) & 0XFF
        delitelL = delitel & 0XFF

        self.i2c_bus.write_word_data(self.i2c_address, delitelH, delitelL)
        self.i2c_bus.write_byte(self.i2c_address, 0xCE)
        self.i2c_bus.write_byte(self.i2c_address, 0x00)
