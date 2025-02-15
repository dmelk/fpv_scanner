from abstarct_tuner import AbstractTuner
from rx5808_tuner import Rx5808Tuner

class TunerFactory():
    def __init__(self):
        pass

    def create_tuner(self, tuner_type, args) -> AbstractTuner:
        if tuner_type == 'rx5808':
            return Rx5808Tuner(args['pin_mosi'], args['pin_clk'], args['pin_cs'], args['rssi'])
        raise ValueError('Invalid tuner type')