# Vận hành cloud & chuẩn bị triển khai

18/10/2026 · Asia/Ho_Chi_Minh. Đây là môi trường Codex Cloud phát triển, **chưa phải website công khai**. Không push, đăng ký dịch vụ hoặc public deploy trong phiên này.

## Phân tách tài nguyên

- Laptop/WSL: không kết nối, không sửa container/volume/.env của máy cá nhân.
- Codex Cloud: PostgreSQL 17.11 container riêng `pg_lab_postgres`, volume mới, chỉ `127.0.0.1:5432`; app role và test role giới hạn, hai DB không CONNECT chéo.
- Secrets sinh mới được lưu cục bộ 0600, không nằm trong source/Git hoặc cấu hình nháp dạng giá trị. Không nhập secrets vào chat.
- Không có tài khoản hay mật khẩu demo mặc định. Đăng ký Customer qua form; cấp Staff/Admin bằng quản trị có thẩm quyền hoặc management command có hỗ trợ nhập password an toàn.

## Startup và xác minh

Dùng README hoặc `start_skill` đã lưu trong Environment settings. Dùng checkout sẵn có `/workspace/NauCoffee-V3`; không tạo worktree mới. Dependencies/file được giữ lại không bảo đảm process sống qua task mới.

```bash
cd /workspace/NauCoffee-V3
.venv/bin/python /workspace/.nau-cloud/database.py start
.venv/bin/python scripts/verify_databases.py
.venv/bin/python scripts/verify_django_database.py
.venv/bin/python manage.py check
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Trong terminal khác chạy `scripts/local_http_smoke.py`. Không cung cấp public preview/loopback link từ onboarding. Sau sửa Python, restart process `--noreload` do chính mình đã chạy.

## Backup và restore

Khi tests đã dừng, chạy `.venv/bin/python /workspace/.nau-cloud/database.py backup`. Hai archive custom-format 0600 ở ngoài checkout; chứa dữ liệu riêng tư, không commit/upload công khai. `pg_dump` dùng snapshot nhất quán từng DB. Không đối chiếu số bản ghi của một backup với DB test vẫn đang chạy/flush fixtures.

Helper `start`:

1. Nếu có container: kiểm tra loopback binding rồi start và chạy identity/isolation verification.
2. Nếu container không còn: yêu cầu đủ credentials và hai archive đã giữ lại, tạo **volume mới**, tạo lại hai role giới hạn bằng secrets cloud hiện có rồi restore. Không xóa/reset volume cũ.
3. Thiếu prerequisite hoặc verification sai: dừng để điều tra, không sinh secrets thay thế/khôi phục đè tự động.

Đã thực hành restore vào container kiểm chứng riêng ở loopback 55432, đối chiếu identity, cấm CONNECT chéo, migrations, catalog/BOM/stock/policies. Container kiểm chứng đã dừng, volume được giữ lại. **Chưa xác minh snapshot trong task mới hoặc sau Publish.** Backup trên cùng môi trường không thay cho backup độc lập cho hệ thống kinh doanh.

## Cấu hình nháp

Đã lưu `install_script` (venv + dependencies + verify + migrate/seed/collectstatic + backup) và `start_skill` (restart DB/web, readiness và tests). Lưu draft không chạy script, không áp dụng network/runtime và không Publish.

Domains tùy chỉnh đã thêm để chuẩn bị ảnh/Maps: `images.unsplash.com`, `unsplash.com`, `www.google.com`; giữ preset package managers. Ảnh ngoài hiện trả proxy HTTP 403, chưa tải được hoặc xác nhận giấy phép cụ thể; UI tiếp tục dùng SVG. Chỉ giữ ảnh được xác minh quyền sử dụng, lưu local static cùng attribution/license, không hotlink làm dependency bắt buộc. Maps có nhãn khu vực tham khảo và link fallback; kiểm thử browser hiện chặn domain để kiểm tra fallback offline.

Người dùng xem và lưu thay đổi ở Environment settings; Publish là bước riêng khi muốn phát hành snapshot môi trường. Việc này không tương đương public deploy website.

## Gate public deployment — chưa được duyệt

Trước khi triển khai Internet, cần chủ dự án chấp thuận provider và phạm vi dữ liệu, kiểm tra gói thật sự miễn phí tại thời điểm chọn, cung cấp secrets qua UI bảo mật. Không tự đăng ký gói trả phí.

Các điều kiện chưa đủ để claim production:

- URL/HTTPS thực, `DEBUG=False`, host và CSRF origins đúng; cấu hình proxy tin cậy theo provider để tránh redirect loop hoặc tin header từ client không đáng tin.
- PostgreSQL production độc lập, TLS xác minh chứng thư qua CA chính thức; không tắt certificate/checksum/signature verification. Không dùng DB trên laptop hoặc mở 5432 công khai.
- Migrations có backup và kiểm tra target; seed chỉ theo phê duyệt, không reset dữ liệu. Seed guard hiện giới hạn tên/role/loopback dev/test: không vô hiệu guard để seed production.
- Static được phục vụ qua WhiteNoise; media uploads cần storage bền hoặc chiến lược backup được xác minh. Chưa kiểm chứng media persistence trên hosting ngoài.
- Chạy đầy đủ tests, responsive/browser QA, `/healthz/`, static, login, một đơn mock, Staff/Admin, persistence sau restart và từ mạng/thiết bị khác.
- Hoàn thiện ảnh có quyền sử dụng, kiểm tra Maps thật; xác nhận thông tin cửa hàng/chính sách trước kinh doanh.

Kiểm tra đã chạy ở cloud: `DJANGO_DEBUG=False manage.py check --deploy` không có cảnh báo; Gunicorn 2 worker trên loopback với cấu hình development trả đúng health/menu/static/contact. Điều này không xác nhận TLS/provider/public routing.
