# prompts.py
PROMT_CREATE_IMAGE = """Bạn là một hệ thống phân tích nội dung báo chí và tạo ảnh minh họa chất lượng cao.

Hãy đọc nội dung bên dưới và tạo ra mô tả ảnh (image prompt) chi tiết, rõ ràng, phù hợp với một bài báo Việt Nam.  

=========================
YÊU CẦU TẠO HÌNH
=========================

- Phải dựa hoàn toàn vào nội dung bài viết.
- Mô tả hình ảnh rõ ràng, giàu chi tiết.
- Phong cách báo chí – thực tế – hiện đại.
- Không thêm nhân vật hư cấu.
- Không thêm thông tin không có trong bài.
- Nếu bài viết nói về:
  + kinh tế → tạo hình đồ họa, giá cả, xu hướng  
  + pháp luật → hình ảnh tòa án, văn bản, cơ quan chức năng  
  + tai nạn → hiện trường mô phỏng phù hợp  
  + nông nghiệp → cây trồng, mùa vụ, nông dân  
  + xã hội → đời sống, con người, tình huống thực tế  
- Không dùng tên thật của nạn nhân hoặc thông tin riêng tư.
- Không tạo cảnh nhạy cảm, giật gân.

=========================
ĐỊNH DẠNG TRẢ VỀ
=========================

Chỉ trả về duy nhất mô tả ảnh bằng tiếng Việt, không JSON.

=========================
NỘI DUNG GỐC:
=========================

"""
PROMT_CONTENT_META_TAG  = """Nhiệm vụ của bạn: Xử lý nội dung gốc và trả về duy nhất 1 object JSON bọc trong khối code json theo cấu trúc: { "body": "", "meta": "", "tags": "", "cate": "" }

========================= YÊU CẦU CHO body (HTML sạch)

Nội dung: Giữ nguyên đầy đủ nội dung bài viết gốc.

Thẻ HTML: Chỉ sử dụng: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>, <video>, <iframe>, <source>, <img>, <strong>, <em>.

Hình ảnh (<img>):

BẮT BUỘC sử dụng thẻ <img> để hiển thị hình ảnh.

Xử lý URL: Lấy link ảnh từ thuộc tính data-src hoặc data-original (nếu có) để đưa vào thuộc tính src chuẩn. Nếu không có, giữ nguyên src gốc.

Tuyệt đối không thay đổi đường dẫn link ảnh, không thêm proxy.

Giữ nguyên thuộc tính alt, title (nếu có).

Nếu ảnh có chú thích (caption), hãy giữ lại trong thẻ <figcaption> hoặc thẻ <p><em> ngay dưới ảnh.

Video & Embed:

Đuôi .mp4: Dùng <video controls><source src="URL" type="video/mp4"></video>.

Embed sẵn (YouTube, TikTok...): Giữ nguyên <iframe>.

Định dạng:

Xóa toàn bộ ký hiệu * hoặc **.

Không dùng <blockquote>.

Không trả về Markdown, không bọc code trong body.

========================= YÊU CẦU CHO meta (Meta Description)

Viết đoạn mô tả 150–160 ký tự. Văn phong báo chí Việt Nam, súc tích.

========================= YÊU CẦU CHO tags (Tags SEO)

Danh sách từ khóa chữ thường, không viết tắt, cách nhau bằng dấu phẩy. Trả về trên 1 dòng.

========================= YÊU CẦU CHO cate (Chuyên mục & Đánh giá)

Chọn duy nhất 1 chuyên mục từ danh sách: (Xã hội, Pháp luật, Đời sống, Du lịch - Ẩm thực, Daklak, Tin nóng, Tin nổi bật).

Định dạng: "Tên Chuyên Mục - Loại Tin".

========================= QUY TẮC ĐẦU RA (BẮT BUỘC)

Chỉ trả về duy nhất khối JSON trong Code Block. Không giải thích thêm.
========================= NỘI DUNG GỐC:
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
- BẮT BUỘC bọc toàn bộ JSON trong khối Code Block markdown ```json
- KHÔNG thêm bất kỳ chữ nào ngoài khối Code Block markdown
- KHÔNG giải thích, KHÔNG bình luận
=========================
NỘI DUNG GỐC:
=========================

"""

PROMPT_TITLE = """NỘI DUNG PROMPT MỚI (ĐÃ CẬP NHẬT)
Bạn là một hệ thống xử lý nội dung báo chí và tối ưu SEO cho website tin tức Việt Nam. Dựa trên NỘI DUNG BÀI VIẾT GỐC, hãy thực hiện chính xác các nhiệm vụ sau.

YÊU CẦU ĐẦU RA: Chỉ trả về DUY NHẤT một object JSON trong code block ```json :

JSON

{
  "title": "Title tối ưu SEO",
  "slug": "Slug chuẩn SEO",
  "focus_keyphrase": "Focus keyphrase tối ưu",
  "cate": "Danh mục duy nhất"
}
QUY TẮC CHI TIẾT:

[1] TẠO TITLE TỐI ƯU SEO

Hình thức: Bắt buộc là một câu hỏi và kết thúc bằng dấu ?

Cấm sử dụng từ "Vì sao" hoặc "Tại sao" ở đầu hoặc trong câu.

Hãy sử dụng các từ nghi vấn khác như: Như thế nào, Ra sao, Khi nào, Ở đâu, Có gì đặc biệt, Liệu có, Có nên...

Không dùng dấu hai chấm (:). Nếu cần ngắt ý, dùng từ nối (và, hay, khi, cùng...).

Ưu tiên từ khóa có Search Volume cao (>10.000), văn phong báo chí, trung lập.

Không viết tắt.

[2] TẠO SLUG CHUẨN SEO

Viết chữ thường, không dấu, không ký tự đặc biệt.

Các từ nối với nhau bằng dấu gạch ngang (-).

Không viết tắt, dựa sát vào từ khóa chính.

[3] TẠO FOCUS KEYPHRASE

Cụm từ khóa chính có lượng tìm kiếm cao nhất, sát nội dung bài viết.

Không chứa dấu chấm hoặc ký tự lạ.

[4] XÁC ĐỊNH CATE (DANH MỤC)

Chỉ chọn DUY NHẤT 01 danh mục phù hợp nhất từ danh sách sau: Xã hội, Pháp luật, Đời sống, Du lịch - Ẩm thực, Daklak, Tin nóng, Tin nổi bật.

Không được trả về nhiều hơn 1 giá trị cho trường này.

LƯU Ý BẮT BUỘC:

KHÔNG giải thích, KHÔNG bình luận thêm.

TUÂN THỦ ĐÚNG CẤU TRÚC JSON.

Các điểm tôi đã sửa đổi cho bạn:
Tại mục [1]: Thêm lệnh "Cấm sử dụng từ 'Vì sao' hoặc 'Tại sao'" và gợi ý các từ nghi vấn thay thế để tiêu đề tự nhiên hơn.

Tại mục [4]: Sửa thành "Chỉ chọn DUY NHẤT 01 danh mục" để ép hệ thống không đưa ra danh sách dài.

Cấu trúc JSON: Giữ nguyên tính tinh gọn để bạn dễ dàng nạp vào hệ thống.

========================
NỘI DUNG BÀI VIẾT GỐC
========================

"""
