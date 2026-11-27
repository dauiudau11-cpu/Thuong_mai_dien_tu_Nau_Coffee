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

## 13/11/2026 — Hoàn tất responsive không mởserver

7/7render mớiPASS, tổng9/9màn hình375/768/1440 (2HTTPtrước+7DjangoGET/Playwrightintercept). Eager voucher quan hệ load trước eventloop; khôngasyncunsafe hoặc sửaapp. Preview45tables/44seq vàschema/datadigest exact unchanged;QA cả2DB trước/sau khớp, runtimeprofile byteunchanged.0DMLattempt, khôngformPOST/dborder/session/consent/voucher mutation. Quote JSON từ projection read-only, không coi làHTTPintegration mới. Server8000/8001/SMTP25251khôngmở, featureOFF. Không chạy lại51tests; kết quả nguồn/ảnh/fingerprint: `docs/qa/2026-11-13-local-cutover/responsive-readonly/`. [Phạm vi](LOCAL_FEATURE_CUTOVER_REVIEW_2026-11-13.md).

## 13/11/2026 — C: migration PASS; smoke integration PASS; responsive BLOCKED

Preflight/fresh encrypted backup+restore PASS; migratepreview0,300s/rerun0,038s, schema45/44/160/209/64/pending0, metadata+2/+7/+28. FullQA370PASS/0FAIL/SKIP,388,373s. LocalC51checksPASS(gồm4races), Customer375/Staff375browserPASS; Admin375 chưa chạy do helper lazyFK async-safe exception,7screens còn thiếu. READONLYrepro và eagerload probePASS; helperfix chưa rerun. FeatureOFF/serverSTOPPED theo quy tắc user; không automaticrestore. Alloldrows preserved, original prices/SKU/BOM/stock/policy/time hashes unchanged;9newmarkedorders valid. QA giữ nguyên từ mốc sau regression đến hết livecutover; test metadata/sequence drift dofullQA không được che. [Chi tiết/giới hạn](LOCAL_FEATURE_CUTOVER_REVIEW_2026-11-13.md).

## 13/11/2026 — B: migration/integration/rollback trên dữ liệu hiện hành sao chép

Migration và rerun PASS; schema45/44/160/209/64 khớp QA canonical.46 kiểm tra integration PASS/0FAIL/SKIP, gồm4PostgreSQL races;9screens ChromiumHTTP/CSRF PASS ở375/768/1440;5negative guard probes PASS; replay consent đúngsession/purpose bị từ chối. Original rows của38bảng không đổi sau fixture/integration; preview38bảng và37sequence khớp baselineA. Recovered target mới trở lại38/37/131/168/48;4GET readonly flagsOFF200. Migrate0,264s, rerun0,036s, restore0,19s, recovery verification28,775s, không gọi làdowntimeSLA. Source221inputs mốc360fullPASS không đổi nên không rerunfull; không testghi preview/QAregression. Check/drift/diffPASS. [Phạm vi và helper attempts](CUTOVER_STAGE_B_REVIEW_2026-11-13.md), evidence `docs/qa/2026-11-13-cutover-stage-b/`.

## 13/11/2026 — Giai đoạn A: backup/restore dữ liệu hiện hành PASS

**PASS thực tế**, không phải synthetic-only: pg_dump snapshot READ ONLY preview `nau_coffee_test`5432→archive mã hóa ngoài repo→DBrestore mới tách biệtQA55441.38/38rows/count/hash,37/37lastvalue/is_called,168constraints/48FKvalidated,indexes/cộtlogic/migrationrowskhớp. Preview38/38trước/sau, flagsOFF và2pending giữ nguyên; QA cũ fingerprint/roleattrs khớp provision, accountsQA45/0pending. Hai helperstops trước kết luận cuối: fetch-BEGIN sửa temphelper; ordinalphysicalgap sau dropcolumn đã xác minh bằng logicalorder, khôngALTER/restorelại. Finalverification10.091s,khôngcoilàRTO. Django check/migrationdrift/diffcheckPASS;221sourceinputs không đổi nên không rerunfull360. Email liveNOTRUN/featureactivation/migrationcurrent/restart8000NOTRUN. [Biên bản và giới hạn](FEATURE_INTEGRATION_CUTOVER_PLAN_2026-11-13.md), evidence `docs/qa/2026-11-13-cutover-stage-a/`.

## 13/11/2026 — Source tích hợp mới: 360/360 PASS

Full PostgreSQL QA17 + Chromium: **360PASS/0FAIL/0SKIP,386.792s**. Targeted sau2adaptererrors đạt108PASS/57.905s (5journeyimported lặp, đã bỏ trướcfull; không cộng targeted vào full). Thêm5backend tests+1HTTPAdminbrowser test. Voucher3races và Account/Reset races trongfullPASS. Admin HTTP/CSRF edit/pause/resume/history3widthsPASS; voucher checkout/POS/Admin list/detail12rendersPASS. Check/migrationdrift/diffcheckPASS,khôngapplymigration;221inputs không đổi.1.552connections đúngQA,preview38/38READONLYhash unchanged,QA cũ giữ nguyên. Email sandboxPASS; GmailAUTH/SEND/DATA250 lúc00:09:58 ngày13/11 +ownerreceived là bằng chứng lượt riêng,khôngsendởlượtnày. Evidence `docs/qa/2026-11-13-feature-integration/`; [phạm vi/giới hạn](NAU_COFFEE_V3_FEATURE_INTEGRATION_REVIEW.md). Preview chưa cập nhật/featureOFF; khôngCI/publicdeployment/cutover.

> Lưu phiên 12/11/2026 21:01:34 (giờ Việt Nam): [SESSION_HANDOFF_SAVED_2026-11-12_210134.md](SESSION_HANDOFF_SAVED_2026-11-12_210134.md). Không chạy lại test;231sourceinputs khớp mốc354PASS,diffcheckPASS; chỉ cập nhật tài liệu, không DB/server/Gitrefs.

## 12/11/2026 — Customer quên/đặt lại mật khẩu đã nghiệm thu QA

**354/354 fullPASS,0FAIL/SKIP**,453.217s; **24/24 targetedPASS**,2PG races,12flow screens+3emailrender375/768/1440PASS. Token/form/hash chuẩnDjango,TTL1h, chỉactive verified unique-emailCustomer, chặnStaff/Admin/unactivated, generic response/rate/CSRF/fragment/no-auto-login/multi-tab binding.231sourceinputs vàcredentials khôngđổi saufull. Lượt resume đầuFAIL dofixtureQAsót saugiánđoạn; normalteardown đãdọn, preflightreadonly0bản ghi và rerunkhôngđổi sourcePASS. QAguard/models/migrations/businesssource giữnguyên,45bảng/0pending; khôngpreview/devSQL/start8000/featureON/Git. SMTPsandboxPASS, liveSMTPNOTRUN. [Báo cáo và file thay đổi](PASSWORD_RESET_REVIEW_2026-11-12.md).

## Gmail SMTP12/11 — source mới330/330PASS, liveBLOCKED

Đọc checkpoint120432, cấu hình Gmail smtp.gmail.com:587/TLS/noSSL/15s/senderchínhthức, optional privateprofile0600/ignoredchưaautonạp. Email activation/Staffinvitation multipartHTML+plain, trustedHTTPSgate; template6/6renderPASS. Targeted58/58PASS, fullPostgreSQL+Chromium **330/330PASS,0SKIP**,375.276s,220sourceinputs khôngđổi; SMTPloopback/mock/racegửi1thưPASS. Không Gmailconnection hoặc mailthật, AppPassword/origin/ngườinhận/phêduyệt cònthiếu: **LIVESMTPBLOCKED**.8000/8001đãdừngđầuphiên, không start/restart; chỉ QAcontainerkhởiđộng, không migratepreview/dev hoặc sửa guard/Git. [Báocáo](GMAIL_SMTP_REVIEW_2026-11-12.md), [ownersteps](GMAIL_SMTP_SETUP_2026-11-12.md).

> Lưu phiên 12/11/2026 12:04:32 (giờ Việt Nam): [SESSION_HANDOFF_SAVED_2026-11-12_120432.md](SESSION_HANDOFF_SAVED_2026-11-12_120432.md). Không chạy lại test;214source inputs khớp mốc320PASS, diff checkPASS; chỉ cập nhật tài liệu, không database/server/Git refs.

## Chốt nghiệm thu12/11 — source cuối320/320PASS, chưa kích hoạt

FullPostgreSQL+Chromium **320/320PASS,0FAIL/SKIP,422.468s**; targeted68/68PASS;214sourceinputs không đổi sau full. Ba voucher racePASS, E2E HTTP3widthsPASS, duplicate blur giữ tổng/submitPASS. QA encrypted backup/restore45bảng+rows+sequencePASS; pg_dump/restore17.9. Người dùng xác nhận login10:54:21 và thêm món11:49:45: hoạt động preview hợp lệ; cuối lượt36/38 bảng giống đầu,33/38 giống mốc gốc, mọi bảng kinh doanh quan trọng giữhash.1464kết nối Django regression đềuQA55441,0preview; network-guard E2E1583requests testport,0attempt8000/8001. SMTPthậtBLOCKED cấu hình; migration/backup dữ liệu hiện hành/feature/GitHub chưa được duyệt. [Chi tiết và phê duyệt còn cần](VOUCHERS_PHASE2_ACCEPTANCE_2026-11-12.md). Các mốc “chưa xác minh actor” phía dưới là lịch sử trước xác nhận của người dùng.

## 12/11/2026 — E2E thực voucher và rehearsal QA

Targeted68/68PASS48.368s,0SKIP; browser HTTP PostgreSQL QA qua3breakpoints gồm đăng ký/kích hoạt/login, PUBLIC/PRIVATE/no voucher, Staff pending/lookup/consent, guestCOUNTER/APP, hủy không trả lượt, min/expiry và duplicate blur/submit. Ba voucher racePASS. Backup/restoreQA45bảng+sequence PASS, sourceQA không đổi trong restore. SMTP loopback2bàiPASS, SMTPprovider thật BLOCKED.320PASS trung gian trước sửa giữ tổng blur là lịch sử; full source cuối đang chạy. [Evidence và giới hạn](VOUCHERS_PHASE2_ACCEPTANCE_2026-11-12.md).

> Cập nhật bảo toàn preview cuối Đợt 2: **34/38 bảng không đổi**, 4 bảng auth_user/cart/session/submissionlimit có drift phù hợp một lượt login lúc 10:54:21 giờ Việt Nam, chưa xác định actor. Không xác nhận 38/38; order/payment/giá/BOM/stock giữ fingerprint. Chi tiết trong review Đợt 2; không tự sửa dữ liệu.

## 12/11/2026 — Voucher V2 trên QA PostgreSQL độc lập

