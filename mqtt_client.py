import paho.mqtt.client as mqtt
import json
from queue import Queue
import os
from dotenv import load_dotenv

load_dotenv()

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.message_queue = Queue()
        self.connected = False
        
        # Configuration from .env
        self.broker = os.getenv("MQTT_BROKER")
        self.port = int(os.getenv("MQTT_PORT"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        self.device_uid = os.getenv("DEVICE_UID")
        
        # Kincony-specific topics
        self.command_topic = f"COLB/{self.device_uid}/command"
        self.state_topic = f"COLB/{self.device_uid}/state"
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.client.subscribe(self.state_topic)
            self.message_queue.put(("connect", "Connected to MQTT Broker"))
        else:
            self.message_queue.put(("error", f"Connection failed with code {rc}"))
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.message_queue.put(("message", payload))
        except Exception as e:
            self.message_queue.put(("error", f"Message error: {str(e)}"))
    
    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            self.message_queue.put(("error", f"Connection error: {str(e)}"))
    
    def publish_command(self, relay_num, state):
        """Send command to control relay (1-32)"""
        cmd = {
            f"R{relay_num}": {
                "on": 1 if state else 0
            }
        }
        self.client.publish(self.command_topic, json.dumps(cmd))
    
    def request_state(self):
        """Request full device state update"""
        self.client.publish(self.command_topic, json.dumps({"get": "all"}))
    
    def get_messages(self):
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages