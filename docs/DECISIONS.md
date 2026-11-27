> **18/11/2026 — Refactor:** targeted148PASS, fullQA434PASS/0FAIL/SKIP;272sourceinputs khớp. Shared voucherforms/accountbase,16source/templatepaths;12render byte-equal,27live screens mỗi lượt PASS. PID22703,featureON/gateOPEN/sandbox; previewbusiness/schema giữ nguyên. [Báo cáo](CODE_CLEANUP_REFACTOR_REVIEW_2026-11-18.md). Chưa stage/commit/push/merge.

> **18/11/2026 — Startup khôi phục:** nguyên nhân QA container đã dừng làm guard PhaseC từ chối trước SQL. Bật lại container QA hiện hữu, không sửa guard/secrets. Preview connection PASS/pending0; PID3694 localhost8000, featuresON/gateOPEN/sandbox; GET smoke25/25PASS, chỉ django_session đổi. Runserver thêm fail-fast. [Báo cáo](STARTUP_IMPROPERLYCONFIGURED_FIX_2026-11-18.md).

> **Đã lưu tiến độ 17/11/2026 15:52:37 giờ Việt Nam:** PID71638 còn bind localhost8000; Git index0, diff checkPASS. Không chạy lại tests hoặc truy vấn database. [Checkpoint mới nhất](SESSION_HANDOFF_POLICY_SAVED_2026-11-17_155237.md).

> **17/11/2026 — Final Policy localhost:** support0003/0004 đã migrate PASS sau backup mã hóa + restore kiểm chứng.11 chính sách đã công bố, ngày01/11/2026; timestamp công bố/consent thực tế17/11, không backfill. QA434/434 PASS,270input khớp; live9nhóm và responsive27/27 PASS. PID71638, featureON/gateOPEN/sandbox. Dữ liệu cũ45bảng bảo toàn;3đơn thử mới được nhận diện. **READY FOR GITHUB REVIEW**, chưa stage/commit/push. [Báo cáo cuối](FINAL_POLICY_LOCALHOST_READINESS_2026-11-17.md). Các trạng tháiOFF/pending/PID phía dưới là lịch sử.

> **17/11/2026 — Policy/Consent:** full QA430/430PASS,0FAIL/SKIP;264input code/JSON khớp. Chromium375/768/1440 và2race mới PASS. Preview45bảng/44sequence/schema nguyên vẹn, **chưa migrate**, Policy featureOFF. Server8000 đã dừng từ trước phiên, chưa mở lại vì2migration pending; không bypassguard.11draft chưa công bố/ngày hiệu lực chưa duyệt. [Báo cáo và blocker](NAU_COFFEE_POLICY_CONSENT_IMPLEMENTATION_REVIEW.md). Các PID/trạng thái cũ phía dưới là lịch sử.

> **Đã lưu phiên 17/11/2026 03:44 (giờ Việt Nam):** source232/232 khớp full QA414 PASS; không rerun tests hoặc kết nối database. PID51856 còn chạy, featureON/gateOPEN/sandbox. Git index trống; patch/untracked giữ nguyên. [Checkpoint để tiếp tục](SESSION_HANDOFF_UNIFIED_VOUCHER_2026-11-17.md).

> **17/11/2026 — Voucher thống nhất và câu chữ:** full QA 414/414 PASS, 0 FAIL/SKIP; 232 input source không đổi trước/sau regression và smoke. Ba race quản trị mới PASS. Live 13 GET/3 role và 15 màn hình/viewport PASS; preview 42 bảng nghiệp vụ/schema bảo toàn, chỉ auth/session/rate-limit đổi do đăng nhập. Phase C PID 51856, feature ON, gate OPEN, sandbox. Một mục **Mã giảm giá / Voucher** tại `/admin/commerce/voucher/`, PUBLIC/VIP/chính sách cũ chung workspace; nhiều khách/quota/audit atomic. Không migration preview hoặc Git/Gmail. [Báo cáo, files, bằng chứng và giới hạn](UNIFIED_VOUCHER_UI_REVIEW.md). Các PID/trạng thái bên dưới là lịch sử.

> **Unified Admin hoàn tất kỹ thuật16/11:** fullQA391/391PASS, source208inputskhớp; live113URL/36screensPASS. PID84932,featureON/gateOPEN/sandbox. [Mapping, ảnh, giới hạn vàbáocáo](ADMIN_UI_UNIFICATION_REVIEW.md); [checkpoint](SESSION_HANDOFF_ADMIN_UNIFIED_2026-11-16.md). Chờusernghiệmthu, khôngcommit/push.

> **Admin polish16/11:** bỏnhómcontentlặp, KPIgrid/Cafécards, chartcột/trục/tooltip, conversion “Chưa đủ dữ liệu”, khôngsođơntrướctrackingvớiphiênmới. QA22/22PASS; Chromium9/9+3clickPASS. PID34167, featureON/gateOPEN/sandbox. [Báo cáo và ảnh before/after](ADMIN_DASHBOARD_POLISH_2026-11-16.md).

> **Dashboard traffic16/11:** đã thêm6KPI, chart/ranges, nguồn/thiết bị/funnel/toptrang/giờ. QA21/21PASS; liveChromium12/12+3clickPASS; schema/businessfingerprintkhớp. Server8000 PID20486 featureON/trafficON/gateOPEN/sandbox. [Báo cáo](ADMIN_TRAFFIC_DASHBOARD_2026-11-16.md).

> **Layout Admin16/11:** index/list/add/change dùngsharedsidebar/breadcrumb; mobilecollapsePASS, QA13/13PASS, Chromium12/12+3clickPASS. Server8000 PID14155 featureON/gateOPEN/sandbox. [Báocáo](ADMIN_SHARED_LAYOUT_2026-11-16.md).

> **Admin Voucher16/11:** đãđồngbộ menu “Quản lý Voucher” vànhãnLegacy; QA23/23PASS, Chromium12/12pages+3clickPASS. Server8000 PID9793,featureON/gateOPEN/sandbox. [Báocáo](ADMIN_VOUCHER_NAVIGATION_2026-11-16.md).

> **Checkpoint mới nhất:** [SESSION_HANDOFF_REGISTRATION_2026-11-13_164537.md](SESSION_HANDOFF_REGISTRATION_2026-11-13_164537.md) — server8000 đang chạy, registerHTTP200/6trường, featureON/gateOPEN/sandbox tại 2026-11-13T16:45:37.488798+07:00. Chờ người dùng nghiệm thu UI.

> **Runtime8000 đã sửa:** launcher legacy pickup_preview.py được thay bằng local_feature_preview.py; form đăng ký6trường liveChromium375/768/1440PASS, HTTP35checksPASS. PID11511, featureON/gateOPEN/sandbox. [Báo cáo](LOCALHOST_REGISTRATION_RUNTIME_FIX_2026-11-13.md).

> **Checkpoint lưu gần nhất:** [SESSION_HANDOFF_LOCALHOST_2026-11-13_120449.md](SESSION_HANDOFF_LOCALHOST_2026-11-13_120449.md); server8000 HTTP200, featureON/gateOPEN/sandbox tại 2026-11-13T12:04:49.542873+07:00. Phase C chờ chủ dự án xác nhận. Không chạy lại test/migration trong lượt lưu.

> **Trạng thái mới nhất — localhost sẵn sàng nghiệm thu:** helper CSRF đã sửa; login3role/35HTTPchecks/5GET sau mở gate PASS. Server127.0.0.1:8000 ON, feature ON, gate OPEN, email sandbox. Dữ liệu kinh doanh/QA khớp; auth/session/rate-limit thay đổi do smoke. Chưa kết thúc Phase C trước chủ dự án xác nhận. [Báo cáo hiện hành](LOCALHOST_ACCEPTANCE_READY_2026-11-13.md). Các trạng thái OFF/FAIL bên dưới là lịch sử.

> **Trạng thái mới nhất — mở localhost nghiệm thu:** preflight PASS; HTTP login smoke bị 403 do helper không chuyển tiếp cookie CSRF. Đã đóng gate, feature OFF, server8000/SMTP25251 STOPPED. Fingerprint preview và QA không đổi. Các route xác thực NOT RUN trong lượt này; chưa hoàn tất Phase C. Xem [báo cáo lần mở localhost](LOCALHOST_ACCEPTANCE_ATTEMPT_2026-11-13.md).

