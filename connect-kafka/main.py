import json
from confluent_kafka import Producer

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC_NAME = "ai-agent"

# Note: GROUP_ID is typically used by Consumers,
# but we can include it in the config if needed for certain setups.
conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'python-producer'
}

# Initialize Producer
producer = Producer(conf)

# The message payload
msg_payload = {
    "description": "Get Bot Info for Shipping & Delivery",
    "topic": "bot-agent",
    "uri": "api/v1/chat_sd",
    "message": {
        "messageId": "550e8400-e29b-41d4-a716-446655440003",
        "uri": "api/v1/chat_sd",
        "sourceId": "bot-agent",
        "transactionId": "txn-bot-info-sd-001",
        "data": {
            "id": "bot-agent-001",
            "name": "Customer Service Bot",
            "greeting": "Hello! How can I assist you today?",
            "instruction": "You are a helpful customer service assistant. Answer user questions about products and services.",
            "isSystem": 0,
            "isPublic": 1,
            "relatedQuestion": 1
        },
        "timestamp": 1713667400000
    }
}

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def send_message():
    try:
        # Trigger any available delivery report callbacks from previous produce() calls
        producer.poll(0)

        # Asynchronously produce a message
        # We serialize the dict to a JSON string, then encode to bytes
        producer.produce(
            TOPIC_NAME,
            value=json.dumps(msg_payload).encode('utf-8'),
            callback=delivery_report
        )

        # Wait for any outstanding messages to be delivered and delivery report
        # callbacks to be triggered.
        producer.flush()

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    send_message()