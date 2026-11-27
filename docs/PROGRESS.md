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

## 13/11/2026 — Responsive 9/9 PASS; chưa mở localhost

Theo phê duyệt7màn hình còn lại: eager-load voucher và render trongRAM, không sửa nghiệp vụ hoặc mởserver8000. Tổng9/9PASS gồm2HTTPtrước+7render/DOM mới; không phải9lượtHTTP mới. Preview45bảng/44sequence/schema/data vàQA fingerprint trước/sau khớp;0DML,không sửa9đơnLOCALSMOKEC. Runtimefile nguyênbyte/featureOFF/serverSTOPPED. Khôngrerun51integration/migrate/restore/email/Git. [Báo cáo cập nhật](LOCAL_FEATURE_CUTOVER_REVIEW_2026-11-13.md). Chờ duyệt mở phiên nghiệm thu localhost riêng.

## 13/11/2026 — C chưa hoàn tất: responsive helper bị chặn

Preview5432 đã migrate PASS (0,300s, rerun0,038s),45bảng/44sequence/160indexes/209constraints/64FK; original rows giữ nguyên. QA chuẩn bị370/370 PASS; integrationC51PASS gồm4races sau retry được duyệt. Responsive mới2/9PASS rồi helper lazyFK trong Playwright bịSynchronousOnlyOperation. Đã dừng8000/25251, featureOFF/gatefailed; chưa mở lại hoặc restore.9đơnLOCALSMOKEC giữ nguyên,0malformed, kho/giá/BOM/policies/time cũ không đổi. [Báo cáo và retry đề xuất](LOCAL_FEATURE_CUTOVER_REVIEW_2026-11-13.md). Không coiCcomplete hoặc cóURLnghiệmthu hoạt động.

## 13/11/2026 — Giai đoạn B PASS, chưa cutover

Migration thực tế trên restore-copy: 38→45 bảng, 37→44 sequence, 131→160 indexes, 168→209 constraints, 48→64 FK; pending0. Migrate0,264s, rerun0,036s không đổi. Original rows giữ nguyên; metadata thêm2/7/28 theo dự kiến. Integration46/46 PASS (gồm4race), Chromium9/9 tại375/768/1440 PASS. Failure catalog-committed/commerce-atomicrollback PASS; restore sang target mới0,19s, recovery verification28,775s. Source/static250files backup mã hóa, media rỗng, credentials không copy/đổi. Preview38bảng/37sequence không đổi, featureOFF,8000dừng. Đã thu hồi CONNECT tạm trên3copy. [Biên bản](CUTOVER_STAGE_B_REVIEW_2026-11-13.md). Chưa thực hiệnC hoặcGitHub.

## 13/11/2026 — Cutover Giai đoạn A hoàn tất, chưa migration/activation

Backup mã hóa **database preview hiện hành**5432 và restore thực tế vào DB mới trên QA55441 **PASS**:38bảng/37sequence/168constraints(48FK), data hashes/migrationstate/indexes/cộtlogic khớp. Archive/key riêng ngoài repo0700/0600, Encrypt-then-MAC; không plaintextdumpdisk, không tạo/đổi credentials. Copy chứa dữ liệu hiện hành chỉpostgresQA truy cập, QAroles bị từchốiCONNECT. Preview38/38hash+flags+migrationplan không đổi, featureOFF/8000dừng. Không migration ngay cả trên restorecopy; source221inputs mốc360PASS không đổi. [Kết quả, giới hạn và phê duyệt tiếp](FEATURE_INTEGRATION_CUTOVER_PLAN_2026-11-13.md). Rehearsalphysicalordinalgap đã đối chiếu, không sửa DB. Chưa cutover/Git/SMTPthật.

## 13/11/2026 — Tích hợp Accounts/SMTP/Reset/Voucher, chưa cutover

Phạm vi mới thay FINAL SYSTEM COMPLETION: không đóng dự án hoặc sửa policies/ngày giờ. Bổ sung Admin voucher edit/pause/resume/filter/history, bảo toàn snapshot/audience; chặn pending/nativeStaff nhận/dùngV2. **360/360 full PostgreSQL+Chromium PASS**,0FAIL/SKIP,386.792s,221sourceinputs không đổi;1.552Djangoconnections đúngQA55441. Targeted108PASS gồm5discoveryjourneys lặp đã bỏ trướcfull. Browser voucher12renders+3AdminHTTPwidthsPASS. Preview38/38hash/flags/pending không đổi,0server8000/8001; featureOFF. Gmail1mail thật đã được chủ dự án xác nhận nhận; không gửi thêm. [Review](NAU_COFFEE_V3_FEATURE_INTEGRATION_REVIEW.md), [cutover chờ duyệt](FEATURE_INTEGRATION_CUTOVER_PLAN_2026-11-13.md). Không stage/commit/push/merge/deploy.

> Lưu phiên 12/11/2026 21:01:34 (giờ Việt Nam): [SESSION_HANDOFF_SAVED_2026-11-12_210134.md](SESSION_HANDOFF_SAVED_2026-11-12_210134.md). Không chạy lại test;231sourceinputs khớp mốc354PASS,diffcheckPASS; chỉ cập nhật tài liệu, không DB/server/Gitrefs.

## 12/11/2026 — Customer quên/đặt lại mật khẩu đã nghiệm thu QA

**354/354 fullPASS,0FAIL/SKIP**,453.217s; **24/24 targetedPASS**,2PG races,12flow screens+3emailrender375/768/1440PASS. Token/form/hash chuẩnDjango,TTL1h, chỉactive verified unique-emailCustomer, chặnStaff/Admin/unactivated, generic response/rate/CSRF/fragment/no-auto-login/multi-tab binding.231sourceinputs vàcredentials khôngđổi saufull. Lượt resume đầuFAIL dofixtureQAsót saugiánđoạn; normalteardown đãdọn, preflightreadonly0bản ghi và rerunkhôngđổi sourcePASS. QAguard/models/migrations/businesssource giữnguyên,45bảng/0pending; khôngpreview/devSQL/start8000/featureON/Git. SMTPsandboxPASS, liveSMTPNOTRUN. [Báo cáo và file thay đổi](PASSWORD_RESET_REVIEW_2026-11-12.md).

## Gmail SMTP12/11 — source mới330/330PASS, liveBLOCKED

Đọc checkpoint120432, cấu hình Gmail smtp.gmail.com:587/TLS/noSSL/15s/senderchínhthức, optional privateprofile0600/ignoredchưaautonạp. Email activation/Staffinvitation multipartHTML+plain, trustedHTTPSgate; template6/6renderPASS. Targeted58/58PASS, fullPostgreSQL+Chromium **330/330PASS,0SKIP**,375.276s,220sourceinputs khôngđổi; SMTPloopback/mock/racegửi1thưPASS. Không Gmailconnection hoặc mailthật, AppPassword/origin/ngườinhận/phêduyệt cònthiếu: **LIVESMTPBLOCKED**.8000/8001đãdừngđầuphiên, không start/restart; chỉ QAcontainerkhởiđộng, không migratepreview/dev hoặc sửa guard/Git. [Báocáo](GMAIL_SMTP_REVIEW_2026-11-12.md), [ownersteps](GMAIL_SMTP_SETUP_2026-11-12.md).

> Lưu phiên 12/11/2026 12:04:32 (giờ Việt Nam): [SESSION_HANDOFF_SAVED_2026-11-12_120432.md](SESSION_HANDOFF_SAVED_2026-11-12_120432.md). Không chạy lại test;214source inputs khớp mốc320PASS, diff checkPASS; chỉ cập nhật tài liệu, không database/server/Git refs.

## Chốt nghiệm thu12/11 — source cuối320/320PASS, chưa kích hoạt

FullPostgreSQL+Chromium **320/320PASS,0FAIL/SKIP,422.468s**; targeted68/68PASS;214sourceinputs không đổi sau full. Ba voucher racePASS, E2E HTTP3widthsPASS, duplicate blur giữ tổng/submitPASS. QA encrypted backup/restore45bảng+rows+sequencePASS; pg_dump/restore17.9. Người dùng xác nhận login10:54:21 và thêm món11:49:45: hoạt động preview hợp lệ; cuối lượt36/38 bảng giống đầu,33/38 giống mốc gốc, mọi bảng kinh doanh quan trọng giữhash.1464kết nối Django regression đềuQA55441,0preview; network-guard E2E1583requests testport,0attempt8000/8001. SMTPthậtBLOCKED cấu hình; migration/backup dữ liệu hiện hành/feature/GitHub chưa được duyệt. [Chi tiết và phê duyệt còn cần](VOUCHERS_PHASE2_ACCEPTANCE_2026-11-12.md). Các mốc “chưa xác minh actor” phía dưới là lịch sử trước xác nhận của người dùng.

## 12/11/2026 — Nghiệm thu Đợt 2, chuẩn bị activation nhưng chưa bật

Điều tra preview read-only:4bảng khác mốc gốc phù hợp login10:54:21, chưa đủ audit quy nguồn;38/38khớp mốc cuối trước nghiệm thu, không drift thêm. Browser HTTP QA mới đi đủ signup/activation/login/voucher/Staff consent/guest/APP ở375/768/1440; targeted68/68PASS. Phát hiện và sửa UI input/change lặp gây nuốt click và ghi đè tổng đã giảm; chỉ sửa voucher-live.js, backend/guard/model/migration giữ nguyên. QA backup mã hóa/restore45bảng+sequence PASS vào DB mới; SMTP thật BLOCKED thiếu cấu hình. Full regression sau UIcuối đang chạy; chưa bật feature/migrate preview/dev/stage/commit/push/merge/deploy. [Báo cáo nghiệm thu và phê duyệt cần có](VOUCHERS_PHASE2_ACCEPTANCE_2026-11-12.md).

> Cập nhật bảo toàn preview cuối Đợt 2: **34/38 bảng không đổi**, 4 bảng auth_user/cart/session/submissionlimit có drift phù hợp một lượt login lúc 10:54:21 giờ Việt Nam, chưa xác định actor. Không xác nhận 38/38; order/payment/giá/BOM/stock giữ fingerprint. Chi tiết trong review Đợt 2; không tự sửa dữ liệu.

## 12/11/2026 — Đợt 2 voucher theo campaign, đang nghiệm thu kỹ thuật

Đã chốt giữ nguyên campaign/redemption cũ, thêm policy có cấu trúc và quota PRIVATE/Admin audit. WEB/COUNTER chọn danh sách, tự tính giá, APP từ chối backend; quote không tiêu lượt/consent, tạo đơn mới tiêu lượt, hủy V2 không hoàn lượt. Migration chỉ QA accounts 55441, 45 bảng/0 pending; targeted **20/20 PASS**, ba race và 9/9 browser page-breakpoint PASS. Full PostgreSQL + browser **319/319 PASS, 0 FAIL/SKIP**, 212 đầu vào source không đổi. Preview 8000 feature OFF, không restart/migrate; không commit/push/merge/deploy. Kế hoạch push checkpoint Đợt 1 mới đã hủy. [Review](VOUCHERS_PHASE2_REVIEW_2026-11-12.md), [SMTP/backup chuẩn bị](SMTP_BACKUP_READINESS_2026-11-12.md).

## 12/11/2026 — Phương án A hoàn tất, PostgreSQL Đợt 1 PASS

Đã tạo role/DB QA accounts mới riêng ở 55441, credentials 0600/Git-ignore; QA cũ được fingerprint bảo toàn. Áp dụng 29 migrations chỉ QA mới, gồm catalog.0005; 41 bảng, 0 pending. Targeted **46/46 PASS**, hai race đều PASS; full PostgreSQL + browser **299/299 PASS, 0 SKIP**, 215 source inputs không đổi. Guard allowlist chặt, preview/dev không migrate/test ghi. 8000 đầu phiên dừng, đã mở lại bằng serve; feature OFF, không 8001. Không commit/push/deploy. [Báo cáo và các phê duyệt còn lại](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md).

## Checkpoint 12/11/2026 02:28 — giờ Việt Nam

Đã lưu [SESSION_HANDOFF_CUSTOMER_ACCOUNTS_2026-11-12_022847.md](SESSION_HANDOFF_CUSTOMER_ACCOUNTS_2026-11-12_022847.md). Giữ trạng thái 122 PASS/2 SKIP trong 124 tests, feature OFF, QA TCP credentials BLOCKED; A/B chưa được duyệt. Lượt lưu chỉ cập nhật tài liệu, không chạy lại test, không đổi code/database/Git refs/server.

## 12/11/2026 — Kiểm chứng kỹ thuật tài khoản, feature tiếp tục OFF

Rà đủ manifest 35 file, sửa lỗi selection POS chưa gắn session/purpose; test tái hiện 3 FAIL trước sửa đã PASS sau sửa. Lượt cuối **124 tests: 122 PASS, 2 SKIP** (race PostgreSQL). SMTP loopback sandbox **2/2 PASS**, responsive **27/27 PASS**; không mail khách thật. QA container/volume/cổng riêng đã xác minh nhưng thiếu credentials SQL, nên PostgreSQL migration/integration vẫn **BLOCKED**. Không sửa guard hoặc apply catalog.0005 lên DB hiện hành, không restart 8000/commit/push/deploy. [Báo cáo cập nhật và kế hoạch backup/rollback](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md). Cập nhật QA: Unix socket local-trust đã xác minh role hạn chế và schema catalog.0004/38 bảng; TCP password chỉ còn verifier SCRAM. Đã trình phương án A role+DB QA mới với allowlist guard, hoặc B rotate password QA cũ; cả hai chưa thực hiện.

## 12/11/2026 — Tài khoản Customer và nhận diện COUNTER, đợt 1

Đã viết CustomerProfile, đăng ký sáu trường, email activation một lần, Staff lookup/create/resend và xác nhận COUNTER bằng mã đồng ý do khách cấp. **Feature OFF mặc định**, migration 0005 chỉ tạo file, chưa áp dụng preview/dev. Lượt cuối **116 tests: 115 PASS, 1 SKIP** (PostgreSQL race); Chromium **27/27** trang-breakpoint đạt. Giữ nguyên 8000, không commit/push/deploy. Email thật/QA PostgreSQL chưa sẵn sàng để nghiệm thu. [Báo cáo, file và kế hoạch duyệt](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md). Preview cuối phiên: **38/38 fingerprint không đổi**, 5/5 HTTP GET PASS, PID 8000 giữ nguyên; migration catalog.0005 vẫn chưa áp dụng.

## 11/11/2026 — Hai P0 sau audit

Đã sửa bộ lọc giá Unicode và bổ sung fail-closed cho test settings/runner. Targeted **22/22 PASS** trên SQLite bộ nhớ, HTTP **9/9 PASS**, fingerprint preview **38/38 không đổi**, Django check/migration drift/diff check PASS. Full PostgreSQL regression **BLOCKED** thiếu credentials QA độc lập; không dùng lại 235/235 làm chứng nhận source mới. Không sửa P1, dữ liệu hoặc Git commit. Chi tiết: [báo cáo P0](P0_PRICE_FILTER_TEST_ISOLATION_FIX_2026-11-11.md).

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

## 2026-11-11_083400 UTC — Lưu phiên làm việc

- Checkpoint ghi trên đĩa, localhost duy nhất8000, source/Git giữ nguyên; không truy cập database hoặc commit/push.
- [Handoff mới nhất](SESSION_HANDOFF_MAIN_2026-11-11_083400.md).

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

# Tiến độ Nâu Coffee V3

## Checkpoint tiếp tục 06/11/2026 — regression và browser PASS

Đã sửa hai kỳ vọng UI được duyệt, giữ templates hiện tại và mọi local patch. Targeted2/2PASS; backend149/149PASS; discovery toàn bộ164/164PASS (149backend+15browser),173.389s,0FAIL/ERROR/SKIP. Browser đủ8detail×375/768/1440, giá/caption/SKU đúng; queue/Kanban/POS/Admin và customer journeys PASS theo suite. AST92/check/drift/diff-checkPASS; tất cả writes chỉ test DB verified. Giữ giới hạn browser E2E giao hàng mới và tái tạo freshclone; không importer/dev writes/deploy. Chuẩn bị commit/push được chủ dự án cho phép; kết quả Git xác nhận riêng sau lệnh thực tế. [Checkpoint, command và36files](CHECKPOINT_2026-11-06.md).