## 13/11/2026 — Responsive riêng biệt với mởnghiệmthu localhost

User chỉ duyệt7responsive cònthiếu, không cho mở8000/bậtfeature. Hoàn tất bằng eager-loading và render trong process test với guardchặnDML/rollback; không server/flagpersist hoặc thay dữliệu hiện có.9/9PASS kết hợp2liveHTTPtrước+7renderDOM, không nâng thành9liveHTTP mới. Giữ featureOFF/serverSTOPPED dùQA PASS; lần mởnghiệmthuUIlocalhost cần duyệtriêng. Khôngmigrate/restore/51integration/SMTP/Git. [Báo cáo](LOCAL_FEATURE_CUTOVER_REVIEW_2026-11-13.md).

## 13/11/2026 — Phê duyệt C local; dừng sau responsive helper FAIL

User phêduyệt preview5432migration+localflags/sandbox, khôngGmail/publicHTTPS/Git. Triển khai helperlocal riêng, không nới regressionguard; backupsource/static/runtime mãhóa ngoài repo. Sau lỗi helperemail, user duyệt tiếp smoke với fixtures cósẵn, khôngsignup/migrate lại;51checkspass. Responsive helper lỗilazyFK trướcAdmin375; theo failure-stop giữfeatureOFF/dừngserver vàphântích, khôngtựrestore hoặc mởlại. Chuẩn bị eagerloadhelper, chờduyệtretry UI; khôngsửalogicapp nếu chưa cólỗi thực tế. Chínđơn test được giữ, khônghủy/xóa. [Báo cáo hiện hành](LOCAL_FEATURE_CUTOVER_REVIEW_2026-11-13.md).

## 13/11/2026 — Giai đoạn B chỉ trên copy; C chờ duyệt

Cho phép migration/integration và rollback rehearsal trên bản sao đã allowlist, không preview5432 hoặc QAregression. RoleQA dùng quyền tạm chỉ trêncopy, không đổi credentials/guard chung; kết thúc thu hồiCONNECT và giữ3DB, khôngDROP/reset. Chỉ thêm metadata Django dự kiến, không backfill User hoặc chuyển voucher legacy. Controlled failure sau catalog commit chứng minh cần rollback cóschema/data, không chỉtắtfeature. Source/static backup250files khôngcredentials; media hiệnrỗng. C cần quyết địnhemail/HTTPS hoặcinternal sandbox, maintenancehelper preview riêng, freshbackup/window và whitelist smoke/data. Không suy phêduyệtC/Git/publicdeployment/mailthật từB. [Biên bản](CUTOVER_STAGE_B_REVIEW_2026-11-13.md).

## 13/11/2026 — Phê duyệt chỉ Giai đoạn A cutover

Được duyệt backup mã hóa database hiện hành và restore sang database mới cách ly; đã thực hiệnPASS trên preview5432→restoreQA55441mới, không ghi preview/dev hoặc QAregression. Archive/key local ngoàiGit, táchdirectory0700/files0600; copyrealdata chỉpostgresQA truy cập, không nốiapp/SMTP hoặc dùngregression. Mappingowner/ACLkhácsource là chủ đích bảo vệ dữ liệu. Không coi DB-onlyrestore là phục hồi media/globals/runtime hoặc cho phép bậtflag/migration/restart8000/SMTP/publicHTTPS/Git. Backup+keycùnglaptop chưaoffsite; downtime/RTOchưaxácđịnh, rollback sauwrites cần đốisoátRPO/restoretargetruntimeđượcduyệt,khôngreverse0005tựđộng. [Phê duyệt tiếp và kế hoạch](FEATURE_INTEGRATION_CUTOVER_PLAN_2026-11-13.md).

## 13/11/2026 — Ưu tiên tích hợp, chưa tổng nghiệm thu hoặc cutover

Theo chỉ đạo mới: hoàn thiện Accounts/Gmail/PasswordReset/Voucher trong sourceQA, khôngFINALcompletion/đóngdựán/sửachínhsách/ngàygiờ. Admin edit giữ audiencecốđịnh,khôngđổisnapshot/redemption/lượtđãdùng;lockvoucher→campaign đồngbộorder,LogEntryactor. V2 chặn nativeStaff vàPUBLIC/STAFFprofilechưaverified dùUseractive; legacyloginchưaprofilegiữnguyên,tuyệtkhôngbackfill. QA360PASSkhôngcấpphép migration/bậtfeature/restart8000 hoặcGit. Gmailđãgửiđúng1thư/nhậnownerconfirmed,khônggửithêm. Cutover cần duyệtbackuphiệnhành+restorecáchly,maintenanceguardedmigrationđúngtarget,trustedHTTPS/emailorigin,flags/authbackend vàsmoke;rollbackkhôngchỉtắtflag/reverse0005khiđãcódữliệu. [Review](NAU_COFFEE_V3_FEATURE_INTEGRATION_REVIEW.md).

## 12/11/2026 — Customer recovery bằng Django, chưa kích hoạt

Dùngdefault_token_generator + SetPasswordForm/validators/hash chuẩn,TTL3600s (env60..86400); translate lỗi hiển thị khôngđổipolicy. Customer active/usable/verifiedProfile+emailAuthkhớp/unique; khôngStaff/Admin/nativeprivileges hoặc unactivated. Khôngtựghép legacy/emailmơhồ. Linkfragment→JSxóahistory→CSRFPOST→serverSession→freshUserrowlock/recheck/hashsave; UIDhidden chốngtabcũđổi nhầmaccount, khôngauto-login. IP5/600s,email1/60s,exchange20/600s,fixedbuckets/directpeer khôngtinXFF; publicresponsekhôngenumerate ởstatus/body, khôngclaimtiminghằngsố. SMTPgenericfailurekhôngđổipassword/activation. Full354PASS/target24PASS, featureOFF. QAresidue saugiánđoạnphảikiểmtra readonlydata trước test, không sửa guard/flushbừa hoặc dùngpreview/dev. Không credentials/migration hiện hành/liveSMTP/GitHub khi chưa duyệtriêng.

## 12/11/2026 — Chọn GmailSMTP, chưa gửi thật/kích hoạt

Chủ dự án chọ[địa chỉ nhận thử nghiệm đã ẩn], FromNâuCoffee, brandNâuCoffee|Hỗtrợkháchhàng. Gmail587STARTTLS/noSSL/15s; AppPassword chỉowner nhập local0600/ignored, không passwordđăngnhập thường/chat. `.env.smtp.gmail` chỉopt-in, whitelist khôngđổiDB/features, khôngfallbackconsole/silent. LIVEBLOCKED cho đếncredentials/trustedpublicHTTPS/recipient/approval1mail. Khôngthay2FAGoogle; nếuAppPasswordkhôngkhảdụng trìnhOAuth2/providerkhác duyệtriêng. Giữnonce/cooldown/role/userdata; HTMLplainemailvà58targeted/330fullPASS. Passwordforgot-resetroutechưacó, khôngtựthêmflow. Không mởlạipreviewvốndừngsau reboot; khôngmigrate/bậtfeature/GitHub.

## Xác nhận hoạt động preview12/11

Chủ dự án xác nhận trực tiếp đã login10:54:21 và thêm món11:49:45 trên8000, phù hợp driftaccount/session/cart/limit và CartItem. Phân loại hoạt động hợp lệ ở mức workflow; không xóa/sửa data hoặc claim audit per-field đầy đủ. Không xem xác nhận này là phê duyệt bật feature/migration/SMTPthật/GitHub. Fullsource mới320PASS và QArehearsalPASS vẫn cần các phê duyệt kích hoạt riêng.

## 12/11/2026 — Nghiệm thu kỹ thuật không đồng nghĩa cho phép kích hoạt

