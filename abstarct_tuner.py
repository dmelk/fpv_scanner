from abc import abstractmethod


class AbstractTuner:
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