import asyncio
import websockets
import json


async def chat(user_id: str):
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        # Gửi user_id khi kết nối
        await websocket.send(json.dumps({"user_id": user_id}))
        print(f"[{user_id}] đã kết nối!")

        while True:
            prompt = input(f"\n[{user_id}] Bạn: ")
            if prompt == "quit":
                break

            await websocket.send(json.dumps({
                "type": "prompt",
                "prompt": prompt
            }))

            print(f"[{user_id}] AI: ", end="", flush=True)
            async for message in websocket:
                data = json.loads(message)
                if data["type"] == "token":
                    print(data["data"], end=" ", flush=True)
                elif data["type"] == "done":
                    print()
                    break


if __name__ == "__main__":
    import sys

    user_id = sys.argv[1] if len(sys.argv) > 1 else "userA"
    asyncio.run(chat(user_id))