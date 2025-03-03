
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

    frequency_table_orig = [
        5645, 5740, 5725, 5733, 5658, 5362, 4867, 4990, 5325, 5333, 5960, 6002,
        5665, 5760, 5745, 5752, 5695, 5399, 4884, 5020, 5348, 5373, 5980, 6028,
        5865, 5780, 5765, 5771, 5732, 5436, 4921, 5050, 5366, 5413, 6000, 6054,
        5705, 5800, 5785, 5790, 5769, 5473, 4958, 5080, 5384, 5453, 6020,
        5885, 5820, 5805, 5809, 5806, 5510, 4995, 5110, 5402, 5493, 6040,
        5905, 5840, 5825, 5828, 5843, 5547, 5032, 5140, 5420, 5533, 6060,
        5925, 5860, 5845, 5847, 5880, 5584, 5069, 5170, 5438, 5573, 
        5945, 5880, 5865, 5866, 5917, 5621, 5099, 5200, 5456, 5613, 
        5695,
    ]

    frequency_table = [
        4884, 4921, 4958, 4990, 4995, 5020, 5032, 5050, 
        5069, 5080, 5099, 5110, 5140, 5170, 5200, 5325, 
        5333, 5348, 5362, 5366, 5373, 5384, 5399, 5402, 
        5413, 5420, 5436, 5438, 5453, 5456, 5473, 5493, 
        5510, 5533, 5547, 5573, 5584, 5613, 5621, 5645, 
        5658, 5665, 5685, 5695, 5705, 5725, 5732, 5733,
        5740, 5745, 5752, 5760, 5765, 5769, 5771, 5780, 
        5785, 5790, 5800, 5805, 5806, 5809, 5820, 5825, 
        5828, 5840, 5843, 5845, 5847, 5860, 5865, 5865, 
        5866, 5880, 5880, 5885, 5905, 5917, 5925, 5945, 
        5960, 5980, 6000, 6002, 6020, 6028, 6040, 6054, 
        6060, 
    ]

    skip_table = []

    min_frequency_idx = 0
    max_frequency_idx = len(frequency_table) - 1
    current_frequency_idx = min_frequency_idx

    def __init__(self, pin_mosi, pin_clk, pin_cs, rssi, rssi_threshold, min_idx, max_idx):
        self.pin_mosi = pin_mosi
        self.pin_clk = pin_clk
        self.pin_cs = pin_cs
        self.rssi_file = f"{self.ADC_DIR}/in_voltage{rssi}_raw"

        self.min_frequency_idx = min_idx
        self.max_frequency_idx = max_idx
        self.rssi_threshold = rssi_threshold

        self.skip_table = []

        # set initial frequency to before step
        self.enableSpiMode()
        self.current_frequency_idx = self.min_frequency_idx
        self.setFrequency(self.frequency_table[self.current_frequency_idx])

    def next(self):
        self.current_frequency_idx += 1            
        if (self.current_frequency_idx > self.max_frequency_idx):
            self.current_frequency_idx = self.min_frequency_idx
        if (self.current_frequency_idx in self.skip_table):
            self.next()
            return
        self.setFrequency(self.frequency_table[self.current_frequency_idx])
    
    def prev(self):
        self.current_frequency_idx -= 1
        if (self.current_frequency_idx < self.min_frequency_idx):
            self.current_frequency_idx = self.max_frequency_idx
        if (self.current_frequency_idx in self.skip_table):
            self.prev()
            return
        self.setFrequency(self.frequency_table[self.current_frequency_idx])

    def isSignalStrong(self):
        with open(self.rssi_file, "r") as file:
            value = float(file.read().strip())
            file.close()
            return value > self.rssi_threshold
    
    def getFrequency(self):
        return self.frequency_table[self.current_frequency_idx]

    def getFrequencyIdx(self):
        return self.current_frequency_idx
    
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
            "rssi_threshold": self.rssi_threshold,
            "min_frequency": self.frequency_table[self.min_frequency_idx],
            "max_frequency": self.frequency_table[self.max_frequency_idx],
            "skip_table": self.skip_table
        }

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