Được duyệt điều tra preview chỉ đọc, E2E trênQAđộc lập và backup/restorechỉQA. Rehearsal dùng fixture synthetic, archive mã hóa/khóa tách ngoàiGit và DBrestore mới; không ghi đè/xóaDBcũ hoặc nới guard để dùngrestore làm regression. Giữ preview8000/featureOFF, không migration hiện hành hoặc gửiSMTPthật. Chuỗi drift4bảng phù hợp login nhưng chưa đủbằngchứng quynguồn; không sửa data làmkhớphash. Sửa UI quote/blur cần regressionmới, không dùng319cũ. Việc bật feature, backup/migration hiện hành, cấu hình/provider SMTP và mọiGitremote vẫn chờ duyệtriêng; GitHubtiếp tục hoãn. [Báo cáo](VOUCHERS_PHASE2_ACCEPTANCE_2026-11-12.md).

## 12/11/2026 — Hoãn đồng bộ GitHub; voucher Đợt 2 chỉ campaign mới

Theo phê duyệt mới, không tạo/push checkpoint Đợt 1 lên remote, không xóa refs đã có; giữ working tree/HEAD/index, chưa commit/push/merge/deploy. Giữ toàn bộ lịch sử/quy tắc voucher cũ. V2 được nhận diện bằng bảng Campaign riêng, usage có marker/snapshot; không dựa vào ngày tạo, không backfill/reset/recount voucher cũ. PUBLIC một lần mỗi Customer; PRIVATE theo lượt Admin cấp có audit. Một voucher/order WEB hoặc COUNTER, không APP; chọn dropdown và quote backend tự cập nhật. Tạo order thành công tính lượt, cancel/refund/failure không trả lượt V2. Counter identity và consent Đợt 1 giữ nguyên, quote chỉ kiểm tra proof. Migration/testing chỉ trên QA accounts độc lập; preview feature OFF. Backup/SMTP và activation dữ liệu hiện hành cần duyệt riêng. [Scope](VOUCHERS_PHASE2_SCOPE_2026-11-12.md).

## 12/11/2026 — Thực hiện phương án A theo phê duyệt

QA mới là cặp cố định nau_coffee_qa_accounts/nau_coffee_qa_accounts_runner trên container QA 55441/volume riêng; runner không sở hữu DB, không superuser/createdb/createrole/replication/bypassrls, chỉ CONNECT và CREATE/USAGE schema mới. `.env.qa.accounts` private 0600/ignored, không đổi creds cũ. Guard/helper nhận đúng tuple mới và attestation + identity PG17; readonly mặc định, migration chỉ qua bước bảo trì accounts_qa.py được duyệt, regression không auto migrate/CREATE/DROP DB. Full **299/299 PASS** gỡ blocker PostgreSQL. Quyền QA không cho phép migrate preview/dev, bật feature, SMTP thật hoặc Git/deploy; các bước đó vẫn chờ duyệt. [Chi tiết](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md).

## Checkpoint 12/11/2026 02:28 — giờ Việt Nam

Đã lưu [SESSION_HANDOFF_CUSTOMER_ACCOUNTS_2026-11-12_022847.md](SESSION_HANDOFF_CUSTOMER_ACCOUNTS_2026-11-12_022847.md). Giữ trạng thái 122 PASS/2 SKIP trong 124 tests, feature OFF, QA TCP credentials BLOCKED; A/B chưa được duyệt. Lượt lưu chỉ cập nhật tài liệu, không chạy lại test, không đổi code/database/Git refs/server.

## 12/11/2026 — Kết luận kiểm chứng trước bật feature

Selection POS v2 ràng buộc nonce phiên Staff + purpose COUNTER_CUSTOMER_LINK, actor/phone và TTL 300 giây. POS chỉ lấy context từ server session, không tin POST; clear/thành công xóa context. Không thay schema/migration 0005 hoặc nới guard P0. SMTP sandbox loopback chỉ nhận .invalid, dữ liệu/mail/token ở bộ nhớ, credentials SMTP thật không được kế thừa trong test. QA vật lý riêng nhưng thiếu credentials SQL => BLOCKED, không dùng preview thay thế. Backup/restore rehearsal, migration DB hiện hành, email provider, bật flag/restart và Git cần phê duyệt riêng; chưa thực thi. [Báo cáo đầy đủ](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md). Cập nhật QA: Unix socket local-trust đã xác minh role hạn chế và schema catalog.0004/38 bảng; TCP password chỉ còn verifier SCRAM. Đã trình phương án A role+DB QA mới với allowlist guard, hoặc B rotate password QA cũ; cả hai chưa thực hiện.

## 12/11/2026 — Danh tính Customer đợt 1

Giữ Django User, bổ sung CustomerProfile OneToOne; phone canonical +84 unique, email profile lower/trim và unique không phân biệt hoa thường. Không thêm unique toàn cục lên email User legacy, không backfill từ lịch sử. Tính năng tắt mặc định chờ duyệt migration/email. Tài khoản mới inactive, Staff dùng unusable password; token Django signing + nonce một lần/24h, email fragment tránh access log. Chỉ liên kết COUNTER sau lựa chọn ký gắn nhân viên và mã đồng ý một lần từ Customer email-verified, đăng nhập + mật khẩu; audit nhân viên, không tự gán theo phone/tên. Guest COUNTER/APP/voucher/payment giữ nguyên. Backend cũ giữ khi OFF; mở flag có thể cần đăng nhập lại. QA PostgreSQL và SMTP thật chưa chạy; không vượt guard. [Chi tiết](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md).

## 11/11/2026 — Test fail-closed và định dạng giá

Management dùng config.test_settings mặc định PostgreSQL READ ONLY; chỉ launcher preview rõ ràng được phục vụ ghi ứng dụng. Regression ghi PostgreSQL phải qua attestation Docker QA loopback 55441/PGDATA riêng, xác minh SQL/schema; runner không tự migrate. Credentials QA dùng file riêng NAU_QA_ENV_FILE, không đổi .env/.env.test; thiếu credentials thì BLOCKED. Preview không nhận file QA override. CI cũ dùng 5432 sẽ bị từ chối và cần cấu hình lại trước chứng nhận. Bộ lọc giá nhận 1–11 chữ số ASCII không âm, đầu vào sai tiếp tục bỏ qua. Không triển khai P1. [Chi tiết](P0_PRICE_FILTER_TEST_ISOLATION_FIX_2026-11-11.md).

## 2026-11-11_213047 (giờ Việt Nam) — Lưu audit read-only,chưa sửa lỗi

- Audit phát hiện HTTP500 với min_price=² và rủi ro runner mặc định trỏ DBpreview;chưa sửa.12yêu cầu local:9PASS,1FAIL,2NOT RUN đầy đủ. Không gọi hệ thống hếtbug hoặcproduction-ready.
-235/235 là kết quả lịch sử trênQA55441;196sourceinputs vẫnkhớp. Source trước lưu1025file khớpcheckpointd23b19d,HEAD activea848a5a,indextrống. Lần lưu chỉ thay docs,không code/data/Gitrefs.
- [Handoff audit mới nhất](SESSION_HANDOFF_AUDIT_2026-11-11_213047.md) ghi đầy đủ bằng chứng,giới hạn và việcP0/P1 chưa làm.

## 11/11/2026 — Bảo toàn bản local đã nghiệm thu,chuẩn bị main

- Source chuẩn đã được người dùng nghiệm thu trên8000;checkpoint riêng checkpoint/nau-v3-accepted-20261111,parent a848a5a,không đổi HEAD/branch/index chính hoặc source runtime.118file source/test/font/docs trong allowlist mới,không thêm QA runtime/secrets.
- **235/235 PASS** mới (209backend+26browser),196inputs không đổi;check/drift/diff-check PASS;38bảng preview READ ONLY hash không đổi,không dev. Không tác động worktree PickupOnly hoặc website8000.
- fetchCLI thiếu HTTPS credentials;GitHub connector xác minh main737efdc vàfeature73103e7 khớp origin refs. main là ancestor;kiểm tra merge-tree riêng,không push/merge/deploy.
- [Review/checkpoint/allowlist](ACCEPTED_LOCAL_CHECKPOINT_REVIEW_2026-11-11.md).

## 11/11/2026 — Sửa TypeError bộ lọc Admin có dữ liệu

