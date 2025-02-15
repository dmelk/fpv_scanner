import json
import time
import paho.mqtt.client as mqtt

from tuner_factory import TunerFactory

class TunerData:
    def __init__(self, tuner, attempts, scanning):
        self.tuner = tuner
        self.attempts = attempts
        self.scanning = scanning

max_attempts = 5
tick_time = 0.2

out_topic = "scanner_out"

def scan(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    if (not tunderData.scanning):
        return
    tuner = tunderData.tuner
    if (tunderData.attempts == 0):
        tuner.next()
        client.publish(out_topic, json.dumps({
            "scanner_id": scanner_id,
            "action": "frequency_change",
            "value": tuner.getFrequency(),
            "tuner_idx": tuner_idx
        }))
    if tuner.isSignalStrong():
        client.publish(out_topic, json.dumps({
            "scanner_id": scanner_id,
            "action": "signal_found",
            "value": tuner.getFrequency(),
            "tuner_idx": tuner_idx
        }))
        tunderData.scanning = False
        tunderData.attempts = 0
        return
    tunderData.attempts += 1
    if (tunderData.attempts == max_attempts):
        tunderData.attempts = 0

def next(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tunderData.scanning = False
    tunderData.attempts == 0
    tuner = tunderData.tuner
    tuner.next()
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "frequency_change",
        "value": tuner.getFrequency(),
        "tuner_idx": tuner_idx
    }))

def prev(tuner_idx):
    tunderData: TunerData = tuners[tuner_idx]
    tunderData.scanning = False
    tunderData.attempts == 0
    tuner = tunderData.tuner
    tuner.prev()
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "frequency_change",
        "value": tuner.getFrequency(),
        "tuner_idx": tuner_idx
    }))


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print(payload)
    return
    if (payload["scanner_id"] != scanner_id):
        return
    action = payload["action"]
    tuner_idx = payload["tuner_idx"]
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
    
def on_connect(client, userdata, flags, reason_code):
    print(f"Connected with result code {reason_code}")
    client.subscribe("scanner_in")

if __name__ == '__main__':
    with open("scanner_config.json", "r") as file:
        config = json.load(file)
        file.close()

    client = mqtt.Client()
    client.username_pw_set(config["rabbitmq"]["user"], config["rabbitmq"]["password"])
    client.on_message = on_message
    client.on_connect = on_connect

    client.connect(config["rabbitmq"]["host"], config["rabbitmq"]["port"], 60)

    scanner_id = config["id"]
    
    tuner_factory = TunerFactory()
    tuners = []
    for tuner_config in config["tuners"]:
        tuner = tuner_factory.create_tuner(tuner_config["type"], tuner_config["createArgs"])
        tuners.append(TunerData(tuner, 0, False))

    tuner_frequncies = []
    for tuner in tuners:
        tuner_frequncies.append(tuner.tuner.getFrequency())

    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "ready",
        "config": config,
        "tuner_frequncies": tuner_frequncies
    }))

    while True:
        client.loop(timeout=0.1)
        for i in range(len(tuners)):
            scan(i)
        time.sleep(tick_time)
