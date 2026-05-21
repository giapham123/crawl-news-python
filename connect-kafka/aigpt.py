from openai import OpenAI

# Khởi tạo client
# Đảm bảo bạn đã có API Key từ platform.openai.com
client = OpenAI(api_key="***REMOVED_OPENAI_KEY***")

def call_gpt(user_input):
    try:
        response = client.chat.completions.create(
            model="gpt-5.4",  # Hoặc "gpt-4o-mini" để tiết kiệm chi phí
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

# Ví dụ thực tế
if __name__ == "__main__":
    prompt = """{"response": "Anh/Chị hiện đang được hỗ trợ bởi Trợ lý ảo (AI Chatbot) của Tài chính Mirae Asset. Để được hỗ trợ tốt nhất, anh chị vui lòng cho em biết anh chị đang cần hỗ trợ vấn đề gì ạ", "conversation_status": 1, "identify": 2, "error_email": 0}"""
    print(f"Trả lời: {call_gpt(prompt)}")