## Checkpoint 06/11/2026 — chưa commit/push do regression FAIL

Đúng nhánh feature/cafe-premium-reference-20261028, HEAD73103e7 và remote dauiudau11-cpu/NauCoffee-V3. Đã rà soát diff/untracked, giữ mọi UI/giao hàng patch; lưu nguyên byte hai script menu/BOM ngoài repo vào scripts/, chưa chạy importer. DBtest identity/role/PostgreSQL17/no CONNECT dev PASS. Targeted menu+delivery30/30PASS; full backend147PASS/2FAIL trong149tests (hai assertion copy UI). Check/drift/diff-check PASS; browser mới NOT RUN. Theo yêu cầu dừng trước stage/commit/push; không sửa tests để lấy PASS, không ghi dev, không đụng backups. Xem [checkpoint và giới hạn tái tạo dữ liệu](CHECKPOINT_2026-11-06.md).

## Checkpoint Git trước khi tắt máy —31/10/2026

Chủ dự án đã cho phép commit/push đúng nhánh feature/cafe-premium-reference-20261028 sau rà soát. [Bàn giao hiện tại](HANDOFF_2026-10-31.md): code menu mới và báo cáo150/150+17/17PASS; dev vẫn menu cũ, chưa backup/migrate/cutover. Còn chờ drift giỏCF04-M, BOM/tồn đầu kỳ và kế hoạch backup/cutover/rollback. CF01 APP37.000đ. Kết quả Git/push cụ thể được báo sau lệnh thực tế, không coi chuẩn bị là đã push.

## Diễn tập menu chuẩn — code/test đã chuẩn bị, dev chưa áp

- Thêm migration additive FIXED+StandardCost, command rehearsal chỉ test DB, stagedflag mặc địnhFalse. Staging giữ13 SKU cũ; cutover/activation tách riêng, activation thiếu BOM/kho thì rollback. Không bypass inventory hoặc tạo BOM/tồn dev.
- Backend guard WEBpickup, cặpgiá WEB=COUNTER, APP riêng, cost Admin-only, giữ legacySKU/order/snapshot/cart. Menu paused vẫn xem8 món/giá nhưng không thêm/đặt; đủ BOM/kho mới bật8 SKU.
- Full suite150/150PASS,148.863s; lượt cuối17/17PASS,28.505s sau sửa nhãn/CTA/bảng.36ảnh mới375/768/1440; không overflow, WEB3CF02=96.000, APP CF01=37.000 bằng fixturetest. Check/drift/diff-check PASS.
- **Preflight dev comparison FAIL vì CartItem1→0** so với audit trước, chưa biết nguyên nhân. Dev vẫn8Product/13SKU/39giá/4Cart/1Order/1OrderItem/1Payment, migration0004 absent/flagFalse. Không tự khôi phục dòng giỏ. Test giữ CF04-M chỉ chứng minh trên fixture, không khẳng định trạng thái dev.
- Không backup/migrate/apply dev/restartserver/commit/push/deploy. [Báo cáo code, trạng thái website, bằng chứng và các bước cần duyệt](STANDARD_MENU_REHEARSAL_2026-10-31.md).

## Chuẩn bị rollout menu mới —31/10/2026

- Giữ nhánh feature/cafe-premium-reference-20261028/HEAD6a10161 và toàn bộ local patch. Chỉ khảo sát read-only, cập nhật tài liệu nguồn chuẩn, không sửa code nghiệp vụ hoặc ghi dev.
- Đã chốt WEB=COUNTER, WEBpickup, APP giá sàn mới. DB hiện8món/13SKU/39giá,1dònggiỏCF04-M,1đơn cũ; chưa có BOM/stock/options/voucher. Đề xuất8SKU chuẩn mới, giữ13SKU cũ/ngừng bán mới, không tự đổi dòng giỏ; cost riêng chỉ quản trị.
- [Quyết định mới](APPROVED_MENU_PRICING_2026-10-31.md), [đối chiếu và phương án cần duyệt](MENU_ROLLOUT_PLAN_2026-10-31.md). Chưa backup/migrate/apply; giá hiển thị website vẫn dữ liệu cũ. Test giá mới NOT RUN. Thiếu BOM/tồn kho là blocker nhận đơn dev, không bypass validation.

## Nội dung và typography — 31/10/2026

- Giữ nhánh feature/cafe-premium-reference-20261028, HEAD6a10161 và mọi patch trước phiên. Bỏ dòng footer được yêu cầu, giảm lời nội bộ Customer/Staff/Admin; giữ cảnh báo thanh toán/giao nhận mô phỏng và giá website chưa chốt.
- Thêm typography chung có fallback tiếng Việt, footer14px/1.65, khoảng cách từ bình thường, input mobile16px; không thay dữ liệu/giá/SKU/đơn hàng hoặc workflow.
- Regression cuối **133/133PASS,0FAIL/ERROR/SKIP,120.251s**, check/diff-check PASS;93ảnh sau ở375/768/1440,0overflow;185links200; localhost smoke9/9PASS. Lượt đầu132PASS/1ERROR do selector nhãn cũ, đã sửa và chạy lại toàn bộ.
- Server localhost:8000 đã restart đúng process. Không commit/push/deploy. Xem [báo cáo và ảnh Before/After](COPY_SPACING_REVIEW_2026-10-31.md), gồm danh sách file và giới hạn; nội dung đã lưu trong DB được giữ nguyên.

## Tiếp tục sau mở máy — căn trang chủ theo ảnh, 30/10/2026

- Đầu phiên xác minh lại nhánh `feature/cafe-premium-reference-20261028`, HEAD `6a10161`, giữ mọi local patch. Các lượt bị ngắt trước mới đọc/xem ảnh, chưa căn lại trang chủ; không coi báo cáo cũ là kết quả mới.
- PostgreSQL cũ đang dừng,8000 trống sau kiểm tra ngoài sandbox. Bật lại đúng container sau phê duyệt, verify PostgreSQL 17/role/no CONNECT chéo PASS; mở Django loopback. Không recreate, seed, migrate hoặc reset dev.
- Mở trực tiếp ảnh Drive `01_trang_chu.png`, chụp Before localhost ở1448×1086,768×1024,375×812. Trước sửa: hero420px,4 cột/8 card, trang2432px ở desktop.
- Đợt này chỉ sửa trang chủ: thêm page_styles block vào base, CSS Home riêng, compact card component và điều chỉnh home template. Hero full-width282px tại y74,6 card/6 cột desktop,3 cột tablet,2 cột mobile; thu gọn category/banner/review/footer. Menu vẫn giữ đủ8 món, giá và SKU từ backend.
- After thực: desktop1168px thay2432px, tablet1522px thay3251px, mobile2101px thay3609px. Cả3 width không overflow. Đã xem ảnh After và chỉnh vị trí ly để không lấn chữ tablet, giữ ly hiện trên mobile.
- Full regression thực mới **133/133 PASS,0 FAIL/ERROR/SKIP,120.065s** trên DB test đãverified.93responsive regression captures và185links HTTP 200; check/diff-check PASS.
- Server --noreload giữ template cũ ở lượt chụp thử; đã restart đúng process của phiên này, chụp lại xác nhận6 card/số đo mới. Website http://localhost:8000/ đang chạy.
- [Báo cáo trực quan và ảnh](HOME_VISUAL_REVIEW_2026-10-30.md). Chưa khớp hoàn toàn: ảnh nền sạch/icon/font, header search, banner không giả voucher, review trống và footer cao hơn. Không copy dữ liệu concept. Bước tiếp theo: Menu theo02_menu, tiếp tục trình tự Customer khi được tiếp tục; không có commit/push/merge/deploy.


## Nguồn Drive ưu tiên — 30/10/2026