Targeted **20/20 PASS, 0 FAIL/SKIP**; public/private/WEB–COUNTER ba race PASS, migration legacy không rewrite lịch sử PASS, responsive/live totals Customer/Staff/Admin 375/768/1440 **9/9 PASS**. DB QA accounts 55441, runner hạn chế/guard attestation; không dùng preview/dev cho tests ghi. Full PostgreSQL + browser **319/319 PASS**, 329.338s, 212 source inputs không đổi; xem [review và evidence](VOUCHERS_PHASE2_REVIEW_2026-11-12.md). System check, migration drift SQLite bộ nhớ và diff check PASS. SMTP thật/backup-restore hiện hành/feature activation NOT RUN.

## 12/11/2026 — Full regression PostgreSQL QA accounts

**299 tests — 299 PASS, 0 FAIL, 0 SKIP**, 322,228 giây trên nau_coffee_qa_accounts/role riêng/55441, Chromium + SMTP sandbox. Targeted **46/46 PASS**, bao gồm hai race và migration legacy/empty/conflict. Source freeze **215/215 không đổi**; old QA fingerprint nguyên vẹn. Django check/drift/diff check PASS. Preview feature OFF, không migration/test ghi preview/dev. SMTP provider thật và GitHub CI NOT RUN. Bằng chứng `docs/qa/2026-11-12-accounts-postgresql/`; [báo cáo cập nhật](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md).

## Checkpoint 12/11/2026 02:28 — giờ Việt Nam

Đã lưu [SESSION_HANDOFF_CUSTOMER_ACCOUNTS_2026-11-12_022847.md](SESSION_HANDOFF_CUSTOMER_ACCOUNTS_2026-11-12_022847.md). Giữ trạng thái 122 PASS/2 SKIP trong 124 tests, feature OFF, QA TCP credentials BLOCKED; A/B chưa được duyệt. Lượt lưu chỉ cập nhật tài liệu, không chạy lại test, không đổi code/database/Git refs/server.

## 12/11/2026 — Technical acceptance phase 1

**124 tests — 122 PASS, 2 SKIP, 0 FAIL**, SQLite bộ nhớ + Chromium + SMTP sink loopback. Hai SKIP là race phone và race consent trên PostgreSQL. Migration ứng dụng trống/legacy/conflict rehearsal PASS trên SQLite; PostgreSQL equivalents **BLOCKED** vì chưa xác minh credentials QA. SMTP protocol send/resend/activation/rejection PASS ở sandbox, provider/TLS/delivery thật NOT RUN. Security-before tái hiện 3 FAIL session/purpose, đã sửa và regression PASS. Browser output tách thư mục QA cũ; 27/27 checks responsive PASS. [Chi tiết, bằng chứng, giới hạn và migration approvals](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md). Cập nhật QA: Unix socket local-trust đã xác minh role hạn chế và schema catalog.0004/38 bảng; TCP password chỉ còn verifier SCRAM. Đã trình phương án A role+DB QA mới với allowlist guard, hoặc B rotate password QA cũ; cả hai chưa thực hiện.

## 12/11/2026 — Customer accounts phase 1

**116 tests, 115 PASS, 1 SKIP**, SQLite bộ nhớ + Chromium render offline; **27/27** lượt responsive 375/768/1440, không mở thêm server. Bao phủ signup/trùng phone-email/legacy/email-token/Staff/POS/checkout/Admin và guard P0. PostgreSQL concurrency/migration/full regression **NOT RUN/BLOCKED**; SMTP thật NOT RUN. Không gọi 116/116 PASS. Django check, migration drift và diff check PASS; migration mới chưa áp dụng preview/dev. [Lệnh, bằng chứng và giới hạn](CUSTOMER_ACCOUNTS_PHASE1_REVIEW_2026-11-12.md). Preview cuối phiên: **38/38 fingerprint không đổi**, 5/5 HTTP GET PASS, PID 8000 giữ nguyên; migration catalog.0005 vẫn chưa áp dụng.

## 11/11/2026 — Regression hai P0

**22/22 targeted PASS** (SQLite :memory:), **9/9 HTTP PASS** trên localhost 8000, quản lý kết nối chỉ đọc và runner từ chối preview trước connection PASS; fingerprint **38/38 bảng giống nhau**. Django check, migration drift không áp dụng migration và git diff --check PASS. Full PostgreSQL/CI **NOT RUN**: credentials QA cũ không còn sau reboot. Responsive NOT RUN vì không sửa UI. Kết quả 235 trước đây chỉ là lịch sử. Lệnh/log/giới hạn: [báo cáo P0](P0_PRICE_FILTER_TEST_ISOLATION_FIX_2026-11-11.md).

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

# Diễn tập menu mới — kết quả31/10/2026

## Kết quả hiện hành sau sửa regression — 06/11/2026

Hai CustomerPresentationTests2/2PASS,0.347s. Backend149/149PASS,13.224s. Discovery không label với config.test_settings/keepdb/parallel1: **164/164PASS (149backend+15browser),173.389s;0FAIL/ERROR/SKIP**. Actual DB/role/PostgreSQL17/noCONNECTdev reverified READONLY. AST92/check0issues/drift/diff-checkPASS. Browser mới dùng Chromium cục bộ, artifacts ignored test-results;60standard-menuchecks gồm24detail,0overflow,93visualcaptures; widths375/768/1440. Không mock/skip/xfail regression để lấy PASS. Delivery mới có rule/integrationPASS nhưng chưa browserE2E hoàn chỉnh bill/60phút/thu tiền; physicaldevices/production NOTRUN. Không seed/import/migrate dev. [Chi tiết và lịch sửFAIL](CHECKPOINT_2026-11-06.md).

## Kiểm thử trước commit/push — 06/11/2026

HEAD73103e7, nhánh feature/cafe-premium-reference-20261028. Preflight READ ONLY xác nhận PostgreSQL17 nau_coffee_test/nau_coffee_test_runner hạn chế, không CONNECT dev. Targeted standard_menu/demo_delivery_rules/demo_delivery_checkout:30PASS/0FAIL,2.188s. Full tests:149executed,147PASS/2FAIL/0ERROR/0SKIP,13.065s. Failures trong CustomerPresentationTests do tiền tố “Từ” và caption ảnh đã đổi ở templates; không sửa/bỏ qua assertion. `manage.py check`0issues; migration drift với test settings và `git diff --check`PASS. Browser mới/stage/commit/fetch/push NOT RUN vì gate regressionFAIL. Không migrate/seed/import trên dev. [Lệnh, failures và phạm vi đầy đủ](CHECKPOINT_2026-11-06.md).

| Kiểm tra | Kết quả |
|---|---|
| Verify PostgreSQL dev/test role, restricted/noCONNECT chéo | PASS |
| Migration0004 | Chỉ áp trong nau_coffee_test qua safe runner/--keepdb; dev chưa áp |
| Full regression tests+browser_tests | **150PASS/0FAIL/0ERROR/0SKIP,148.863s** (135backend+15browser) |
| Test cuối sau sửa nhãn FIXED/CTA/table | **17PASS/0FAIL/0ERROR/0SKIP,28.505s**,16rollout+1browser |
| Lượt liên quan trước đó |27/27PASS,66.707s; full trước150/150PASS,126.693s |
| Check / migration drift / diff--check |PASS / No changes detected / PASS |
| UI menu mới |36ảnh,375/768/1440,HTTP200,0overflow,imagesloaded;12paused+24ready |
| Nghiệp vụ mới |8SKU/24giá/8cost, idempotence, rollback/drift guards, WEBpickup/tampering, APP/COUNTER, costRBAC, historicalsnapshots/stalecart PASS trên fixture |
| Backup/restore/migrate/apply dev | **NOT RUN**, chưa được duyệt |
| Dev cuối so với audit trước | **FAIL preflight:** CartItem1→0; chưa rõ tác nhân.8món/13SKU/39giá/4Cart/1đơn/1item/1payment, migration0004absent/flagFalse. Không tự sửa drift |

Test phát triển shortage từng lỗi fixture delta=0 và reason quá12ký tự; đã sửa ledger fixture hợp lệ, giữ nguyên constraints, chạy lại. Không dùng133PASS trước để nghiệm thu menu mới. Regression cờFalse giữ luồng cũ; test cờTrue riêng chứng minh quy tắc mới. Không claim apply dev hoặc BOM/tồn thực đã được xác nhận.

[Báo cáo và ảnh](STANDARD_MENU_REHEARSAL_2026-10-31.md). Cần khảo sát lại/owner xác nhận giỏ dev trước bước ghi. Giữ CartItem fixture trong test không đồng nghĩa CartItem dev hiện còn.

---

# Khảo sát menu mới —31/10/2026

PASS kiểm tra chỉ đọc actual nau_coffee_dev/nau_coffee_app restricted; audit catalog/relations trong REPEATABLE READ READ ONLY, không PII/secrets.8products/13SKU/39prices/4carts/1cartline/1order/1orderitem/1payment;0BOM/stockmovements/options/vouchers. Dòng giỏCF04-M, đơnWEB/PICKUP với CF01-STANDARD. Không sửa lịch sử.

`git diff --check` PASS. Test hồi quy giá mới/apply/migrations/backup/restore/browser menu mới: **NOT RUN**, đang chờ duyệt phương án; không lấy133PASS cũ thay nghiệm thu mới. [Bảng đối chiếu, phạm vi ghi và rollback](MENU_ROLLOUT_PLAN_2026-10-31.md).

---

# Nội dung, tiếng Việt và khoảng cách — 31/10/2026

- Kiểm tra database read-only PASS: PostgreSQL17 dev/test đúng role, không CONNECT chéo; suite chỉ nau_coffee_test qua guarded runner và --keepdb.
- `manage.py check` PASS; `git diff --check` PASS.
- Full regression lượt đầu132PASS/1ERROR (145.910s): browser tìm nhãn xác minh cũ. Sửa selector, giữ assertions nghiệp vụ, chạy lại: **133PASS/0FAIL/0ERROR/0SKIP (119backend+14browser),120.251s**.
- Before93/93 và After93/93 màn hình HTTP200,0overflow ở375/768/1440;185/185links200. Kiểm tra footer semantic/text/spacing/min-font mới PASS. Localhost read-only HTTP smoke9/9PASS sau restart.
- [File đã đổi, ảnh đối chiếu, phạm vi kiểm chứng và NOT RUN](COPY_SPACING_REVIEW_2026-10-31.md). Không dùng kết quả này để claim pixel-match toàn bộ Drive hay Windows-browser acceptance. Không ghi dev; fixtures chỉ test DB.

---

# Căn trang chủ sau mở máy — 30/10/2026

Nhánh `feature/cafe-premium-reference-20261028`, HEAD `6a10161` + local patch giữ nguyên. Đây là lượt kiểm thử mới sau reboot, không lấy133 PASS phiên trước thay thế.