- lookup_choices của AllValuesFieldListFilter là scalar int/string/NULL,không phải luôn cặp. Giữ dữ liệu tra cứu native,chỉ dịch dictionary display trong choices().
- **209/209 backend PASS**,69GET của27model dướiREAD ONLY PASS;browserReview8000 HTTP200 tại375/768/1440 PASS. Test mới có rating1/5,scalar chuỗi/NULL,facets và giữ quyền. System check/drift/diff-check PASS;196 inputs không đổi.
- Preview38 bảng không đổi,không dev;chỉ2file source/test đổi. QA55441 đã dừng;server8000 PID35865,không8001. Chưa stage/commit/push/merge/deploy.
- [Nguyên nhân,dòng127,bản sửa và bằng chứng](ADMIN_FILTER_TYPEERROR_FIX_2026-11-11.md).

## 11/11/2026 — Việt hóa toàn bộ giao diện

- Customer/Staff/Admin: Việt hóa nhãn/văn bản/lịch sử,27 model và207 trường Admin; giữ mã lưu/quyền và _meta gốc để không tạo migration. Café Premium/Noto Serif/Be Vietnam Pro được giữ; hero trang trí tiếng Việt dùng đúng Noto Serif.
- **231/231 regression PASS** (205 backend+26 browser), thêm1/1 Customer QA PASS;check/drift/diff-check PASS;195 source inputs không đổi. 96 ảnh Before,237 ảnh After ở375/768/1440;không tràn ngang.
- Chỉ QA mới trên55441 nhận fixture/tests;preview38 bảng READ ONLY fingerprint không đổi,không kết nối dev. Nạp lại đúng server8000 PID29020,không8001. Chưa stage/commit/push/merge/deploy;chờ người dùng nghiệm thu UI mới.
- [Báo cáo Việt hóa, files và ảnh](VIETNAMESE_LOCALIZATION_REVIEW_2026-11-11.md).

## 11/11/2026 — Localhost duy nhất 8000

- Người dùng nghiệm thu Café Premium/font tại 8000. Giữ server PID66782; 8001 đã không còn listener từ đầu phiên, không tạo server mới hoặc gửi tín hiệu vào PID cũ.
- Launcher default8000; cập nhật Runserver/README, không có launch.json/tasks.json cần sửa. Giữ config.test_settings và DB preview nau_coffee_test, không chuyển dev.
- System check/diff-check/CLI syntax/default PASS; HTTP200;16 CSS/font assets khớp;38 bảng preview READ ONLY fingerprint không đổi. Không chạy full regression ghi dữ liệu;225/225 là kết quả của phiên trước, trước thay đổi default launcher.
- Không đổi UI/business/data hoặc stage/commit/push/merge/deploy. [Checkpoint localhost duy nhất](SINGLE_LOCALHOST_8000_2026-11-11.md).

## 11/11/2026 — Đối chiếu preview 8001 và hệ thống chính 8000

- 8001 đã dùng source chính `/home/thientran/projects/NauCoffee`, branch feature/cafe-premium-reference-20261028, HEAD a848a5a. 8000 ban đầu không có listener; đã mở cùng launcher/settings test trên 8000, giữ nguyên PID 8001. Không cần copy code/CSS.
- **225/225 PASS mới**, check/drift/diff-check PASS; 189 source input không đổi; 32 lượt static/font khớp source; 6 cặp ảnh home/menu 375/768/1440 khớp pixel. Regression chỉ tại cluster QA độc lập 55441.
- Preview 38 bảng không đổi (READ ONLY fingerprint), worktree tham chiếu 1551 file không đổi; không kết nối dev. Ngoài tài liệu chỉ cập nhật Runserver; chưa stage/commit/push/merge/deploy. Chờ người dùng nghiệm thu 8000.
- [Checkpoint và bằng chứng](PREVIEW_MAIN_SYNC_REVIEW_2026-11-11.md).

## 11/11/2026 — Font tiếng Việt toàn hệ thống

- Root cause:Georgia Windows thiếu các glyph Việt,CDP thấy mixed Georgia/fallback trong cùng heading;DOM/source đúng NFC. Thay family content bằng Noto Serif/Be Vietnam Pro WOFF2 self-hostOFL,giữ logo và tracking/kerning;chỉ nới mô tả hero mobile290→310 để giữ CTA trong khung.
- **225/225 PASS** (200 backend+25 browser),189 source/export/freeze khớp;check/drift/diff-check PASS;96 BEFORE/96 AFTER375/768/1440,24 glyph NFC/NFD/weight cases offline,ảnh promo A/B và đủ Customer/Staff/Admin.
- Không đổi nghiệp vụ/models/migrations/menu/giá/BOM/ảnh;test fixtures ở QA riêng55441,preview38 hashes không đổi từ mốc kiểm READ ONLY;không kết nối dev. Chưa commit/push/merge/deploy,allowlist95 cũ cần rà soát lại.
- [Báo cáo font,license,Before/After và giới hạn](VIETNAMESE_TYPOGRAPHY_REVIEW_2026-11-11.md).

## 11/11/2026 — Refund & POS nhiều món

- Tái hiện POS standard-menu lỗiJS null options→management/index không cập nhật→chỉ1 item; sửa JS và formset strict để không tạo đơn thiếu món. Summary unit/line/subtotal/total,DELETE và bound errors đúng;giữ max10,duplicateSKU riêng,giá backend và Payment UNPAID.
- Refund backend không tự hoàn; thêm Customer status/amount/time,audit refund_requested và Admin /dashboard/refunds/ với confirm dialog/strict locked replay. Không backfill dữ liệu lịch sử.
- **224/224 PASS:200 backend+24 browser**,175 source inputs/export/freeze khớp;check/drift/diff-check PASS,responsive375/768/1440 PASS.211 tests/allowlist78 cũ không chứng nhận bản mới.
- QA PostgreSQL17 độc lập55441;38 preview table hashes không đổi,không kết nối dev/migration mới/giá/BOM hoặc sửa reference. Chờ người dùng nghiệm thu lại;chưa stage/commit/push/merge/deploy.
- [Báo cáo,POST/DB/ảnh và allowlist mới](REFUND_POS_FIX_REVIEW_2026-11-11.md).

## 11/11/2026 — Staff V2 trên source chính

- Bốn cột Kanban,ba nút bất đồng bộ,drawer cả đơn hoàn tất,poll12s giữ bản nháp và không ghi đè action. Version guard và row locks; finish READY→PICKUP_WAITING atomic.
- WEB PAID không thu lại; COUNTER qua POS thật ghi PAID/event một lần. Từ chối tách khỏi lịch sử thành công; Staff không bỏ qua Kanban bằng route dropdown cũ,Admin giữ ngoại lệ có validation.
- **211/211 PASS:191 backend +20 browser**,170 source inputs freeze khớp; check/drift/diff-check PASS,375/768/1440 PASS. Không dùng kết quả190 tests cũ để thay regression này.
- Regression dùng PostgreSQL17 độc lập55439 trong /tmp vì preview5432 đang có6 đơn. Preview38 table fingerprints trước/sau bằng nhau; không kết nối dev. Cluster QA tạm đã dừng. Không model/migration/giá/BOM thay đổi,không sửa reference.
- [Báo cáo Staff V2,nguyên nhân,file/test/ảnh và cách nghiệm thu](STAFF_V2_REVIEW_2026-11-11.md). Chưa stage/commit/push/merge/deploy; chờ người dùng nghiệm thu. Ghi chú drawer chỉ tạm trên tab,không lưu DB; đơn#1 tiếp tục chặn pha an toàn.

## 10/11/2026 — Tích hợp Pickup Only trực tiếp vào source chính

Theo yêu cầu mới nhất, sửa source chính NauCoffee tại a848a5a; PickupOnly chỉ đọc. Giữ migrations/models/giá/menu/BOM và workflow legacy, chỉ khóa WEB mới PICKUP/MOCK_ONLINE, tự lịch, checkout tới payment; thêm partner page và hero/header links. Manual POS giữ lịch nhận riêng. Không kết nối dev, không stage/commit/push/merge/deploy.

**190/190 PASS** (173 backend +17 browser), 162 inputs freeze không đổi; check/drift PASS, responsive375/768/1440 PASS. Không code đổi sau regression. Kết quả/bằng chứng cuối: [báo cáo tích hợp](MAIN_PICKUP_INTEGRATION_2026-11-10.md), [QA](qa/2026-11-10-main-pickup/). Báo cáo này thay thế hướng dẫn giữ nguyên source chính của phiên tham khảo trước. Chờ nhóm nghiệm thu local; không dùng kết quả reference làm kết quả regression main.