- Giữ nhánh `feature/cafe-premium-reference-20261028`, HEAD `6a10161` và mọi local diff đầu phiên. Bộ Drive mới được chủ dự án chỉ định thay thế bộ21 ảnh làm nguồn giao diện ưu tiên.
- Connector list đủ31 ảnh:10 Customer/5 Staff/16 Admin. Đã tải bản gốc, xác minh ảnh/hash và lưu riêng tại `/home/thientran/naucoffee-ui-reference-drive-20261030` sau phê duyệt filesystem; không ghi đè Downloads/project.15 ảnh Customer/Staff trùng byte với bộ đã xem;16 Admin mới đã xem trực tiếp, gồm6 trang cấu hình. Signed download links chỉ dùng cục bộ, không vào Git/report.
- Giai đoạn Customer: CSS Drive riêng giữ WIP cũ; Home/Menu/Product/Cart/Checkout/Login đồng bộ phong cách; Product gallery dùng ảnh upload thật và related products từ backend; Orders search/status/pagination; Contact/Policy hero/cards/tabs nhưng không copy địa chỉ/giá/policy concept. Backend sau Customer114/114 PASS10.336s.
- Giai đoạn Staff: Kanban3 cột/FIFO/count thực và nút chuyển trạng thái qua service cũ; POS thẻ SKU chọn vào formset/options/qty và preview theo channel; queue lọc mã/tên/channel/fulfillment/status. Giữ stock/payment/idempotency/RBAC. Không có timer/drag-drop/print/draft giả.
- Giai đoạn Admin: trang quản lý product/category/voucher/customer/staff có search/state/pagination, bảng SKU/volume/COUNTER/APP đọc DB và native CRUD links.6 trang config thật, GET-only, ADMIN-only: store/appearance/payment/delivery/notifications/security. Không có Save/toggle/backup giả cho backend chưa tồn tại. Native product edit vẫn là Django Admin, chưa custom hoàn toàn theo ảnh.
- Lượt full đầu132 PASS/1 FAIL do assertion config đếm nhầm header search; đã sửa selector giới hạn workspace. **Full cuối133/133 PASS,128.701s,0 FAIL/ERROR/SKIP** (119 backend+14 browser). Bổ sung assertion Kanban CONFIRMED→PREPARING→READY và giữ UNPAID; chạy lại7 tests liên quan PASS52.771s, không cộng thành140.
- **93 captures (31 screens×375/768/1440),0 overflow,185 internal links HTTP 200**. Giá trong ảnh QA là fixture legacy, không phải WEB/COUNTER/APP mới được chốt. [Đối chiếu31 ảnh](DRIVE_UI_REVIEW_2026-10-30.md), [bằng chứng](qa/2026-10-30-drive/manifest.json).
- Dev/test identity/isolation verify PASS trước test. Không seed/bootstrap/migrate/reset dev, không sửa giá/SKU/orders. Restart đúng Django server đã xác minh PID/cwd để nạp routes; URL http://localhost:8000/. Không commit/push/merge/deploy.
- Còn thiếu: khớp pixel/tỷ lệ toàn bộ mẫu, forms CRUD tùy chỉnh, chart/report phân vùng, cost schema/menu rollout, banner/theme editor, notification email/SMS, expiry batch, auto-backup/restore, physical-device/production QA. Không claim31/31 UI DONE hoặc12/12productionPASS.


## Phiên hiện tại — 30/10/2026: khởi động local và đối chiếu21 ảnh

- Xác minh thực vẫn nhánh `feature/cafe-premium-reference-20261028`, HEAD `6a101619ea484cd2e2c9dc3546d6280d0ef6cc24`. Đầu phiên15 tracked files modified + CSS/9 WebP/QA untracked; giữ nguyên tất cả. Mốc127PASS28/10 là lịch sử, đã chạy lại kiểm thử trong phiên này.
- Docker sandbox bị permission denied; kiểm tra ngoài sandbox có phê duyệt xác nhận `pg_lab_postgres`/pgAdmin đã Exited255, cổng8000/5432 trống. Được duyệt bật lại duy nhất container PostgreSQL cũ bằng `docker start pg_lab_postgres`; không recreate/seed/reset/migrate dev. PgAdmin giữ dừng.
- Read-only verify dev/test PASS PostgreSQL17 và role hạn chế/no CONNECT chéo; Django dev identity `nau_coffee_dev/nau_coffee_app` PASS. Khởi động `.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload`; PID3912 được xác minh, không dừng tiến trình lạ. URL Windows http://localhost:8000/ hoặc http://127.0.0.1:8000/. HTTP smoke9/9PASS.
- Tìm được bộ gốc trong Windows Downloads, hai ZIP giống SHA256. Đủ21/21 ảnh đọc được:10 Customer (9 màn hình+1 mẫu),5 Staff,6 Admin (nhiều collage). Đã xem từng ảnh và đối chiếu source/QA, xem [REFERENCE_REVIEW_2026-10-30.md](REFERENCE_REVIEW_2026-10-30.md), [kiểm kê](qa/2026-10-30/references.json). Các ghi chú thiếu bộ ảnh ở28/10 đã được giải quyết.
- Tiếp tục UI mua hàng: Cart hero/cream summary, Checkout thumbnails từ backend, Login ảnh minh họa/olive submit, sửa tương phản chữ trên nền tối. Admin sidebar thêm lối vào Category/Review/Feedback/User CRUD đã tồn tại, giữ backend RBAC. Không đưa dữ liệu concept/giá mới hoặc chức năng OAuth/timer/shift giả vào app.
- Backend114/114 PASS, 10.189s; browser13/13 PASS, 92.812s,0FAIL/ERROR/SKIP sau khôi phục runtime, tổng127distinct tests trong hai lượt. Capture lại sau sửa contrast ghi ở TEST_REPORT.51 screens / 0 overflow,151 internal links HTTP 200. Check/drift/diff-check PASS.
- Chưa hoàn thiện toàn bộ thiết kế: Product gallery, account accordion/filter, Staff Kanban/filter theo nhiều chiều, POS card-grid/print/draft, Admin custom CRUD/graphs và cost schema.21 ảnh đủ không đồng nghĩa21 màn hình nghiệm thuPASS. Giá WEB/SKU rollout/chính sách/địa chỉ/production vẫn cần xác nhận. Không commit/push/merge/deploy.


## Phiên hiện tại — 28/10/2026: nghiệm thu patch Café Premium

- Workspace thực tế: `feature/cafe-premium-reference-20261028`, HEAD `6a101619ea484cd2e2c9dc3546d6280d0ef6cc24`; giữ nguyên nhánh, 7 file tracked đã sửa và 9 WebP + CSS untracked có từ đầu phiên. Không checkout/reset/commit/push/merge/deploy. Các checkpoint WIP bên dưới là lịch sử.
- Đã đọc AGENTS, MASTER_SPEC, APPROVED_MENU_UI và TEST_REPORT; đối chiếu thêm APPROVED_REFERENCE_IMPLEMENTATION. Bộ 21 ảnh gốc chưa tìm thấy trong workspace; đã yêu cầu đường dẫn, chưa nghiệm thu giống từng mockup.
- Giai đoạn 1: sửa test menu rỗng theo heading thật, giữ kiểm tra count=0/list rỗng/không có card và link xóa lọc. Giữ patch hero/ảnh minh họa/giá backend hiện có. Sửa header mobile, danh mục không co chữ, CTA44px, giỏ SVG và khôi phục POST logout desktop.
- Giai đoạn 2: sửa nhãn điều hướng Staff/Admin và trạng thái active Báo cáo; POS/dashboard tiếp tục dùng backend hiện hữu. Browser exercise mua hàng→mock retry→Staff lifecycle→review moderation, cart/logout/refund, POS APP/COUNTER, kho, reports và Admin Category CRUD chỉ fixture test.
- Database cách ly xác minh thực: `nau_coffee_test` / `nau_coffee_test_runner`, NOSUPERUSER/NOCREATEDB/NOCREATEROLE, không CONNECT dev. Không ghi/migrate/seed/reset dev. Fixtures seed và TransactionTestCase cleanup chỉ diễn ra trong DB test.
- Foundation/safety23/23 PASS; full regression sau fix127/127 PASS,109.536s,0 FAIL/ERROR/SKIP. Lượt đầu122 PASS/2 FAIL/3 ERROR đã sửa; **lượt cuối sau icon/CTA127/127 PASS,103.585s,0 FAIL/ERROR/SKIP**.
- Ảnh QA mới: `docs/qa/2026-10-28-premium-regression/after`; không ghi đè bộ Before/After cũ.51 screens × width/role,0 overflow;151 links HTTP200 ở lượt127PASS. System check và migration drift PASS.
- Chưa nghiệm thu:21 mockups gốc, WEB prices/SKU rollout, ảnh sản phẩm thật/license/media bền, Maps online, thiết bị vật lý và public production. Không đánh dấu12/12 DONE. Không có thay đổi dữ liệu kinh doanh.


