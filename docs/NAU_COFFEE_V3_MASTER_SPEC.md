> **17/11/2026 — Final Policy localhost:** support0003/0004 đã migrate PASS sau backup mã hóa + restore kiểm chứng.11 chính sách đã công bố, ngày01/11/2026; timestamp công bố/consent thực tế17/11, không backfill. QA434/434 PASS,270input khớp; live9nhóm và responsive27/27 PASS. PID71638, featureON/gateOPEN/sandbox. Dữ liệu cũ45bảng bảo toàn;3đơn thử mới được nhận diện. **READY FOR GITHUB REVIEW**, chưa stage/commit/push. [Báo cáo cuối](FINAL_POLICY_LOCALHOST_READINESS_2026-11-17.md). Các trạng tháiOFF/pending/PID phía dưới là lịch sử.

> **Xác nhận ngày 17/11/2026:** chủ dự án xác nhận địa chỉ 457/9 Điện Biên Phủ, phường Bàn Cờ, TP.HCM; hotline 0824672384; email naucoffee.official@gmail.com. Các câu “địa chỉ chưa xác nhận” bên dưới là bối cảnh cũ. Bộ 11 chính sách mới và consent đã qua QA nhưng chưa công bố/cutover preview; xem [báo cáo](NAU_COFFEE_POLICY_CONSENT_IMPLEMENTATION_REVIEW.md). Không đổi giá 31/10 hoặc quy tắc giờ.

# NÂU COFFEE V3 | MASTER SPECIFICATION & CODEX IMPLEMENTATION CONTRACT

> **Quyết định mới nhất31/10/2026:** [APPROVED_MENU_PRICING_2026-10-31.md](APPROVED_MENU_PRICING_2026-10-31.md) là nguồn ưu tiên cho tên/dung tích/cost/giá: WEB=COUNTER, WEB chỉ PICKUP đặt trước; giao hàng qua sàn, APP nhập tay, chưa tích hợp. Những quy tắc WEB giao≤3km/giá chưa chốt/size mở rộng ở các phần lịch sử dưới đây không áp dụng cho đơn WEB mới. Chưa áp dụng dữ liệu dev; xem MENU_ROLLOUT_PLAN_2026-10-31.md.

> **Loại tài liệu:** Product Requirements Document (PRD) + Software Requirements Specification (SRS) + Architecture Decision Record (ADR) + Acceptance/Test Plan + Execution Plan.
>
> **Dự án:** Nâu Coffee, website thương mại điện tử B2C kết hợp mô hình cửa hàng đồ uống giả định gần chợ Bàn Cờ, TP.HCM.
>
> **Phiên bản tài liệu:** 3.0 | **Ngày tổng hợp:** 13/10/2026 | **Ngôn ngữ website:** Tiếng Việt | **Tiền tệ:** VND.
>
> **Tình trạng thực tế:** Đây là **đặc tả để triển khai**, KHÔNG PHẢI bằng chứng website đã được lập trình, chạy test hay triển khai online.

---

## 0. QUY TẮC BẮT BUỘC CHO CODEX (ĐỌC ĐẦU TIÊN)

Bạn là kỹ sư phần mềm full-stack kiêm QA/DevOps phụ trách dự án `NauCoffee`. Đọc hết tài liệu này, đối chiếu code hiện có trước khi thay đổi và thực hiện theo thứ tự ưu tiên. Không được chỉ tạo mockup tĩnh rồi nói đã hoàn thành hệ thống TMĐT.

1. **Giữ stack đã chốt:** Python + Django + Django Templates + CSS/JS + PostgreSQL 17. VS Code chạy trên Windows, project/terminal chạy trong WSL2 Ubuntu, PostgreSQL phát triển chạy trong Docker Desktop qua WSL. **Không tự ý đổi sang Next.js, Supabase hoặc MySQL** dù kế hoạch sơ bộ từng nhắc đến chúng.
2. **Tôn trọng yêu cầu cuối kỳ PDF:** 12 nhóm bắt buộc ở Mục 2 là điều kiện nghiệm thu tối thiểu. Phần mở rộng lấy từ mô hình Nâu Coffee ban đầu.
3. **Không nhầm kế hoạch với trạng thái triển khai:** Đầu mỗi phiên đọc repository, `git status`, danh sách file, README, migration, test và môi trường; xác định cái gì đã có, cái gì chưa.
4. **Chỉ chạy lệnh phá hủy khi được phê duyệt:** không xóa container `pg_lab_postgres`, `pg_lab_pgadmin`, volume, database cũ; không `docker compose down -v`, `DROP DATABASE`, `flush`, reset migrations hoặc ghi đè secrets ngoài phạm vi Nâu Coffee.
5. **Thiết kế sử dụng thật:** tài khoản, phân quyền, CRUD, database, ảnh, giỏ hàng, thanh toán mô phỏng, trạng thái đơn, tồn kho, báo cáo phải có backend thật và test được.
6. **Không xử lý thanh toán thật, dữ liệu thẻ thật hay thu tiền thật** trong đồ án. Giữ nhãn `DEMO / THANH TOÁN MÔ PHỎNG` rõ ràng; không giả mạo tích hợp cổng thanh toán hoặc dịch vụ giao hàng thật.
7. **Bảo mật:** Django Auth, mật khẩu hash, CSRF, ORM, server-side validation, RBAC, environment variables, bảo vệ admin, HTTPS production; tránh log PII/secrets.
8. **Có bằng chứng kiểm thử:** chạy unit/integration/E2E, ghi output đạt/trượt; không đánh dấu hoàn thành theo suy đoán. Một tính năng chỉ `DONE` nếu đã có màn hình/API, DB logic và test phù hợp.
9. **Triển khai Internet cần phê duyệt:** staging/production trên host cloud và database riêng, có URL công khai, HTTPS, kiểm thử từ thiết bị hoặc mạng khác. Không tự đăng công khai trước khi chủ dự án duyệt.
10. **Ưu tiên P0:** nếu thời gian hạn chế, tập trung đủ đề thầy + full luồng mua hàng + admin + online + test trước P1 nâng cao. Luôn cập nhật `docs/PROGRESS.md`, `docs/TEST_REPORT.md`, `docs/DECISIONS.md` khi triển khai.
11. **Khi có mâu thuẫn:** (a) đề thầy bắt buộc; (b) chỉ đạo cụ thể mới nhất của chủ dự án; (c) các quyết định đã chốt trong tài liệu; (d) đề xuất giả định. Báo cáo xung đột, không tự biến giả định thành yêu cầu của thầy.
12. **Tính độc lập:** tránh phụ thuộc các plugin trả phí hoặc AI API phải trả phí; có chế độ demo khi không có Internet ngoại trừ lúc kiểm thử môi trường online.

### Hướng dẫn vận hành Codex

- Kiểm tra repository hiện tại, không giả sử folder trống. Nếu đã có mã nguồn, cải tiến thay vì viết đè.
- Tạo nhánh/commit Git theo cột mốc hợp lý sau khi xác nhận git repository. Không đưa `.env`, credential, dữ liệu riêng tư lên Git.
- Tự thực hiện các thao tác an toàn trong phạm vi workspace và test; chỉ dừng để xin phép khi phải can thiệp data/hosting/secrets hay hành động gây mất dữ liệu.
- Sau mỗi giai đoạn in ra: **Đã làm**, **Lệnh và kết quả test**, **Chưa làm**, **Rủi ro**, **Cần phê duyệt**, **Bước tiếp theo**.
- Không dừng ở lập kế hoạch nếu có thể tiếp tục triển khai an toàn. Không gộp code phát triển + deploy + kết luận đã hoàn thành nếu chưa có xác thực.

---

## 1. NGUỒN YÊU CẦU, MỨC ĐỘ ƯU TIÊN, GIẢ ĐỊNH

### 1.1 Nguồn phân biệt rõ

| Mã nguồn | Tài liệu / lịch sử | Cấp độ |
|---|---|---|
| `TEACHER-CASE` | File người dùng cung cấp: `TMDT_CASE STUDY.pdf`, 1 trang. | **Bắt buộc nộp/đạt** |
| `USER-BASE` | Kế hoạch kinh doanh Nâu Coffee từ Chương 2: quán gần chợ Bàn Cờ, đa kênh, vai trò Admin/Nhân viên/Khách hàng, phải đăng nhập mới đặt, đặt trước theo giờ, tự nhận hoặc giao ≤3 km, kho nguyên liệu, tích điểm, báo cáo. | **Yêu cầu nghiệp vụ đã bàn và được người dùng chốt** |
| `USER-V3` | Yêu cầu trong các lần trao đổi sau: Django/PostgreSQL Docker, UI theo mẫu Nâu Coffee, Codex VS Code WSL Ubuntu, triển khai **online miễn phí nếu có thể**, test thật. | **Yêu cầu triển khai hiện hành** |
| `DESIGN-PROPOSAL` | Ma trận mô hình dữ liệu, mức phí, chi tiết voucher, số size, copy marketing, tài khoản demo. | **Đề xuất/giả định, có thể chỉnh** |
| `COURSE` | 8 file bài giảng Thương mại điện tử được người dùng cung cấp, Chương 1–8. | Tài liệu học thuật nền tảng, **không thay thế yêu cầu đề thi** |

> **Nguồn xung đột đã giải quyết:** Một bản thiết kế V2 từng đề xuất *guest checkout*. Nhưng trong kế hoạch kinh doanh sau đó người dùng đã chốt **bắt buộc có tài khoản/đăng nhập để đặt hàng**. **Quy định cuối cùng:** khách chưa đăng nhập vẫn xem và có thể chuẩn bị giỏ; bấm checkout phải đăng nhập/đăng ký, giữ nguyên giỏ. Không triển khai guest checkout trừ khi người dùng đổi yêu cầu.

> **Xung đột công nghệ:** Có đề xuất sơ bộ ở cuộc trao đổi khác về Next.js + Supabase. Bản được chốt cho triển khai hiện tại là **Django + PostgreSQL 17 Docker**. Không mix hai stack.