## Chuẩn bị menu chuẩn — cờ staging và rehearsal test-only

## 06/11/2026 — cập nhật contract UI và đủ điều kiện checkpoint

- Người dùng phê duyệt bỏ “Từ” và caption “Hình ảnh minh họa.”; chỉ cập nhật assertion/selector lỗi thời, giữ SKU/WEB/VND/form/no-write guards và templates hiện tại. Thêm coverage card legacy/FIXED và8detail tại3widths.
- Backend149/149 và browser15/15PASS trong lượt discovery164/164. Không chạy importer hoặc test trên dev. Không commit ảnh QA mới; dùng artifactroot ignored. Giữ lịch sửFAIL trong báo cáo thay vì xóa.
- Đã rà soát script clone prerequisites/guards; --help chỉ kiểm tra CLI không DB. Không xem script là quy trình tái tạo đã nghiệm thu hoặc backup tồn tại là restoreverified. Commit/push đúng featurebranch đã được phép; không force/merge/rebase/deploy. Xem [checkpoint](CHECKPOINT_2026-11-06.md).

## 06/11/2026 — bảo toàn trước commit, dừng khi regression FAIL

- Quyền commit/push đã được chủ dự án cấp trong nhiệm vụ lưu tiến độ; vẫn phải đạt gate tests trước stage/commit/push. Không force/merge/rebase/reset/stash/deploy.
- Giữ nguyên patch giao hàng/UI và tests. Hai assertions copy UI thất bại trong full regression không được âm thầm đổi để lấy PASS; dừng Git publish và báo cáo.
- Lưu hai script sync menu/inventory tìm thấy ở thư mục cha vào scripts/ nguyên byte, giữ nguyên bản gốc và không thực thi. Không mang dump/env/PII vào Git; không tạo data migration hoặc pipeline khởi tạo nguy cơ ghi đè. Fresh-clone tái tạo đầy đủ mô tả/activation/config chưa được kiểm chứng.
- Các tests chỉ dùng nau_coffee_test sau xác minh actual role/PostgreSQL17 và không CONNECT dev; không audit hoặc ghi dữ liệu dev trong phiên này. Chi tiết tại [checkpoint](CHECKPOINT_2026-11-06.md).

Chủ dự án chỉ duyệt code/test, chưa duyệt backup/ghi dev. Dùng sizeFIXED để giữ unique(product,size) và13SKU cũ, tạo8SKU mới + cost riêng Admin-only. Không tự tính công thức từ cost. Staging không tắt legacy; activate phải qua BOM/kho hiện hữu, atomic hoặc rollback. Nếu cutover khi thiếu BOM thì chỉ xem8 món/giá, không nhận đặt; không giả định zero-downtime. Featureflag mặc địnhFalse, chưa sửa .env. Rehearsal command từ chối dev; apply dev cần chuẩn bị/review riêng sau backup/approval.

Chặn DELIVERY WEB mới ở form+service khi cờTrue, giữ workflow lịch sử. Giá WEB/COUNTER Admin lưu đồng bộ, APP độc lập; validator failclosed khi lệch. Giữ CF04-M trong fixture và yêu cầu chọn lại, không tự đổi dung tích. Cuối phiên phát hiện CartItemdev1→0 so với audit trước, chưa rõ nguyên nhân; dừng tại chuẩn bị, không tự phục hồi và không claim dev nguyên trạng từ testfixture. [Chi tiết](STANDARD_MENU_REHEARSAL_2026-10-31.md).

## Menu và giá mới nhất —31/10/2026

Chủ dự án chốt WEB=COUNTER, WEB chỉ nhận tại quán, APP theo giá sàn, mỗi món một dung tích. APP CF04=54.000,TE02=46.000,OT01=66.000,OT02=62.000 thay giá25/10; bảng8 món đầy đủ tại [quyết định mới](APPROVED_MENU_PRICING_2026-10-31.md). Không suy BOM từ cost, không thêm option/sale/voucher. Quyết định thay thế các ghi chú “WEB chưa chốt” lịch sử, chưa đồng nghĩa apply DB. [Phương án tạo8SKU mới/giữ13SKU cũ và xử lý giỏ](MENU_ROLLOUT_PLAN_2026-10-31.md) chờ duyệt; DB thiếu BOM/kho cần xác nhận riêng. Lượt này chỉ tài liệu+SELECT, không code nghiệp vụ/migrate/seed/ghi dev.

## Nội dung người dùng và minh bạch mô phỏng — 31/10/2026

Theo yêu cầu chủ dự án, bỏ nhãn đồ án/DEMO khỏi footer và nội dung chung không cần thiết. Không bỏ cảnh báo trạng thái thật: checkout/payment/order/thu tiền/hoàn tiền/đối soát và báo cáo vẫn nêu mô phỏng, không thu tiền thật; giá WEB chưa chốt. Không chỉnh dữ liệu lưu sẵn để thay câu chữ. Giữ enum/field/permissions và quy tắc backend.

Typography dùng fallback hệ thống hỗ trợ tiếng Việt, class footer riêng nạp sau CSS các trang; chuẩn hóa khoảng cách thay vì chèn NBSP hoặc xuống dòng cứng. Unicode nguồn footer NFC; không kết luận lỗi font cho ảnh chưa đính kèm. [Bằng chứng và giới hạn](COPY_SPACING_REVIEW_2026-10-31.md).

# Quyết định triển khai

## 30/10/2026 — Căn lại trang chủ bằng ảnh cùng kích thước

- Giữ mọi WIP cũ; tạo stylesheet chỉ nạp ở Home thay vì sửa toàn bộ giao diện. Base thêm block page_styles, Home thêm compact card riêng, không đổi cards Menu hoặc backend pricing.
- Featured Home hiển thị6 món bằng template slice để đạt cấu trúc6 thẻ như ảnh. Queryset/backend/menu8 món và13 SKU không đổi; toàn thẻ dẫn tới detail thật, không thêm wishlist/slider giả.
- Review không có dữ liệu được duyệt hiển thị empty state gọn, không sao chép3 review/avatar từ mẫu. Banner không có voucher thực dùng editorial CTA; không tạo NAU20 hoặc sale giả.
- Chỉ dùng tài sản minh họa hiện có và CSS định vị ảnh. Ảnh nền chưa trùng mẫu nên không claim pixel-match; không đưa screenshot nguyên trang thành nền website.
- Chụp Before/After public Home bằng browser guest ở cùng1448×1086, cộng768/375. Public GET không ghi business data. Test mutation chỉ guarded nau_coffee_test/--keepdb sau actual isolation verification.
- Phát hiện server --noreload giữ compiled template; lượt capture giốngBefore bị loại khỏi kết luận After. Restart đúng server do phiên này mở rồi chụp lại, không kill tiến trình lạ.


## 30/10/2026 — Drive31 là nguồn UI ưu tiên

- Dùng Google Drive connector theo skill google-drive, metadata trước raw-file download; không thay sharing/quyền trên Drive. Có đủ ảnh nên không cần chủ dự án cung cấp đường dẫn khác. Bản tải riêng ngoài project, không ghi đè bản cũ.
- Tạo `drive-reference.css` sau các stylesheet WIP để bảo toàn các thay đổi local. Không áp ảnh nguyên màn hình thành website hoặc giả backend bằng nội dung mockup.
- Management/config projections GET-only có ADMIN guard phía server. Gallery/related và bộ lọc dùng ORM; querystring pagination giữ filters. Native CRUD tiếp tục kiểm tra Django permissions; không tự nâng role/is_staff.
- Config store/appearance/payment/delivery/notifications/security hiển thị allowlist trạng thái/giá trị thực. Nếu thiếu StoreSettings chỉ dùng instance chưa save để đọc DEMO default; không get_or_create trên GET. Không lộ secrets, không giả bật email/backup hoặc thêm Save khi chưa có backend.
- POS cards chỉ ghi lựa chọn vào formset hiện hữu, giữ bound errors/max10/options per-product. Kanban gửi POST tới transition endpoint cũ để stock/state/payment/audit rules được giữ nguyên. Không thu tiền tự động và không tạo shadow lifecycle.
- Không copy giá trong ảnh vào DB. Product table đọc từng SKU/volume/channel price hiện hữu; cost schema thiếu được ghi rõ. Image/avatar/HR branch/favorites/timer chưa có backend thì không làm control giả.
- Artifact mới dùng DB test fixtures, không dùng phiên dev hoặc ghi cookie/auth state. HTTP smoke dev chỉ public GET; mutation tests chỉ guarded PostgreSQL test --keepdb.