| Kiểm tra | Kết quả thực |
|---|---|
| Git status/HEAD/diff | Giữ toàn bộ local patch; đúng nhánh/HEAD; diff--check PASS |
| Docker/port trong sandbox | Permission denied/netlink, không kết luận sai môi trường |
| Ngoài sandbox, đã duyệt | PostgreSQL cũ đang Exited(0),8000 trống; bật lại đúng container cũ, không recreate/reset |
| `scripts/verify_databases.py` sau start | PASS PostgreSQL 17 dev/test identity, role hạn chế, no CONNECT chéo |
| Django check | PASS,0 issues |
| Full `test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1` | **133 PASS,0 FAIL/ERROR/SKIP,120.065s** (119 backend+14 Chromium) |
| Responsive regression |93 screens,0 overflow,185 internal links HTTP 200 |
| Public localhost Home capture |3 Before +3 After, HTTP200, visible images loaded;0 overflow ở1448/768/375 |

Runtime Chromium/libs trong/tmp mất sau reboot, được duyệt tải lại và giải nén riêng/tmp. Không sudo/cài dependency vào hệ thống. Không ghi/migrate/seed/bootstrap/reset dev. Các dòng seed trong output là fixtures DB test. Không commit/push/merge/deploy.

Lệnh regression:

```bash
NAU_QA_ROOT=docs/qa/2026-10-30-home-alignment/regression LD_LIBRARY_PATH=/tmp/nau-browser-libs/root/usr/lib/x86_64-linux-gnu CHROMIUM_PATH=/tmp/nau-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell .venv/bin/python manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1
```

Đã mở ảnh mẫu gốc và xem trực tiếp After desktop/tablet/mobile. Desktop: header50px, hero282px full-width tại y74,6 cards/6 cột; page height2432→1168px. Tablet3251→1522px/3 cột; mobile3609→2101px/2 cột. Gallery giá/menu/backend giữ nguyên. Server --noreload ban đầu trả template cũ: đã restart đúng process và chụp lại; không tính lượt capture cũ là After PASS.

File source thay đổi đợt này: `templates/base.html`, `templates/catalog/home.html`, mới `templates/includes/home_product_card.html`, `static/catalog/home-alignment.css`. Các WIP ngoài phạm vi này giữ nguyên.

[Review trực quan](HOME_VISUAL_REVIEW_2026-10-30.md), [manifest/source hashes](qa/2026-10-30-home-alignment/manifest.json), [Before desktop](qa/2026-10-30-home-alignment/before/home-1448.png), [After desktop](qa/2026-10-30-home-alignment/after/home-1448.png), [After tablet](qa/2026-10-30-home-alignment/after/home-768.png), [After mobile](qa/2026-10-30-home-alignment/after/home-375.png).

Chưa khớp hoàn toàn: ảnh hero/banner, icon/font và header search khác mẫu; không giả voucher/review/avatar khi DB chưa có; footer/trang vẫn cao hơn mẫu. Không coi responsive PASS là pixel-match hoặc physical-device/WCAG/production PASS. Các trang Menu/Staff/Admin có hồi quy, nhưng chưa thực hiện vòng căn trực quan mới trong phiên này. URL http://localhost:8000/.

---

# UI theo Drive31 — 30/10/2026

Branch `feature/cafe-premium-reference-20261028`, HEAD `6a10161` + local diff. Không commit/push/merge/deploy. Đã đọc AGENTS/đặc tả/tiến độ và giữ mọi local patch cũ. Drive là nguồn UI ưu tiên theo yêu cầu mới.

## Giai đoạn và kết quả

| Giai đoạn / command | Kết quả thực |
|---|---|
| Drive connector metadata/list/fetch + download ảnh gốc |31/31 ảnh verified,10 Customer/5 Staff/16 Admin;6 config; tải riêng ngoài repo |
| Mạng sandbox download | FAIL DNS/URLError; retry ngoài sandbox theo phê duyệt.8 ảnh timeout/URLhết hạn được fetch reference mới và tải lại thành công; không bỏ ảnh |
| `scripts/verify_databases.py` ngoài sandbox | PASS PostgreSQL 17, đúng dev/test roles hạn chế/noCONNECTchéo; không thay DB |
| Customer backend regression |114/114 PASS,10.336s |
| `tests.test_drive_reference` |5/5PASS,0.533s; ADMIN guard/GET-only/no write/default/search |
| Full 133 đầu |132 PASS/1 FAIL,136.815s; assertion mới đếm cả nút search header, không phải config có Save |
| Full 133 sau sửa selector/nav/POS/table |**133 PASS,0 FAIL/ERROR/SKIP,128.701s**,119 backend+14Chromium |
|7 tests liên quan sau bổ sung assertion Kanban và VND |**7 PASS,52.771s**;5 backend+1 POS/Kanban/config+1 capture đã có trong133, không cộng test trùng |
| `manage.py check`, `git diff --check` |PASS |
| `node --check static/catalog/site.js` |NOTRUN: Node không có; JS thực đã exercise trong Chromium, không cài system dependencies để thay framework |

Lệnh full:

```bash
NAU_QA_ROOT=docs/qa/2026-10-30-drive LD_LIBRARY_PATH=/tmp/nau-browser-libs/root/usr/lib/x86_64-linux-gnu CHROMIUM_PATH=/tmp/nau-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell .venv/bin/python manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1
```

DB test được xác minh trước chạy. `config.test_settings` chỉ lấy .env.test, runner kiểm tra actual identity trước migrate, không CREATE/DROP/clone và không CONNECTdev; test cleanup/seed fixtures chỉ trong nau_coffee_test. Không migrate/seed/bootstrap/reset dev. Không dùng SQLite thay PostgreSQL.

## Hành vi đã kiểm chứng

- Customer search/filter/sort/cart/server quote/checkout/mock retry→Staff lifecycle→loyalty/review/Adminmoderation giữ suite cũ. Gallery/related lấy data backend; Contact/Policy không copy thông tin cửa hàng giả từ ảnh.
- POS card chọn CF02-STANDARD thật vào formset:2 ly COUNTER60.000đ→APP70.000đ (fixture legacy), submit tạo đúng1order, UNPAID. Không nhận giá client hoặc tự áp giá25/10.
- Trên Kanban, click Bắt đầu pha→PREPARING, click Sẵn sàng→READY, payment vẫn UNPAID. Đi qua transition service cũ; stock/permission/audit giữ nguyên.
- Config6pages: roleCustomer/Staff GET/POST 403; Admin GET 200 / POST 405; GET không tạo StoreSettings hoặc sửa DB. Management filter thật và GET không đổi Product/ChannelPrice.
- Browser capture **93screens=31pages×375/768/1440**,0 overflow,185 internal links HTTP 200. Gồm Customer, StaffKanban/POS/kho,5managementlists và6 config. Không suy ra physical-device/WCAG/pixelmatchPASS.

[Source inventory31 ảnh](qa/2026-10-30-drive/references.json), [QAmanifest](qa/2026-10-30-drive/manifest.json), [93 captures](qa/2026-10-30-drive/after/manifest.json), [linkaudit](qa/2026-10-30-drive/after/links.json), [đối chiếu từng ảnh](DRIVE_UI_REVIEW_2026-10-30.md). Bộ ảnh gốc lưu `/home/thientran/naucoffee-ui-reference-drive-20261030`, không nằm trong Git. Không lưu signed URL/cookie/secret vào evidence.

## File và cách kiểm chứng

Customer: `drive-reference.css`, base/product/contact/policy/orders templates, related-products projection, orders filters/pagination. Staff: reference_views.kitchen, kitchen template, POS card metadata/template/site.js, queue filters, operations sidebar. Admin: reference_views.management/configuration,2templates,3routes và5tests mới. Source WIP cũ được giữ; không schema migration.

Website http://localhost:8000/ đã restart đúng process runserver do Codex mở (xác minh PID/cwd trước dừng), không kill tiến trình lạ. Các route mới: `/dashboard/kitchen/`, `/dashboard/manage/products/`, `/dashboard/manage/categories/`, `/dashboard/manage/promotions/`, `/dashboard/manage/customers/`, `/dashboard/manage/staff/`, `/dashboard/settings/store/` và5tabs còn lại. Yêu cầu đăng nhập đúng vai trò; Customer không vào Admin.

## Chưa nghiệm thu

Chưa khớp pixel toàn bộ31 ảnh; native product/user/voucher edit forms chưa thay hoàn toàn thành custom form; chưa cost schema/WEBprice/SKUrollout, expiry batch, HRbranches/avatar, timer/drag-drop/print/draft, theme/banner editor, email/SMS/push hoặc auto-backup/restore.6 config có trang đọc thật và link workflow đã có, không phải6form chỉnh sửa lưu được. Không có nút giả cho phần chưa triển khai. Maps online/physical devices/license/media persistence/publicHTTPS vẫnNOTRUN. Không claim31/31UI hoàn thiện hoặc12/12productionPASS.

---

# Khởi động local và đối chiếu ảnh — 30/10/2026

Nhánh `feature/cafe-premium-reference-20261028`, HEAD `6a10161` cùng patch local được giữ nguyên. Kết quả 127 PASS ngày 28/10 là lịch sử; dưới đây là kiểm tra thực của phiên mới.

| Kiểm tra | Kết quả thực tế |
|---|---|
| Git status/branch/HEAD/diff | Giữ 15 file tracked đang sửa và toàn bộ untracked đầu phiên; đúng nhánh/HEAD |
| Docker/ports trong sandbox | Permission denied/netlink; không suy ra cổng đang trống |
| Docker/ports ngoài sandbox, đã duyệt | PostgreSQL và pgAdmin đang Exited (255); cổng 8000/5432 trống |
| `docker start pg_lab_postgres` | PASS sau phê duyệt công cụ; chỉ bật container cũ, giữ DB/volume; pgAdmin vẫn dừng |
| `scripts/verify_databases.py`, `scripts/verify_django_database.py`, pg_isready | Ban đầu FAIL khi DB dừng; sau start PASS PostgreSQL 17, đúng dev/test identity, role hạn chế, không CONNECT chéo |
| `.venv/bin/python manage.py check` | PASS, 0 issues |
| `runserver 127.0.0.1:8000 --noreload` và ss | PASS, Python PID 3912; không dừng tiến trình lạ |
| `scripts/local_http_smoke.py` | 9/9 PASS, chỉ GET; không submit dữ liệu dev |
| Kiểm kê và xem ảnh gốc | 21/21 ảnh đọc được; 10 Customer, 5 Staff, 6 Admin; hai ZIP trùng SHA-256 |
| `manage.py test tests --settings=config.test_settings --keepdb --verbosity 1` | **114 PASS, 0 FAIL/ERROR/SKIP, 10.189s** |
| Browser lần đầu | 0 PASS, 13 ERROR, 11.545s; Chromium thiếu libnspr4, chưa kiểm tra được UI |
| Browser sau phục hồi runtime | **13 PASS, 0 FAIL/ERROR/SKIP, 92.812s** |
| Capture sau sửa tương phản | **1 PASS, 30.937s**; chạy lại bài có trong 13 browser tests, không cộng thành 128 |
| `makemigrations --check --dry-run --settings=config.test_settings` | PASS, No changes detected; không apply migration dev |
| `git diff --check` | PASS |

