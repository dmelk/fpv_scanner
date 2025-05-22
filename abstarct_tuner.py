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
    def is_signal_strong(self):
        raise NotImplementedError

    @abstractmethod
    def set_frequency(self, frequency):
        raise NotImplementedError

    @abstractmethod
    def get_frequency(self):
        raise NotImplementedError
    
    @abstractmethod
    def get_frequency_idx(self):
        raise NotImplementedError
    
    @abstractmethod
    def skip_frequency(self, frequency_idx):
        raise NotImplementedError
    
    @abstractmethod
    def clear_skip(self, frequency_idx, all_values = False):
        raise NotImplementedError
    
    @abstractmethod
    def get_config(self):
        raise NotImplementedError

    def set_rssi_threshold(self, rssi_threshold):
        self.rssi_threshold = rssi_threshold    