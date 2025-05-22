import json
import time
import paho.mqtt.client as mqtt

from tuner_factory import TunerFactory

class TunerData:
    def __init__(self, tuner, attempts, scanning):
        self.tuner = tuner
        self.attempts = attempts
        self.scanning = scanning

max_attempts = 4
tick_time = 0.05

ping_time = 1 / tick_time

out_topic = "scanner_out"

sw_version = "0.1.0"

def scan(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    if (not tunerData.scanning):
        return
    tuner = tunerData.tuner
    if tunerData.attempts == 0:
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
            "scanning": False,
        }))
        tunerData.scanning = False
        tunerData.attempts = 0
        return
    tunerData.attempts += 1
    if tunerData.attempts == max_attempts:
        tunerData.attempts = 0

def start_scan(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    tunerData.scanning = True
    tunerData.attempts == 0
    publish_frequency(tuner_idx)

def stop(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    tunerData.scanning = False
    tunerData.attempts == 0
    publish_frequency(tuner_idx)

def next(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    tunerData.scanning = False
    tunerData.attempts == 0
    tuner = tunerData.tuner
    tuner.next()
    publish_frequency(tuner_idx)

def prev(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    tunerData.scanning = False
    tunerData.attempts == 0
    tuner = tunerData.tuner
    tuner.prev()
    publish_frequency(tuner_idx)

def set(tuner_idx, frequency):
    tunerData: TunerData = tuners[tuner_idx]
    tunerData.scanning = False
    tunerData.attempts == 0
    tuner = tunerData.tuner
    tuner.set_frequency(frequency)
    publish_frequency(tuner_idx)

def skip(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    tunerData.attempts == 0
    tuner = tunerData.tuner
    tuner.skip_frequency(tuner.get_frequency_idx())
    tuner.next()
    publish_frequency(tuner_idx)

def clear_skip(tuner_idx, idx, all_values = False):
    tunerData: TunerData = tuners[tuner_idx]
    tuner = tunerData.tuner
    tuner.clear_skip(idx, all_values)
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "clear_skip",
        "tuner_idx": tuner_idx,
        "config": tuner.get_config(),
        "scanning": tunerData.scanning,
    }))

def tune(tuner_idx, rssi_threshold):
    tunerData: TunerData = tuners[tuner_idx]
    tuner = tunerData.tuner
    tuner.set_rssi_threshold(rssi_threshold)
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "tune",
        "tuner_idx": tuner_idx,
        "config": tuner.get_config(),
        "scanning": tunerData.scanning,
    }))

def publish_frequency(tuner_idx):
    tunerData: TunerData = tuners[tuner_idx]
    tuner = tunerData.tuner
    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "frequency_change",
        "value": tuner.get_frequency_idx(),
        "frequency": tuner.get_frequency(),
        "config": tuner.get_config(),
        "scanning": tunerData.scanning,
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
        start_scan(tuner_idx)
        return
    if (action == "stop"):
        stop(tuner_idx)
        return
    if (action == "next"):
        next(tuner_idx)
        return
    if (action == "prev"):
        prev(tuner_idx)
        return
    if (action == "set"):
        set(tuner_idx, payload["value"])
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
    with open("/fpv_scanner/scanner_config.json", "r") as file:
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
        tuner_configs.append({
            "scanning": False,
            "tuner": tuner.get_config()
        })

    config_to_publish = {
        "id": scanner_id,
        "tuners": config["tuners"],
    }

    client.publish(out_topic, json.dumps({
        "scanner_id": scanner_id,
        "action": "ready",
        "sw_version": sw_version,
        "config": config_to_publish,
        "tuner_configs": tuner_configs
    }))

    ping_attempt = 0
    while True:
        try:
            client.loop(timeout=0.1)
        except Exception as e:
            print("MQTT loop error:", e)

        if not client.is_connected():
            try:
                print("Reconnecting...")
                client.reconnect()
            except Exception as e:
                print("Reconnect failed:", e)
                time.sleep(1)  # prevent tight loop on failure
            time.sleep(tick_time)
            # do not scan if not connected
            continue

        for i in range(len(tuners)):
            scan(i)
        time.sleep(tick_time)
        ping_attempt += 1
        if ping_attempt >= ping_time:
            tuner_configs = []
            for tuner in tuners:
                tuner_configs.append({
                    "scanning": tuner.scanning,
                    "tuner": tuner.tuner.get_config()
                })
            client.publish(out_topic, json.dumps({
                "scanner_id": scanner_id,
                "action": "ping",
                "sw_version": sw_version,
                "config": config_to_publish,
                "tuner_configs": tuner_configs
            }))
            ping_attempt = 0
