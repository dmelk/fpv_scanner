from abstarct_tuner import AbstractTuner
from rx5808_tuner import Rx5808Tuner
from ta8804_tuner import Ta8804Tuner

class TunerFactory():
    def __init__(self):
        pass

    def create_tuner(self, tuner_type, rssi_threshold, args) -> AbstractTuner:
        if tuner_type == 'rx5808':
            return Rx5808Tuner(args['pin_mosi'], args['pin_clk'], args['pin_cs'], args['rssi'], rssi_threshold, args['min'], args['max'])
        if tuner_type == 'ta8804':
            return Ta8804Tuner(args['i2c'], args['rssi'], rssi_threshold, args['min'], args['max'])
        raise ValueError('Invalid tuner type')