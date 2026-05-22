import os
from pathlib import Path

from openai import OpenAI

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Keep one persistent client connection
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:20128/v1")
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "cx/gpt-5.3-codex-none")

print("AI Chat Started")
print("Type 'exit' to quit\n")

# conversation memory
messages = [
    {
        "role": "system",
        "content": "You are a senior software engineer assistant."
    }
]

while True:
    question = input("You: ")

    if question.lower() == "exit":
        break

    # add user question
    messages.append({
        "role": "user",
        "content": question
    })

    try:
        # keep using same client/model connection
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3,
            stream=True
        )

        print("\nAI: ", end="", flush=True)

        full_answer = ""

        # streaming response
        for chunk in response:
            delta = chunk.choices[0].delta.content

            if delta:
                full_answer += delta
                print(delta, end="", flush=True)

        print("\n")

        # save assistant response to history
        messages.append({
            "role": "assistant",
            "content": full_answer
        })

    except Exception as e:
        print(f"\nError: {e}\n")