### 1.2 Quy ước ưu tiên

- **P0:** 12 nhóm yêu cầu đề thầy, luồng mua hàng đặt hàng thật và test, phân quyền tối thiểu, triển khai online.
- **P1:** Nghiệp vụ đã chốt từ mô hình ban đầu: đặt trước, nhận tại quán/giao ≤3 km, nhân viên vận hành, đơn đa kênh, kho BOM, tích điểm, báo cáo.
- **P2:** Nâng cao UI, SEO, email, biểu đồ mở rộng, tối ưu hiệu năng, các tiện ích phụ.
- **BLOCKER:** Lỗi khiến đăng nhập/checkout/đơn hàng/bảo mật/URL công khai không hoạt động.

### 1.3 Điều chưa có xác nhận, phải cấu hình/thể hiện là demo

- Địa chỉ số nhà chính xác, tọa độ cửa hàng, số điện thoại, giấy phép của Nâu Coffee **chưa được cung cấp**. Không bịa địa chỉ thật hoặc giả mạo một cửa hàng đang tồn tại; Google Maps có nhãn vị trí **minh họa** khi chưa được xác nhận.
- Giá, size, công thức đồ uống, phí giao, khuyến mãi: các số trong tài liệu này là **dữ liệu mô phỏng/dự kiến**, không khẳng định là giá thị trường hay giá kinh doanh chính thức.
- Đề case study **không yêu cầu thanh toán ngân hàng thật, tích hợp Grab/ShopeeFood thật, hay tự động gửi SMS**. Có mock/simulator là đủ để minh họa luồng, không được tuyên bố là hệ thống đã tích hợp thật.
- Ngân sách hosting mục tiêu **0đ**, nhưng phải kiểm tra lại điều khoản, quota và thời hạn của dịch vụ tại lúc đăng ký; tuyệt đối không cam kết 24/7 với gói miễn phí.

---

## 2. ĐỀ THẦY: MA TRẬN TRUY XUẤT YÊU CẦU (12/12)

Trích theo đúng nghĩa trong `TMDT_CASE STUDY.pdf`: đề yêu cầu **xây dựng và triển khai website TMĐT**, nộp **source code**, **báo cáo Word `.docx`**, **trình chiếu**, tất cả trong một **ZIP** có tên theo mẫu `TMDT_NHOM_<SO_NHOM>.zip`; báo cáo có bảng thành viên, **phần trăm tham gia**, ghi chú. Mỗi nhóm nộp một lần qua hệ thống môn học.

| ID | Nội dung theo đề | Màn hình/module nghiệm thu | Tiêu chí chấp nhận P0 |
|---|---|---|---|
| `REQ-01` | Lọc, tìm kiếm | `/menu` / catalog | Tìm tên, lọc danh mục, mức giá; kết hợp filters; trường hợp không có kết quả; truy vấn backend và phân trang. |
| `REQ-02` | Sắp xếp | `/menu` | Giá tăng/giảm, tên A–Z, mới nhất; thứ tự thật và giữ filter đang chọn. |
| `REQ-03` | Đăng nhập, đăng xuất | `/accounts/login/`, `/accounts/logout/` | Đăng nhập/logout thực; mật khẩu hash; phân quyền/redirect; không xem trang riêng sau logout. |
| `REQ-04` | Giỏ hàng, thanh toán | `/cart/`, `/checkout/`, `/orders/` | Thêm/sửa/xóa; backend tính tiền; tạo order + payment transaction mô phỏng; trạng thái nhất quán. |
| `REQ-05` | Ảnh sản phẩm | Menu, detail, admin | Có ảnh thật trong UI (quyền sử dụng phù hợp), fallback ảnh; admin quản lý ảnh; ảnh không vỡ khi deploy. |
| `REQ-06` | Responsive | Toàn site | Desktop 1440, tablet 768, mobile 375; không tràn ngang, nút vẫn chạm được. |
| `REQ-07` | Liên hệ, feedback | `/contact/`, `/feedback/`, admin | Form validation, lưu DB, admin xem/đánh dấu đã xử lý; chống spam cơ bản. |
| `REQ-08` | Khuyến mại, giá mới, giá cũ | Product, promo admin, cart | Hiển thị giá gốc gạch ngang, giá mới, thời hạn, tính khuyến mãi đúng; không sửa giá client. |
| `REQ-09` | Chính sách đổi trả, bảo hành, vận chuyển | `/policies/*` | 3 trang chính sách dễ tìm; đổi trả phù hợp đồ uống; nội dung chính sách là demo và không khẳng định quá mức. |
| `REQ-10` | Google Maps | `/contact/` | Bản đồ nhúng hoạt động, fallback link khi iframe bị chặn, địa điểm minh họa được ghi rõ. |
| `REQ-11` | Đánh giá sản phẩm, bình luận | Detail + reviews + admin | Rating 1–5, bình luận, kiểm duyệt, phân trang; kiểm tra quyền/đơn hợp lệ. |
| `REQ-12` | Trang quản trị | `/admin/` và/hoặc `/dashboard/` | Admin login, CRUD sản phẩm/ảnh/danh mục/giá/đơn/khuyến mãi/phản hồi/đánh giá; role check server. |

**Chấm P0:** Mỗi `REQ-XX` phải có ít nhất một test tự động hoặc bước manual QA có ghi kết quả, bằng chứng screenshot nếu là UI. P0 chỉ pass sau deploy nếu chức năng truy cập được trên URL thực.

---

## 3. PHẠM VI KINH DOANH NÂU COFFEE (CHƯƠNG 2)

### 3.1 Khái niệm

- **Mô hình:** B2C e-tailer kết hợp cửa hàng offline và các kênh nền tảng bên ngoài (omnichannel ở mức nhập liệu/quản lý hợp nhất, **không API tích hợp thật**).
- **Thương hiệu giả định:** Nâu Coffee.
- **Khu vực mô hình:** gần chợ Bàn Cờ, TP.HCM; dự kiến quán 20–35 m², 6–10 chỗ, 07:00–22:00. Người dùng từng ưu tiên mặt bằng hẻm đủ hai xe máy tránh nhau, điện nước sẵn, chi phí thuê mục tiêu khoảng 6 triệu/tháng nhưng có thể thương lượng hơn. **Đây là bối cảnh bản kế hoạch, không phải địa chỉ cửa hàng thực tế.**
- **Kênh:** trực tiếp tại quầy `COUNTER`, website `WEB`, đơn nền tảng đối tác nhập tay `APP` (GrabFood/ShopeeFood minh họa), có thể dùng social để tiếp thị chứ không giả lập kênh bán riêng nếu không có yêu cầu.
- **Mục tiêu cơ cấu đơn hàng tháng 6:** Quầy 50%, Website 30%, Ứng dụng 20%. Đây là **mục tiêu/giả định kế hoạch**, không phải số liệu thực.
- **Phương thức nhận:** `PICKUP` tại quán hoặc `DELIVERY` trong phạm vi 3 km theo cấu hình.
- **Đơn đặt trước:** chọn thời gian pickup/delivery trong giờ 07:00–22:00, giới hạn lead time và ngày nhận bằng cấu hình; timezone `Asia/Ho_Chi_Minh`.
- **Thanh toán:** COD/tiền mặt khi nhận (theo phương thức nhận) hoặc thanh toán **mô phỏng**. Nếu nhận tại quán, hiển thị “Thanh toán khi nhận”.
- **Giao hàng:** đối tác giao hàng theo từng đơn, ghi nhận bàn giao/tracking mô phỏng; không tuyên bố đã kết nối hệ thống đối tác thật.
- **Hủy/đổi:** khách được yêu cầu hủy hoặc sửa trước khi pha chế; khi đã chuyển `PREPARING`, khách không được tự hủy qua web. Với đơn đã thanh toán giả lập, kiểm soát luồng hoàn tiền mô phỏng.

### 3.2 MENU 8 MÓN — QUYẾT ĐỊNH MỚI NHẤT31/10/2026

Nguồn chuẩn: [APPROVED_MENU_PRICING_2026-10-31.md](APPROVED_MENU_PRICING_2026-10-31.md). Chỉ đạo này thay thế giá/quy tắc25/10; thay đổi dữ liệu dev vẫn phải duyệt phương án riêng.

| Mã | Món | ml | Cost (chỉ quản trị) | WEB=COUNTER | APP |
|---|---|---:|---:|---:|---:|
| CF01 | Cà phê đen |360|7.000|28.000|37.000|
| CF02 | Cà phê sữa |360|8.000|32.000|43.000|
| CF03 | Bạc xỉu |360|8.250|33.000|44.000|
| CF04 | Cold Brew |500|10.000|40.000|54.000|
| TE01 | Trà đào |700|9.500|38.000|51.000|
| TE02 | Trà chanh |700|8.500|34.000|46.000|
| OT01 | Matcha |700|12.250|49.000|66.000|
| OT02 | Cacao sữa |700|11.500|46.000|62.000|

VND nguyên. Mỗi món một dung tích chuẩn; không thêm size/topping/phụ thu/khuyến mại chưa duyệt. WEB đặt trước và nhận tại quán; APP dùng giá sàn, chưa có tích hợp hoặc link gian hàng được xác nhận. Chi phí không công khai cho Customer. Tổng tiền từ backend. Thanh toán mô phỏng, không thu tiền thật. Giữ SKU/đơn/snapshot cũ, không reset database. [Phương án an toàn đang chờ duyệt](MENU_ROLLOUT_PLAN_2026-10-31.md).

### 3.3 Giá, chi phí và chính sách vận hành

