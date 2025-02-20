import smbus
from abstarct_tuner import AbstractTuner

class Ta8804Tuner(AbstractTuner):
    min_frequency = 900
    max_frequency = 1500
    current_frequency = min_frequency
    frequency_step = 10
    i2c = 3
    rssi_file = None
    i2c_address = 0x60

    skip_table = []

    ADC_DIR = "/sys/bus/iio/devices/iio:device0"

    def __init__(self, i2c, rssi, min, max):
        self.i2c = i2c
        self.rssi_file = f"{self.ADC_DIR}/in_voltage{rssi}_raw"

        self.skip_table = []

        self.min_frequency = min
        self.max_frequency = max
        self.current_frequency = self.min_frequency
        self.setFrequency(self.current_frequency)

    def next(self):
        self.current_frequency += self.frequency_step
        if (self.current_frequency > self.max_frequency):
            self.current_frequency = self.min_frequency
        if (self.current_frequency in self.skip_table):
            self.next()
            return
        self.setFrequency(self.current_frequency)

    def prev(self):
        self.current_frequency -= self.frequency_step
        if (self.current_frequency < self.min_frequency):
            self.current_frequency = self.max_frequency
        if (self.current_frequency in self.skip_table):
            self.prev()
            return
        self.setFrequency(self.current_frequency)

    def isSignalStrong(self):
        with open(self.rssi_file, "r") as file:
            value = float(file.read().strip())
            file.close()
            return value > 840

    def getFrequency(self):
        return self.current_frequency

    def getFrequencyIdx(self):
        return self.current_frequency

    def skipFrequency(self, frequency_idx):
        if (frequency_idx not in self.skip_table):
            self.skip_table.append(frequency_idx)

    def clearSkip(self, frequency_idx, all = False):
        if (all):
            self.skip_table = []
        else:
            if (frequency_idx in self.skip_table):
                self.skip_table.remove(frequency_idx)

    def getConfig(self):
        return {
            "frequency": self.getFrequency(),
            "frequency_idx": self.getFrequencyIdx(),
            "min_frequency": self.min_frequency,
            "max_frequency": self.max_frequency,
            "skip_table": self.skip_table
        }        

    def setFrequency(self, frequency):
        delitel = frequency*8 + 3836
        delitelH = delitel >> 8
        delitelL = delitel & 0XFF

        i2c_bus = smbus.SMBus(self.i2c)
        i2c_bus.write_byte(self.i2c_address, delitelH)
        i2c_bus.write_byte(self.i2c_address, delitelL)
        i2c_bus.write_byte(self.i2c_address, 0xCE)
        i2c_bus.write_byte(self.i2c_address, 0x00)
        i2c_bus.close()

