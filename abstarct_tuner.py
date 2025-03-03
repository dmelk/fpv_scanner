from abc import abstractmethod


class AbstractTuner:
    rssi_threshold = 1000

    @abstractmethod
    def next(self):
        raise NotImplementedError
    
    @abstractmethod
    def prev(self):
        raise NotImplementedError
    
    @abstractmethod
    def isSignalStrong(self):
        raise NotImplementedError
    
    @abstractmethod
    def getFrequency(self):
        raise NotImplementedError
    
    @abstractmethod
    def getFrequencyIdx(self):
        raise NotImplementedError
    
    @abstractmethod
    def skipFrequency(self, frequency_idx):
        raise NotImplementedError
    
    @abstractmethod
    def clearSkip(self, frequency_idx, all = False):
        raise NotImplementedError
    
    @abstractmethod
    def getConfig(self):
        raise NotImplementedError

    def setRssiTrheshold(self, rssi_threshold):
        self.rssi_threshold = rssi_threshold    