- Giá bán có thể khác nhau theo **kênh** (`WEB`, `COUNTER`, `APP`) và **SKU/size**, nên phải mô hình hóa rõ thay vì một cột giá bất biến.
- Chính sách giá cũ/giá mới theo đợt, khuyến mãi voucher theo điều kiện; tuyệt đối không giả discount nếu chưa có `original_price > final_price` và thời hạn hợp lệ.
- Phí giao hàng `DELIVERY` theo cấu hình (ví dụ base fee, miễn ship theo ngưỡng), không hardcode số tiền từ concept; `PICKUP` không thu shipping.
- VAT/thuế, thời gian giao thực tế, hình thức xử lý đổi trả cần lưu chính sách/config và xác minh với quy định áp dụng nếu kinh doanh thật. **Website đồ án giả định không thay thế tư vấn pháp lý hay đăng ký kinh doanh.**

### 3.4 Mô hình kinh doanh: BMC và SWOT cho báo cáo, không lẫn với code

**BMC (đề xuất khung phân tích):** Customer Segments (sinh viên, nhân viên văn phòng, cư dân gần khu vực); Value Proposition (đặt món nhanh, tùy biến, nhận tại quán hoặc giao gần); Channels (quầy, website, app bên thứ ba); Customer Relationships (tích điểm, phản hồi); Revenue Streams (bán đồ uống); Key Resources (mặt bằng, nguyên liệu, website, đội ngũ); Key Activities (pha chế, xử lý đơn, marketing); Key Partners (nhà cung ứng và đơn vị giao); Cost Structure (nguyên liệu, mặt bằng, nhân sự, marketing, vận hành công nghệ). **Các nhóm khách hàng là giả thuyết cần chứng minh bằng khảo sát khi viết báo cáo.**

**SWOT:** Chỉ sử dụng các ý có logic và gắn KPI/kịch bản: Strength (bán đa kênh + cá nhân hóa), Weakness (thương hiệu mới/quán nhỏ), Opportunity (thói quen đặt đồ uống online trong phân khúc giả định), Threat (đối thủ, chi phí app, biến động nguyên liệu). Không tự khẳng định tỷ lệ thị phần. Dashboard dùng dữ liệu demo để minh họa các KPI đơn, doanh thu, AOV, tỉ lệ hủy, doanh thu theo kênh, SKU bán chạy, lượng nguyên liệu hao hụt. KPI mục tiêu kênh 50/30/20 chỉ là **mốc kế hoạch**.

---

## 4. ACTORS, PHÂN QUYỀN RBAC VÀ USE CASE

### 4.1 Vai trò (final)

1. **Guest / Khách chưa đăng nhập:** duyệt menu, tìm/lọc/sort, xem chi tiết/đánh giá/chính sách/contact, tạo giỏ session (nếu triển khai), xem nội dung khuyến mãi; **không được đặt hàng**.
2. **Customer / Khách hàng:** Guest + đăng ký/đăng nhập/logout, quản lý profile/địa chỉ, giỏ hàng, checkout, đặt trước, đơn của chính mình, hủy/sửa đủ điều kiện, xem điểm, đánh giá đơn hoàn tất, gửi feedback.
3. **Staff / Nhân viên:** truy cập dashboard vận hành theo quyền, xem danh sách đơn cần xử lý, xác nhận/pha chế/bàn giao, nhập đơn quầy/đơn app thủ công, nhận tiền khi được phân công, ghi nhận nguyên liệu tiêu hao/biến động; không chỉnh permission người dùng, không xem toàn bộ báo cáo tài chính nhạy cảm nếu không được cấp.
4. **Admin / Quản trị viên:** quản lý accounts/roles, sản phẩm/size/topping/giá/ảnh/danh mục, voucher/chương trình, đơn/đổi trả/hoàn tiền mô phỏng, nhân viên, tồn kho/định mức, khách hàng/phản hồi/review, chính sách, địa điểm, cấu hình và báo cáo.
5. **External actors (mô phỏng):** Payment Simulator, Delivery Simulator; không phải người dùng website. Có thể thực hiện bằng **service adapter nội bộ** ở MVP, không bắt buộc 2 ứng dụng FastAPI riêng.

**Quy tắc nghiệp vụ:** `request.user.is_staff` Django **không đồng nghĩa** với vai trò `Staff` Nâu Coffee. Ánh xạ RBAC minh bạch bằng Django Groups/Permissions (`CUSTOMER`, `STAFF`, `ADMIN`), superuser chỉ là quyền kỹ thuật. Admin route riêng có decorator/mixin kiểm tra permission trên server.

### 4.2 Ma trận quyền

Ký hiệu: `R` đọc; `C` tạo; `U` sửa; `D` xóa mềm; `O` chỉ tài nguyên của chính mình; `-` không được phép.

| Tài nguyên / hành động | Guest | Customer | Staff | Admin |
|---|---|---|---|---|
| Menu, tìm/lọc/sort, chính sách, bản đồ | R | R | R | CRUD |
| Giỏ hàng phiên / giỏ của mình | C/R/U | C/R/U/O | R/O | R (nếu cần hỗ trợ có audit) |
| Đăng ký/đăng nhập/logout | C/R | C/R/U/O | C/R/U/O | C/R/U/O |
| Tạo đơn WEB | - | C/O | C (hỗ trợ, phải ghi nhân viên) | C |
| Xem đơn cá nhân | - | R/O | - | R |
| Danh sách đơn vận hành | - | - | R | R |
| Cập nhật trạng thái pha chế/bàn giao | - | - | U theo bước hợp lệ | U theo bước hợp lệ |
| Hủy đơn trước pha chế | - | U/O hợp lệ | U hợp lệ | U hợp lệ |
| Đơn COUNTER/APP nhập tay | - | - | C/R/U có audit | C/R/U có audit |
| Xem/điều chỉnh tồn kho | - | - | R/U nghiệp vụ được cấp | CRUD |
| Quản lý SKU, giá, mã giảm giá, định mức | - | - | R giới hạn | CRUD |
| Review sản phẩm | R (đã duyệt) | C/O đủ điều kiện; R | R và flag | R/U moderation |
| Gửi feedback/contact | C | C | C | C |
| Xem dữ liệu feedback khách | - | O nếu có màn hình riêng | R theo phân công | R/U |
| Quản lý quyền tài khoản | - | - | - | C/R/U |
| Báo cáo tổng hợp theo kênh | - | - | R giới hạn | R |
| Cấu hình chính sách/địa điểm | R | R | R | CRUD |

**Invariant:** User không được tự nâng role; route admin không chỉ ẩn trên UI mà phải có permission ở view/service; staff không thể gọi API của admin trực tiếp; chỉ chủ đơn mới xem chi tiết đơn cá nhân.

### 4.3 Use Cases chính theo vai trò

**Guest**: UC-G01 browse category, UC-G02 search/filter/sort, UC-G03 product detail, UC-G04 register/login, UC-G05 contact/feedback, UC-G06 view legal.

**Customer**: UC-C01 manage address/profile, UC-C02 configure drink, UC-C03 cart, UC-C04 apply promotion, UC-C05 choose pickup/delivery, UC-C06 choose slot, UC-C07 place order COD/mock, UC-C08 payment simulation status, UC-C09 track own orders, UC-C10 cancel/change before preparation, UC-C11 review completed order, UC-C12 loyalty history.

**Staff**: UC-S01 view kitchen queue, UC-S02 confirm order, UC-S03 start/finish preparing, UC-S04 handoff/delivery status, UC-S05 record cash settlement, UC-S06 manual APP/COUNTER order, UC-S07 stock adjustments with reason and audit.

**Admin**: UC-A01 manage categories/SKUs/images, UC-A02 campaigns/vouchers, UC-A03 staff/permissions, UC-A04 monitor/refund/cancel, UC-A05 inventory/BOM, UC-A06 content/policies/map, UC-A07 moderation, UC-A08 reports by channel/order/product, UC-A09 audit logs and settings.

---

## 5. USER JOURNEYS / QUY TRÌNH NGHIỆP VỤ

### 5.1 Luồng mua trên website bắt buộc phải chạy thật

1. Guest vào trang chủ `/`, menu `/menu/`; tìm kiếm, lọc, sắp xếp.
2. Chọn sản phẩm và cấu hình size, đường, đá, topping, số lượng; JavaScript cho preview nhưng **backend quyết định giá**.
3. Thêm giỏ, sửa/xóa và giữ giỏ khi đăng nhập nếu guest tạo giỏ tạm.
4. Tại `/checkout/`, nếu chưa đăng nhập → login/register → quay lại checkout, không mất giỏ.
5. Nhập/chọn thông tin nhận: `PICKUP` chọn slot nhận; `DELIVERY` chọn địa chỉ, kiểm tra vùng 3km theo quy tắc đã công bố (MVP có thể admin-defined zone hoặc API geocoding nếu sẵn; KHÔNG giả khoảng cách). Nếu không xác minh được khoảng cách tự động, hiển thị rõ “địa chỉ cần nhân viên xác nhận” thay vì nhận bừa đơn ngoài vùng.
6. Chọn thanh toán: `COD`/`PAY_AT_PICKUP` hoặc `MOCK_ONLINE`.
7. Tính lại toàn bộ tiền/khuyến mãi/phí giao, xác minh voucher và tồn kho/khả năng cung ứng, chống submit lặp; tạo `Order`, `OrderItem` snapshots và `Payment` trong transaction atomic.
8. Nếu thanh toán mô phỏng, mở `/payments/mock/<id>/` có nút giả lập **Thành công/Thất bại**, xác thực quyền, callback/handler chống lặp. Nếu thất bại không hoàn tất đơn thành đã trả.
9. Hiển thị màn hình thành công hoặc đang chờ và trang `/account/orders/<id>/`, chỉ chủ đơn truy cập; theo dõi trạng thái thực.
10. Admin/Staff cập nhật đúng thứ tự, có lịch sử `OrderStatusHistory` và audit.
11. Khi hoàn thành, khách có thể đánh giá sản phẩm đã mua; điểm trung thành được cộng đúng 1 lần theo chính sách demo.

### 5.2 Luồng quầy và đơn ứng dụng ngoài (đã chốt)

