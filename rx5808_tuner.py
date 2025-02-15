
import time
import sys
from periphery import GPIO

from abstarct_tuner import AbstractTuner

class Rx5808Tuner(AbstractTuner):
    pin_mosi = 55
    pin_clk = 54
    pin_cs = 53

    low = False
    high = True

    bit_bang_freq = 10000
    reg_b = 0x01
    write_cntrl_bit = 0x01
    packet_length = 25

    ADC_DIR = "/sys/bus/iio/devices/iio:device0"
    rssi_file = ''

    spi_mode_enabled = False    

    frequency_table = [
        4990, 5020, 5050, 5080, 5110, 5140, 5170, 5200,
        5333, 5373, 5413, 5453, 5493, 5533, 5573, 5613,
        5645, 5658, 5665, 5685, 5695, 5705, 5725, 5732, 
        5733, 5740, 5745, 5752, 5760, 5765, 5769, 5771, 
        5780, 5785, 5790, 5800, 5805, 5806, 5809, 5820, 
        5825, 5828, 5840, 5843, 5845, 5847, 5860, 5865,
        5866, 5880, 5880, 5885, 5905, 5917, 5925, 5945,
    ]

    min_frequency = 4890
    max_frequency = 6050
    current_frequency = min_frequency
    freq_step = 10

    def __init__(self, pin_mosi, pin_clk, pin_cs, rssi):
        self.pin_mosi = pin_mosi
        self.pin_clk = pin_clk
        self.pin_cs = pin_cs
        self.rssi_file = f"{self.ADC_DIR}/in_voltage{rssi}_raw"
        # set initial frequency to before step
        self.enableSpiMode()
        self.current_frequency = self.min_frequency
        self.setFrequency(self.current_frequency)

    def next(self):
        self.current_frequency += self.freq_step
        if (self.current_frequency > self.max_frequency):
            self.current_frequency = self.min_frequency
        self.setFrequency(self.current_frequency)
    
    def prev(self):
        self.current_frequency -= self.freq_step
        if (self.current_frequency < self.min_frequency):
            self.current_frequency = self.max_frequency
        self.setFrequency(self.current_frequency)

    def isSignalStrong(self):
        with open(self.rssi_file, "r") as file:
            value = float(file.read().strip())
            file.close()
            return value > 840
    
    def getFrequency(self):
        return self.current_frequency

    def enableSpiMode(self):
        self.write_mosi = GPIO(self.pin_mosi, "out")
        self.write_clk = GPIO(self.pin_clk, "out")
        self.write_cs = GPIO(self.pin_cs, "out")

        self.write_mosi.write(self.low)
        self.write_clk.write(self.low)
        self.write_cs.write(self.high)

        self.spi_mode_enabled = True

    def finish(self):
        self.write_mosi.close()
        self.write_clk.close()
        self.write_cs.close()
        self.spi_mode_enabled = False

    def setFrequency(self, frequency):
        freq = (frequency - 479) // 2
        data = ((freq // 32) << 7) | (freq % 32)
        newRegisterData = self.reg_b  | (self.write_cntrl_bit << 4) | (data << 5)
        self.writeRegister(newRegisterData)

    def writeRegister(self, buf):
        if (not self.spi_mode_enabled):
            self.enableSpiMode()
        period_sec = 100.0 / self.bit_bang_freq

        self.write_cs.write(self.low)
        time.sleep(period_sec)

        for i in range(0, self.packet_length):
            self.write_clk.write(self.low)
            time.sleep(period_sec / 4)
            self.write_mosi.write(self.high if buf & 0x01 else self.low)
            time.sleep(period_sec / 4)
            self.write_clk.write(self.high)
            time.sleep(period_sec / 2)

            buf >>= 1
        
        self.write_clk.write(self.low)
        time.sleep(period_sec)
        self.write_mosi.write(self.low)
        self.write_clk.write(self.low)
        self.write_cs.write(self.high)