## 30/10/2026 — Resume local, bộ ảnh gốc và ranh giới dữ liệu

- Đã tìm đủ 21 ảnh gốc trên Windows Downloads; kiểm kê hash/khả năng đọc riêng, không copy21 ảnh concept cỡ lớn vào static hay PostgreSQL. Hai bản ZIP là duplicate. Admin collage là tham chiếu nhiều màn hình, không đếm thành chức năng đã code.
- `docker start pg_lab_postgres` thực hiện sau phê duyệt công cụ chỉ để bật container cũ; không recreate, thay port/volume/grants/schema hoặc bật pgAdmin không cần thiết. Chỉ start web sau verify dev/test identity/isolation PASS và cổng8000trống.
- Mọi test ghi dữ liệu chỉ dùng config.test_settings, verified pre-created nau_coffee_test và --keepdb. Không SQLite thay cho PostgreSQL hoặc test trên dev.
- Chỉ đổi templates/CSS ở đợt này; thumbnails dùng Product.image_url, tiền/qty/POST/idempotency/validation giữ backend. Không copy dữ liệu mockup (giáAPP, sizeXL, faux discounts/rating, địa chỉCầnThơ, social OAuth, thanh toán bank) vào nghiệp vụ.
- Staff vẫn không được truy cập CRUD Admin; các shortcut mới nằm trong ADMIN+is_staff branch, quyền server của Django Admin tiếp tục là ranh giới. Không cấp permission mới.
- Chromium/libs riêng /tmp mất sau reboot; tải lại sau cấp quyền mạng, giải nén apt packages vào/tmp thay vì sudo cài hệ thống. Không ghi secrets/cookie/auth state vào artifact. Screenshots mới chỉ fixtures DB test.


## 28/10/2026 — Bảo toàn patch Café Premium đang có

- Ưu tiên yêu cầu hiện tại: giữ nhánh thực `feature/cafe-premium-reference-20261028` và toàn bộ local diff, không quay về nhánh WIP lịch sử; không commit/push khi chưa duyệt.
- Giữ copy menu rỗng “Chưa tìm thấy món phù hợp”; cập nhật assertion kèm kiểm chứng kết quả thực rỗng và hành động xóa lọc, không bỏ test hoặc skip.
- Image URL property chỉ thay fallback hiển thị theo product code, ưu tiên ProductImage nếu có; không schema migration/ghi ProductImage/giá/SKU. WebP là ảnh minh họa từ patch local, không xác nhận ảnh chụp chính thức hay quyền khai thác production.
- Khôi phục các affordance bị mất trong bản tham chiếu: desktop POST logout+CSRF, accessible cart SVG, mobile nav labels, active report link; backend authorization/pricing/payment/stock giữ nguyên.
- Test runner preflight thực và role không CONNECT dev là bằng chứng cách ly; không dùng SQLite để thay PostgreSQL acceptance. Sandbox chặn kết nối được chạy lại ngoài sandbox theo phê duyệt công cụ, vẫn chỉ DB test.
- Cho phép chọn NAU_QA_ROOT cho capture test để lưu bằng chứng mới, mặc định cũ giữ tương thích. Reset scrollLeft rail sau lazy loading chỉ phục vụ ảnh QA đúng vị trí đầu; không bỏ assertion ảnh/overflow/link.
- Chưa có bộ21 ảnh gốc trong workspace; không giả đã đối chiếu pixel hoặc hoàn thiện21/21 màn hình. Không thay giá WEB/COUNTER/APP hoặc mapping13SKU dựa trên mockup.


## 28/10/2026 — WIP local Customer/Operations UI

- Chỉ nhánh wip/ui-redesign-local-20261027 theo chỉ dẫn hiện hành; Issue #2/#3 đọc được và ghi nhận, nhưng tên nhánh cũ trong Issue không thay chỉ dẫn mới. Không đóng Issue/comment/push hoặc merge main.
- Không chạm models/migrations/seed/pricing/stock/BOM/payment/RBAC services. Query projection Home/Menu và POS metadata chỉ đọc giá hiện có; giá WEB chưa chốt được ghi rõ. COUNTER/APP preview không ngầm áp bảng 25/10 lên dữ liệu legacy.
- Screenshot before lấy từ `git archive 5d233a0` trong /tmp với fixtures DB test; after từ source WIP sửa. Không checkout/reset nhánh hoặc database. Artifacts chỉ chứa fixture giả lập.
- Chromium dùng runtime/thư viện riêng /tmp do môi trường Codex không thấy libs do Terminal cài; không đổi PostgreSQL/container/host config. Browser tests dùng `.env.test`/safe runner/--keepdb, không đụng .env/dev data.
- UI enhancement không đổi contract POST: preview từ numeric backend data, giá cuối luôn server re-quote. POS retain max_num/min_num/idempotency/stock/channel guards; JS add/remove/reindex và options filter; no-JS fallback cũ vẫn hoạt động.
- Giữ SVG minh họa, không gọi placeholder là ảnh sản phẩm được duyệt; favicon tự viết SVG cùng brand hiện có, không phải PWA manifest.
- Native Django Admin CRUD/permissions giữ nguyên; CSS tablet/sidebar được sửa, chỉ thêm browser CRUD đối với category fixture test. Không suy rộng thành toàn bộ admin acceptance đã xong.

Ngày: 13/10/2026 (Asia/Ho_Chi_Minh).

## Sprint 0

- Đọc toàn bộ AGENTS.md và master spec. Workspace ban đầu chỉ có hai tài liệu, không có ứng dụng. `.git` là thư mục đặc biệt chỉ đọc; `git status --short` trả `fatal: not a git repository`. Không cố ghi đè `.git` hay tạo commit giả.
- Stack giữ nguyên Django Templates + PostgreSQL 17. Docker read-only sau cấp quyền xác nhận container `pg_lab_postgres postgres:17`. Không truy cập credentials, tạo DB/user hoặc thay đổi container.
- Theo chỉ đạo mới của chủ dự án, bootstrap pip/venv dùng apt. Không dùng get-pip.py. Thư viện dự án chỉ cài trong `.venv`.
- DB riêng vẫn cần thiết lập an toàn và duyệt trước tạo theo Sprint 0; thiếu DB không cản tạo source/tests. SQLite in-memory là fallback test có bật rõ ràng, không dùng mặc định và không coi là PostgreSQL PASS.

## Sprint 1

- Dùng Django User mặc định và groups CUSTOMER/STAFF/ADMIN; Guest là người chưa đăng nhập. Không nhận role từ form đăng ký. `is_staff` không đồng nghĩa Staff nghiệp vụ. Admin site có role gate server-side riêng.
- Gom catalog/auth foundation trong app `catalog` lúc đầu; các domain giao dịch sẽ tách module ở Sprint 2, không dựng microservices.
- Seed theo bảng mục 3.2: trà đào WEB/COUNTER 25.000, APP 42.000 VND. 3 món đầu size STANDARD 350ml; 5 món còn lại M 350/L 500ml, L thêm 5.000đ theo từng kênh. Tất cả là giả định DEMO chưa được duyệt kinh doanh/nộp bài.
- Giá sale chỉ hiệu lực khi có đầy đủ thời hạn hợp lệ và sale nhỏ hơn giá gốc. Không seed sale giả; admin cấu hình được. Chưa có voucher (Sprint 2).
- Ảnh fallback SVG tự vẽ lưu trong repo, có nhãn DEMO. Chưa coi là đã đủ ảnh đồ uống thật theo REQ-05. Upload admin dùng ImageField, giới hạn 5MB/định dạng; production storage bền chưa cấu hình.
- Seed idempotent, chỉ tạo thiếu, giữ các chỉnh sửa hiện hữu; không tạo mật khẩu hardcode.
- `/healthz/` hiện chỉ kiểm tra web liveness, không xác nhận database readiness.

## Rà soát bootstrap trước khi chạy (13/10/2026)

