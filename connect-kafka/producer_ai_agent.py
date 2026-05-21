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
            "uri":"/api/v1/bot/init",
            # "uri":"/api/v1/bot/chat/sd",
            "username": "test-user",
            "password": "test-password",
            "message_id":str(uuid.uuid4()),
            "data": {
                "username": "admin",
                "password": "123456",
                "mode": "NORMAL",
                "channel_id": "test-channel",
                "agent_id": "test-agent",
                "question": "tôi muốn biết lịch bảo trì hệ thống",
                "params": {
                    "platform": "GROUPWARE",
                    "device-id": "device-groupware-12345"
                },
                "headers": {
                    "platform": "GROUPWARE",
                    "device-id": "device-groupware-12345"
                },
                "chat_history": [
                    	{
                    		"type": "human",
                    		"content": "xin chào"
                    	},
                    	# {
                    	# 	"type": "ai",
                    	# 	"content": "Chào mừng Anh/Chị đã liên hệ đến kênh Zalo OA của Công ty Tài Chính TNHH MTV Mirae Asset (Việt Nam) (“Công Ty”). Để được hỗ trợ tốt nhất, Anh/Chị vui lòng cho em biết Anh/Chị đang gặp vấn đề gì ạ hoặc Anh/Chị cần hỗ trợ về vấn đề gì ạ?"
                    	# },
                ],
                "device-id": "device-groupware-12345",
                            "conversation_status": 0,
                "user": None,
                "platform": "GROUPWARE",
            },

            # "message": {
            #     "uri": "api/v1/chat_sd",
            #     "message_id": str(uuid.uuid4()),
            #     "transactionId": f"txn-id-{1000 + i}",
            #     "data": {
            #         "id": f"bot-{i}",
            #         "name": f"Assistant Bot {i}"
            #     },
            #     "timestamp": int(time.time() * 1000)
            # },

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