**127 test riêng biệt PASS trong hai lượt: 114 backend + 13 browser**, không mô tả là một lần chạy full suite. Tests ghi dữ liệu chỉ trên `nau_coffee_test` đã xác minh, role `nau_coffee_test_runner`, guarded runner và `--keepdb`. Các dòng seed trong output là fixtures của DB test. Không bootstrap, seed, migrate hoặc reset dev.

Browser đã exercise Customer đặt hàng/mock retry → Staff lifecycle → loyalty/review/Admin moderation, cart/logout/refund/delivery/shortage/POS và CRUD danh mục fixture mới. Giữ các assertion giá, tồn kho, quyền và payment.

```bash
NAU_QA_ROOT=docs/qa/2026-10-30 LD_LIBRARY_PATH=/tmp/nau-browser-libs/root/usr/lib/x86_64-linux-gnu CHROMIUM_PATH=/tmp/nau-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell .venv/bin/python manage.py test browser_tests --settings=config.test_settings --keepdb --verbosity 1
```

Chromium cũ trong `/tmp` đã mất sau reboot. Download trong sandbox lỗi DNS; ngoài sandbox được duyệt tải thành công. Tải ba gói `libnspr4 libnss3 libasound2t64` và giải nén vào `/tmp/nau-browser-libs`, không sudo/cài vào hệ thống. Helper kiểm kê ảnh ban đầu dùng system Python thiếu Pillow; chạy lại bằng `.venv` thành công. Không sửa dependencies hoặc skip tests để che lỗi.

## Thay đổi và bằng chứng

- Chỉnh `templates/commerce/cart.html`, `checkout.html`, `operations_base.html`, `templates/registration/login.html`, `static/catalog/premium-approved.css`.
- Cart có hero/summary kem; checkout thêm thumbnail lấy từ backend; login dùng ảnh minh họa và nút olive; Admin có shortcut danh mục/review/feedback/users hiện hữu. Sửa tương phản chữ Cart/Login sau khi xem ảnh QA.
- Không đổi views/services/models/migrations, POST fields, CSRF, idempotency, server quote, tồn kho hoặc RBAC trong phiên 30/10. Những local diff Python/Home/Menu trước đó được giữ nguyên.
- **51 màn hình/kích thước, 0 overflow, 151 liên kết nội bộ HTTP 200**. [Manifest và source hashes](qa/2026-10-30/manifest.json), [capture](qa/2026-10-30/after/manifest.json), [links](qa/2026-10-30/after/links.json). Giữ ảnh lịch sử 28/10.
- [Đối chiếu từng ảnh mẫu](REFERENCE_REVIEW_2026-10-30.md), [kiểm kê 21 ảnh](qa/2026-10-30/references.json). Admin có nhiều collage; không coi 21 ảnh là 21 trang đã nghiệm thu.

## Xác minh và giới hạn

Windows: http://localhost:8000/ hoặc http://127.0.0.1:8000/. Xem Home/Menu/Product/Cart/Checkout/Login ở 375/768/1440px. Dừng server an toàn bằng Ctrl+C tại terminal runserver. Server dùng `--noreload`; khi sửa Python cần restart đúng tiến trình đã xác minh.

Account demo hiện hữu có thể dùng để kiểm tra thủ công. Đặt đơn bằng tay sẽ ghi đơn demo vào dev; Codex không làm điều đó trong phiên này. Browser journey đã thử trên DB cách ly.

Chưa nghiệm thu: khớp toàn bộ mockup, full WCAG, điện thoại thật, Maps online, giá WEB/SKU/cost rollout, mọi Admin CRUD, Staff Kanban/shift/print/POS grid, media/license production và HTTPS/public smoke. Không claim 12/12 DONE. Không commit/push/merge/deploy.

---

# Nghiệm thu patch Café Premium — 28/10/2026 (Asia/Ho_Chi_Minh)

Nhánh thực `feature/cafe-premium-reference-20261028`, HEAD `6a101619ea484cd2e2c9dc3546d6280d0ef6cc24` + local diff chưa commit. Giữ các thay đổi có từ đầu phiên (catalog models/views, base/home/menu/card, foundation test, CSS và9 WebP). Không commit/push/merge/deploy hoặc ghi database phát triển.

## Giai đoạn 1 — Regression và Customer

- Empty menu thực tế là heading **“Chưa tìm thấy món phù hợp”**. Sửa expectation cũ “Không tìm thấy món”; bổ sung count0, page_obj rỗng, không có product-card và link xóa bộ lọc. Giữ assertion kết hợp search/category/price/sort cho TE02/TE01.
- Sửa header mobile grid, category label không co, CTA44px, cart SVG không phụ thuộc emoji font, POST logout desktop với CSRF. Giữ ảnh minh họa/giá WEB legacy từ backend.
- Browser selectors cập nhật theo ngữ nghĩa mới của menu/CTA/thông báo DEMO. Giữ mọi assertion tiền/stock/payment/roles và trạng thái rỗng, không skip bài lỗi.

## Giai đoạn 2 — Staff/Admin

- Sửa accessible navigation label và active Báo cáo; POS plus icon dùng ký tự có font fallback.
- Hồi quy thực Customer order/mock failure+retry, Staff lifecycle, loyalty/review→Admin moderation; cart update/remove/logout, refund, delivery/COD, shortage, options/filters/POS multi-line, role gates và Admin Category CRUD trên bản ghi test mới. Chưa chứng minh mọi form Admin CRUD.

## An toàn database và lệnh thực chạy

`config.test_settings` lấy `.env.test`, ghi đè biến môi trường dev; NAME/TEST.NAME=`nau_coffee_test`, USER=`nau_coffee_test_runner`. Guard bắt buộc keepdb, sequential,1 alias và xác minh current_database/current_user/role flags trước migrate. Không qua stock CREATE/DROP/clone runner; teardown đóng connection. TransactionTestCase cleanup và seed fixtures chỉ tác động DB test.

Truy vấn chỉ đọc thực trả `nau_coffee_test / nau_coffee_test_runner`, rolsuper=False, rolcreatedb=False, rolcreaterole=False; has_database_privilege cho CONNECT tới `nau_coffee_dev`=False. Không dùng connection dev để kiểm thử.

| Command/check | Kết quả |
|---|---|
| `.venv/bin/python manage.py check` và `check --settings=config.test_settings` | PASS0 issues |
| `manage.py test tests.test_foundation tests.test_database_safety --settings=config.test_settings --keepdb --verbosity 1` |23 PASS,0 FAIL/ERROR/SKIP,1.582s |
| Full127 đầu trên patch local |122 PASS,2 FAIL,3 ERROR,0 SKIP,174.782s; logout desktop thiếu + selectors/menu/navigation lệch |
| Full127 sau sửa lỗi |127 PASS,0 FAIL/ERROR/SKIP,109.536s |
| **Full cuối sau SVG/CTA/capture fix** |**127 PASS,0 FAIL/ERROR/SKIP,103.585s**;114 backend +13 Chromium tests |
| `manage.py makemigrations --check --dry-run --settings=config.test_settings` ngoài sandbox |PASS No changes detected; không sinh/apply migration dev |
| `git diff --check` |PASS |

Lượt trong sandbox lỗi kết nối PostgreSQL trước khi chạy test (0 executed), không coi là test FAIL logic hoặc PASS. Đã chạy lại ngoài sandbox bằng phê duyệt công cụ. Migration dry-run trong sandbox cảnh báo không đọc được history; đã chạy lại ngoài sandbox không cảnh báo. Không đổi role/container/cấu hình DB để vượt lỗi.

Lệnh full regression (môi trường browser local có sẵn):

```bash
NAU_QA_ROOT=docs/qa/2026-10-28-premium-regression LD_LIBRARY_PATH=/tmp/nau-browser-libs/root/usr/lib/x86_64-linux-gnu CHROMIUM_PATH=/tmp/nau-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell .venv/bin/python manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1
```

Kết quả cuối: **51 screens,0 overflow;151 links HTTP200**. [Manifest tổng + source hashes](qa/2026-10-28-premium-regression/manifest.json). Ảnh mới tại [capture manifest](qa/2026-10-28-premium-regression/after/manifest.json); [link audit](qa/2026-10-28-premium-regression/after/links.json). Không ghi đè ảnh Before/After lịch sử. Bộ hiện tại là regression screenshots, không gọi Before mới từ patch local chưa lưu snapshot ban đầu.

## Chủ dự án kiểm chứng

- Localhost `/menu/?q=missing`: heading rỗng + nút Xóa bộ lọc, không có card; bấm xóa thấy menu.
- 375/768/1440px: Home/Menu/Product/Cart/Checkout/Login; mobile menu mở/đóng bằng Escape, icon giỏ rõ; desktop Customer có POST Đăng xuất, logout xong route đơn cá nhân yêu cầu login.
- Staff `/dashboard/`, `/dashboard/orders/`, POS và kho; Admin `/dashboard/reports/` có active nav, Customer bị403 khi gọi route vận hành. Thử đặt đơn bằng browser test trên DB cách ly nếu không muốn thêm đơn vào dev.

## NOT RUN / chưa nghiệm thu

- Đối chiếu chính xác21 ảnh mẫu: thiếu đường dẫn bộ ảnh gốc; tài liệu reference chỉ mô tả bộ ảnh. Đã yêu cầu chủ dự án cung cấp đường dẫn. Không claim21/21 match.
- Điện thoại vật lý, full WCAG, Maps online, ảnh chụp chính thức/license/media bền, WEB pricing/SKU rollout, mọi Admin Image/Voucher/User CRUD và production HTTPS/deploy.
- Không có lỗi backend còn biết từ suite đã PASS; không suy rộng thành12/12 production DONE.

---

# Kiểm thử UI WIP local — 28/10/2026

## 28/10/2026 — WIP local Customer và Staff/Admin

Branch `wip/ui-redesign-local-20261027`, source bắt đầu `5d233a0`; kết quả local trước checkpoint, không phải kết quả CI trên commit mới. Django 5.2.18, Playwright 1.63.0, Chromium headless 153. Chỉ test DB `nau_coffee_test` bằng guarded runner và `--keepdb`; không migrate/seed/write dev, không reset/drop/clone DB/container. `seed_demo` trong output suite là fixtures hiện hữu chỉ ở DB test.

