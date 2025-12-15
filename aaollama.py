import ollama
response = ollama.chat(
    model='deepseek-r1:7b',
    messages=[{"role": "user", "content": """
    Bạn là một hệ thống phân tích nội dung báo chí và tạo ảnh minh họa chất lượng cao.

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



Phường Bảy Hiền TPHCM thuộc địa bàn quản lý của Thuế cơ sở nào? Phường Bảy Hiền TPHCM được thành lập từ những phường cũ nào? Phường Bảy Hiền TPHCM thuộc địa bàn quản lý của Thuế cơ sở nào? Phường Bảy Hiền TPHCM được thành lập từ những phường nào sau sắp xếp? Thuế cơ sở 16 thành phố Hồ Chí Minh có cưỡng chế thi hành quyết định hành chính thuế không? Nội dung chính Phường Bảy Hiền TPHCM thuộc địa bàn quản lý của Thuế cơ sở nào? Phường Bảy Hiền TPHCM được thành lập từ những phường nào sau sắp xếp? Thuế cơ sở 16 thành phố Hồ Chí Minh có cưỡng chế thi hành quyết định hành chính thuế không? Phường Bảy Hiền TPHCM thuộc địa bàn quản lý của Thuế cơ sở nào? Căn cứ vào danh sách ban hành kèm theo Quyết định 1378/QĐ-CT năm 2025 quy định về tên gọi trụ sở và địa bàn quản lý của các thuế cơ sở thuộc thuế thành phố Hồ Chí Minh như sau: STT TÊN GỌI ĐỊA BÀN QUẢN LÝ NƠI ĐẶT TRỤ SỞ CHÍNH ... ... ... 15 Thuế cơ sở 15 Thành phố Hồ Chí Minh Phường Hạnh Thông, Phường An Nhơn, Phường Gò Vấp, Phường Thông Tây Hội, Phường An Hội Tây, Phường An Hội Đông Phường An Hội Đông 16 Thuế cơ sở 16 Thành phố Hồ Chí Minh Phường Tân Sơn Hòa, Phường Tân Sơn Nhất, Phường Tân Hòa, Phường Bảy Hiền , Phường Tân Bình, Phường Tân Sơn Phường Tân Bình 17 Thuế cơ sở 17 Thành phố Hồ Chí Minh Phường Tây Thạnh, Phường Tân Sơn Nhì, Phường Phú Thọ Hòa, Phường Phú Thạnh, Phường Tân Phú Phường Tân Sơn Nhì 18 Thuế cơ sở 18 Thành phố Hồ Chí Minh Xã Vĩnh Lộc, Xã Tân Vĩnh Lộc, Xã Bình Lợi, Xã Tân Nhựt, Xã Bình Chánh, Xã Hưng Long, Xã Bình Hưng Xã Tân Nhựt 19 Thuế cơ sở 19 Thành phố Hồ Chí Minh Xã An Nhơn Tây, Xã Thái Mỹ, Xã Nhuận Đức, Xã Tân An Hội, Xã Củ Chi, Xã Phú Hòa Đông, Xã Bình Mỹ Xã Tân An Hội 20 Thuế cơ sở 20 Thành phố Hồ Chí Minh Xã Bình Khánh, Xã Cần Giờ, Xã An Thới Đông, Xã Thạnh An Xã Cần Giờ ... ... ... ... Theo đó, phường Bảy Hiền TPHCM thuộc địa bàn quản lý của Thuế cơ sở 16 Thành phố Hồ Chí Minh. Phường Bảy Hiền TPHCM thuộc địa bàn quản lý của Thuế cơ sở nào? Phường Bảy Hiền TPHCM được thành lập từ những phường cũ nào? (Hình từ Internet) Phường Bảy Hiền TPHCM được thành lập từ những phường nào sau sắp xếp? Phường Bảy Hiền TPHCM được thành lập từ những phường nào sau sắp xếp, căn cứ theo khoản 59 Điều 1 Nghị quyết 1685/NQ-UBTVQH15 năm 2025 về sắp xếp đơn vị hành chính cấp xã của Thành phố Hồ Chí Minh có quy định như sau: Sắp xếp các đơn vị hành chính cấp xã của Thành phố Hồ Chí Minh ... 57. Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của Phường 4, Phường 5 và Phường 7 (quận Tân Bình) thành phường mới có tên gọi là phường Tân Sơn Nhất. 58. Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của Phường 6, Phường 8 và Phường 9 (quận Tân Bình) thành phường mới có tên gọi là phường Tân Hòa. 59. Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của Phường 10, Phường 11 và Phường 12 (quận Tân Bình) thành phường mới có tên gọi là phường Bảy Hiền . 60. Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của Phường 13 và Phường 14 (quận Tân Bình), một phần diện tích tự nhiên, quy mô dân số của Phường 15 (quận Tân Bình) thành phường mới có tên gọi là phường Tân Bình. ... Theo đó, phường Bảy Hiền TPHCM được hình thành từ những phường sau: (1) Phường 10 (quận Tân Bình) (2) Phường 11 (quận Tân Bình) (3) Phường 12 (quận Tân Bình) Thuế cơ sở 16 thành phố Hồ Chí Minh có cưỡng chế thi hành quyết định hành chính thuế không? Căn cứ Điều 2 Quy định ban hành kèm theo Quyết định 1377/QĐ-CT năm 2025 quy định về nhiệm vụ quyền hạn của Thuế cơ sở như sau: Nhiệm vụ, quyền hạn 1. Tổ chức thực hiện nhiệm vụ quản lý thuế đối với người nộp thuế thuộc phạm vi quản lý của Thuế cơ sở về đăng ký thuế, khai thuế, tính thuế, thông báo thuế, nộp thuế, hoàn thuế, khấu trừ thuế, miễn thuế, giảm thuế; quản lý nghĩa vụ người nộp thuế; giám sát hồ sơ khai thuế tại trụ sở cơ quan thuế, kiểm tra tại trụ sở người nộp thuế; đăng ký, sử dụng và tiếp nhận dữ liệu hóa đơn, chứng từ, cấp hóa đơn điện tử có mã của cơ quan thuế; quản lý nợ thuế; gia hạn nộp thuế; khoanh tiền thuế nợ; xóa nợ tiền thuế, tiền chậm nộp, tiền phạt, nộp dần tiền thuế nợ; miễn tiền chậm nộp; không tính tiển chậm nộp và cưỡng chế thu tiền thuế nợ, (sau đây gọi chung là quản lý nghiệp vụ thuế) và các nghiệp vụ khác có liên quan đến quản lý nghĩa vụ thuế của người nộp thuế. 2. Thực hiện công tác phân tích, dự báo, lập, triển khai thực hiện dự toán, thống kê, kế toán, quyết toán thu ngân sách nhà nước, báo cáo tài chính nhà nước đối với những nguồn thu được phân công quản lý; tổ chức thực hiện các giải pháp đảm bảo nguồn thu, chống thất thu ngân sách nhà nước. Phân tích, tổng hợp, đánh giá công tác quản lý thuế; tham mưu với cấp ủy, chính quyền địa phương về lập dự toán thu ngân sách nhà nước, về công tác quản lý thuế trên địa bàn; chủ trì và phối hợp với các ngành, cơ quan, đơn vị liên quan để thực hiện nhiệm vụ được giao; theo dõi, tổng hợp báo cáo kết quả thực hiện thu ngân sách. 3. Cung cấp thông tin, tài liệu để thực hiện nghĩa vụ, quyền lợi về thuế, hướng dẫn thực hiện, giải đáp vướng mắc về chính sách thuế, quản lý thuế cho người nộp thuế; tổ chức tuyên truyền, hỗ trợ người nộp thuế thực hiện các thủ tục hành chính về thuế và thực hiện nghĩa vụ thuế theo quy định của pháp luật. 4. Được yêu cầu người nộp thuế, các cơ quan Nhà nước, các tổ chức, cá nhân có liên quan cung cấp thông tin cho việc quản lý thu thuế, đề nghị cơ quan có thẩm quyền xử lý các tổ chức, cá nhân không thực hiện trách nhiệm trọng việc phối hợp với cơ quan thuế để thu thuế vào ngân sách nhà nước. 5. Được ấn định thuế, thực hiện các biện pháp quản lý nợ và cưỡng chế thi hành quyết định hành chính thuế theo quy định của pháp luật; thông báo trên các phương tiện thông tin đại chúng đối với người nộp thuế vi phạm pháp luật thuế. 6. Bồi thường thiệt hại cho người nộp thuế theo quy định của pháp luật về trách nhiệm bồi thường của nhà nước; giữ bí mật thông tin của người nộp thuế; xác nhận việc thực hiện nghĩa vụ thuế, cung cấp thông tin của người nộp thuể theo quy định của pháp luật thuộc phạm vi quản lý của Thuế cơ sở. ... Như vậy, cưỡng chế thi hành quyết định hành chính thuế theo quy định của pháp luật là một trong những nhiệm vụ quyền hạn của Thuế cơ sở 16 thành phố Hồ Chí Minh nói riêng và Thuế cơ sở nói chung.
    """}]
)

print(response["message"]["content"])