- Chủ dự án yêu cầu báo cáo trước bootstrap. Lệnh bootstrap trước đó bị từ chối ở bước quyền thực thi, chưa chạy; chưa tạo DB/role/env. Không thử lại trước báo cáo.
- Đọc trực tiếp source Django 5.2.18 PostgreSQL creation: `--keepdb` bỏ CREATE nếu DB tồn tại nhưng vẫn có nhánh CREATE nếu thiếu; clone parallel cũng có nhánh DROP. Vì vậy dùng `config.test_runner.NauTestRunner` riêng: không đi qua database creation/clone/destruction của PostgreSQL.
- PostgreSQL test chỉ cho phép DB NAME/TEST.NAME `nau_coffee_test`, USER `nau_coffee_test_runner`, loopback HOST, `--keepdb`, parallel=1, một alias. Preflight read-only xác nhận actual database/user và NOSUPERUSER/NOCREATEDB/NOCREATEROLE trước migrate. Thiếu DB thì lỗi kết nối, không tự tạo.
- `config.test_settings` chỉ đọc credentials `.env.test`; ghi đè DATABASE_URL từ môi trường để tránh dùng nhầm dev credentials. Normal settings dùng runner guard nên lệnh test nhầm trên .env dev bị từ chối.
- TestCase rollback/TransactionTestCase flush và migrations chỉ ở DB test riêng. Không kết nối maintenance DB qua runner. Teardown chỉ đóng connection, không xóa DB test. SQLite fallback chỉ nhận `:memory:`.
- Bootstrap preflight Docker/readiness + từ chối DB/role/file đã tồn tại. Secrets tạo mới lưu 0600/O_EXCL trước CREATE để không mất password khi lỗi. Mỗi CREATE riêng được ghi nhận; lỗi giữa chừng báo confirmed_created/local_files/last_attempt (bước cuối có thể chưa rõ), không DROP/revoke role/reset tự động.
- PUBLIC quyền DB Nâu mới bị revoke; test role không được CONNECT DB dev. Script không sửa grants/schema/data của database cũ, không đổi cấu hình/container/volume. Chưa kiểm thử live các quyền này vì bootstrap chưa được chạy.

## Bootstrap thành công và phê duyệt tách bước

- Chủ dự án đã chạy bootstrap thành công. Live read-only verify PASS: cả hai role hạn chế trên PostgreSQL 17 và không CONNECT chéo. Không chạy lại bootstrap/cleanup.
- Theo yêu cầu mới nhất, check → actual Django identity → migration plan → phê duyệt riêng migrate; từng command riêng, dừng nếu bước trước lỗi. Đã áp dụng 21 migrations chỉ ở nau_coffee_dev sau phê duyệt riêng.
- Seed cần xác nhận riêng và **chưa chạy trên dev**. Command chỉ thêm catalog/role setup demo bằng get_or_create; giữ giá chỉnh tay; không tạo password/user, order hoặc payments. Không tạo voucher/options demo ở phiên hiện tại.
- Seed ADMIN permissions chỉ `.add` permissions thiếu; không `.set`/remove quyền. Target guard nhận đúng DB/role Nâu trên loopback 5432 và xác nhận actual current_database/current_user trước mutation. SQLite test fallback chỉ in-memory explicit. Wrong target dừng trước writes.
- Read-only admin commerce không cho sửa snapshots/totals/payment/history tùy tiện. Transition nghiệp vụ sẽ qua service ở Sprint 2; voucher CRUD riêng cho Admin.
- Nếu sudo chạy bootstrap, file secrets được chown về SUDO_UID/SUDO_GID và giữ 0600; không công khai secrets.

## Sprint 1 PostgreSQL và Sprint 2

- Chủ dự án xác nhận riêng seed dev; đã chạy đúng lệnh seed một lần trong phiên này, verify dữ liệu trước/sau PostgreSQL tests PASS. Không chạy lại bootstrap, không sửa DB/container cũ.
- Test runner nhận parallel=0 mặc định và 1, từ chối >1; vẫn không gọi stock DB creation path. Kết quả suite mới nhất 57 PASS PostgreSQL, có race tests dùng Barrier/connections riêng.
- Cart merge giữ token session UUID qua login; cùng cấu hình merge, giới hạn 99 ly; trường hợp tổng vượt 99 đang cap 99 (cần thông báo UX tốt hơn). Snapshot order giữ nguyên tên/SKU/options/giá lúc mua.
- Voucher reserve lúc tạo order atomic; giới hạn đọc dưới lock voucher; cancel release. Mặc định không stacking sale/voucher. Dev chưa seed NAU10; Admin có thể CRUD voucher trong phạm vi demo.
- Pickup chỉ PAY_AT_PICKUP hoặc MOCK_ONLINE; delivery COD/MOCK_ONLINE. Shipping demo fallback StoreSettings 15.000đ, miễn ship từ 200.000đ sau discount, có thể cấu hình Admin. Quote không tạo StoreSettings trong GET.
- WEB order idempotency user+UUID; lock user/cart khi place_order, voucher/price khi quote. Repeated submit trả existing order trước khi đọc cart đã tiêu thụ. GET checkout cho giỏ mới sinh key mới khi key cũ đã có order.
- Lifecycle CONFIRMED→PREPARING→READY→PICKUP_WAITING/DELIVERING→COMPLETED; không tự đánh dấu COD paid khi completed. Cash capture do Staff/Admin có event demo. Mock payment success/failure/retry idempotent, hủy paid mock tạo REFUND_PENDING và Admin refund tạo REFUNDED/event.
- Delivery chưa có vị trí được duyệt, luôn chờ xác minh; không cho PREPARING nếu delivery_verified false. Chưa có workflow cấp delivery_verified qua Staff UI, bổ sung Sprint 4; không giả geocoding/km thực.
- PREPARING hiện chưa tiêu hao nguyên liệu; BOM/ledger/loyalty/manual APP/COUNTER vẫn unfinished Sprint 4, ghi rõ trong dashboard. Chưa có browser QA nên không mark DONE gate đầy đủ.


## Phiên Codex Cloud — 18/10/2026

- Chủ dự án phê duyệt PostgreSQL **chỉ trong Codex Cloud**, DB/role dev/test riêng, secrets sinh mới, không laptop, không công khai DB và không tài nguyên trả phí. Tiếp tục source sau onboarding được phê duyệt rõ; quy tắc giữ source trong giai đoạn setup không ngăn nhiệm vụ coding mới này. Không push/public deploy.
- Trạng thái checkpoint WSL tạm dừng cũ đã được chỉ đạo tiếp tục trong cloud thay thế. Dùng checkout sẵn có; không tạo worktree. Nhánh `codex/cloud-sprints-3-4` dành cho milestone này.
- Các module mới giữ Django monolith: `support` cho messages/reviews/policies/rate limiting; `commerce.operations` cho schedules/stock/loyalty/manual order/report views; profiles/addresses trong catalog. Không thêm dịch vụ/API có phí.
- Store-row lock giữ slot 15 phút, mặc định lead 15 phút/horizon 7 ngày/capacity 10. Để trống schedule là chọn slot sớm nhất còn chỗ; PENDING_PAYMENT cũng chiếm slot tới khi khách hủy. Admin sửa các tham số hợp lệ trong StoreSettings.
- BOM/stock nguyên liệu theo SKU và topping. Công thức hỗn hợp/nước/ly/thạch cùng tồn đầu chỉ DEMO; ledger append-only, seed không bổ sung lại tồn đã dùng. Order lock trước ingredient locks theo ID để tránh overspend; missing recipe chặn pha. Options snapshot mới giữ ID để tra BOM topping; đơn legacy thiếu mapping topping phải được rà soát, không giả tiêu hao.
- Loyalty mặc định floor((subtotal-discount)/10000) khi COMPLETED và PAID; event EARN unique theo order. COD thu sau completion vẫn tích đúng một lần. Không redeem tiền/điểm. Refund hiện chỉ luồng hủy trước pha chế, không refund đơn completed nên không có nhánh đảo điểm của completed refund chưa được triển khai.
- Đơn APP/COUNTER nhập tay dùng cùng lifecycle/kho, price lookup theo channel, không tin giá client. APP cần external reference và method EXTERNAL_DEMO, đối soát riêng, không dùng cash/gateway website. Form manual hiện phục vụ pickup/bàn giao bên ngoài; không giả tích hợp partner delivery.
- Delivery dùng người vận hành xác minh thủ công 0–3 km kèm căn cứ và audit; không dùng tọa độ cửa hàng chưa xác nhận, không gọi Haversine thành khoảng cách đường đi/GPS. StatusHistory cũng ghi thao tác bị từ chối do thiếu kho.
- Stock adjustment cần ADMIN hoặc STAFF + explicit add_stockmovement permission. Seed không cấp quyền điều chỉnh cho tất cả Staff. Các ledger bất biến trong Admin; cấu hình Ingredient/Recipe/Policy có CRUD.
- Review source fields bất biến trong Admin, moderation ghi actor; public chỉ APPROVED. Contact/feedback chỉ gắn order của người gửi, CSRF + honeypot + DB-backed counters. Login/register cũng giới hạn qua counters; không tin X-Forwarded-For client. Production proxy identity/rate policy cần rà soát tại lúc deploy; không dùng header thiếu trust config.
- Giao diện dùng CSS/system fonts, SVG nội bộ, không phụ thuộc CDN. Ảnh ngoài bị policy 403; lưu allowlist domains cần thiết nhưng không giả là tải/licensing đã xong. Google Maps khu vực chỉ minh họa, fallback luôn hiển thị. Chưa thay placeholder bằng ảnh chưa xác minh bản quyền.
- Snapshot files và live process tách biệt. Helper cloud/archives 0600 ngoài checkout; thử restore vào instance/volume mới và giữ nguyên original. Lưu config draft không Publish hoặc áp dụng runtime. Fresh-task restoration còn NOT RUN.
- `check --deploy` PASS là kiểm tra settings; Gunicorn smoke hiện dùng development settings. Chưa xác nhận TLS/provider/public deployment. Không nới bảo mật để làm checks PASS.


