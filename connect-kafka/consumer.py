from confluent_kafka import Consumer

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'bot-data-processors',
    'auto.offset.reset': 'latest'
}

consumer = Consumer(conf)
consumer.subscribe(['bot-agent'])

try:
    while True:
        msg = consumer.poll(1.0) # Timeout in seconds
        if msg is None: continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        print(f"Received message: {msg.value().decode('utf-8')}")
finally:
    consumer.close()