# Menu, giá và kênh nhận món — quyết định mới nhất 31/10/2026

Nguồn: bảng giá và quy tắc chủ dự án vừa phê duyệt trong cuộc trò chuyện. Tài liệu này thay thế các giá/quy tắc mâu thuẫn ở MASTER_SPEC, APPROVED_MENU_UI_2026-10-25 và các báo cáo đối chiếu cũ. **Quyết định đã chốt; việc ghi database dev CHƯA được duyệt/thực hiện.**

Đơn vị: VND nguyên; dung tích ml.

| Mã | Món | ml | Chi phí nguyên liệu (chỉ quản trị) | WEB = COUNTER | APP |
|---|---|---:|---:|---:|---:|
| CF01 | Cà phê đen | 360 | 7.000 | 28.000 | 37.000 |
| CF02 | Cà phê sữa | 360 | 8.000 | 32.000 | 43.000 |
| CF03 | Bạc xỉu | 360 | 8.250 | 33.000 | 44.000 |
| CF04 | Cold Brew | 500 | 10.000 | 40.000 | 54.000 |
| TE01 | Trà đào | 700 | 9.500 | 38.000 | 51.000 |
| TE02 | Trà chanh | 700 | 8.500 | 34.000 | 46.000 |
| OT01 | Matcha | 700 | 12.250 | 49.000 | 66.000 |
| OT02 | Cacao sữa | 700 | 11.500 | 46.000 | 62.000 |

- Website đặt trước và nhận tại quán, WEB chỉ PICKUP. Giao hàng đặt qua sàn như ShopeeFood; không có tích hợp API hoặc link gian hàng được xác nhận. APP là giá sàn dùng cho nhập đơn thủ công hiện có.
- Mỗi món chỉ một dung tích; không tự thêm size, topping, phụ thu hoặc khuyến mại. Hạ tầng voucher/khuyến mại vẫn được giữ để đáp ứng yêu cầu môn học, không tự bật chương trình trong dev.
- Chi phí là tổng chi phí chuẩn phục vụ quản trị; không phải công thức BOM hay chứng cứ tồn kho. Không suy ra nguyên liệu/định lượng từ tổng chi phí; không hiện cost cho Customer hoặc công khai qua HTML/JSON.
- Giá hiển thị và tổng tiền phải đọc backend theo SKU/kênh. Thanh toán vẫn mô phỏng, không thu tiền thật.
- Giữ nguyên sản phẩm/SKU cũ, giá và snapshot đơn lịch sử; cần duyệt phương án triển khai bên dưới trước khi ghi dev.

[Khảo sát thực tế và phương án cần duyệt](MENU_ROLLOUT_PLAN_2026-10-31.md).
