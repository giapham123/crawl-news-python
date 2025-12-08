# # gemini_api.py
# import requests
# import json
# import time
#
# API_KEY = "AIzaSyAShXN9SbSUzDlki1bl7HPv18ZXeaNYdA0"
# MODEL_ID = "gemini-2.0-flash"
# API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"
#
#
# def generate_text(prompt: str, timeout=120, max_retries=3) -> str:
#     """
#     Gửi prompt đến Google Gemini API và trả về text.
#     Có retry + tăng timeout để tránh lỗi Read timed out.
#     """
#
#     body = {
#         "contents": [
#             {
#                 "parts": [
#                     {"text": prompt}
#                 ]
#             }
#         ]
#     }
#
#     headers = {"Content-Type": "application/json"}
#
#     for attempt in range(max_retries):
#         try:
#             response = requests.post(
#                 API_URL,
#                 headers=headers,
#                 json=body,           # dùng json thay vì data
#                 timeout=timeout      # ↑ timeout tăng lên 120s
#             )
#
#             if response.status_code != 200:
#                 print(f"⚠ API Error {response.status_code}: {response.text}")
#                 time.sleep(2)
#                 continue
#
#             data = response.json()
#
#             # Lấy text trả về
#             return data.get("candidates", [{}])[0] \
#                        .get("content", {}) \
#                        .get("parts", [{}])[0] \
#                        .get("text", "")
#
#         except requests.exceptions.Timeout:
#             print(f"⏳ Timeout attempt {attempt+1}/{max_retries}, retrying...")
#             time.sleep(2)
#
#         except Exception as e:
#             print(f"❌ Unexpected API error: {str(e)}")
#             time.sleep(2)
#
#     # Sau max retry vẫn fail → trả về lỗi
#     return "ERROR: API TIMEOUT"


# gemini_api.py
import requests
import json
import time

API_KEY = "AIzaSyApZGXhQa7olqkhcKay63mxjUY1-ZsS9Oo"
# MODEL_ID = "gemini-2.0-flash-lite"    # <<< UPDATE TẠI ĐÂY
MODEL_ID = "gemini-2.0-flash"    # <<< UPDATE TẠI ĐÂY
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"


def generate_text(prompt: str, timeout=120, max_retries=5) -> str:
    """
    Gửi prompt đến Google Gemini API và trả về text.
    Có retry + xử lý riêng lỗi 429 (quota/rate limit).
    """

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=body,
                timeout=timeout
            )

            # Nếu lỗi HTTP
            if response.status_code != 200:
                print(f"⚠ API Error {response.status_code}: {response.text}")

                # ===== XỬ LÝ 429 RIÊNG =====
                if response.status_code == 429:
                    try:
                        # Google đôi khi trả retry delay
                        retry_after = response.json().get("error", {}) \
                            .get("details", [{}])[0] \
                            .get("retryDelay", "0s")

                        # "55.364s" → 55 giây
                        if retry_after.endswith("s"):
                            delay = float(retry_after[:-1])
                        else:
                            delay = 10
                    except:
                        delay = 10

                    print(f"⏳ Quota/Ratelimit → đợi {delay} giây rồi retry...")
                    time.sleep(delay)
                    continue

                # Lỗi khác → delay nhẹ và retry
                time.sleep(2)
                continue

            # Parse JSON
            data = response.json()
            text = (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                        .get("parts", [{}])[0]
                            .get("text", "")
            )
            return text.strip()

        except requests.exceptions.Timeout:
            print(f"⏳ Timeout attempt {attempt+1}/{max_retries}…")
            time.sleep(2)

        except Exception as e:
            print(f"❌ Unexpected API error: {str(e)}")
            time.sleep(2)

    return "ERROR: API TIMEOUT"
