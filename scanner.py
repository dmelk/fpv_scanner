import json
import time
import paho.mqtt.client as mqtt

from tuner_factory import TunerFactory

class TunerData:
    def __init__(self, tuner, attempts, scanning):
        self.tuner = tuner
        self.attempts = attempts
        self.scanning = scanning

max_attempts = 2
tick_time = 0.05

out_topic = "scanner_out"

def scan(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    if (not tunderData.scanning):
        return
    tuner = tunderData.tuner
    if (tunderData.attempts == 0):
        tuner.next()
        publish_frequency(tuner_idx)
    if tuner.is_signal_strong():
        client.publish(out_topic, json.dumps({
            "scanner_id": scanner_id,
            "action": "signal_found",
            "value": tuner.get_frequency_idx(),
            "frequency": tuner.get_frequency(),
            "tuner_idx": tuner_idx,
            "config": tuner.get_config(),
        }))
        tunderData.scanning = False
        tunderData.attempts = 0
        return
    tunderData.attempts += 1
    if (tunderData.attempts == max_attempts):
        tunderData.attempts = 0

def stop(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tunderData.scanning = False
    tunderData.attempts == 0
    publish_frequency(tuner_idx)

def next(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tunderData.scanning = False
    tunderData.attempts == 0
    tuner = tunderData.tuner
    tuner.next()
    publish_frequency(tuner_idx)

def prev(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tunderData.scanning = False
    tunderData.attempts == 0
    tuner = tunderData.tuner
    tuner.prev()
    publish_frequency(tuner_idx)

def skip(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tunderData.attempts == 0
    tuner = tunderData.tuner
    tuner.skip_frequency(tuner.get_frequency_idx())
    tuner.next()
    publish_frequency(tuner_idx)

def clear_skip(tuner_idx, idx, all_values = False):
    tunderData: TunerData = tuners[tuner_idx]
    tuner = tunderData.tuner
    tuner.clear_skip(idx, all_values)
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "clear_skip",
        "tuner_idx": tuner_idx,
        "config": tuner.get_config(),
    }))

def tune(tuner_idx, rssi_threshold):
    tunderData: TunerData = tuners[tuner_idx]
    tuner = tunderData.tuner
    tuner.set_rssi_threshold(rssi_threshold)
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "tune",
        "tuner_idx": tuner_idx,
        "config": tuner.get_config(),
    }))

def publish_frequency(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tuner = tunderData.tuner
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "frequency_change",
        "value": tuner.get_frequency_idx(),
        "frequency": tuner.get_frequency(),
        "config": tuner.get_config(),
        "tuner_idx": tuner_idx
    }))

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    if (payload["scanner_id"] != scanner_id):
        return
    action = payload["action"]
    tuner_idx = payload["tuner_idx"]
    if (tuner_idx >= len(tuners)):
        return
    if (action == "scan"):
        tuners[tuner_idx].scanning = True
        return
    if (action == "stop"):
        tuners[tuner_idx].scanning = False
        return
    if (action == "next"):
        next(tuner_idx)
        return
    if (action == "prev"):
        prev(tuner_idx)
        return
    if (action == "skip"):
        skip(tuner_idx)
        return
    if (action == "tune"):
        tune(tuner_idx, payload["value"])
        return
    if (action == "clear_skip"):
        clear_skip(tuner_idx, payload["value"], payload["all_values"] == '1')
        return
    
def on_connect(client, userdata, flags, reason_code):
    print(f"Connected with result code {reason_code}")
    client.subscribe("scanner_in")

if __name__ == '__main__':
    with open("scanner_config.json", "r") as file:
        config = json.load(file)
        file.close()

    client = mqtt.Client()
    client.username_pw_set(config["mqtt"]["user"], config["mqtt"]["password"])
    client.on_message = on_message
    client.on_connect = on_connect

    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)

    scanner_id = config["id"]
    
    tuner_factory = TunerFactory()
    tuners = []
    tuner_configs = []
    for tuner_config in config["tuners"]:
        tuner = tuner_factory.create_tuner(tuner_config["type"], tuner_config['rssi_threshold'], tuner_config["createArgs"])
        tuners.append(TunerData(tuner, 0, False))
        tuner_configs.append(tuner.get_config())

    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "ready",
        "config": config,
        "tuner_configs": tuner_configs
    }))

    while True:
        client.loop(timeout=0.1)
        for i in range(len(tuners)):
            scan(i)
        time.sleep(tick_time)