- Staff nhập đơn `COUNTER` hoặc `APP` bằng form đơn thủ công. Gắn kênh, tên khách/mã tham chiếu ngoài (nếu có), món, lựa chọn, giá áp dụng riêng và phương thức thanh toán; không cần giả API Grab/ShopeeFood.
- Mọi đơn đều dùng cùng lifecycle, quản lý kho, báo cáo theo kênh; nhưng đơn APP không giả đã thu tiền tại website.
- Có khóa idempotency hoặc cảnh báo trùng theo kênh + mã tham chiếu để tránh staff nhập 2 lần.

### 5.3 Đặt trước, hủy/sửa, giao hàng

- Slot phải trong giờ quán, sau thời điểm hiện tại + lead time cấu hình; xử lý trường hợp quá tải/giờ đóng cửa/thay đổi giờ.
- Sửa đơn trước pha chế: cách an toàn MVP là **hủy đơn cũ, tạo lại đơn mới** nếu thay đổi món/giá, giữ lịch sử; chỉnh thông tin nhỏ (ghi chú/địa chỉ) có validation và audit, không sửa tổng tiền tùy tiện.
- Hủy trước `PREPARING` hoặc theo chính sách vận hành rõ ràng; không tự động hoàn tiền thật.
- Giao ≤3 km; phí giao theo cấu hình; DeliverySimulator minh họa giao đối tác, không tự động nhận shipper thật.
- Với đơn giao thất bại, lưu lý do, xử lý lại/đóng theo chính sách, không tự động ghi nhận doanh thu đã thu.

### 5.4 Mô hình trạng thái và transition (đề xuất thống nhất)

**Order.status:**

`PENDING_PAYMENT` (mock online chờ) → `CONFIRMED` → `PREPARING` → `READY` → [`PICKUP_WAITING` hoặc `DELIVERING`] → `COMPLETED`.

Nhánh: `CANCELLED` chỉ khi hợp lệ trước pha chế; `DELIVERY_FAILED` nếu giao thất bại; `CLOSED` (tùy nhu cầu, không bắt buộc) khi xử lý xong sự cố. COD có thể bắt đầu `CONFIRMED` hoặc `AWAITING_CONFIRMATION` nếu muốn staff xác nhận. Chỉ triển khai **một phiên bản state machine rõ ràng** và test các cạnh hợp lệ/không hợp lệ.

**Payment.status (độc lập Order):** `UNPAID`, `PENDING`, `PAID`, `FAILED`, `REFUND_PENDING`, `REFUNDED`. Thanh toán mô phỏng thành công → `PAID` chỉ sau khi xác minh transaction; COD trả tiền khi nhận → `PAID` khi nhân viên được phép ghi nhận thực thu. Demo không cóเงินจริง.

**Fulfillment/Delivery.status:** `NOT_REQUIRED` (pickup), `WAITING`, `ASSIGNED`, `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, `FAILED`. Nếu chưa mô phỏng tác nhân shipper riêng, Staff quản lý bằng form có audit.

**Inventory:** snapshot/BOM tiêu hao **một lần** tại `PREPARING` (hoặc bước khác nếu lựa chọn nhất quán); không trừ lần hai nếu retry. Nếu hủy trước PREPARING chưa trừ kho; nếu đã trừ kho phải có quy trình điều chỉnh không tự cộng ngược đồ uống đã pha.

**Loyalty:** chỉ cộng một lần khi đơn chuyển `COMPLETED` và điều kiện thanh toán hợp lệ, rollback/adjust theo hủy/refund; lưu ledger, tránh thay `customer.points += n` thiếu lịch sử.

**Định nghĩa doanh thu:** báo cáo tách `gross_order_value`, `discount`, `shipping`, `net_sales` và `payments_collected`; không cộng đơn `CANCELLED`, không tính thanh toán mock như doanh thu thật của cửa hàng.

---

## 6. THIẾT KẾ GIAO DIỆN UI/UX CHI TIẾT

### 6.1 Ngôn ngữ thiết kế

- **Mood:** ấm áp, sạch, hiện đại, cafe Việt Nam, khác biệt so với template cửa hàng điện tử chung chung.
- **Màu đề xuất:** coffee espresso `#3A271C`, coffee `#6B422B`, kem nhạt `#F7F0E6`, nâu sáng `#C9A27C`, accent lá/đất nhẹ `#7A8F65`, text `#29221C`. Đảm bảo contrast WCAG AA cho chữ và nút quan trọng.
- **Font:** ưu tiên font hỗ trợ tiếng Việt (Be Vietnam Pro / Inter / system), dùng fallback, không phụ thuộc font trả phí.
- **Ảnh:** đồ uống chụp thật, tone ấm, tự nhiên; nếu ảnh AI, tránh nhãn hiệu/trang trí sai và phải đảm bảo quyền sử dụng. Hero nhẹ, ảnh tối ưu WebP/AVIF khi có thể.
- **Responsive:** mobile-first 360–430px, tablet 768px, desktop 1280–1440px; nav hamburger, mobile cart badge, sticky purchase bar ở product detail, button 44px tối thiểu nếu có thể, form label rõ.
- **Trang chủ concept:** logo `NÂU COFFEE`, nav `Trang chủ / Menu / Khuyến mãi / Tra cứu đơn hàng / Liên hệ`, search/icon account/cart; hero “Một chút Nâu cho ngày dịu lại”; danh mục; sản phẩm nổi bật; combo/voucher; USP; review hợp lệ; footer. **Ảnh demo cũ là thiết kế tham khảo, giá và tên sản phẩm phải dùng dữ liệu seed đã thống nhất.**

### 6.2 Sitemap / Pages

| Route gợi ý | Ai truy cập | UI / tính năng |
|---|---|---|
| `/` | Tất cả | Hero, category, featured, banners, how-it-works, CTA menu. |
| `/menu/` | Tất cả | Search, filters, sort, pagination, cards giá cũ/mới, quick add khi hợp lệ. |
| `/products/<slug>/` | Tất cả | Gallery, badge giảm giá, biến thể size/đường/đá/topping, số lượng, tính tổng preview, review, add cart. |
| `/promotions/` | Tất cả | Danh sách chương trình và voucher hợp lệ, điều kiện minh bạch. |
| `/cart/` | Guest/Customer | Sửa giỏ, xóa, cập nhật số lượng, tổng; thông báo cần đăng nhập để checkout. |
| `/accounts/register/`, `/accounts/login/`, `/accounts/logout/` | Theo auth | Validation, thông báo lỗi an toàn, redirect quay checkout. |
| `/checkout/` | Customer | Pickup/delivery, lịch đặt trước, address, voucher, COD/mock, xác nhận điều khoản; totals backend. |
| `/payments/mock/<token>/` | Customer sở hữu | Mô phỏng thành công/thất bại, demo banner. |
| `/checkout/success/<order_code>/` | Customer sở hữu | Xác nhận, mã đơn, tổng, theo dõi. |
| `/account/profile/`, `/account/addresses/` | Customer | Hồ sơ, địa chỉ, thay đổi mật khẩu theo Django. |
| `/account/orders/` | Customer | Lịch sử, filter status, chi tiết, hủy hợp lệ, theo dõi và đánh giá. |
| `/account/loyalty/` | Customer | Điểm và ledger giao dịch. |
| `/contact/` | Tất cả | Thông tin liên hệ, Google Maps, form contact. |
| `/feedback/` | Tất cả | Form phản hồi, optional order reference có ownership validation. |
| `/policies/returns/`, `/policies/warranty/`, `/policies/shipping/`, `/policies/privacy/`, `/policies/terms/` | Tất cả | Nội dung chính sách demo rõ ràng, liên kết footer/checkout. |
| `/dashboard/` | Staff/Admin | KPI và menu điều hành phù hợp role. |
| `/dashboard/orders/`, `/dashboard/orders/<id>/` | Staff/Admin | Queue, filter, cập nhật status, nguồn đơn, log. |
| `/dashboard/orders/new-manual/` | Staff/Admin | Nhập đơn COUNTER/APP. |
| `/dashboard/catalog/`, `/dashboard/variants/`, `/dashboard/media/` | Admin | CRUD sản phẩm/variants/ảnh/giá. |
| `/dashboard/promotions/`, `/dashboard/vouchers/` | Admin | CRUD chiến dịch/voucher. |
| `/dashboard/inventory/`, `/dashboard/recipes/` | Staff/Admin theo quyền | Stock ledger, BOM, cảnh báo tồn thấp. |
| `/dashboard/reviews/`, `/dashboard/feedback/` | Staff/Admin theo quyền | Moderation/support queue. |
| `/dashboard/customers/`, `/dashboard/staff/` | Admin | Account status/roles, không xem mật khẩu. |
| `/dashboard/reports/` | Admin | Bộ lọc theo ngày/kênh; KPI, CSV export (không chứa PII không cần thiết). |
| `/admin/` | Admin kỹ thuật | Django Admin cấu hình an toàn làm fallback CRUD. |

### 6.3 Empty/error/loading states và usability

- Không có kết quả lọc; giỏ trống; hết hàng; invalid voucher; item vừa ngừng bán; cửa hàng đóng; slot không hợp lệ; thanh toán mock thất bại; không có quyền; trang 404/500 có UX tử tế.
- Search/filter có trạng thái URL query (chia sẻ link được); khi thay sort giữ filter; phân trang có query parameters.
- Product card có tên, ảnh, category, giá, badge, rating nếu có review xác thực, nút detail/add; không hiển thị rating giả.
- Checkout rõ subtotal, discount, shipping, grand total; lỗi field cạnh input; xác nhận đơn không tự submit lặp.
- Admin có sidebar, breadcrumbs, bảng responsive, filter/search, confirm cho thao tác dữ liệu quan trọng, thông báo sau submit, trạng thái loading.
- Accessibility cơ bản: keyboard navigation, focus visible, label, alt text, contrast, aria-live cho thông báo, language `vi`.
- Tránh icon/link chức năng chết. Button nào trông click được phải có kết quả thật.

---

## 7. KIẾN TRÚC KỸ THUẬT VÀ CẤU TRÚC REPOSITORY

### 7.1 Architecture decisions (ADR)

