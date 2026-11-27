# Kịch bản demo nội bộ

Chỉ thực hiện trong môi trường đồ án với dữ liệu giả lập; không nhập thẻ, địa chỉ hoặc tiền thật. Chưa có URL công khai. Dùng tài khoản Customer/Staff/Admin riêng, không dùng chung phiên browser; không hardcode password demo.

1. Guest xem homepage, menu; tìm/lọc/sắp xếp; chọn cỡ ly/tùy chọn, thêm vào giỏ.
2. Checkout yêu cầu đăng nhập. Đăng ký/login Customer, giỏ được giữ lại. Chọn giờ nhận hợp lệ hoặc để hệ thống chọn slot sớm nhất, xác nhận điều khoản DEMO.
3. Thanh toán MOCK_ONLINE: giả lập thất bại, kiểm tra chưa PAID; thử lại thành công. Order của người khác phải bị từ chối.
4. Staff vào queue, bắt đầu PREPARING → READY → PICKUP_WAITING → COMPLETED. Kiểm tra sổ kho trừ đúng 1 lần và điểm chỉ cộng khi hoàn tất + PAID.
5. Customer mở sản phẩm trong đơn hoàn tất, gửi review. Admin duyệt, kiểm tra review mới xuất hiện và HTML được escape.
6. Gửi contact/feedback, gắn mã đơn của chính mình. Admin xử lý. Mở chính sách và Maps minh họa; thử link fallback khi iframe bị chặn.
7. Staff nhập APP với mã tham chiếu DEMO, chọn món; giá APP khác WEB/COUNTER. Thử submit lại không nhân đôi. Ghi đối soát mô phỏng riêng, không tuyên bố gateway thật.
8. Admin xem báo cáo ngày/kênh, so sánh giá trị đơn với ghi nhận thu, xuất CSV không PII. Staff/Customer không được xem report Admin.
9. Kiểm tra kho thiếu thì PREPARING bị chặn và lưu lý do; điều chỉnh cần quyền được cấp và lý do, không được âm kho.
10. Đơn DELIVERY chưa xác minh không được pha. Staff xác minh thủ công khoảng cách 0–3 km kèm căn cứ DEMO; không mô phỏng thành định vị GPS thật.

Đính kèm screenshots và log test thật; nêu rõ ảnh thật/Maps online/public deployment vẫn chưa nghiệm thu. Tài liệu Word/PPTX/ZIP theo nhóm chỉ hoàn thiện sau khi có số nhóm, tên thành viên, tỷ lệ tham gia và URL production được xác minh.