| Lệnh / giai đoạn | Kết quả thực chạy |
|---|---|
| `.venv/bin/python manage.py check` | PASS, 0 issues |
| Backend sau Customer UI: `manage.py test tests --settings=config.test_settings --keepdb --verbosity 1` | PASS 114/114, 10.481s |
| Before capture trên snapshot 5d233a0, cùng fixtures | PASS 1 capture test, 51 PNG, 15.505s; ghi nhận 1 overflow Admin catalog 768px |
| After capture đầu | FAIL 1 assertion: Admin 768px tràn ngang; đã sửa CSS tablet/sidebar |
| After capture sau fix | PASS 1 test, 51 PNG/0 overflow, 15.925s |
| Browser regression đầu sau WIP | 7 PASS/3 FAIL: assertion text cũ không còn khớp UI WIP (cart subtotal, order heading, payment label) |
| Browser suite sau semantic selectors/logout/POS tests | PASS 12/12, 71.066s |
| **Suite cuối `manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1`** | **PASS 127/127, 0 FAIL/0 ERROR/0 SKIP, 93.878s** |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py makemigrations --check --dry-run` | PASS, No changes detected (chỉ kiểm tra drift; suite chính dùng PostgreSQL) |
| `git diff --check` | PASS |
| HTTP GET localhost:8000 sau restart --noreload | PASS200; favicon mới + featured prices hiện diện trong HTML; không dùng GET cart/session hoặc submit vào DB dev |

Browser command dùng executable `/tmp/nau-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell` và `LD_LIBRARY_PATH=/tmp/nau-browser-libs/root/usr/lib/x86_64-linux-gnu`. Ban đầu FAIL setup do sai executable path/thiếu libnspr4/libnss3/libasound; đã tải runtime+ba thư viện riêng /tmp qua quyền được duyệt. Không tính các lỗi môi trường là browser PASS. Helper screenshot chỉ scroll ảnh hiển thị (auth artwork ẩn có chủ đích trên mobile); test broken-image/lazy-image vẫn giữ assertions thực.

Suite cuối gồm **114 backend + 13 browser tests**. Assertions về tổng tiền/payment/snapshot/stock/RBAC được giữ nguyên; text assertions cũ đổi sang vùng `.summary-total`/`.order-summary .status-badge` và heading WIP. Chạy lại toàn journey mua hàng→mock retry→Staff lifecycle→loyalty→review moderation; cart update/remove/logout; cancel/refund Admin; delivery verification/COD; shortage/cart preserved; manual APP/COUNTER không tự PAID; no-JS Maps fallback.

Các test mới kiểm tra: Home/Menu lấy cùng giá backend, GET không sửa giá; category link giữ q/min_price/sort và reset page; product POST contract/preview metadata; mobile touch CTA 44×44, checkbox SUGAR một lựa chọn, topping preview vs tổng server; Escape mobile nav; POS bắt đầu một dòng, thêm/bớt/reindex, options chỉ thuộc món, đổi kênh giữ giá backend; Admin Category create/update/delete **chỉ category fixture mới trong DB test** và giữ count Product.

**Bằng chứng:** [manifest tổng](qa/2026-10-28/manifest.json), [before 51 PNG](qa/2026-10-28/before/manifest.json), [after 51 PNG](qa/2026-10-28/after/manifest.json), [152 internal links HTTP200](qa/2026-10-28/after/links.json). 17 screens × 375/768/1440 mỗi bản, bao gồm Home/Menu/Product/Cart/Checkout/Login và account/operations. Trình duyệt là headless thật; không phải điện thoại vật lý hoặc xác nhận thẩm mỹ của chủ dự án. Giá trong screenshot là fixtures legacy, không phải giá WEB đã được duyệt.

**NOT RUN / chưa đủ:** điện thoại thật, online Maps/địa chỉ đã xác nhận, production URL/HTTPS/persistence, screenshot dữ liệu menu 25/10 đã rollout, ảnh 8 món/license/durable media, mọi nhánh Admin Image/Voucher/User CRUD. Native Admin Category CRUD không thay cho toàn bộ REQ-12. Không đánh dấu 12/12 nghiệm thu production.

> **Lịch sử phiên 13/10/2026:** suite khi đó đạt 57 PASS, 2.562s, chưa chạy browser QA. Kết quả hiện hành ngày 28/10 là 127/127 PASS được ghi ở đầu báo cáo; không dùng con số lịch sử này làm trạng thái mới nhất.

---

# UI/UX sau đồng bộ tài liệu menu — 27/10/2026

Nhánh `feature/sprint-3-4`; base CI `473d23b`. Đã fetch và merge an toàn `origin/main` (`939e642` → `11ee3b1` → `737efdc`) bằng merge commit `0bf94b7`, giữ cả hai parent, không sửa `main` hoặc force-push.

## Những thay đổi đã kiểm thử

| Phạm vi | Kết quả thực tế |
|---|---|
| Checkout giỏ trống | GET có empty state, link chọn món/giỏ hàng, không hiện form thanh toán/đặt đơn hoặc lỗi quote thừa; bỏ món cuối quay checkout đúng empty state. Giữ nguyên POST service/idempotency/RBAC |
| Nguyên liệu mobile | Bảng có caption/scope, 375px thành thẻ với nhãn tồn/ngưỡng và cảnh báo; 768/1440px giữ bảng. Staff không có nút ghi khi chưa được cấp quyền; đọc UI không tạo stock movements |
| APP/COUNTER | Form chia nhóm, labels/errors/management form/token giữ nguyên; JS bắt buộc reference khi chọn APP, thông báo theo kênh. Tạo 2 món CF02 fixture: APP70.000đ, COUNTER60.000đ; backend giữ UNPAID và BOM snapshot. Đây là giá seed cũ, không phải bảng giá mới |
| Maps fallback | Link dự phòng và nhãn vị trí minh họa luôn hiện; iframe chỉ yêu cầu Google khi người dùng mở details. Browser chủ động abort Google vẫn sử dụng được trang/fallback ở 3 widths; context tắt JS vẫn có link và hướng dẫn. Maps online chưa nghiệm thu |
| Header/menu/khung điều hành | Mobile menu thao tác được, aria-current theo trang; sidebar espresso/olive dùng chung Staff/Admin, link báo cáo/quản trị theo vai trò, backend RBAC không đổi |
| VND/khả năng đọc | Grouping `30.000 đ`, zero/large/integer Decimal; không làm tròn giá lẻ/invalid âm thầm. Menu/product/cart/checkout/order/payment/report cùng filter hiển thị. Giữ nguyên input values, CSV và server pricing. Sửa block title product vốn chứa lặp HTML review |

## Lệnh và kết quả cuối

Môi trường mới: Python3.12.14, Django5.2.18, PostgreSQL17.11, Chromium154.0.8037.57, Playwright1.63.0. Môi trường không còn DB hoặc secrets của phiên21/10; không lấy dữ liệu/credentials laptop.

| Check | Kết quả |
|---|---|
| Preflight DB | PASS actual identity nau_coffee_test/nau_coffee_test_runner, NOSUPERUSER/NOCREATEDB/NOCREATEROLE, PostgreSQL17; không có nau_coffee_dev trong cluster |
| `python -m pip check` | PASS |
| `manage.py check --settings=config.test_settings` | PASS, 0 issues |
| `manage.py makemigrations --check --dry-run --settings=config.test_settings` | PASS, No changes detected |
| `manage.py collectstatic --noinput --settings=config.test_settings` | PASS |
| `node --check static/catalog/site.js` | PASS |
| `manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 2` | **120 PASS / 0 FAIL / 0 SKIP, 118.568s**: 111 backend +9 browser; 4 PostgreSQL concurrency tests |
| Browser QA | 30 PNG mới =10 màn hình/trạng thái ×375/768/1440; suite cũ48 page/width +2 trạng thái cũng PASS, tổng80 PNG của lần chạy cuối |

Bằng chứng mới: [raw regression](qa/2026-10-27/regression.txt), [checks](qa/2026-10-27/django-checks.txt), [manifest/source hashes](qa/2026-10-27/manifest.json). Ví dụ: [checkout trống375](qa/2026-10-27/ui-375-checkout-empty.png), [kho375](qa/2026-10-27/ui-375-inventory-staff.png), [APP768](qa/2026-10-27/ui-768-manual-app.png), [checkout1440](qa/2026-10-27/ui-1440-checkout-filled.png). Chụp cả Django Admin catalog, nhưng không tuyên bố đã thay thế Admin CRUD bằng UI mockup mới.

Các lượt chưa đạt trước đó được phân biệt: focused9 có1 error do dùng viewport ở BrowserContext.new_page; đã chuyển viewport về new_context. Lượt Maps riêng1 có1 failure ở kỳ vọng noscript; hướng dẫn fallback được render thường để không phụ thuộc JS/parser, context tắt JS sau đó PASS. Full120 đầu có1 failure do test cũ tìm “Giỏ hàng trống” thay vì heading mới “Giỏ hàng đang trống”; cập nhật expectation giữ nguyên kiểm tra trang và chạy lại full120 đạt như bảng. Không skip hoặc xóa assertion ảnh/RBAC/giá/stock.

## Dữ liệu, menu và giới hạn nghiệm thu

Đối chiếu [8 món/13 SKU](MENU_RECONCILIATION_2026-10-27.md) hoàn tất ở mức source/schema. Chưa có DB phát triển để kiểm kê thực; chưa áp dụng menu25/10, chưa thêm cost field hoặc giá WEB mới. Models/migrations/seed và các services pricing/payment/stock/BOM giữ nguyên so với473d23b. Chỉ sau đối chiếu mới tạo container test PostgreSQL17 riêng, port127.0.0.1:5432, secrets mới .env.test0600; Django test runner áp dụng schema/fixtures chỉ trên DB test này. Không manual migration/seed/reset/flush development hoặc laptop, không phục hồi backup cũ tự động.

Issue#2 và GitHub Actions API trả Forbidden. Phạm vi UI lấy từ yêu cầu trực tiếp ngày27/10; chưa đọc được toàn bộ Issue nên chưa đóng/tuyên bố hoàn tất Issue. GitHub111/111 tại473d23b là kết quả chủ dự án xác nhận; CI của commit mới chưa được xác minh, không dùng cloud120/120 thay cho GitHub CI PASS.

Thiếu ảnh tham chiếu Customer/Menu, Staff/POS, Admin25/10 và ảnh8 món/quyền sử dụng; chỉ kiểm tra theo mô tả Café Premium, không claim khớp mockup. Giá WEB, mapping/version SKU/size/options, cost schema/BOM và quy trình cập nhật DB cần phê duyệt riêng. Chưa nghiệm thu Maps online/physical devices/public HTTPS/deploy. Không có dịch vụ trả phí hoặc public deployment.

---

# Khắc phục browser lazy-image check — 21/10/2026

Base source `5b4b081`; nhánh `feature/sprint-3-4`, Draft PR #1. Run GitHub [39560813302](https://github.com/dauiudau11-cpu/NauCoffee-V3/actions/runs/39560813302) có 1/110 failure theo log chủ dự án cung cấp: assertion ảnh ngay sau navigation tại `/`, viewport 768px. Các kết quả GitHub dưới đây không được suy ra từ kết quả cloud.

## Chẩn đoán và cách sửa

- Trang chủ nguyên bản ở 768×1000: 30/30 lượt assertion cũ PASS tại cloud. Không tái hiện chính xác timing của CI. Chromium cloud 154.0.8037.57 / Playwright 1.63.0; tải Chromium pin như CI bị network proxy chặn HTTP 403, không bypass TLS/network policy.
- 5 thẻ img trang chủ đều dùng `/static/catalog/drink.svg`; 4 thẻ có `loading="lazy"`. Ảnh trả HTTP 200, naturalWidth=480, không tìm thấy ảnh sản phẩm hỏng. Console 404 ban đầu thuộc `/favicon.ico`, không thuộc document.images.
- Fixture kiểm soát tại 768×1000, dùng chính static SVG với URL chưa cache và ảnh nằm ngoài ngưỡng lazy-load: assertion cũ FALSE, `complete=false`, `naturalWidth=0`, chưa có HTTP image response. Sau scroll vào viewport: HTTP 200, complete=true, naturalWidth=480. Đây là tái hiện có kiểm soát của thiếu đồng bộ lazy-load; không khẳng định đã quan sát đúng trạng thái thất bại trong GitHub run cũ.
- `page.goto()`/load event không bảo đảm native lazy images đã tải. Test mới scroll từng img vào viewport, chờ `complete=true` tối đa 10 giây, kiểm tra naturalWidth>0 và giữ nguyên assertion tổng hợp ban đầu. Scroll lại đầu trang trước screenshot. Không thêm sleep, không xóa assertion, không skip/retry toàn bài.
- Regression bổ sung xác nhận lazy image tải thành công và helper vẫn ném AssertionError cho ảnh HTTP 404 thật (`/static/catalog/missing-regression-image.svg`). Không đổi templates, nguồn ảnh, static/media config, business logic hoặc migrations.

## Kiểm thử thực tế tại cloud

| Kiểm tra | Kết quả |
|---|---|
| Preflight actual DB/version/role | PASS PostgreSQL 17; nau_coffee_test / nau_coffee_test_runner; NOSUPERUSER, NOCREATEDB, NOCREATEROLE |
| `manage.py check --settings=config.test_settings` | PASS, 0 issues |
| `manage.py makemigrations --check --dry-run --settings=config.test_settings` | PASS, No changes detected |
| `manage.py collectstatic --noinput --settings=config.test_settings` | PASS, 129 unchanged |
| Focused lazy + broken image regression | PASS 1/1, 1.664s |
| `manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 2` | **111 PASS / 0 FAIL / 0 SKIP, 40.978s**, 106 backend +5 browser, gồm 4 PostgreSQL concurrency cases |
| Responsive journey | PASS 375/768/1440px; 48 page/viewport checks, 50 screenshots kể cả 2 trạng thái commerce |

Bằng chứng: [diagnostic-768.json](qa/2026-10-21-lazy-images/diagnostic-768.json) chứa thẻ img, URL chuẩn hóa, loading/complete/naturalWidth, HTTP và console; [ảnh trang chủ 768](qa/2026-10-21-lazy-images/home-768.png); [raw regression log](qa/2026-10-21-lazy-images/regression.txt). Fixture broken-image tạo 404 có chủ đích, được tách rõ khỏi trang chủ.

Chỉ test DB riêng được kết nối và ghi test fixtures. Không bootstrap/reset hoặc kết nối database phát triển/laptop. Workflow CI không đổi: PostgreSQL17 service dùng một lần, secrets mới, không dùng dev/repo credentials cho PR, role giới hạn, preflight trước migrations, `--keepdb`, không dùng pull_request_target. GitHub Actions API trả Forbidden trong môi trường cloud; CI sau push cần kiểm tra thực tế, chưa được ghi PASS. Không merge/deploy.

---

# Kiểm thử milestone checkout/BOM — 21/10/2026

Python3.12.14, Django5.2.18, PostgreSQL17.11, Chromium154/Playwright1.63.0; DB test riêng/role giới hạn được kiểm tra identity/isolation trước khi chạy. Baseline ở các mục dưới được giữ làm lịch sử, không nhầm với lần chạy mới này.

| Kiểm tra đã chạy | Kết quả |
|---|---|
| `manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1` | **110 PASS, 0 FAIL, 0 SKIP, 38.368s**; 106 backend +4 browser journeys, bao gồm4 real PostgreSQL race tests |
| Checkout inventory tests mới | 10 PASS: stock thiếu/tổng nhiều dòng, không trừ lúc checkout, không tin client snapshot, recipe edit không đổi đơn cũ, topping snapshot, thiếu recipe/inactive, unit change block, legacy audit, corrupt snapshot fail closed, manual channels |
| Browser journeys bổ sung | PASS cart update/remove, paid mock cancel→Admin refund, logout, shortage error/cart preservation, custom slot delivery+zone verification, COD thu sau completed, loyalty ship-excluded |
| Responsive/artifacts | PASS48 page/width checks từ16 trang×3 widths, thêm2 state screenshots/375px (checkout thiếu kho và delivery complete), tổng50PNG; manifest/source hashes giữ trong docs/qa/2026-10-21 |
| `manage.py check`; `makemigrations --check --dry-run` | PASS0 issues; No changes detected |
| `sqlmigrate commerce 0003`; migration dev | Chỉ `ADD COLUMN recipe_snapshot jsonb NULL`; apply PASS, không DROP/reset/bootstrap hoặc seed lại dev |
| Dữ liệu trước/sau migration | Read-only fingerprint các model records business/account cũ (loại cột mới) khớp; backup trước/sau giữ riêng; verify_demo PASS8/13/39/3 |
| `scripts/local_http_smoke.py` sau restart mới | **9/9 PASS**, home/menu/product/auth/promotions/health/static |

Raw run: [regression.txt](qa/2026-10-21/regression.txt). [Manifest và source hashes](qa/2026-10-21/manifest.json). Hai ảnh trạng thái mới: [thiếu kho](qa/2026-10-21/375-checkout-shortage.png), [giao hàng COD hoàn tất](qa/2026-10-21/375-delivery-completed.png). Dữ liệu/account trong browser đều giả lập ở DB test; không tạo user/order dev từ QA.

Hai lần browser mới ban đầu báo strict locator trùng text/field trong thông báo+audit và trong hai forms. Đã scope locator theo .notice và accessible label; rerun nhánh delivery PASS1/1, sau đó full110 PASS. Không tắt assertions hoặc bypass auth/async safety để làm test đạt.

Giới hạn: kiểm tra tồn tại thời điểm đặt không phải reservation; hai đơn có thể cùng đạt khi còn nguyên liệu, kiểm tra lại lúc PREPARING ngăn âm kho. Recipe edits đã được cách ly với đơn mới bằng snapshot; legacy NULL không có lịch sử công thức checkout nên được ghi audit khi chốt lúc pha. Online Maps/ảnh thật/production/public HTTPS/GitHub CI vẫn NOT RUN; GH007 chưa xử lý, chưa push mới. Không tự nhận DONE toàn MASTER_SPEC.

---

# Checkpoint kiểm thử & bảo toàn — 18/10/2026

- Baseline application commit `9174433`: **90/90 PASS**, 0 FAIL/0 SKIP; có 4 real PostgreSQL concurrency tests. Đây là lần chạy đã ghi trong báo cáo phía dưới, không chạy lại trong checkpoint.
- Browser mở rộng trước đó: 1 PASS, 16.438s, 48 screenshots/geometry checks (16 pages × 375/768/1440), source9174433; giữ manifest và sáu ảnh mẫu ở `docs/qa/2026-10-18`, archive48 ngoài checkout. Maps bị chặn chủ động để thử fallback, không claim online Maps PASS.
- Tái lập source git archive9174433, chỉ bổ sung CI helper + 7 safety tests mới, trong venv/PostgreSQL17 mới không mở host port, không DB/credentials phát triển: identity/privilege preflight PASS, Django check PASS, migration drift PASS, **96 backend tests PASS / 0 FAIL / 0 SKIP (8.063s)**. Không chạy browser trong instance độc lập này. Log `docs/qa/2026-10-18/independent-regression.txt`.
- CI bootstrap safety unittest: 7/7 PASS; workflow actionlint1.7.7 PASS (artifact checksum verified). GitHub Actions chưa chạy, không báo CI cloud/GitHub97 PASS.
- Không reset/bootstrap/migrate/seed DB hiện có theo yêu cầu checkpoint; CI instance tạm đã dừng, không xóa dữ liệu.
- Git/security: commit9174433 tồn tại, lịch sử không shallow và bundle verified; 125 blobs lịch sử gốc quét không thấy secrets cloud thực hoặc file env/dump/key bị commit. Đường dẫn WSL cá nhân lịch sử đã chuẩn hóa ở bản hiện tại, lịch sử giữ nguyên. Fixture credentials không phải credentials dev.
- Chưa push/PR/merge/public deploy. Private repo còn chưa xác minh API (Forbidden). Xem CHECKPOINT.md và ACCEPTANCE_MATRIX.md để tiếp tục; mọi tiêu chí nghiệm thu còn chờ chủ dự án.

---

# Cloud validation — 18/10/2026 (Asia/Ho_Chi_Minh)

Trạng thái mới nhất của phiên Codex Cloud; các báo cáo WSL phía dưới là lịch sử. Base source `2e0681d7903d7f47f41239ac421e77ef845c4987`, nhánh `codex/cloud-sprints-3-4`. Không có URL production hoặc public deployment.

Môi trường: Python 3.12.14, Django 5.2.18, PostgreSQL 17.11, Playwright 1.63.0, Chromium 154. App/dev và test dùng DB/role riêng, loopback; không kết nối laptop. Kiểm tra quyền/identity hoàn tất trước migrations/tests. Không sử dụng superuser làm app/test runner, không CREATE/DROP/clone test DB từ Django.

| Lệnh / kiểm tra | Kết quả thực tế |
|---|---|
| Install `requirements.lock`, sau đó Playwright + pinned dev dependencies | PASS; `pip check` không có lỗi |
| Fallback SQLite trước provisioning | 57 discovered: 55 PASS, 2 SKIP (row locks), không coi là PostgreSQL PASS |
| `scripts/verify_databases.py` + `scripts/verify_django_database.py` | PASS PostgreSQL 17, role giới hạn, không CONNECT chéo |
| `manage.py migrate --noinput` trên dev | PASS toàn bộ migrations, gồm catalog 0003 / commerce 0002 / support 0002 |
| `seed_demo` lặp + `verify_demo` | PASS 8 products / 13 SKUs / 39 channel prices / 3 roles; không duplicate hoặc ghi đè giá; BOM/options/tồn đầu thêm theo key idempotent |
| `manage.py check` | PASS, 0 issues |
| `manage.py makemigrations --check --dry-run` | PASS, No changes detected |
| `DJANGO_DEBUG=False manage.py check --deploy` | PASS, 0 issues; kiểm tra cấu hình, không chứng minh HTTPS thực |
| `manage.py collectstatic --noinput` | PASS |
| `manage.py test tests browser_tests --settings=config.test_settings --keepdb --verbosity 1` | **90 tests PASS, 21.787s, 0 FAIL, 0 SKIP**; 89 backend/DB + 1 browser journey |
| Browser suite mở rộng Admin moderation + Staff/Admin responsive, chạy riêng sau đó | **1 PASS, 16.438s**; không cộng thành 91 distinct tests |
| `scripts/local_http_smoke.py` sau restart web | **9/9 PASS** (home/menu/product/login/register/promotions/health/static CSS/SVG) |
| Gunicorn 2 worker loopback: health/menu/static/contact | **4/4 PASS**, status 200 và expected body markers; dùng development settings, không claim public production |
| Backup/restore vào PostgreSQL kiểm chứng riêng | PASS cả dev/test: identity, privileges/isolation, migrations và selected table counts; original DB/volume giữ nguyên; containers kiểm chứng đã dừng |
| File permissions + ignore + scan private values | `.env`, `.env.test`, admin credential file, archives đều 0600; Git ignore đúng; không in secret values |
| `git diff --check` | PASS |

Artifacts: `test-results/cloud-20261018-full.log`, `test-results/cloud-20261018-browser.log`, `test-results/browser/*.png` (ignored, hiện có trong workspace). Log không chứa passwords; dữ liệu Customer/Staff/Admin trong browser chỉ tồn tại ở DB test và được test runner cleanup, không tạo account demo/password dev.

## Phạm vi đã exercise

- **4 PostgreSQL race tests thực**: cùng checkout key chỉ một order; voucher lượt cuối một redemption; ly cuối không bị tiêu hao hai lần; slot cuối không đặt hai lần.
- Support: validation, honeypot/throttle, CSRF, contact/feedback lưu DB, ownership mã đơn; review owner/completed/matching product/rating/uniqueness, pending moderation, HTML escape; staff không có quyền Admin.
- Operations: BOM × số lượng, retry không trừ lần hai, thiếu kho rollback/status giữ nguyên; HTTP từ chối lưu audit; topping tiêu hao và missing BOM chặn; stock role/idempotency/no-negative; lịch hours/lead/horizon/grid/capacity; delivery distance/permission/audit; loyalty completion+payment đúng một lần; APP/COUNTER channel price/reference/idempotency/reconcile; Admin report dates/channel/totals/cancel/CSV không PII.
- Accounts: profile whitelist không nâng role; đổi mật khẩu; address create/edit/delete own-only + CSRF; checkout saved-address không nhận address của người khác; login/register throttle; Policy Admin text được escape.
- Browser: Customer register/login → search → product/cart → checkout → mock failure/retry success → Staff lifecycle → loyalty → review pending → **Admin duyệt trong Django Admin UI thật** → approved review xuất hiện → contact submit → Staff nhập APP từ formset. Không vô hiệu async safety của Django; ORM verification đi qua thread đồng bộ riêng.
- **48 responsive page checks/screenshots**: 12 storefront/account pages + 3 Staff pages (queue/inventory/manual) + 1 Admin report, mỗi trang ở 375/768/1440. Không document overflow ngang; ảnh nội bộ của storefront tải được; mobile menu mở được. Bảng kho/report cuộn trong container khi cần. Không coi đây là QA mọi kích thước/thiết bị vật lý.

## Lỗi gặp trong quá trình triển khai và xác minh lại

- Report aggregate alias `discount` trùng field gây FieldError: sửa thứ tự biểu thức net; report totals/CSV tests PASS.
- Playwright sync API tạo event loop, ORM trực tiếp bị Django chặn: chuyển ORM assertions sang thread riêng, không tắt safety guard; browser journey PASS.
- Throttle trả form unbound khiến `add_error` thiếu cleaned_data: dùng form bound với dữ liệu trống, không chạy xác thực credentials sau ngưỡng; throttle test PASS.
- Lần đối chiếu backup DB test đầu tiên diễn ra trong khi fixtures đang thay đổi nên count mismatch; không tuyên bố restore đầy đủ PASS lúc đó. Chạy lại backup/restore và đối chiếu khi tests đã dừng: cả hai DB PASS trên instance mới.

## NOT RUN / chưa nghiệm thu

- Ảnh chụp sản phẩm/licensing REQ-05: hiện SVG fallback. Request ảnh ngoài nhận proxy 403; đã lưu domains vào draft, chưa xác minh runtime được áp dụng.
- Google Maps online: có iframe + vị trí minh họa + fallback; browser suite cố ý chặn Google. Chưa claim Maps tải thật PASS.
- Public URL/HTTPS, cross-network smoke, provider restart/media persistence; chưa phê duyệt triển khai.
- Fresh-task snapshot/Publish restoration; chỉ restore archive vào instance khác trên cùng cloud machine được xác minh.
- Word/PPTX/ZIP nhóm chính thức: thiếu số nhóm, thành viên/tỷ lệ, URL production và gate P0; chưa phát hành.

Không gọi toàn bộ Sprint 3/P0/P1 hoặc website hoàn thành 100%. Đây là bằng chứng môi trường phát triển và các luồng đã kiểm thử, không phải nghiệm thu production.

---

# Kết quả kiểm thử thực tế


Ngày: 13/10/2026. Environment Ubuntu WSL2, Python 3.14.4; không có Git commit khả dụng. URL public: chưa deploy.

## Sprint 0

| Command | Kết quả |
|---|---|
| `pwd`, `ls -la`, `rg --files` | PASS khảo sát: chỉ có hướng dẫn/đặc tả |
| `git status --short` | FAIL: `.git` không phải repository khả dụng |
| `python3 --version` | PASS: 3.14.4 |
| `python3 -m pip --version` | FAIL: No module named pip |
| `python3 -c "import django"` | FAIL: No module named django |
| `python3 -m venv .venv` | FAIL: ensurepip not available; `.venv` tạo dở |
| `docker ps`, `docker port pg_lab_postgres` (sandbox) | FAIL: permission denied Docker socket |
| `docker ps --format '{{.Names}} {{.Image}}'` (approved read-only) | PASS: pg_lab_postgres postgres:17 |
| `sudo apt-get update` | FAIL: terminal required to authenticate |
| `dpkg-query -W` sau khi chủ dự án cài apt | PASS: python3-pip, python3-venv, python3.14-venv installed |
| `python3 -m venv .venv` sau apt | PASS |
| `.venv/bin/python -m pip install -r requirements.txt` sandbox | FAIL: DNS / Name or service not known |
| pip cài có quyền mạng, lần đầu | FAIL: tải Django bị timeout/incomplete-download |
| `.venv/bin/python -m pip install --no-cache-dir --timeout 180 --resume-retries 5 -r requirements.txt` | PASS: installed trong .venv, Django 5.2.18 / psycopg 3.3.6 |

## Sprint 1

Bộ test đã viết kiểm tra seed idempotency, filter/sort, sale windows/constraints, inactive items, registration/RBAC, logout, CSRF/XSS escaping và safe login redirect. Không tính test chưa chạy là PASS.

| Kiểm tra | Trạng thái |
|---|---|
| `python3 -m compileall -q config catalog tests manage.py` | PASS: cú pháp Python |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py check` | FAIL khởi động: No module named django |
| Django generate migration | NOT RUN: chờ Django |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py test tests --verbosity 2` | FAIL khởi động: No module named django; 0 test executed |
| PostgreSQL migrations/test suite | NOT RUN: DB/user riêng chưa thiết lập |
| Browser responsive / E2E | NOT RUN |
| Production smoke / restart persistence | NOT RUN: chưa duyệt deploy |

### Chạy lại sau khi apt/dependencies đã cài

| Command | Kết quả thực tế cuối |
|---|---|
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py makemigrations catalog` | PASS: sinh 0001_initial, 5 models và constraints |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py check` | PASS: System check identified no issues (0 silenced) |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py test tests --verbosity 2` | PASS: Found 12 tests, Ran 12 tests in 0.810s, OK, exit 0 |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: No changes detected |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py collectstatic --noinput` | PASS: 129 static files copied |
| `.venv/bin/python -m pip check` | PASS: No broken requirements found |

12 tests PASS: seed idempotency/preserve edits, public pages, combined filters/sort/empty results, active/expired sale & price filtering, invalid sale DB constraint, inactive category/SKU, registration hash/role injection, group gate vs is_staff, logout/account access, CSRF/escaped script, safe next redirect, disguised image rejection. Đây là integration tests trên SQLite in-memory, migrations auth/admin/catalog/sessions thực sự được áp dụng trong test DB.

Cảnh báo lần test: WhiteNoise chưa có staticfiles directory; sau đó collectstatic thành công. Pip có cảnh báo cache không writable nhưng cài vào `.venv` thành công; không cài project libraries vào Python hệ thống.

Known limitations: PostgreSQL tests NOT RUN; chưa checkout/cart/payment; ảnh đồ uống là placeholder; chưa đủ 12/12. Không có bằng chứng UI screenshot hay cloud smoke. Không xác nhận hoàn thành Sprint 1 theo gate đầy đủ.

## Rà soát bootstrap/Test Runner — trước thực thi

Ngày: 13/10/2026. Chưa chạy bootstrap do chủ dự án yêu cầu kiểm tra/báo cáo trước khi chạy. Lệnh bootstrap gửi trước đó bị từ chối quyền thực thi; không tạo DB/role/env.

| Command / check | Kết quả |
|---|---|
| Docker exec psql read-only có cấp quyền: server_version + existence nau_coffee_dev | PASS: 17.9, database chưa tồn tại |
| `id`, `stat /var/run/docker.sock`, `docker ps` sandbox | FAIL truy cập Docker: permission denied; socket 660 nobody:nogroup |
| `.venv/bin/python -m unittest tests.test_database_safety -v` | PASS: 11 tests, 0 FAIL, 0.008s |
| `python3 -m compileall -q scripts config commerce catalog tests` | PASS |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py check` sau safety changes | PASS: 0 issues |
| File existence check chỉ in boolean | PASS: .env=False, .env.test=False; không đọc/in secrets |
| `.gitignore` pattern safety test | PASS: .env và .env.test ignored; .env.example exception |
| Live bootstrap / DB permission isolation / PostgreSQL migrations | NOT RUN: chờ review bootstrap |
| Full foundation/commerce suite sau schema mới | NOT RUN: schema/services/migrations vẫn đang triển khai |

Safety tests cover: đúng pre-created test target; từ chối dev/old DB/superuser/app role/host khác; bắt buộc keepdb và cấm parallel; SQLite in-memory only; mock runner chỉ migrate test, không create/drop; suppress SQL secrets; ignore files; Docker deny không tạo gì; partial failure báo role đã tạo/last attempt, giữ env 0600 và không cleanup; resources tồn tại không sửa.

Giới hạn: 11 tests là unit tests/mocks kiểm tra hàng rào an toàn, không chứng minh live PostgreSQL grants hoặc migrations PASS. Các kết quả 12 PASS của phiên trước là lịch sử, không phải xác nhận suite hiện tại sau schema commerce.

## Kết quả mới nhất — bootstrap của chủ dự án và migrations tách bước

Ngày: 13/10/2026. Không có commit Git khả dụng; URL public chưa triển khai. Bootstrap thành công do chủ dự án báo qua Terminal Ubuntu, không chạy lại bởi Codex.

| Command / check (mỗi thao tác riêng) | Kết quả |
|---|---|
| `scripts/verify_databases.py` sandbox | FAIL kết nối, chi tiết suppressed |
| `.venv/bin/python scripts/verify_databases.py` ngoài sandbox approved | PASS: 2 DB, riêng role, PostgreSQL 17, no cross CONNECT |
| `.venv/bin/python manage.py check` | PASS: 0 issues |
| `.venv/bin/python scripts/verify_django_database.py` approved read-only | PASS: actual Django connection nau_coffee_dev/nau_coffee_app |
| `.venv/bin/python manage.py showmigrations --plan` approved read-only | PASS: 21 unapplied migrations |
| `.venv/bin/python manage.py migrate --noinput` phê duyệt riêng | PASS: 21 migrations OK trên nau_coffee_dev |
| SQLite full suite đầu sau schema | FAIL: 34 tests, 30 PASS, 1 FAIL, 3 ERROR |
| SQLite full suite sau fix | PASS: 34/34, 0.883s |
| SQLite full suite sau bổ sung introspection + Staff role POST test | PASS: 36/36, 0.945s |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: No changes detected |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py test tests.test_seed_safety tests.test_database_safety --verbosity 1` sau seed guard | PASS: 14/14, 0.006s; không seed hoặc kết nối database |
| `seed_demo` trên nau_coffee_dev | NOT RUN: chờ xác nhận riêng của chủ dự án |
| PostgreSQL integration suite --keepdb | NOT RUN |

Fix: login signal gán request.user từ user đã xác thực (Django test login request không có AuthenticationMiddleware). Assertion OneToOne refresh order sau lần tạo payment trùng thất bại để bỏ reverse cache của object chưa lưu.

Schema tests cover tất cả 10 commerce models + options M2M; introspect named constraints; owner XOR; cart quantity/config uniqueness; merge login một lần; options thuộc đúng product; tổng tiền/discount/user WEB; order idempotency/snapshots/PROTECT; order-item qty/line; payment OneToOne/event unique/history actor; voucher case-insensitive uniqueness/bounds/date/usage limits; redemption OneToOne/PROTECT; Staff không POST nâng quyền admin. Các kết quả schema này hiện là SQLite fallback, chưa phải PostgreSQL PASS.

Migrations dev PASS không đồng nghĩa seed hoặc PostgreSQL integration suite PASS. Full suite chưa chạy lại sau seed target guard mới; chỉ safety suite 14 tests đã chạy ở revision hiện tại. Chưa hoàn thành gate Sprint 1 hoặc triển khai Internet.

## Sprint 1 — Seed và PostgreSQL thực tế

Ngày 13/10/2026, Django 5.2.18/Python 3.14.4/PostgreSQL 17. Dedicated database nau_coffee_test, role nau_coffee_test_runner NOCREATEDB. Runner tự kiểm tra identity, chỉ migrate DB đã tạo sẵn, không create/drop/clone, teardown chỉ đóng connection. TestCase rollback và TransactionTestCase cleanup chỉ trong DB test; --keepdb giữ schema/database.

| Command | Kết quả |
|---|---|
| `.venv/bin/python manage.py seed_demo` (được xác nhận riêng) | PASS: 8 products / 13 SKUs, dữ liệu hiện hữu giữ nguyên |
| `.venv/bin/python manage.py verify_demo` | PASS: 8 products / 13 SKUs / 39 prices / 3 roles, quan hệ đúng/không duplicate |
| `.venv/bin/python manage.py test tests --settings=config.test_settings --keepdb --verbosity 2` lần đầu | FAIL setup: 0 executed, runner từ chối parallel=0 mặc định của Django |
| Cùng lệnh sau fix runner nhận parallel 0/1 | PASS: 39 tests, 1.258s, 0 FAIL; 21 migrations DB test OK |

Fix runner: Django DiscoverRunner mặc định `parallel=0` nghĩa là sequential. Guard cũ chỉ nhận 1 nên từ chối nhầm. Cho phép 0/1 và vẫn từ chối >1; thêm assertion unit cho 0. Không thay quyền role, không tạo lại DB.

## Sprint 2 — Commerce flow và concurrency

| Command | Kết quả |
|---|---|
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py test tests --verbosity 1` trước bổ sung race tests | PASS: 55 tests, 1.461s (fallback) |
| `.venv/bin/python manage.py test tests --settings=config.test_settings --keepdb --verbosity 2` | PASS: 57 tests, 2.613s, 0 FAIL, 0 SKIP |
| `.venv/bin/python manage.py test tests --settings=config.test_settings --keepdb --verbosity 1` sau thêm Barrier cho race tests | **PASS cuối: 57 tests, 2.562s, 0 FAIL, 0 SKIP** |
| `.venv/bin/python manage.py check` | PASS: 0 issues |
| `NAU_TEST_SQLITE=True .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: No changes detected |
| `.venv/bin/python manage.py collectstatic --noinput` | PASS: 1 file copied / 128 unmodified |
| `.venv/bin/python manage.py verify_demo` sau suite cuối | PASS: 8/13/39/3, không duplicate, dev demo vẫn đúng |

Suite 57 gồm 43 tests catalog/auth/schema/commerce integration hoặc concurrency với DB PostgreSQL thật và 14 safety unit tests/mocks. Hai concurrency tests dùng connection riêng từng thread, Barrier đảm bảo cùng bắt đầu; xác nhận double-submit trả cùng order và voucher last use chỉ một redemption/order thành công.

Coverage mới: AUTH-01/CART-01, CART-02 (options/quantity), CHK-01/02/03/04/05, PAY-01/02/03, ORD-01/02/03, RBAC-01/02/03, CSRF, snapshots/rollback. Shipping config/free threshold có implementation, lịch nhận/capacity/zone verification đầy đủ chưa có tests nghiệm thu Sprint 4. Delivery chỉ pending verification và bị chặn pha chế, không claim tính khoảng cách thật. UI templates được render qua Django client; chưa chạy browser responsive/E2E.

NOT RUN: Playwright/mobile/tablet/desktop screenshots (không có browser/Playwright cài sẵn), production smoke/HTTPS/restart cloud (chưa duyệt deploy). Unfinished: REQ-07/09/10/11, ảnh thật REQ-05, scheduling/manual orders/inventory/loyalty/reports Sprint 4. Không lỗi test backend còn tồn đọng trong suite đã chạy; không suy rộng sang QA chưa thực hiện.

## Localhost smoke và preview accounts

13/10/2026: `manage.py check` PASS 0 issues. `runserver 127.0.0.1:8000 --noreload` sandbox FAIL DB connection; cùng lệnh ngoài sandbox approved khởi chạy, GET / HTTP 200. URL Windows được cung cấp http://localhost:8000/; Windows browser accessibility chưa được người dùng xác nhận.

`.venv/bin/python scripts/local_http_smoke.py` outside sandbox approved: **9 PASS/0 FAIL** cho `/`, `/menu/`, `/products/ca-phe-sua-da/`, `/accounts/login/`, `/accounts/register/`, `/promotions/`, `/healthz/`, `/static/catalog/site.css`, `/static/catalog/drink.svg`. Không submit/khởi tạo user, order; chưa đánh giá visual layout.

Read-only User role counts ban đầu: Customer=0, Staff=0, Admin=0, superuser=0; không in PII/password. Hai lệnh preview `create_demo_account --username demo_customer --role CUSTOMER` và tương tự demo_staff/STAFF đều PASS: database dev, no writes, is_staff=False, is_superuser=False. Chưa chạy --apply; không có test hành trình trên browser bằng account thật.

Playwright 1.63.0 cài thành công trong .venv; chưa cài browser runtime hoặc chạy browser QA. Các thay đổi provisioning command chưa nằm trong suite 57 tests trước đó; preview actual PASS không thay thế security regression suite. Sprint 3/4 giữ nguyên unfinished trong lúc ưu tiên owner QA localhost.
# Bổ sung 20/11/2026 — Customer UI/UX refinement

- `manage.py check`: PASS.
- `makemigrations --check --dry-run`: No changes detected (warning kết nối default DB trong sandbox; không áp dụng migration).
- Targeted backend QA 55441: 70/70 PASS.
- Full backend: 400/401 PASS; một ERROR do sandbox không cho local SMTP test bind cổng, không có assertion nghiệp vụ FAIL.
- Browser: các 35 trường hợp có bằng chứng PASS tích lũy; responsive 375/768/1440 PASS. Chưa chạy lại một lượt full 35 duy nhất sau assertion cuối.
- `git diff --check`: PASS.
# Bổ sung 20/11/2026 — Checkout 24-hour picker

- Pickup/Checkout backend QA 55441: 16/16 PASS.
- Chromium 24-hour selection/storage: 1/1 PASS, gồm 09:30, 14:30, 23:00 tại 375/768/1440px.
- Journey Checkout → mock payment → Staff: 1/1 PASS.
- Không dùng database preview và không gửi email thật.
# Bổ sung 20/11/2026 — Policy Rich Text Editor

- Targeted Policy/Consent QA 55441: 16/16 PASS.
- Chromium Admin editor, preview, draft, publish và Customer render: 1/1 journey PASS tại 375/768/1440px.
- XSS regression: raw script/HTML được escape; `javascript:` link bị từ chối; liên kết HTTPS hợp lệ PASS.
- Legacy plain text/`**heading**`/list rendering PASS.
> **20/11/2026 — Customer UI/UX Round 2:** backend QA PostgreSQL 55441:60/60PASS; Chromium About/Contact/Partners và Policy/Consent tại375/768/1440PASS, khôngoverflow/pageerror; Staff/Admin khôngloadMaps. Check/migration drift/diff checkPASS. Full434 NOT RUN; không ghi preview/dev/Neon. [Chi tiết](CUSTOMER_UI_UX_REFINEMENT_ROUND2_2026-11-20.md).

## 20/11/2026 — Customer/Internal Login separation

- Environment: PostgreSQL QA độc lập `127.0.0.1:55441`; safety guard PASS.
- `manage.py check`: PASS; migration drift: PASS/no changes; `git diff --check`: PASS.
- Authentication/RBAC targeted: 36/36 PASS.
- Chromium two-gateway responsive 375/768/1440: 1/1 PASS.
- Backend suite attempt: 413 PASS, 1 fixture FAIL, 1 unrelated SMTP sandbox ERROR / 415. Fixture đã sửa và targeted rerun PASS; SMTP sandbox vẫn là environment limitation, không claim full PASS.