## Checkpoint mới nhất — 28/10/2026: hoàn thiện WIP local

Chủ dự án đã phê duyệt tạo checkpoint với message `Refine WIP customer and operations UI with responsive QA` và push riêng origin/wip/ui-redesign-local-20261027. Kết quả test là local; không merge main hoặc public deploy. Các ghi chú chưa commit/push bên dưới mô tả trạng thái trước phê duyệt.

- Giữ nhánh `wip/ui-redesign-local-20261027`, bắt đầu clean `5d233a0`/baseline `16ea806`; không thay nhánh, commit/push/merge/deploy. Đã đọc hai đặc tả menu/master và tài liệu đối chiếu/acceptance; Issue #2/#3 hiện đã đọc được qua connector.
- Đánh giá đủ 29 file WIP: [UI_REVIEW_2026-10-28.md](UI_REVIEW_2026-10-28.md). Giữ hero, illustration, màu, cấu trúc và các phần hoàn thiện; chỉ sửa thiếu sót.
- Giai đoạn 1: Home featured giá backend; menu giữ filter/category query; card padding/CTA 44px; favicon; Product options/qty/server-data price preview; cart unit/line quote; checkout form grid/errors; profile design; header POST logout/mobile. Không đổi giá WEB, SKU hoặc dữ liệu.
- Giai đoạn 2: POS một dòng + thêm/bớt/reindex, options lọc theo món, preview COUNTER/APP từ DB; không JS giữ formset fallback. Native Admin 768px không overflow và sidebar rõ hơn; queue/inventory/reports/RBAC giữ nguyên.
- PostgreSQL local backend suite 114/114 PASS; browser suite mở rộng gồm capture, link audit, Customer/Staff journeys và category CRUD chỉ test fixture. Suite cuối **127/127 PASS (114 backend + 13 browser), 93.878s**, 0 FAIL/ERROR/SKIP. Xem TEST_REPORT cho lệnh/bằng chứng.
- 102 PNG before/after (51 mỗi bản, 17 screens × 375/768/1440). Before từ snapshot gốc 5d233a0; after 0 overflow. 152 internal links trả HTTP 200. Không dùng screenshot/session/dữ liệu riêng dev để tạo artifacts.
- Chưa đủ nghiệm thu toàn bộ: ảnh thật/license/media production, giá WEB + rollout 8 định lượng chuẩn/13 SKU cũ, Maps online/địa chỉ/policies, thiết bị thật và production vẫn mở. Không đánh dấu 12/12 DONE.
- Đề xuất checkpoint sau kiểm tra cuối: `Refine WIP customer and operations UI with responsive QA`; chưa tự tạo commit theo chỉ dẫn chủ dự án.
- Đã khởi động lại đúng runserver local vì PID cũ dùng --noreload. http://127.0.0.1:8000/ sau restart HTTP200, kiểm tra HTML xác nhận favicon và featured-price projection mới đã nạp. Chỉ GET trang chủ; không submit hoặc ghi dữ liệu dev. Server mới vẫn --noreload, sửa Python lần sau cần restart nhẹ.

## UI/UX và menu đã chốt — 27/10/2026

- GitHub Draft PR#1 còn mở theo chủ dự án; baseline473d23b đã đạt111/111 CI theo xác nhận của chủ dự án. Đã fetch ba commit main939e642/11ee3b1/737efdc và merge vào feature/sprint-3-4 bằng0bf94b7, giữ nguyên lịch sử/main.
- Đã đọc AGENTS, toàn MASTER_SPEC, APPROVED_MENU_UI và ACCEPTANCE_MATRIX. Issue#2 API Forbidden, thực thi các ưu tiên do chủ dự án nêu; chưa claim đã đọc/hoàn tất toàn Issue.
- Đã đối chiếu8 món với13 SKU/350–500ml/giá cũ, schema chưa có cost; xem MENU_RECONCILIATION_2026-10-27.md. Không cập nhật DB/seed/menu, không gán COUNTER/APP mới cho WEB. Khung Customer và form Staff nêu rõ giá/dung tích hiện tại chưa theo menu mới.
- Đã sửa empty checkout, thẻ kho mobile, form APP/COUNTER, Maps fallback luôn sẵn, header/mobile navigation, khung điều hành espresso/olive và VND grouping. Server pricing, RBAC, stock, BOM snapshots, payments/order history giữ nguyên.
- Full cloud120/120 PASS (111 backend+9 browser),118.568s,4 PostgreSQL races; check/drift PASS. 30 ảnh UI mới ở375/768/1440 và manifest/raw log tại docs/qa/2026-10-27. Chi tiết các lượt sửa test trong TEST_REPORT; không tự ghi GitHub CI mới PASS khi API bị chặn.
- Cloud mới không còn development DB/secrets phiên cũ. Chỉ tạo PostgreSQL17 test-only, không dev DB, secrets mới0600; không thay đổi dữ liệu laptop/DB cũ. Đã lưu draft install/start cho môi trường kiểm thử; draft cần review/save/publish để có hiệu lực cho phiên sau, chưa xác nhận fresh-task restoration.
- Chờ nghiệm thu: giá WEB; mapping/phiên bản SKU chuẩn360/500/700ml và size/topping; cost schema/BOM; ảnh8 món/license và bộ mockup Customer/Staff/Admin25/10; nội dung Issue#2 đầy đủ. Chưa merge main, chưa deploy hoặc phát sinh dịch vụ trả phí.

## Sửa CI Draft PR #1 — 21/10/2026

GH007 đã xử lý bằng noreply theo phê duyệt; toàn bộ code checkpoint73c50c5 đã push với tree giữ nguyên thành5b4b081 trên feature/sprint-3-4. Các thông tin chưa push/GH007 ở mục lịch sử bên dưới không còn là trạng thái hiện tại. Main không đổi.

Sửa responsive browser test để kích hoạt native lazy images bằng scroll và bounded wait, giữ assertion ảnh; thêm regression xác nhận ảnh404 thật vẫn fail. Không đổi code ứng dụng hoặc database schema. Cloud PASS111/111 (106 backend+5 browser),40.978s, check/drift PASS; chi tiết và giới hạn tái hiện768px trong TEST_REPORT.md. GitHub run39560813302 FAIL theo log chủ dự án; API Actions Forbidden nên chưa xác nhận kết quả CI mới. Chưa merge/deploy, vẫn chờ nghiệm thu.

## Tiếp tục triển khai — 21/10/2026 (Asia/Ho_Chi_Minh)

Chủ dự án đã quay lại và yêu cầu đánh giá/tiếp tục; checkpoint tạm nghỉ ở dưới là lịch sử. Giữ nguyên commits9174433 vàb7ff758; tiếp tục trên feature/sprint-3-4, không push/merge/deploy. Push trước đó bị GitHub GH007 bảo vệ email; repo Private đã được chủ dự án xác nhận, không tự đổi cấu hình riêng tư hoặc rewrite history.

| Phạm vi | Tiến độ thực tế |
|---|---|
| Sprint1–2 | Catalog/auth/cart/checkout/payment/Staff lifecycle có source và tests; vẫn cần acceptance/public smoke |
| Sprint3 | Support/policies/reviews/Admin và responsive đã code, browser QA mở rộng; ảnh thật/license và Maps online chưa nghiệm thu |
| Sprint4 | Slot, stock/BOM, loyalty/manual/report đã code; **mới thêm kiểm tra kho tại checkout và snapshot BOM**, chưa giữ chỗ nguyên liệu |
| Sprint5–6 | Chưa public deployment, chưa đủ URL/thông tin nhóm để hoàn thiện Word/PPTX/ZIP; docs/runbook/matrix đã có |

