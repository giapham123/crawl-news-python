import json
import time
import uuid
from confluent_kafka import Producer

conf = {
    'bootstrap.servers': "localhost:9092",
    'client.id': 'python-producer'
}

producer = Producer(conf)
TOPIC_NAME = "ai-agent"

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def send_burst_messages(count=10):
    for i in range(count):
        msg_payload = {
            "uri": "api/v1/chat_gp",
        "message_id": str(uuid.uuid4()),
        "data": {
            "mode": "NORMAL",
            "channel_id": "test-channel",
            "agent_id": "test-agent",
            "question": "CHO TÔI biết các sản pẩhm của gpfarm",
            "tool_messages": [],
            # List of MinIO image object names for multi-image detection
            "image_url": [],
           	"recursion_count": 0,
			"last_tool_name": "",
            "conversation_status": 0,
            "user": None,
            "platform": "ZALO",
        }

        }

        producer.produce(
            TOPIC_NAME,
            value=json.dumps(msg_payload).encode('utf-8'),
            callback=delivery_report
        )
        # Polling helps trigger the delivery reports
        producer.poll(0)
        time.sleep(0.5) # Space them out so you can watch the consumer

    producer.flush()

if __name__ == "__main__":
    send_burst_messages(1)