- `ADR-001` **Modular monolith Django** để giảm chi phí và rủi ro demo; Django views/templates cho frontend; domain services tách business logic khỏi view; DRF API là optional, không bắt buộc.
- `ADR-002` PostgreSQL 17 cho local; cloud PostgreSQL riêng cho production. Không trỏ production về localhost/laptop, tránh mất kết nối khi tắt máy.
- `ADR-003` Payment & Delivery mô phỏng **bằng modules/adapters nội bộ** trong MVP. Nếu muốn tách FastAPI services sau khi P0/P1 pass, có thể thêm `mock_payment/`, `mock_delivery/`; không để microservice trì hoãn demo.
- `ADR-004` Use Django Auth, groups/permissions; Django ORM, database migrations có review. Tiền dùng `PositiveBigIntegerField`/integer VND hoặc decimal integer-like (không float).
- `ADR-005` Hệ thống gửi email, bản đồ, geocoding, CDN media là **optional adapter** có fallback để bản demo vẫn chạy khi quota hết.

### 7.2 Repository đề xuất

```text
NauCoffee/
├── AGENTS.md                         # chỉ dẫn Codex, trỏ file này
├── README.md
├── .gitignore
├── .env.example                     # không có secret thật
├── requirements.txt                 # pin versions phù hợp
├── pyproject.toml                   # pytest/ruff nếu dùng
├── render.yaml                      # nếu hosting hỗ trợ và phù hợp
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                         # home, settings, store location, legal
│   ├── accounts/                     # user, addresses, group permissions
│   ├── catalog/                      # categories, products, variants, pictures
│   ├── cart/                         # cart line, session/customer merge
│   ├── checkout/                     # place_order, pricing service
│   ├── orders/                       # order, order item, history, manual orders
│   ├── payments/                     # mock gateway, COD, transactions
│   ├── fulfillment/                  # pickup, delivery, slots, assignments
│   ├── promotions/                   # product sales, vouchers, redemptions
│   ├── inventory/                    # ingredients, recipes, stock ledger
│   ├── loyalty/                      # account, points ledger
│   ├── reviews/                      # verified reviews, moderation
│   ├── support/                      # contact, feedback
│   └── dashboard/                    # staff/admin backoffice + reporting
├── templates/
├── static/
├── media/                            # development only, production strategy needed
├── docs/
│   ├── NAU_COFFEE_V3_MASTER_SPEC.md
│   ├── DECISIONS.md
│   ├── PROGRESS.md
│   ├── ERD.md
│   ├── TEST_REPORT.md
│   ├── DEPLOYMENT.md
│   ├── UI_CHECKLIST.md
│   └── DEMO_SCRIPT.md
├── fixtures/ or apps/*/management/commands/seed_demo.py
└── tests/ or tests within each app/
```

Tùy thực tế Django scaffold, có thể điều chỉnh tên package `apps` nếu gây rối imports; cần giữ logic phân module và migrations ổn định.

### 7.3 DB kết nối và môi trường

- Đã quan sát: Docker image PostgreSQL `postgres:17`, container `pg_lab_postgres`; đã `pg_isready` = accepting connections; port mapping `5432/tcp -> 0.0.0.0:5432` và `[::]:5432`; container `pg_lab_pgadmin` là pgAdmin 4 v9.5. **Không suy ra đã có database hoặc user Nâu Coffee.**
- Local Django chạy WSL Ubuntu, nên thử `127.0.0.1:5432` sau khi xác nhận auth thành công. Database riêng `nau_coffee_dev`, user riêng `nau_coffee_app` có quyền tối thiểu; không in password/credentials, không dùng `postgres` superuser làm app user lâu dài.
- **Không thực hiện** `docker compose down -v`, xóa volume, nâng phiên bản Postgres container hiện có hay chỉnh schema của ứng dụng cũ.
- Env sample (placeholder, KHÔNG đặt thật trong git):

```dotenv
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=GENERATE_LOCALLY_AND_KEEP_SECRET
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://nau_coffee_app:YOUR_LOCAL_SECRET@127.0.0.1:5432/nau_coffee_dev
TIME_ZONE=Asia/Ho_Chi_Minh
PAYMENT_MODE=SIMULATED
SITE_MODE=DEMO
```

- Production: `DEBUG=False`, strong `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` đúng host, SSL, secure cookies, Gunicorn/Uvicorn phù hợp, static manifest/WhiteNoise nếu dùng, migration trước release, health check; secrets lưu trong dashboard provider. Cloud DB có thể ephemeral/giới hạn thời gian nên cần backup demo và kiểm tra retention.
- **Cổng 5432 local map tất cả interface**: không mở firewall/router ra Internet; nếu cần, đổi bind về localhost sau khi đánh giá không làm gián đoạn app khác. Production database kết nối bằng private URL/TLS nếu provider hỗ trợ.
- Media uploads: hệ thống host miễn phí thường có filesystem tạm; P0 nên dùng ảnh seed **static trong repo** cho danh mục; ảnh user-upload trong production cần object storage bền hoặc đường dẫn ngoài đáng tin + validation. Không tuyên bố quản lý ảnh production bền vững nếu chỉ lưu trên disk tạm.

---

## 8. DATA MODEL / ERD LOGICAL (ĐỦ TRIỂN KHAI)

Tất cả model có `id`, `created_at`, `updated_at` hợp lý, audit nếu nhạy cảm; ưu tiên constraints, indexes, FK `PROTECT`/`SET_NULL` phù hợp. Không xóa cứng sản phẩm có đơn đã bán; dùng `is_active`/soft delete. Django migrations được generate từ models, không viết SQL thủ công tùy tiện.

| Domain / Entity | Fields cốt lõi và quan hệ |
|---|---|
| `User` | Django auth user; email unique nếu dùng; phone optional verified status; group role; is_active. Nếu custom User, tạo **trước migration đầu tiên**. |
| `CustomerProfile` | FK OneToOne User, tên, contact consent tùy chọn, loyalty summary derived. |
| `Address` | FK User, label, recipient, phone, city/district/ward/address text, lat/lng nullable, is_default. Data validation, own-only. |
| `StoreLocation` | name, address_text, lat/lng nullable, is_demo_location, opening_hours, service_radius_km=3, contact details only when confirmed. |
| `Category` | name, slug unique, sort_order, is_active. |
| `Product` | category FK, name, slug unique, description, is_active, is_featured, product_code, primary_image, base_currency, status. |
| `ProductImage` | FK Product, image/path, alt, sort_order, is_primary; safe file type/size. |
| `ProductVariant` | FK Product, SKU unique, size_code STANDARD/M/L, volume_ml nullable, is_available; one SKU per combination. |
| `ChannelPrice` | FK ProductVariant, channel enum WEB/COUNTER/APP, `original_price_vnd`, `current_price_vnd` hoặc chương trình linked; effective period; uniqueness/overlap rule. |
| `OptionGroup` / `ProductOption` | Sugar %, Ice %, Topping; allowed variants/products; price_delta_vnd, min/max select, active status. |
| `Cart` / `CartItem` | FK User nullable/session_key; FK Variant, quantity, selected_options serialized validated or FK set; cart merge. Không lưu client total như nguồn chân lý. |
| `Promotion` | title, type, period, priority, applicability, active; product sale hoặc campaign; tránh discount stacking không chủ đích. |
| `Voucher` | code unique case-insensitive, type PERCENT/FIXED, amount, cap, min_subtotal, max_uses, per_user_limit, effective dates, usage count derived from redemptions. |
| `VoucherRedemption` | FK Voucher/User/Order, unique constraints as appropriate, status; atomic redeem on successful order, release on eligible cancellation. |
| `Order` | public_code unique, FK user nullable for manual external orders only, channel, fulfillment_type, scheduled_for, customer_snapshot, address_snapshot, store_location, subtotal_vnd, discount_vnd, shipping_vnd, total_vnd, status, payment_state summary derived, notes, version, idempotency_key. |
| `OrderItem` | FK Order, nullable FK product/variant + **snapshot** name, SKU, base/unit_price, options label/prices JSON, qty, line_total_vnd; nguyên vẹn khi menu thay đổi. |
| `OrderStatusHistory` | FK Order, from_state, to_state, actor FK, timestamp, reason. Immutable history. |
| `Payment` | FK Order, method COD/PAY_AT_PICKUP/MOCK_ONLINE, status, amount_vnd, demo_provider_ref nullable, idempotency_key, paid_at, refunded_at. |
| `PaymentEvent` | FK Payment, event_type, payload đã sanitize, event_key unique, timestamp. Không lưu thẻ thật. |
| `Delivery` | OneToOne Order (chỉ DELIVERY), carrier_name demo nullable, tracking_ref demo, status, shipping_fee, proof note, timestamps. |
| `DeliveryEvent` | FK Delivery, status transition, actor, timestamp, note; không giả POD là giao thật. |
| `Review` | FK User/Product/OrderItem (nếu có), rating 1..5, body, status PENDING/APPROVED/REJECTED, unique review per purchased order item. |
| `ContactMessage` | name, email/phone optional, subject, content, status, assigned_to; captcha/honeypot/rate limiting. |
| `Feedback` | FK User nullable, order nullable, category, rating_optional, content, status, admin_reply, resolved_at. |
| `Ingredient` | sku, name, unit (`ml`, `g`, `piece`...), current stock derived or cached, low_stock_threshold, is_active. |
| `RecipeLine` (BOM) | FK ProductVariant, FK Ingredient, quantity_per_unit + topping consumption if chosen, unique tuple. |
| `StockMovement` | FK Ingredient, delta, reason enum PURCHASE/CONSUME/ADJUST/WASTE/REVERSAL, order_id nullable, external_ref, idempotency_key, created_by, timestamp. |
| `LoyaltyAccount` | OneToOne User; points_balance derived/cache. |
| `LoyaltyLedger` | FK User/Order, points_delta, event EARN/REDEEM/ADJUST/REVERSE, unique idempotency_key, timestamp. |
| `AuditLog` | actor, action, object_type, object_id, before/after sanitized, timestamp; restricted access. |
| `StoreSettings` | opening times, preorder lead/min/max days, shipping settings, loyalty_rate, demo contact, order capacity, business policy version. |

