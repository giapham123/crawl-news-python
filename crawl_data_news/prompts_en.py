# prompts.py
PROMT_CREATE_IMAGE = """You are a system that analyzes news content and creates high-quality illustrative images for Vietnamese digital journalism.

Read the provided article carefully and generate one detailed image description (image prompt) that is accurate, realistic, and suitable as a news illustration image.

🔹 IMAGE GENERATION REQUIREMENTS

The image must strictly reflect the article’s content, with no assumptions or exaggeration.

The description should be clear, specific, and visually detailed.

Style: journalistic – realistic – modern – neutral tone.

Do not add fictional characters or events.

Do not include any information not stated in the article.

Do not use real names, identifiable faces, or private information of victims.

Avoid sensational, graphic, or sensitive scenes.

🔹 VISUAL DIRECTION BY TOPIC

Economy → price charts, market trends, financial graphics

Law / Legal → courtrooms, legal documents, government authorities

Accidents → reconstructed scenes, vehicles, safety warnings

Agriculture → crops, farming activities, seasonal landscapes

Social issues → daily life, people in real situations, public spaces

🔹 OUTPUT FORMAT

Return only the image description in English

No JSON, no explanations, no extra text
ORIGINAL CONTENT:

"""
PROMT_CONTENT_META_TAG  = """Your task: Process the original content and return only 1 JSON object, wrapped inside a json code block, following this structure:
{ "body": "", "meta": "", "tags": "", "cate": "" }

REQUIREMENTS FOR body (Clean HTML)

Content: Keep the entire original article content unchanged.

Allowed HTML tags:
Only use:
<h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>, <video>, <iframe>, <source>, <img>, <strong>, <em>.

Images (<img>)

MUST use the <img> tag to display images.

URL handling:

Use the image link from data-src or data-original (if available) and put it into the standard src attribute.

If not available, keep the original src.

Absolutely do not modify image URLs, do not add any proxy.

Preserve alt and title attributes (if any).

If the image has a caption, keep it using <figcaption> or <p><em> right below the image.

Video & Embed

For .mp4 files:
Use
<video controls><source src="URL" type="video/mp4"></video>

Existing embeds (YouTube, TikTok, etc.): Keep the original <iframe>.

Formatting Rules

Remove all * or ** characters.

Do not use <blockquote>.

Do not return Markdown.

Do not wrap code inside the body.

REQUIREMENTS FOR meta (Meta Description)

Write a 150–160 character description.

Vietnamese news-style writing: concise and journalistic.

REQUIREMENTS FOR tags (SEO Tags)

List of keywords in lowercase, no abbreviations.

Separated by commas.

Returned on one single line.

REQUIREMENTS FOR cate (Category & News Type)

Choose only one category from the list:
(Xã hội, Pháp luật, Đời sống, Du lịch - Ẩm thực, Daklak, Tin nóng, Tin nổi bật)

Format:
"Category Name - News Type"

OUTPUT RULES (MANDATORY)

Return only one JSON block inside a code block.

No additional explanations.

ORIGINAL CONTENT:
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