Milestone mới: WEB và APP/COUNTER kiểm tra tổng nhu cầu nguyên liệu toàn đơn trước khi tạo Order/Payment; thiếu/BOM lỗi/ingredient inactive thì từ chối và giữ giỏ. OrderItem.recipe_snapshot chốt per-drink quantity dưới dạng Decimal string, gồm SKU recipe và topping. Khi PREPARING dùng bản đã lưu, vẫn kiểm tra stock/active/unit và trừ đúng một lần. Đơn legacy NULL chốt recipe hiện tại ở lần pha chế thành công và ghi audit rõ thời điểm, không bịa công thức lúc đặt. Staff có thể xem recipe snapshot trong queue.

**Lần chạy mới 21/10: 110/110 PASS**, 106 backend +4 Chromium journeys, 4 concurrency cases, 0 FAIL/0 SKIP (38.368s). Browser đã exercise thêm cart update/remove, cancel→Admin mock refund, logout/private-route redirect, thiếu kho giữ cart, custom delivery slot, manual zone verification, delivery completion/COD capture và loyalty không gồm phí ship. Evidence50 PNG/manifest và raw log tại docs/qa/2026-10-21. HTTP smoke sau restart9/9 PASS; Django check/migration drift PASS.

Migration commerce0003 chỉ ADD COLUMN recipe_snapshot jsonb NULL, không xóa/reset/bootstrap/seed dev. Đã giữ backups cũ, tạo archive trước migration và backup sau migration. Read-only fingerprints các bản ghi business/account hiện có (bỏ cột mới) khớp trước/sau; demo8/13/39/3 còn nguyên. Web đã restart với source mới. Kho **không được reserve** khi checkout: tồn có thể thay đổi; Staff vẫn bị chặn khi PREPARING nếu thiếu.


## CHECKPOINT TẠM NGHỈ — 18/10/2026 (Asia/Ho_Chi_Minh)

Chủ dự án chuẩn bị tắt laptop. Dừng phát triển sau khi lưu checkpoint này; đọc [CHECKPOINT.md](CHECKPOINT.md) ở phiên sau. Commit ứng dụng `9174433` còn nguyên, nhánh hiện tại `feature/sprint-3-4`; code/CI/docs/evidence được commit nối tiếp, không rewrite main. **Chưa push, chưa PR, chưa có backup source mới trên GitHub.** Private chưa xác minh vì GitHub API Forbidden.

Baseline 90/90 PASS và browser QA48 ảnh được giữ nguyên. Kiểm thử độc lập mới: 96/96 backend PASS (89 cũ + 7 CI safety), PostgreSQL17/venv mới; browser không chạy lại. GitHub Actions chưa chạy; actionlint PASS. Đã lập CI và [ma trận nghiệm thu](ACCEPTANCE_MATRIX.md), vẫn chờ chủ dự án duyệt. Ảnh thật/Maps online, các khác biệt MASTER_SPEC, public deploy và hồ sơ nhóm còn thiếu. Không coi toàn bộ Sprint3/4 hoặc P0 đã nghiệm thu.

Không reset/bootstrap/seed/migrate DB hiện có trong checkpoint. Backup cloud gần nhất 18/10/2026 01:28:06 +07:00, files0600; draft cấu hình đã lưu, Publish/fresh-task recovery chưa xác minh. Git bundle/DB dump vẫn cùng cloud, không bảo đảm sống sót nếu môi trường bị tạo lại.


## Cập nhật cloud — 18/10/2026 (Asia/Ho_Chi_Minh)

Chỉ đạo tiếp tục của chủ dự án trong phiên cloud này thay thế checkpoint tạm dừng cũ ở dưới. Đã hoàn tất môi trường phát triển độc lập laptop; đã tiếp tục source theo Sprint 3/4 trên nhánh `codex/cloud-sprints-3-4`. Không push/public deploy.

- Cloud PostgreSQL 17.11: DB dev/test riêng và hai role NOSUPERUSER/NOCREATEDB/NOCREATEROLE, không CONNECT chéo; secrets mới, file 0600; bind loopback. Backup riêng ngoài Git; restore hai DB trên instance riêng đã kiểm tra identity, quyền, migrations và số bản ghi chọn mẫu. Chưa kiểm chứng fresh-task snapshot.
- Sprint 3: giao diện mới với menu mobile, hero/footer, responsive; contact/feedback có CSRF/honeypot/rate limit DB, ownership mã đơn; policies Admin-editable; Google Maps khu vực minh họa + link fallback; review chỉ món của đơn hoàn tất, chờ kiểm duyệt; Admin support/review. Profile/địa chỉ/password và rate limit auth bổ sung.
- Sprint 4: đặt slot 15 phút + lead time/horizon/capacity có khóa; xác minh giao 0–3 km thủ công có audit; công thức SKU/topping và sổ kho append-only, chặn thiếu/missing BOM; tích điểm COMPLETED+PAID đúng một lần; đơn APP/COUNTER nhập tay giá theo kênh + idempotency/reference + đối soát riêng; báo cáo Admin theo ngày/kênh và CSV không PII. Công thức, giá, tồn đầu và điểm đều DEMO.
- Suite cuối gần nhất: **90 PASS, 0 FAIL, 0 SKIP** trên PostgreSQL thật + Chromium. 4 concurrency tests; E2E Customer → payment retry → Staff fulfillment → loyalty → review/contact/manual APP. Xem TEST_REPORT cho phạm vi browser.
- Không nghiệm thu DONE toàn bộ Sprint 3/P0: ảnh vẫn là SVG fallback, chưa có ảnh chụp từng món; Maps online chưa xác minh. Tải ảnh ngoài bị proxy 403; đã thêm domains cần thiết vào draft, chưa khẳng định runtime đã áp dụng.
- Sprint 5 chưa triển khai Internet vì chưa có phê duyệt public deploy/provider/credentials; `check --deploy` cấu hình production PASS, Gunicorn loopback smoke PASS. Không tạo tài nguyên trả phí.
- Sprint 6 đã chuẩn bị runbook/ERD/UI checklist/demo script; Word/PPTX/ZIP chưa phát hành vì chưa có số nhóm/thành viên/tỷ lệ, địa chỉ chính thức và URL production. Không bịa dữ liệu nghiệm thu.

Chi tiết bên dưới là **lịch sử WSL trước phiên cloud**, không phải trạng thái hiện tại.


## CHECKPOINT TẠM DỪNG — 13/10/2026 (Asia/Ho_Chi_Minh)

**Chủ dự án yêu cầu tạm dừng để tắt máy.** Các thay đổi source đã lưu trong workspace; chưa commit/push (Git repository chưa khả dụng). Không phát triển tiếp cho đến khi chủ dự án tiếp tục.

- Sprint 1 và Sprint 2: suite PostgreSQL gần nhất **57/57 PASS**, 0 FAIL; đây là kết quả trước các thay đổi provisioning/local QA, chưa chạy lại toàn suite sau các thay đổi đó.
- Website đã chạy trên **http://localhost:8000/** bằng `.venv`, bind `127.0.0.1:8000`, `--noreload`. Không phải deployment công khai.
- HTTP smoke thực tế **9/9 PASS**. Browser QA **đang tiến hành**, chưa nghiệm thu PASS toàn bộ.
- Database `nau_coffee_dev`: **8 món, 13 SKU, 39 bản ghi giá**, đã xác minh trước đó. Giữ nguyên PostgreSQL/container/volume và secrets cục bộ `.env`, `.env.test`.
- Chủ dự án xác nhận đã tạo **demo_customer** và **demo_staff** trong Terminal Ubuntu; không có mật khẩu được gửi vào chat hoặc ghi trong báo cáo.
- Chủ dự án xác nhận Customer đã đặt thành công đơn DEMO **75.000đ**, gồm **3 cà phê đen đá**. Chưa xác minh riêng trạng thái payment/order cuối cùng hoặc mã đơn; không suy diễn đã thanh toán/hoàn tất.
- HTTP **403 ở `/dashboard/orders/`** xảy ra khi dùng phiên **demo_customer**. Chưa phải lỗi phân quyền được xác nhận; Customer bị chặn là hành vi dự kiến. Cần đăng nhập **demo_staff** để kiểm tra queue và xử lý đơn.
- Chưa chạy browser screenshots/E2E đầy đủ, chưa xác nhận DONE gate toàn dự án; ảnh sản phẩm vẫn placeholder, Sprint 3/4 còn thiếu theo báo cáo trên.