### 8.1 Constraints quan trọng

- Mọi giá/tổng tiền ≥0; qty >0; `Order.total = max(0, subtotal - discount) + shipping`; discount không vượt subtotal; không float VND.
- `ProductVariant.sku` unique, `Order.public_code` unique khó đoán, voucher uniqueness case-insensitive, stock transaction idempotent.
- Unavailable/inactive products/options không được checkout; nhưng vẫn hiển thị snapshot ở lịch sử đơn.
- Không đổi `OrderItem` sau khi confirmed/đã trả nếu làm mất dấu vết; điều chỉnh qua workflow/version/audit.
- Race-condition: `transaction.atomic`, select_for_update thích hợp khi redeem voucher/trừ kho/assign slot; callback mock payment xử lý idempotent, không double payment.
- Không thay đổi số dư điểm bằng mutate không ledger; báo cáo số dư từ ledger.
- Đánh giá gắn order item thuộc chính user và đơn hoàn tất; unique review mỗi order item.
- Không lưu/hiển thị phone, địa chỉ, email cho bên ngoài nếu không cần.

### 8.2 Sơ đồ quan hệ ở mức khái niệm

```text
User --1:1--> CustomerProfile
User --1:N--> Address
User --1:N--> Order --1:N--> OrderItem --> ProductVariant --> Product --> Category
                   |                  |                 |
                   |                  |                 +--> ProductImage
                   |                  +--> Options snapshot
                   +--1:N--> Payment --1:N--> PaymentEvent
                   +--1:N--> OrderStatusHistory
                   +--0:1--> Delivery --1:N--> DeliveryEvent
                   +--0:1--> VoucherRedemption --> Voucher
User --1:N--> Review --> Product / OrderItem
User --1:N--> LoyaltyLedger --> Order
ProductVariant --1:N--> RecipeLine --> Ingredient --1:N--> StockMovement
Promotion --> Product / Category / ChannelPrice (rules)
Staff/Admin --> Order manual entry, StockMovement, AuditLog
```

Vẽ ERD chuẩn với cardinalities từ Django models và sinh `docs/ERD.md`; không dùng sơ đồ trên làm thay cho migration thật.

---

## 9. DOMAIN RULES: ĐƠN HÀNG, KHUYẾN MÃI, ĐIỂM, KHO, VẬN CHUYỂN

### 9.1 Pricing engine

Hàm service gợi ý:

```python
quote_cart(user, cart, channel='WEB', fulfillment='PICKUP', address=None,
           scheduled_for=None, voucher_code=None) -> PriceQuote
```

Pipeline: validate active items/options → lookup `ChannelPrice` theo channel/variant/effective window → compute unit + options → subtotal → campaign sale (nếu được phép) → voucher rules → shipping based on fulfillment/distance zone → total + quote hash/expiry. Backend quote lại trong transaction checkout, không tin quote JS. Snapshot ghi vào order.

**Ví dụ giá chỉ để test logic, không phải bảng giá chốt:** món A web 30.000, topping 8.000, 2 ly → subtotal 76.000; voucher ngưỡng 100.000 không áp dụng; giao 15.000 nếu config → tổng 91.000. Test cả tình huống voucher áp dụng khi subtotal đạt ngưỡng và không thể giảm âm.

### 9.2 Promotions và voucher

- Khuyến mãi giá cũ/mới có khoảng hiệu lực và display rule thống nhất với cart/checkout.
- Voucher có mã, loại, điều kiện tối thiểu, trần giảm, phạm vi sản phẩm/kênh, giới hạn lượt dùng và user; voucher expired/disabled/used phải bị từ chối bằng thông báo rõ.
- Demo concept `NAU10` = giảm 10% đơn hàng từ 100.000đ là **đề xuất từ ảnh homepage**, có thể dùng seed nếu admin thống nhất. KHÔNG áp voucher cho đơn dưới 100.000 như ví dụ wireframe cũ. Chính sách chồng giảm phải được code rõ (ví dụ không chồng nếu chưa chốt).
- Check vòng đời voucher lúc checkout bằng locking/atomic; rollback nếu tạo đơn thất bại; không redeem hai lần khi user double click.

### 9.3 Điểm thành viên

- Quy đổi tích điểm là **config demo** (không có tỉ lệ chốt). Đề xuất ví dụ 1 điểm / 10.000đ **sau khuyến mãi, không gồm phí ship**; hiển thị rõ quy tắc trong chính sách loyalty nếu dùng.
- Cộng khi completed + payment hợp lệ, trừ khi hoàn/hủy, unique ledger event; user không được tự thay đổi điểm qua request.
- Nếu dùng điểm để thanh toán, đó là P2 và phải kiểm toán tương tự voucher; P1 tối thiểu là tích/tra cứu điểm.

### 9.4 Kho và công thức (BOM)

- Seed `Ingredient` demo (cà phê, sữa, trà, đá, ly, ống hút...), `RecipeLine` định lượng theo SKU. **Định mức và số lượng demo không phải công thức thật**.
- Trừ nguyên liệu khi chuyển `PREPARING`; staff/admin có thể nhập stock in/adjust kèm lý do.
- Test đơn 2 ly trừ 2× định mức; trừ 1 lần dù retry; nếu nguyên liệu không đủ, không cho chuyển PREPARING và báo thiếu; báo cáo tồn thấp.
- Order hủy trước pha chế không trừ; sau pha chế xử lý hao hụt/scrap có audit, không cộng kho vô lý.

### 9.5 Pickup và delivery

- Pickup chỉ hiển thị giờ mở và slot hợp lệ; phải kiểm tra timezone và capacity khi xác nhận.
- Delivery zone 3 km tính từ tọa độ cửa hàng được **xác nhận**; nếu chưa có tọa độ thật, chế độ demo chỉ mô phỏng vùng và thông báo “chờ xác nhận”, không tuyên bố giao tới bất cứ địa chỉ nào. Tính khoảng cách đường chim bay bằng Haversine chỉ là **quy tắc tham khảo**, không phải km đường đi; UI phải ghi đúng phương pháp nếu áp dụng.
- Delivery fee theo rule; order delivery ngoài vùng bị từ chối hoặc chờ xác nhận bằng workflow minh bạch.
- Trang chính sách nêu thời gian giao **dự kiến**, trường hợp chậm/giao thất bại, không giả realtime GPS.

### 9.6 Đổi trả / bảo hành / hủy / hoàn tiền

- Đồ uống không có bảo hành kỹ thuật truyền thống. Trang “Bảo hành & đảm bảo chất lượng” nêu phạm vi không áp dụng bảo hành dài hạn và quy trình tiếp nhận khi sai món/lỗi chất lượng.
- Trả/đổi là tiếp nhận khi giao sai hoặc lỗi được xác minh theo chính sách, xét thời gian hợp lý vì đồ uống dễ hỏng; không hứa hoàn tiền tự động.
- COD chưa thu thì hủy không có dòng refund tiền; online mock đã success thì mock `REFUND_PENDING` → `REFUNDED` bởi Admin (audit), không trả tiền thật.
- Không suy diễn các quy định pháp lý cụ thể nếu chưa nghiên cứu văn bản hiện hành; trong đồ án các chính sách cần có tên doanh nghiệp/hộ kinh doanh ghi **mô hình giả định**.

---

## 10. FRONTEND / BACKEND IMPLEMENTATION DETAILS

### 10.1 Django patterns

- Business logic trong `services.py` (pricing, order placement, fulfillment, refund simulation, stock, loyalty), `validators.py` và permission classes/mixins; views mỏng, forms/server validation.
- Forms kiểm tra CSRF; POST + redirect sau mutation; REST-like endpoints nếu AJAX thì POST/PUT/DELETE với CSRF; rate limit login/contact/review.
- Search sanitized ORM `icontains` + indexed/sensible pagination; sort whitelist field map tránh user tùy nhập SQL.
- Address/location access own-only; order detail use `Order.objects.filter(user=request.user)`, không lookup bằng code và lộ dữ liệu.
- Sử dụng timezone-aware datetime, `Asia/Ho_Chi_Minh` cho UI, DB UTC; không hardcode hôm nay.
- Xử lý product image upload giới hạn định dạng/kích thước, dọn tên file, content validation; demo static fallback.
- Django admin `list_display`, `search_fields`, `list_filter`, permissions theo role; dashboard nghiệp vụ là ưu tiên UI chính, Django admin làm backup.

### 10.2 Public interfaces (gợi ý)

Không cần xây API public full REST nếu server-rendered Django đáp ứng được. Nhưng các service function / endpoint nội bộ cần dễ test:

```text
GET  /menu/?q=&category=&min_price=&max_price=&sort=&page=
GET  /products/<slug>/
POST /cart/add/
POST /cart/items/<id>/update/
POST /cart/items/<id>/remove/
GET  /checkout/
POST /checkout/quote/
POST /checkout/place-order/
POST /payments/mock/<id>/simulate-success/
POST /payments/mock/<id>/simulate-failure/
GET  /account/orders/<code>/
POST /account/orders/<code>/cancel/
POST /products/<slug>/reviews/
POST /contact/
POST /feedback/
GET  /dashboard/orders/
POST /dashboard/orders/<id>/transition/
POST /dashboard/orders/new-manual/
GET  /dashboard/reports/
GET  /healthz/
```

URL tên gọi là gợi ý, code có thể dùng namespaced Django URL names; mọi mutation có server-side auth, CSRF, idempotency thích hợp.

### 10.3 Chính sách session, auth và quyền

- Password validators Django, không tạo mật khẩu hardcode trong source; demo staff/admin chỉ tạo bằng management command với env/CLI nhập mật khẩu, hoặc in link hướng dẫn `createsuperuser`.
- CSRF/secure cookies, session expiration theo môi trường, redirect validation cho `next` để tránh open redirect.
- Guest cart merge khi login transaction-safe, không nhân đôi món. Customer phải authenticated để place order.
- Form checkout không gửi thanh toán thực; mock payment phải có visual banner và test.
- Đối với fake maps, không hiển thị dữ liệu cá nhân hoặc tọa độ không được duyệt.