## Checkout stock và recipe snapshot — 21/10/2026

- Chốt một milestone tiếp theo theo §5.1.7/§9.4: kiểm tra tổng nhu cầu nguyên liệu toàn đơn ở WEB và manual APP/COUNTER trước khi tạo Order/Payment. Dùng ingredient row locks theo ID; transaction rollback giữ cart và không tạo payment khi thiếu kho/BOM hoặc ingredient inactive. Không trừ hoặc reserve stock lúc checkout; thông báo rõ cho khách và recheck ở PREPARING. Reservation/expiry/release là phạm vi riêng, chưa claim đã chống nhận mọi đơn vượt khả năng cung ứng tương lai.
- Thêm duy nhất OrderItem.recipe_snapshot JSON nullable bằng migration0003. Snapshot ghi ingredient ID/name/unit và quantity per drink bằng Decimal string; cộng cả SKU và topping, tổng hợp ingredients chung giữa nhiều dòng trước khi check. Staff/Admin chỉ đọc snapshot; không nhận recipe từ client.
- PREPARING dùng recipe đã lưu và item.quantity, không đọc BOM mới cho order mới. Kiểm tra unit/active/supply vẫn thực hiện để không áp quantity của đơn vị cũ lên nguyên liệu đã đổi unit. Ledger unique consume key tiếp tục chống trừ hai lần; snapshots sai/NaN/missing ingredients fail closed.
- Legacy NULL không backfill tự động hoặc giả lịch sử: chỉ chốt recipe hiện tại ở lần PREPARING thành công, ghi OrderStatusHistory rõ đây không phải recipe lịch sử checkout. Thiếu supply/BOM thì rollback, không âm thầm sửa order cũ.
- Migration dev là ADD COLUMN nullable, giữ bản sao lưu trước/sau. Không reset, bootstrap, reseed hoặc sửa bản ghi hiện có ngoài cột mới NULL; fingerprints đã đối chiếu. Các tests chỉ chạy DB test riêng, không dùng dữ liệu dev để mô phỏng orders.
- Browser QA mới bổ sung refund/logout/cart edits/delivery/COD/shortage; scope assertions theo field label và role để phân biệt audit với thông báo. Không tắt Django async safety hoặc weakening assertions.


## CI image readiness — 21/10/2026

Giữ loading="lazy" và static image source của ứng dụng. Browser QA phải scroll ảnh vào viewport, chờ complete tối đa10s/ảnh và giữ naturalWidth>0 cùng assertion tổng hợp; không dùng fixed sleep hay skip để giấu lỗi. Thêm fixture768px deterministic kiểm tra lazy image và helper từ chối HTTP404. Không coi kết quả cloud là CI PASS; chẩn đoán gốc GitHub chỉ dựa log được cung cấp do API Forbidden.


## UI/UX theo menu duyệt25/10 — 27/10/2026

Merge main737efdc vào feature, không rebase/force. Chỉ sửa presentation và empty checkout GET; không gán giá WEB, đổi13 SKU hoặc cost/BOM/seed/migrations. PostgreSQL cũ không có trên cloud mới nên đối chiếu source/schema, tạo test-only cluster mới sau đối chiếu để chạy regression. Shared operations navigation chỉ là hiển thị; giữ authorization ở view/service. Maps link thường trực và iframe opt-in không dựa vào onload iframe để tuyên bố Google hoạt động. Mockup không có trongrepo thì không claim pixel match; Issue API Forbidden thì chỉ xử lý phạm vi chủ dự án liệt kê. Dữ liệu rollout/menu cần phê duyệt riêng theo MENU_RECONCILIATION_2026-10-27.md.
# Quyết định triển khai 20/11/2026 — Lịch nhận món và UI Customer

- Mốc vào thực đơn được ghi server-side trong session; thời gian chọn tay tối thiểu là mốc này +35 phút.
- Nếu không chọn, `scheduled_for` chỉ được xác định khi thanh toán mô phỏng thành công và bằng chính xác `paid_at + 30 phút`, có kiểm tra khả năng phục vụ.
- Không ghi ngược thông tin người nhận đã sửa tại checkout vào CustomerProfile.
- Mapping trạng thái thân thiện chỉ áp dụng ở Customer UI; enum và Staff/Admin giữ nguyên.
- Google Maps được nhúng trực tiếp dưới footer bằng địa chỉ đã chốt, kèm link fallback; cần chủ dự án xác nhận ghim hiển thị thực tế.
# Quyết định UI 20/11/2026 — Chọn giờ 24 giờ

- Customer chọn ngày bằng date control và chọn giờ/phút bằng select tách biệt; không dùng `datetime-local` vì cách hiển thị 12/24 giờ do trình duyệt/hệ điều hành quyết định.
- Server vẫn là nguồn xác thực cuối cùng và ghép giá trị theo timezone `Asia/Ho_Chi_Minh`; không đổi quy tắc scheduling hiện hữu.
# Quyết định 20/11/2026 — Định dạng chính sách

- Không lưu HTML tùy ý và không thêm editor phụ thuộc CDN. Admin editor chuyển thao tác trực quan thành tập Markdown giới hạn trong `PolicyRevision.body` hiện có.
- Server renderer dùng allowlist cấu trúc/thẻ và allowlist scheme liên kết; preview, history và Customer tái sử dụng cùng renderer.
- Giữ nguyên hash, draft/review/publish/archive và bằng chứng chấp thuận; không migration/backfill nội dung lịch sử.
> **20/11/2026 — UI Round 2:** thông tin cửa hàng lấy từ `catalog.store_identity.STORE`; Customer giữ Maps dưới Footer còn Staff/Admin không render iframe. `/ve-nau/` là route giới thiệu chuẩn; Contact vẫn ở Footer nhưng bỏ khỏi main nav. Privacy Customer chỉ trình bày sự kiện MARKETING/ANALYTICS, dữ liệu ConsentEvent/hash vẫn giữ nguyên. Asset đối tác lưu local, không tích hợp API.

## 20/11/2026 — Tách cổng Customer và Internal

- Giữ một Django User/session/backend; không tạo auth system thứ hai.
- Gateway role precedence: ADMIN > STAFF > CUSTOMER; superuser thuộc Internal/ADMIN.
- `/accounts/login/` chỉ cho Customer; `/internal/login/` chỉ cho Staff/Admin.
- Internal session được xem website công khai nhưng bị chặn server-side khỏi cart/checkout/customer account.
