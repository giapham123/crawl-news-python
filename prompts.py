# prompts.py

PROMPT_CLEAN_HTML = """Bạn là một hệ thống xử lý nội dung báo chí và tối ưu SEO cho website tin tức Việt Nam.

Nhiệm vụ của bạn: xử lý nội dung bên dưới và trả về DUY NHẤT nội dung HTML sạch (không phải JSON).

=========================
YÊU CẦU
=========================

- Giữ nguyên đầy đủ nội dung bài viết.
- Chỉnh sửa lại cấu trúc thẻ cho chuẩn: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>.
- Làm nổi bật thông tin quan trọng bằng <strong> hoặc <em>.
- Loại bỏ toàn bộ ký hiệu * hoặc **.
- Không sử dụng <blockquote>.
- Giữ nguyên tất cả hình ảnh và video.
- Chuẩn hóa ảnh:
    + Chuyển mọi data-src, data-original, lazyload, srcset → src thực.
    + Giữ nguyên alt, title, caption.
- Giữ iframe/video hợp lệ.
- Không thêm <title>, <meta>, từ khóa SEO hoặc liên kết ngoài.
- Chỉ tạo HTML nằm trong phần <body>.

=========================
ĐẦU RA
=========================

Chỉ trả về HTML sạch, KHÔNG JSON, KHÔNG giải thích, KHÔNG markdown, KHÔNG ```.

=========================
NỘI DUNG GỐC:
=========================
"""
PROMPT_TAGS_META = """
Bạn là một hệ thống tối ưu SEO cho website tin tức Việt Nam.

Hãy đọc nội dung văn bản bên dưới và trả về duy nhất 1 object JSON chứa:
- tags
- meta_description

=========================
YÊU CẦU
=========================

2. Tags SEO:
   - Tạo danh sách từ khóa SEO.
   - Chỉ dùng chữ thường, không viết tắt.
   - Không mô tả dài dòng.
   - Các tags phân cách bằng dấu phẩy.
   - Chỉ in đúng 1 dòng.

3. Meta Description:
   - Viết đoạn mô tả 150–160 ký tự.
   - Ngắn gọn, xúc tích, liên quan đến pháp luật Việt Nam.
   - Không thêm tiêu đề hoặc nhãn.
   - Chỉ in đúng 1 dòng.

=========================
ĐỊNH DẠNG TRẢ VỀ
=========================

{
  "tags": "tag1, tag2, tag3",
  "meta_description": "Đoạn mô tả 150–160 ký tự"
}

Không giải thích thêm, không thêm text ngoài JSON.

=========================
NỘI DUNG GỐC:
=========================

"""

PROMPT_TITLE = """Dựa trên nội dung bài viết sau, hãy thực hiện 3 nhiệm vụ **theo đúng thứ tự** và **mỗi nhiệm vụ chỉ trả về 1 giá trị**, không giải thích thêm, và trả về duy nhất **một object JSON** theo định dạng:

{
  "title": "Title tối ưu SEO",
  "slug": "Slug chuẩn SEO",
  "focus_keyphrase": "Focus keyphrase tối ưu"
}

---

🎯 **[1] TẠO TITLE TỐI ƯU SEO**

Sử dụng tất cả công cụ phân tích từ khóa có thể truy cập (Google Trends, Google Keyword Planner, KeywordTool.io, Ahrefs, Semrush, Google Analytics nếu có) để chọn **title tối ưu** cho bài viết trong lĩnh vực pháp lý / luật Việt Nam, phạm vi tìm kiếm Việt Nam, 12 tháng gần nhất.

Quy tắc:
- Ưu tiên từ khóa có search volume >10.000, nếu không có thì vẫn lấy dưới 10.000.
- Title là **câu hỏi kết thúc bằng ?**
- KHÔNG sử dụng dấu hai chấm “:”.
- KHÔNG viết tắt.
- Nếu cần thay dấu hai chấm → dùng từ nối.

---

🎯 **[2] TẠO SLUG CHUẨN SEO**

Sử dụng dữ liệu từ khóa như trên để chọn **slug chuẩn SEO** cho bài viết.

Quy tắc:
- Chữ thường.
- Không chứa /
- Không viết tắt.
- Các từ nối bằng dấu "-".
- Dựa vào từ khóa có search volume cao nhất phù hợp nội dung.

---

🎯 **[3] TẠO FOCUS KEYPHRASE**

Sử dụng các công cụ phân tích từ khóa tương tự để chọn **focus keyphrase tối ưu** cho bài viết.

Quy tắc:
- Dùng cụm từ chính xác, sát nội dung nhất.
- Không dấu chấm, không ký tự lạ.
- Không viết tắt.
- Ưu tiên search volume >10.000, nếu không có thì chọn từ liên quan nhất.

---

📌 **Cuối prompt, đặt nội dung bài viết tại đây:**
"""
