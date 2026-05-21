import asyncio
import websockets
import json

# Lưu tất cả connections đang active
connected_users = {}  # {user_id: websocket}


async def stream_ai_response(websocket, user_id, prompt):
    """Giả lập AI generate token - chạy độc lập cho từng user"""
    print(f"[{user_id}] hỏi: {prompt}")

    words = f"Xin chào {user_id}! Câu trả lời cho '{prompt}' là đây nè!".split()

    for word in words:
        # Kiểm tra user còn kết nối không
        if user_id not in connected_users:
            print(f"[{user_id}] đã ngắt kết nối, dừng generate")
            break

        await websocket.send(json.dumps({
            "type": "token",
            "data": word
        }))
        await asyncio.sleep(0.1)

    await websocket.send(json.dumps({"type": "done"}))


async def chat_handler(websocket):
    user_id = None

    try:
        # Nhận user_id đầu tiên khi kết nối
        init = await websocket.recv()
        data = json.loads(init)
        user_id = data.get("user_id", f"user_{id(websocket)}")

        connected_users[user_id] = websocket
        print(f"[{user_id}] đã kết nối | Tổng: {len(connected_users)} users")

        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "prompt":
                # Chạy generate KHÔNG block các user khác
                asyncio.create_task(
                    stream_ai_response(websocket, user_id, data["prompt"])
                )

    except websockets.exceptions.ConnectionClosed:
        print(f"[{user_id}] ngắt kết nối")

    finally:
        if user_id in connected_users:
            del connected_users[user_id]
        print(f"Còn lại: {len(connected_users)} users")


async def main():
    print("Server chạy tại ws://localhost:8765")
    async with websockets.serve(chat_handler, "localhost", 8765):
        await asyncio.Future()


asyncio.run(main())