---

## 11. QUALITY ASSURANCE: BỘ TEST BẮT BUỘC

### 11.1 Các lớp kiểm thử

1. **Unit tests:** pricing, price sale windows, voucher edge cases, status transitions, distance/slots, BOM consumption, loyalty idempotency.
2. **Integration tests:** auth, account order ownership, cart → checkout DB transaction, mock payment → paid, COD capture, staff status, manual order channel, review linked completed order, feedback/admin CRUD.
3. **Security tests:** forbidden admin/staff endpoints 403, user A order URL không xem được B, CSRF rejected, invalid quantities, SQLi/XSS payload not executed, untrusted `price` ignored, secret not leaked.
4. **UI/E2E tests (Playwright nếu phù hợp):** user đăng ký/login, lọc menu, tùy chọn món, cart, checkout mock, order tracking, staff/admin processing, review; desktop + mobile.
5. **Production smoke:** URL công khai trả 200, static/images tải, login/logout, 1 mock order lưu cloud DB, admin cập nhật trạng thái, contact/map, review, HTTPS, database persistence across restart.

### 11.2 Test matrix tối thiểu (mỗi dòng cần PASS/FAIL bằng chứng)

| Test ID | Scenario | Expected |
|---|---|---|
| `AUTH-01` | Guest mở checkout | Redirect login và giỏ không mất |
| `AUTH-02` | Customer logout | Route riêng yêu cầu login lại |
| `RBAC-01` | Customer GET admin/dashboard | Forbidden/redirect hợp lệ |
| `RBAC-02` | Staff POST đổi quyền admin | Forbidden |
| `RBAC-03` | User A xem order của B | 404/403, không leak PII |
| `CAT-01` | Search + category + price + sort | Đúng kết quả & thứ tự, query giữ nguyên |
| `CAT-02` | Không có kết quả | Empty state hữu ích, không 500 |
| `PRD-01` | Product có sale price hợp lệ | Giá cũ gạch ngang, tính giá mới |
| `PRD-02` | Product/option inactive | Không checkout |
| `CART-01` | Add 2 same config | Merge quantity đúng |
| `CART-02` | Change topping/size | Recalculate server totals |
| `CHK-01` | JS gửi `total=1` | Server bỏ qua, giá chính xác |
| `CHK-02` | Double click place order | Không tạo 2 order trùng |
| `CHK-03` | Voucher `NAU10` dưới minimum | Không áp dụng |
| `CHK-04` | Voucher valid/expired/usage limit | Kết quả đúng, race-safe |
| `CHK-05` | Pickup vs delivery | Pickup ship=0; delivery theo rule |
| `CHK-06` | Slot ngoài 07:00–22:00 | Từ chối/hiển thị lỗi rõ |
| `CHK-07` | Delivery ngoài 3 km theo dữ liệu xác nhận | Không silently accept |
| `PAY-01` | Mock success 2 lần | `PAID` một lần, không double amount |
| `PAY-02` | Mock failed | Không `PAID`, thông báo để thử lại |
| `PAY-03` | COD hoàn tất chưa ghi nhận thu | Payment vẫn unpaid, không tự đánh dấu paid |
| `ORD-01` | Order CONFIRMED → PREPARING → READY | Chuyển hợp lệ và audit |
| `ORD-02` | Hủy trước pha chế | Thành công, không trừ tồn |
| `ORD-03` | Khách hủy sau PREPARING | Bị chặn, hướng dẫn hỗ trợ |
| `INV-01` | Bắt đầu pha 2 ly | BOM ×2, chỉ trừ một lần |
| `INV-02` | Thiếu nguyên liệu | Chặn PREPARING, lưu lý do |
| `APP-01` | Staff nhập order APP/COUNTER | Report channel đúng, không giả gateway |
| `LOY-01` | Complete cùng order 2 lần | Loyalty cộng 1 lần |
| `REV-01` | Chưa từng mua/đơn chưa complete | Không đăng review xác thực |
| `REV-02` | Đơn hoàn thành & chủ đơn | Tạo review, chờ duyệt/hiển thị theo rule |
| `FB-01` | Contact/feedback valid | Lưu, admin xem/giải quyết |
| `MAP-01` | Contact page | Embed hoặc fallback có nhãn demo |
| `UI-01` | 375/768/1440 widths | Không horizontal scroll, CTAs usable |
| `OPS-01` | Production `/healthz/` và static | OK, không lộ config |
| `OPS-02` | Restart web app | Data orders còn trên cloud DB |
| `SEC-01` | Input chứa script HTML | Escape, không execute |
| `SEC-02` | Secrets in repo/log | Không hiện secret |

### 11.3 Tiêu chí DONE và test report

- **DONE =** implement + migration + demo seed + passing test + manual UI review + deployment smoke (đối với P0 deploy) + documentation.
- `docs/TEST_REPORT.md` phải có ngày, command, pass/fail count, environment, commit, URL (nếu đã deploy), ảnh/chứng cứ lỗi, cách fix, known limitations.
- Không fabricate số test passes. Nếu chưa chạy Playwright/cloud, ghi `NOT RUN` và lý do.
- `CI`: có thể dùng GitHub Actions miễn phí theo quota để `python manage.py check`, `pytest`, static lint, migration check. DB test PostgreSQL service container là ưu tiên; SQLite chỉ mock fallback không phải thay thế test Postgres thật.

---

## 12. TRIỂN KHAI ONLINE 0Đ HOẶC CHI PHÍ THẤP

**Bắt buộc:** Website cần URL truy cập từ Internet, không chỉ `localhost` hoặc WSL của người làm bài.

### 12.1 Phân tách environments

- `LOCAL`: WSL Ubuntu + VS Code + Docker PostgreSQL 17 container hiện tại; hỗ trợ Codex chạy terminal/test.
- `STAGING/PROD-DEMO`: Django web app hosted (ví dụ Render Free) + PostgreSQL cloud; HTTPS + URL do nhà cung cấp cấp (`<service>.onrender.com` nếu tên khả dụng). Hosting và DB phải chọn dựa trên chính sách miễn phí được kiểm tra **tại thời điểm triển khai**.
- `BACKUP`: export dữ liệu demo an toàn và khả năng re-seed (không lộ PII); cloud free DB có thể hết hạn / sleep / giới hạn storage, không hứa 24/7.

### 12.2 Các bước deploy có phê duyệt

1. Chạy local test; `python manage.py check --deploy` và kiểm tra production settings; `collectstatic`; Gunicorn health check.
2. Đẩy source lên **GitHub repo** riêng (chỉ sau khi user chấp thuận repo/public visibility). `.env` ignored.
3. Người dùng tạo/tích hợp account Render và cloud PostgreSQL an toàn, nhập env secrets trực tiếp ở provider UI, không gửi mật khẩu trong chat.
4. Deploy migrations với điều kiện backup/DB target đúng, seed demo **idempotent** nếu cần, tạo admin bằng management command bí mật.
5. Kiểm tra URL HTTPS từ thiết bị/mạng khác, chạy smoke, đo UI performance và chụp screenshots.
6. Bàn giao URL, tài khoản DEMO bằng cơ chế an toàn không nhúng credentials vào repo, deployment runbook, dự phòng nếu host ngủ.

### 12.3 Nguy cơ cần tránh

- Host free `sleep`, quota; database free có thời hạn; có thể mất dữ liệu nếu không backup.
- Ephemeral filesystem không thích hợp lưu user-upload images. Dùng ảnh static demo hoặc object storage bền khi có lựa chọn phù hợp.
- Không mở port Postgres 5432 lên Internet; kết nối cloud DB có TLS; không chạy Django `runserver` public.
- Không dùng IP/URL nhà thật cho cửa hàng giả định. Không claim bản demo có chức năng xử lý đơn với thanh toán thật.

---

## 13. BÁO CÁO, SLIDE VÀ KỊCH BẢN THUYẾT TRÌNH

### 13.1 File bắt buộc theo PDF thầy

```text
TMDT_NHOM_<SO_NHOM>.zip
├── 01_SOURCE_CODE/
│   ├── Django project + app modules
│   ├── requirements.txt (hoặc lockfile)
│   ├── .env.example
│   ├── README.md (local + cloud deploy instructions)
│   ├── migrations/
│   ├── test scripts/
│   └── docs/
├── 02_BAO_CAO/
│   └── Bao_cao_Nau_Coffee.docx
└── 03_TRINH_CHIEU/
    └── Thuyet_trinh_Nau_Coffee.pptx
```

- Báo cáo **phải có bảng**: STT, Họ và tên, Phần trăm tham gia, Ghi chú. Không tự bịa tên/thành viên/tỷ lệ.
- File trình chiếu có thể PPTX; không yêu cầu riêng phần báo cáo bằng PDF nếu thầy chỉ nêu `.docx`.
- Lưu URL online/QR trong báo cáo/slide sau khi xác nhận website hoạt động.
- Nén một ZIP, đặt tên số nhóm thật, nộp qua course đúng hạn. Không tự khẳng định hạn ngày chính xác nếu chưa xem LMS.

### 13.2 Đề cương báo cáo đề xuất

1. Trang bìa + bảng thành viên % tham gia.
2. Bối cảnh và mục tiêu Nâu Coffee (quầy + e-commerce B2C).
3. Phân tích mô hình kinh doanh (BMC, SWOT có số liệu giả định minh bạch).
4. Yêu cầu theo bảng `REQ-01`–`REQ-12`, scope P0/P1/P2.
5. Use Case/ma trận quyền và flow giao dịch.
6. Kiến trúc Django + WSL/Docker PostgreSQL + cloud, ERD.
7. Thiết kế UI/UX, wireframe/màn hình thực tế responsive.
8. Mô tả chức năng frontend + admin + kho + loyalty.
9. An ninh, thanh toán mô phỏng và giao hàng eLogistics.
10. Test cases, kết quả chạy thật, lỗi đã sửa/known limitations.
11. Triển khai online: URL, thao tác, bằng chứng screenshot.
12. Kết luận, hướng phát triển và tài liệu tham khảo.

