# prompts.py

PROMT_CREATE_IMAGE = """ Bạn là một hệ thống tạo hình ảnh minh họa cho báo chí Việt Nam.

Hãy đọc kỹ nội dung bài viết bên dưới và tạo ra MỘT hình ảnh minh họa chất lượng cao, chân thực, phù hợp để đăng trong bài báo điện tử.

=========================
YÊU CẦU TẠO HÌNH
=========================

1. Hình ảnh PHẢI dựa HOÀN TOÀN vào nội dung bài viết.
2. Không suy diễn, không thêm chi tiết không được đề cập trong bài.
3. Không tạo nhân vật hư cấu, không đặt tên người thật, không dùng thông tin riêng tư.
4. Phong cách:
   - Báo chí
   - Thực tế
   - Hiện đại
   - Trung tính
5. Hình ảnh rõ nét, bố cục hợp lý, ánh sáng tự nhiên, màu sắc chân thực.
6. Không tạo cảnh giật gân, phản cảm, nhạy cảm.
7. Không thêm chữ, ký tự, tiêu đề, watermark hoặc văn bản vào hình ảnh.

=========================
ĐỊNH HƯỚNG THEO CHỦ ĐỀ
=========================

- Nếu nội dung thuộc KINH TẾ:
  → Biểu đồ, giá cả, hàng hóa, thị trường, giao dịch, xu hướng tăng/giảm.

- Nếu nội dung thuộc PHÁP LUẬT:
  → Trụ sở cơ quan chức năng, tòa án, văn bản pháp luật, hồ sơ, cảnh làm việc hành chính.

- Nếu nội dung là TAI NẠN / SỰ CỐ:
  → Hiện trường mô phỏng ở mức độ phù hợp, không máu me, không gây sốc.

- Nếu nội dung là NÔNG NGHIỆP:
  → Cây trồng, mùa vụ, đồng ruộng, nông dân lao động thực tế.

- Nếu nội dung là XÃ HỘI:
  → Đời sống thường ngày, con người, bối cảnh xã hội đúng thực tế Việt Nam.

=========================
ĐỊNH DẠNG BẮT BUỘC
=========================

- Chỉ tạo HÌNH ẢNH
- KHÔNG chèn bất kỳ chữ hoặc đoạn text nào vào hình

=========================
NỘI DUNG BÀI VIẾT
=========================

"""
# PROMT_CREATE_IMAGE = """Bạn là một hệ thống phân tích nội dung báo chí và tạo ảnh minh họa chất lượng cao.
#
# Hãy đọc nội dung bên dưới và tạo ra mô tả ảnh (image prompt) chi tiết, rõ ràng, phù hợp với một bài báo Việt Nam.
#
# =========================
# YÊU CẦU TẠO HÌNH
# =========================
#
# - Phải dựa hoàn toàn vào nội dung bài viết.
# - Mô tả hình ảnh rõ ràng, giàu chi tiết.
# - Phong cách báo chí – thực tế – hiện đại.
# - Không thêm nhân vật hư cấu.
# - Không thêm thông tin không có trong bài.
# - Nếu bài viết nói về:
#   + kinh tế → tạo hình đồ họa, giá cả, xu hướng
#   + pháp luật → hình ảnh tòa án, văn bản, cơ quan chức năng
#   + tai nạn → hiện trường mô phỏng phù hợp
#   + nông nghiệp → cây trồng, mùa vụ, nông dân
#   + xã hội → đời sống, con người, tình huống thực tế
# - Không dùng tên thật của nạn nhân hoặc thông tin riêng tư.
# - Không tạo cảnh nhạy cảm, giật gân.
#
# =========================
# ĐỊNH DẠNG TRẢ VỀ
# =========================
#
# Chỉ trả về duy nhất mô tả ảnh bằng tiếng Việt, không JSON.
#
# =========================
# NỘI DUNG GỐC:
# =========================
#
# """
PROMT_CONTENT_META_TAG = """Bạn là một hệ thống xử lý nội dung báo chí và tối ưu SEO cho website tin tức Việt Nam.

Nhiệm vụ của bạn: Xử lý nội dung bên dưới và trả về DUY NHẤT 1 object JSON theo cấu trúc xác định.

=========================
YÊU CẦU CHO body (HTML sạch)
=========================

- Giữ nguyên đầy đủ nội dung bài viết.
- Chỉ tạo HTML phần body, KHÔNG tạo <html>, <head>, <body>.
- Chuẩn hóa cấu trúc thẻ HTML:
  <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>.
- Làm nổi bật thông tin quan trọng bằng <strong> hoặc <em>.
- Xóa toàn bộ ký hiệu * hoặc **.
- KHÔNG sử dụng <blockquote>.
- Giữ nguyên tất cả hình ảnh, video và iframe.
- Chuẩn hóa ảnh:
  + Chuyển mọi data-src, data-original, lazyload, srcset → src chuẩn.
  + Giữ nguyên alt, title, caption.
- KHÔNG thêm:
  <title>, <meta>, từ khóa SEO, liên kết ngoài.
- KHÔNG trả về markdown trong nội dung body.

=========================
YÊU CẦU CHO meta (Meta Description)
=========================

- Viết đoạn mô tả dài 150–160 ký tự.
- Nội dung súc tích, chính xác, văn phong báo chí Việt Nam.
- KHÔNG thêm tiêu đề, nhãn hoặc ký hiệu.

=========================
YÊU CẦU CHO tags (SEO Tags)
=========================

- Danh sách từ khóa SEO liên quan nội dung bài viết.
- Chữ thường, không viết tắt.
- Chỉ là từ khóa, không mô tả.
- Phân tách bằng dấu phẩy.
- Trả về đúng 1 dòng.

=========================
ĐỊNH DẠNG ĐẦU RA (RẤT QUAN TRỌNG)
=========================

- Trả về DUY NHẤT 1 object JSON
- BẮT BUỘC bọc toàn bộ JSON trong khối Code Block markdown ```json
- KHÔNG thêm bất kỳ chữ nào ngoài khối Code Block markdown
- KHÔNG giải thích, KHÔNG bình luận

=========================
NỘI DUNG GỐC
=========================

"""


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
- BẮT BUỘC bọc toàn bộ JSON trong khối Code Block markdown ```json
- KHÔNG thêm bất kỳ chữ nào ngoài khối Code Block markdown
- KHÔNG giải thích, KHÔNG bình luận
---

📌 **Cuối prompt, đặt nội dung bài viết tại đây:**
"""