### Tiếp tục khi bật máy

1. Mở Ubuntu WSL và workspace `/home/<user>/projects/NauCoffee`; bảo đảm Docker Desktop/PostgreSQL hiện có hoạt động. Không chạy bootstrap/seed/reset.
2. Chạy `.venv/bin/python manage.py check`, rồi `.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload`.
3. Mở http://localhost:8000/, logout Customer hoặc dùng browser profile riêng, login **demo_staff** tại `/accounts/login/`.
4. Mở `/dashboard/orders/`, tìm đơn 75.000đ, kiểm tra trạng thái payment và chuyển đúng lifecycle. Nếu PENDING_PAYMENT, Customer cần hoàn tất mô phỏng trước; không nhảy bước.
5. Ghi kết quả browser QA thực tế; hoàn thiện giao diện và Sprint 3 tiếp theo. Sprint 4 vẫn trong phạm vi backlog.

**Dừng server an toàn:** ở Terminal đang chạy `runserver`, nhấn **Ctrl+C**; thao tác này chỉ dừng web process, không reset/xóa DB và không dừng/xóa container PostgreSQL.

> **Trạng thái hiện hành (13/10/2026):** seed dev PASS, migrations dev/test PASS, Sprint 1 backend suite **39/39 PASS PostgreSQL**; đã triển khai Sprint 2 commerce core và suite cuối **57/57 PASS PostgreSQL** (0 FAIL). Browser QA, ảnh thật từng món và production smoke chưa chạy; chưa đủ gate DONE toàn dự án. Các mục bên dưới giữ lịch sử các phiên.

Ngày: 13/10/2026. Không có URL public; chưa đạt gate DONE của master spec.

## Sprint 0 — Khảo sát

Đã đọc toàn bộ hướng dẫn/đặc tả. Source ban đầu trống (chỉ có AGENTS/master spec). Cả 12 yêu cầu, DB schema, auth, cart/payment, staff/admin, test và deployment đều thiếu.

- Python 3.14.4 có sẵn; pip/Django chưa cài; `python3 -m venv .venv` thất bại vì thiếu ensurepip.
- Docker mặc định báo permission denied; kiểm tra read-only có cấp quyền thấy `pg_lab_postgres postgres:17`. Không sửa container/volume/database.
- `.git` không phải Git repo khả dụng và chỉ đọc; chưa tạo nhánh/commit.
- `sudo apt-get update` bị chặn vì cần terminal nhập mật khẩu. Đã yêu cầu chủ dự án chạy apt trong WSL, không chia sẻ password.
- Chủ dự án xác nhận cài apt thành công; `dpkg-query` xác nhận python3-pip/python3-venv/python3.14-venv installed. `.venv` đã tạo thành công. Pip trong sandbox lỗi DNS; đang cài dependencies vào `.venv` với quyền mạng được duyệt.

## Sprint 1 — IN PROGRESS, chưa xác nhận DONE

Đã tạo source: `manage.py`, `config/`, `catalog/` (models, migration 0001, auth views, permissions, admin, seed), `templates/`, `static/catalog/`, `tests/test_foundation.py`, requirements + lockfile, env example, README và ERD.

Kết quả cuối: tạo `.venv` PASS; cài dependencies chỉ trong `.venv` PASS; Django check PASS; 12/12 tests SQLite fallback PASS (0.810s); migration drift PASS; collectstatic PASS (129 files); pip check PASS. Chi tiết lệnh trong TEST_REPORT. Không coi fallback là PostgreSQL PASS.

| REQ | Hiện trạng source | Chưa đạt |
|---|---|---|
| 01 | Backend search/category/price/pagination; filter test PASS fallback | PostgreSQL/browser/production QA |
| 02 | Sort whitelist; query filter giữ khi phân trang; sort test PASS | PostgreSQL/browser/production QA |
| 03 | Register/login/POST logout, hash Django, private account; auth test PASS | PostgreSQL/browser/production QA |
| 04 | Chưa triển khai | Cart/checkout/order/payment Sprint 2 |
| 05 | SVG fallback offline; upload admin có validation | Ảnh từng món, deployment media QA |
| 06 | CSS responsive, labels, focus, nút 44px | Browser QA 375/768/1440 NOT RUN |
| 07 | Chưa triển khai | Contact/feedback Sprint 3 |
| 08 | Model sale window, giá cũ/mới detail và giá filter; tests PASS fallback | Voucher Sprint 2, PostgreSQL/production QA |
| 09 | Chưa triển khai | Policies Sprint 3 |
| 10 | Chưa triển khai | Maps demo Sprint 3 |
| 11 | Chưa triển khai | Verified reviews Sprint 3 |
| 12 | Catalog/category/SKU/pricing/image admin, dashboard role gate | Orders/support/reviews/admin workflows còn thiếu |

Sprint 2–4 chưa bắt đầu. Sprint 5 chưa duyệt. Sprint 6 chưa có thông tin nhóm/thành viên để tạo bàn giao chính thức.

## Bước tiếp theo

Thiết lập DB PostgreSQL riêng qua secrets cục bộ và phê duyệt tạo DB; chạy migrations/seed/tests PostgreSQL. Bổ sung foundation schema/cart/order/payment còn thiếu của Sprint 1, browser QA và ảnh từng món. Tiếp theo triển khai commerce Sprint 2. Chưa public deploy hoặc push; không xóa/tạo lại container PostgreSQL.

## Phiên tiếp theo — schema và kiểm tra bootstrap

- Đã bổ sung source `commerce/models.py`: Cart/CartItem/Order/OrderItem/Payment/Voucher, histories/events/redemption và StoreSettings; thêm ProductOption, ownership/money/quantity/uniqueness constraints. **IN PROGRESS**: migrations commerce/services/UI giao dịch chưa hoàn tất, chưa chạy test suite nền tảng sau các thay đổi này.
- Docker read-only có quyền xác nhận PostgreSQL 17.9 và `nau_coffee_dev` chưa tồn tại ở thời điểm kiểm tra. Bootstrap bị từ chối quyền thực thi, chưa tạo tài nguyên.
- Theo chỉ đạo mới: dừng trước bootstrap để rà soát. Đã sửa bootstrap, thêm test_settings/guarded test runner và safety tests, cập nhật README. Safety suite **11 PASS / 0 FAIL** (unit mocks, không kết nối DB); compileall PASS.
- Docker trong sandbox vẫn `permission denied`; cần quyền thực thi ngoài sandbox cho lệnh Docker/bootstrap. Không tự sửa socket/group/container.
- PostgreSQL migration/tests vẫn **NOT RUN**; chưa kết thúc Sprint 1, Sprint 2 chưa bắt đầu. Báo cáo review trước khi chạy bootstrap theo yêu cầu.

## Trạng thái mới nhất — thao tác tách bước theo chủ dự án

- Chủ dự án chạy bootstrap thành công trong Terminal Ubuntu. Không chạy lại bootstrap. `.env`/`.env.test` đã tồn tại; không in nội dung.
- Verification trực tiếp credentials riêng PASS cả hai DB PostgreSQL 17; NOSUPERUSER/NOCREATEDB/NOCREATEROLE, không được CONNECT chéo. Docker sandbox vẫn permission denied; truy cập PostgreSQL ngoài sandbox có cấp quyền.
- Bước 1 `manage.py check` PASS 0 issues. Bước 2 `scripts/verify_django_database.py` PASS xác nhận Django thực sự kết nối nau_coffee_dev/nau_coffee_app. Bước 3 `showmigrations --plan` PASS: 21 unapplied migrations hợp lệ.
- Chủ dự án phê duyệt riêng bước 4 qua công cụ quyền: `migrate --noinput` PASS, 21/21 migrations trên DB dev. Chưa chạy seed.
- Schema có `catalog/0002_productoption`, `commerce/0001_initial`; đã thêm cart services/merge login, schema tests và read-only commerce admin + voucher admin. Fallback suite trước seed guard mới đạt **36 PASS/0 FAIL**; lỗi signal login và assertion cache OneToOne đã sửa.
- Bước 5 seed review: get_or_create giữ dữ liệu hiện hữu; ADMIN permissions đổi từ set sang add để không loại bỏ quyền; thêm target guard xác nhận dedicated DB/role thực tế. Safety suite hiện tại **14 PASS/0 FAIL**, không seed DB.
- **Đang chờ xác nhận riêng bước 6 seed_demo** theo yêu cầu mới nhất. PostgreSQL integration tests vẫn NOT RUN. Sprint 1 chưa xác nhận PASS đầy đủ; Sprint 2 chưa bắt đầu. Không sửa DB cũ, xóa tài nguyên hoặc deploy online.

