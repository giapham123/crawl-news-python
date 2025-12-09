import json
import re

def clean_and_parse_json(text):
    """
    Làm sạch text JSON bị bọc bởi ``` hoặc escape
    và parse thành dict.
    """
    # Trim đầu cuối
    cleaned = text.strip()

    # Xóa ```json và ```
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    # Chuyển escape thành ký tự thật
    # cleaned = cleaned.encode("utf-8").decode("unicode_escape")

    # Loại bỏ các ký tự xuống dòng & escape
    cleaned = (
        cleaned.replace("\n", " ")
               .replace("\r", " ")
               .replace("\\", " ")
    )

    # Xóa khoảng trắng dư
    cleaned = " ".join(cleaned.split())

    # Parse JSON
    return json.loads(cleaned)


def clean_and_parse_json_html(text):
    """
    Làm sạch text JSON bị bọc bởi ```json, ```
    nhưng KHÔNG phá nội dung clean_html.
    """
    cleaned = text.strip()

    # Remove triple backticks
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # Trim lại một lần nữa
    cleaned = cleaned.strip()

    # Không replace \n hoặc \\ vì sẽ phá JSON
    # Chỉ cần parse JSON trực tiếp
    return json.loads(cleaned)

def cleanSpaceEnter(text):
    text = text.replace("\n", " ")
    # Gom nhiều khoảng trắng thành 1
    text = re.sub(r"\s+", " ", text)
    # Xóa khoảng trắng đầu và cuối
    text = text.strip()
    return text