### 13.3 Liên hệ 8 chương môn TMĐT (để giải thích với thầy)

| Chương học | Nâu Coffee minh họa |
|---|---|
| 1. Tổng quan TMĐT | B2C, bán qua website, quy trình số |
| 2. Mô hình kinh doanh TMĐT | BMC, SWOT, kênh bán/quầy/web/app, giá trị khách hàng |
| 3. Hạ tầng | Django, PostgreSQL, Docker, cloud hosting, HTTP/HTTPS |
| 4. An ninh thông tin | RBAC, HTTPS, CSRF, SQLi/XSS prevention, auth, audit |
| 5. Thanh toán | COD, mock online, payment events, xử lý thất bại/hoàn tiền |
| 6. Tiếp thị | SEO, banner, voucher, UX/customer journey, tích điểm |
| 7. eLogistics | Vùng giao, pickup, tracking, stock BOM, đổi trả |
| 8. Phát triển hệ thống TMĐT | Requirements → UI/ERD → implementation → tests → deploy |

**Phần “tính thương mại điện tử” khi thầy hỏi:** Hệ thống không chỉ là website giới thiệu; có digital product catalog, tìm/lọc/sort, tài khoản/phân quyền, cart, checkout, xử lý thanh toán mô phỏng, đơn hàng, lịch sử, theo dõi, khuyến mãi, khách hàng phản hồi, hậu cần, quản trị và lưu vết giao dịch trên database online. Mô phỏng phải được nêu đúng bản chất.

### 13.4 Demo script 7–10 phút

1. Mở URL HTTPS Nâu Coffee bằng điện thoại hoặc tab ẩn danh, xem responsive.
2. Tìm `matcha`, lọc danh mục, sort giá, mở chi tiết có ảnh/giá cũ mới.
3. Thêm sản phẩm size/topping, mở cart, thao tác số lượng và voucher invalid/valid.
4. Vào checkout, yêu cầu login, chọn pickup/delivery và slot, chọn mock payment, hoàn tất đơn.
5. Mở lịch sử đơn, theo dõi trạng thái.
6. Login nhân viên/admin, xác nhận/pha chế/bàn giao/hoàn tất đơn; đối chiếu kho giảm một lần và dashboard doanh thu theo WEB.
7. Nhập một đơn `APP` thủ công, xem phân tích kênh.
8. Customer gửi feedback, review đơn hoàn tất; Admin moderation; mở Google Maps và chính sách.
9. Cho thấy test results/URL/README; nêu các phần mô phỏng và hạn chế hosting miễn phí.

---

## 14. PLAN ĐỂ CODEX TRIỂN KHAI THÀNH WEBSITE THẬT

> **Không được tuyên bố website đã hoàn thiện chỉ vì file này tồn tại.** File là hợp đồng thực hiện và tiêu chí nghiệm thu.

### Sprint 0: Khảo sát (tự chạy ngay)

- `pwd`, `ls -la`, `git status`, `python3 --version`, `docker ps`, `docker port pg_lab_postgres`, kiểm tra toolchain; không in `.env`.
- Đọc code hiện có và xác định app nào đã triển khai. Nếu workspace trống, scaffold Django.
- Kiểm tra có thể dùng PostgreSQL hiện tại bằng kết nối tối thiểu. Nếu thiếu credentials, hỏi cách thiết lập secure credentials thay vì đoán/hardcode; tạo DB riêng có sự phê duyệt của người dùng.
- Ghi `docs/DECISIONS.md` + `docs/PROGRESS.md`; tạo repo và `.gitignore` nếu chưa có.

### Sprint 1: Foundation P0

- Django settings dev/prod, auth + groups, models catalog/SKU/images, cart, order/payment, sample fixtures, migration.
- 8 món sample, layout CSS responsive, homepage + menu + product detail + login/logout; smoke test + unit.

### Sprint 2: Commerce core P0

- Cart authenticated flow, checkout, totals server, promotion sale + voucher, COD + mock online + status history, order tracking, staff queue/admin CRUD; integration tests.

### Sprint 3: Case Study P0

- 12/12 checklist: filters/sorts, contact/feedback, policies, Google Maps demo, verified review, product images production-safe, responsive QA, admin CRUD, test report.

### Sprint 4: Business model P1

- Scheduled pickup, delivery ≤3 km với chính sách xác minh minh bạch, staff manual orders APP/COUNTER, BOM/stock ledger, loyalty ledger, dashboard KPI theo kênh, cancel/refund workflow; tests.

### Sprint 5: Production online (sau phê duyệt)

- GitHub, deployment config, cloud DB, HTTPS, static/media strategy, seed idempotent, smoke e2e từ thiết bị khác, backups, release checklist.

### Sprint 6: Handover

- Code cleanup, README, ERD, TEST_REPORT, screenshot, Word report, slides, ZIP theo thầy; test lại từ clean environment.

### Gate trước khi công bố 'HOÀN THÀNH'

- [ ] 12/12 yêu cầu thầy pass trong local + production smoke.
- [ ] Customer auth/cart/checkout/order history hoạt động.
- [ ] Staff/Admin role matrix enforced server-side.
- [ ] PostgreSQL migrations/seed idempotent, restart giữ dữ liệu.
- [ ] Online URL công khai hoạt động HTTPS từ một mạng khác.
- [ ] Demo payment rõ là mô phỏng; không thu tiền thật.
- [ ] Test suite thực sự chạy, các lỗi blocker được khắc phục.
- [ ] Inventory/manual APP/COUNTER/loyalty/scheduling P1 hoặc ghi rõ unfinished nếu chưa xong; tuyệt đối không giấu.
- [ ] README cài local/deploy; docs ảnh/ERD/report đầy đủ.
- [ ] ZIP source, Word, slide đủ và bảng % tham gia có thông tin thực.

---

## 15. PROMPT DÀNH CHO CODEX SAU KHI ĐÃ THÊM FILE VÀO REPO

Sao chép nguyên đoạn sau vào Codex VS Code khi mở `NauCoffee`:

```text
Hãy đọc AGENTS.md và toàn bộ docs/NAU_COFFEE_V3_MASTER_SPEC.md.
Đây là đặc tả chuẩn (source of truth) của dự án Nâu Coffee V3.

Nhiệm vụ của bạn là CHỦ ĐỘNG XÂY DỰNG mã nguồn thật theo từng Sprint,
không dừng ở sơ đồ hay mockup tĩnh. Tuân thủ 12/12 yêu cầu giảng viên,
phân quyền Guest/Customer/Staff/Admin, luồng bán WEB/COUNTER/APP,
đặt trước, pickup/delivery, kho BOM, loyalty, báo cáo, mock payment,
responsive, kiểm thử tự động và chuẩn bị deploy online.

Bắt đầu bằng việc khảo sát code trong workspace, cập nhật docs/PROGRESS.md,
liệt kê chênh lệch so với spec và triển khai Sprint 0 → Sprint 1.
Sau mỗi Sprint chạy test phù hợp, ghi lệnh + kết quả thực tế vào
`docs/TEST_REPORT.md`; sửa lỗi và tiếp tục các phần có thể làm an toàn.
Giữ PostgreSQL/Docker hiện có nguyên vẹn, tạo DB Nâu Coffee riêng.
Không dùng thanh toán thật và không deploy public khi chưa được tôi duyệt.
Nếu gặp xung đột giữa giá seed/menu, ghi quyết định vào docs/DECISIONS.md
và chỉ hỏi khi thực sự chặn việc tiếp tục.

Khi mọi P0/P1 hoàn tất local, dừng để xin phê duyệt triển khai Render/cloud.
Không được nói 'hoàn thiện 100%' nếu chưa chạy toàn bộ test và production smoke.
```

---

## 16. CHECKLIST NGHIỆM THU VÀ BÀN GIAO CHO CHỦ DỰ ÁN

**Sau Sprint 1, chủ dự án nên nhận:** homepage/menu/product/auth demo + ảnh + seed/README; URL localhost chỉ để QA nội bộ.

**Sau Sprint 2–3:** cả 12 yêu cầu case study, giỏ hàng, mock checkout, đặt hàng/tra cứu, contact/review/chính sách/admin, test logs.

**Sau Sprint 4:** nhân viên/đa kênh, nhận hàng/giao, đặt trước, tồn kho BOM, tích điểm, báo cáo minh họa.

**Sau Sprint 5–6:** URL online, smoke test, báo cáo `.docx`, slide `.pptx`, ZIP final; checklist pass được ký xác nhận bằng chứng.

**Các quyết định chủ dự án sẽ cần duyệt trước nộp:** menu/giá/cỡ ly cuối cùng; số nhóm và tỷ lệ thành viên; địa chỉ Google Maps demo hay vị trí thực; tên URL; dữ liệu DEMO; thông tin chính sách/điều kiện voucher; dịch vụ hosting (quy định gói miễn phí).

---

## 17. CHANGELOG / TRẠNG THÁI

- `V1`: Khung kế hoạch kinh doanh quán Nâu Coffee (BMC/SWOT, đa kênh) phục vụ Chương 2.
- `V2`: Thiết kế website B2C, use cases, ERD sơ bộ, Django/PostgreSQL, giao diện homepage/menu/cart/checkout/admin, thanh toán/giao hàng mô phỏng.
- `V3`: Ghép **đầy đủ đề cuối kỳ** + bảo toàn **quyết định mới nhất** (đăng nhập bắt buộc, thêm Staff, đa kênh, lịch hẹn, kho, tích điểm), kế hoạch QA/deploy công khai, xử lý mâu thuẫn giá/guest checkout/công nghệ.
- `13/10/2026`: Tạo bản đặc tả bàn giao cho Codex; **chưa khẳng định các tính năng đã được code/test/deploy**.