## Sprint 1 — Backend/PostgreSQL đã xác minh

- Seed chạy đúng `.venv/bin/python manage.py seed_demo` sau xác nhận riêng. Read-only `verify_demo` PASS trước/sau các tests: 8 món, 13 SKU, 39 giá, 3 roles, đúng quan hệ, không trùng.
- Migrations catalog/commerce/auth/admin/session đã áp dụng dev và DB test riêng. Schema tests introspect constraints thật PostgreSQL, FK/PROTECT, số lượng/giá, cart ownership, payment/redemption uniqueness, snapshots, voucher bounds/case/date, RBAC.
- Lần đầu runner chặn default `parallel=0`; đã sửa nhận 0/1 (không chạy nhiều worker). Suite Sprint 1 **39 PASS, 0 FAIL**, PostgreSQL, 1.258s. DB test giữ nguyên với --keepdb; không tạo/drop/clone database.
- Chưa xác nhận DONE đầy đủ: browser QA responsive và ảnh thật từng món còn thiếu; chưa production smoke.

## Sprint 2 — Commerce core backend PASS, UI/E2E chưa nghiệm thu

Đã triển khai trong `commerce/services.py`, `forms.py`, `views.py`, `urls.py`, `templates/commerce/`; cập nhật nav/product/account/dashboard và CSS; thêm `tests/test_commerce_flow.py`, `tests/test_commerce_concurrency.py`.

- Guest giỏ tạm → login merge một lần; Customer thêm/sửa/xóa, xem tổng tiền, đăng nhập bắt buộc checkout, tiếp tục giỏ cũ.
- Price engine đọc WEB/active sale/options từ DB, bỏ qua total/price client; tính subtotal/discount/shipping/grand total và quote lại khi tạo đơn atomic.
- Voucher CRUD Admin và trang promotions; ngưỡng tối thiểu, dates, percent/fixed/cap, giới hạn tổng/per-user, chặn stacking mặc định, release khi cancel. Không seed voucher mới vào dev.
- OrderItem snapshots; idempotency gửi đơn lặp và checkout key mới cho giỏ mới; ownership order history/detail.
- COD/pickup unpaid độc lập order status; staff ghi nhận thu DEMO có event idempotent. Mock failure/retry/success có event, success một lần; hủy trước pha chế, refund mô phỏng chỉ Admin.
- Staff/Admin queue, status filter/pagination, chuyển trạng thái theo graph có history actor/reason; Customer không truy cập operation endpoints; admin giao dịch chỉ đọc để không sửa snapshots/totals tùy tiện.
- Delivery lưu rõ chờ xác minh, phí cấu hình demo, chặn PREPARING khi chưa xác minh ≤3 km. Workflow xác minh/đặt trước, BOM, loyalty, đơn APP/COUNTER, reports thuộc Sprint 4 và chưa triển khai.
- Suite cuối PostgreSQL **57 PASS, 0 FAIL**, 2.562s, gồm 2 race tests với 2 connection thật và Barrier đồng thời (double submit, voucher last use). Django check/migration drift/collectstatic PASS. Dev catalog verify vẫn PASS sau tests.
- Browser/E2E **NOT RUN**: chưa có Playwright/browser trong môi trường. Chưa có screenshot 375/768/1440; không claim responsive nghiệm thu xong. Sprint 3 chưa triển khai; chưa deploy/push hoặc can thiệp DB cũ.

## Localhost và tài khoản QA — hiện hành

- Theo yêu cầu, ưu tiên mở website trước phát triển Sprint 3/4. `manage.py check` PASS. Runserver trong sandbox lỗi kết nối PostgreSQL; sau quyền chạy ngoài sandbox đang bind **127.0.0.1:8000**, --noreload. Windows URL: http://localhost:8000/ (chưa xác nhận truy cập từ browser Windows).
- HTTP smoke thật 9/9 PASS: home/menu/product/login/register/promotions/health/static CSS/SVG. Không gửi form, không tạo order/user. Đây không phải visual/browser QA.
- Đọc DB thấy Customer/Staff/Admin/superuser đều 0 lúc kiểm tra. Chủ dự án cho phép Customer+Staff, không Admin/superuser; mật khẩu tự nhập ẩn tại Terminal Ubuntu.
- Tạo command `create_demo_account`: mặc định PREVIEW không ghi; chỉ --apply + TTY nhập ẩn + password validators mới tạo user. Chỉ nau_coffee_dev; không ghi đè username; không sửa/xóa user cũ. STAFF group nghiệp vụ, is_staff=False/is_superuser=False; CUSTOMER tương tự.
- Hai PREVIEW demo_customer/CUSTOMER và demo_staff/STAFF đều PASS; **chưa chạy --apply**, chưa có bằng chứng account đã tạo. Đợi chủ dự án nhập mật khẩu tại Terminal rồi thử journey.
- Playwright package đã cài trong .venv để chuẩn bị browser QA; browser runtime/chụp màn hình/E2E chưa chạy. Không claim browser PASS.
# Cập nhật 20/11/2026 — Final Customer UI/UX refinement

- Hoàn thiện 13/13 hạng mục Customer UI/UX và lịch nhận món trên source local; không tạo migration.
- Lịch mặc định được chốt tại thanh toán mock thành công +30 phút; lựa chọn tay dùng mốc server vào menu +35 phút và được kiểm tra lại khi thanh toán.
- Targeted backend 70/70 PASS trên QA 55441; responsive 375/768/1440 PASS. Chi tiết: `docs/FINAL_CUSTOMER_UI_UX_REFINEMENT_REVIEW_2026-11-20.md`.
- Chưa commit/push/deploy; preview/Neon không nhận thao tác ghi.
# Cập nhật 20/11/2026 — Checkout 24 giờ

- Thay `datetime-local` Customer bằng ngày + giờ `00–23` + phút `00–59`; không còn phụ thuộc popup SA/CH của Chrome.
- Backend 16/16 PASS; Chromium 09:30/14:30/23:00 và responsive 375/768/1440 PASS trên QA độc lập.
- Chi tiết: `docs/CHECKOUT_24H_PICKER_FIX_2026-11-20.md`.
# Cập nhật 20/11/2026 — Policy Rich Text Editor

- Hoàn thiện editor chính sách trực quan với bold, italic, H2/H3, danh sách và liên kết; không thêm thư viện ngoài hoặc migration.
- Preview/lịch sử/Customer dùng chung renderer an toàn, tương thích cú pháp cũ.
- Policy/Consent 16/16 PASS; Chromium publish flow 375/768/1440 PASS trên QA 55441.
- Chi tiết: `docs/POLICY_RICH_TEXT_EDITOR_REVIEW_2026-11-20.md`.
> **20/11/2026 — Customer UI/UX Round 2:** hoàn thiện9/9: shared contact, Maps Customer-only, `/ve-nau/` với4ảnhđúngthứtự, Footer4cột/social, nav, Contact prefill, logo đối tác, Privacy cleanup. QA targeted60/60PASS; Chromium Round2+Policy tại375/768/1440PASS; migration drift/diff checkPASS. Không DB/migration/Git/deploy. [Báo cáo](CUSTOMER_UI_UX_REFINEMENT_ROUND2_2026-11-20.md).

## 20/11/2026 — Separate Customer/Internal Login

- DONE: hai login gateway, role redirect, internal website navigation, contextual logout, server-side transaction denial cho internal session.
- DONE: targeted auth/RBAC 36/36 PASS; Chromium responsive 1/1 PASS trên QA 55441.
- Không migration, không thay đổi dữ liệu/tài khoản hiện hữu, chưa commit/push/deploy.
