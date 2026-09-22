# Tiến độ biên soạn Full-stack Roadmap

File này là **nguồn sự thật duy nhất** về phạm vi và tiến độ. Mỗi checkbox tương ứng với một file Markdown phải có trong bộ tài liệu; source code chạy kèm bài sẽ được tạo và kiểm tra khi viết bài đó. Riêng Module 12 có hai nhánh framework song song: người học hoàn thành phần nền tảng chung, chọn **React hoặc Angular**, rồi học phần frontend dùng chung.

## Trạng thái hiện tại

- Giai đoạn: `Biên soạn nội dung — module 01–09 đã hoàn thành; module 00 còn các bài hướng dẫn môi trường`.
- Checkpoint hiện tại: module `09-linq-va-ef-core` đạt `24 / 24` bài; GitHub Actions đã kiểm tra Lesson Authoring Standard v2, compile 10 sample LINQ độc lập, build/test EF Core 10, generate/apply migration, chạy SQL Server 2025 smoke test và build MkDocs thành công.
- Bài tiếp theo theo dependency của các module đã hoàn thành: `10-web-nen-tang/01-internet-dns-tcp-tls-va-trinh-duyet.md`; nếu lấp khoảng trống theo số thứ tự toàn cục, bắt đầu tại `00-huong-dan/01-cach-su-dung-bo-tai-lieu.md`.
- Tiến độ: `164 / 421` file hoàn thành (`39,0%`).

## Quy ước checkbox

- `[ ]`: mới nằm trong kế hoạch; file bài học chưa được tạo hoặc chưa đạt Definition of Done.
- `[x]`: file tồn tại, đã đủ nội dung, code đã được chạy/kiểm tra và cross-link hợp lệ.
- README, roadmap và PROGRESS là tài liệu quản trị nên không áp dụng template tám phần của bài học.
- Chỉ cập nhật một bài sang `[x]` sau khi hoàn tất; hoàn thành trọn module hiện tại rồi mới viết module tiếp theo.
- Khi thêm, đổi tên hoặc tách bài, phải cập nhật tổng số, prerequisite, roadmap và mọi cross-link liên quan.

## Baseline cần giữ nhất quán

| Thành phần | Baseline biên soạn |
|---|---|
| C | C11 |
| C++ | C++20 |
| .NET | Target framework `net9.0`; pin exact SDK trong bài môi trường |
| C# | Dùng compiler đã pin và các tính năng ngôn ngữ mới tương thích với target; nêu rõ `LangVersion` khi không dùng mặc định |
| ASP.NET Core / EF Core | Major version 9; pin package patch version trong project |
| Database chính | SQL Server; Module 08 được chạy kiểm chứng trên SQL Server 2025; ghi chú khác biệt PostgreSQL khi điều đó giúp hiểu provider/dialect |
| Frontend | Node.js LTS, TypeScript; người học chọn React hoặc Angular và pin version bằng lockfile khi viết project |
| Hạ tầng | Docker làm môi trường tái tạo cục bộ; GitHub Actions và GitLab CI đều có pipeline mẫu |

## Definition of Done cho một bài học

- Đủ tám phần: mục tiêu, bài toán, code chạy được, cơ chế, kiến thức nền, lỗi thường gặp, bài tập và checklist/link.
- Mở đầu problem-first; giải thích bằng tiếng Việt, code/keyword giữ nguyên tiếng Anh.
- Có lệnh build/run/test và version cần thiết; không phụ thuộc trạng thái riêng của IDE.
- Có sơ đồ text mô tả stack/heap/reference/ownership khi liên quan.
- Có 3–5 bài tập kèm gợi ý, không đưa lời giải đầy đủ.
- Link prerequisite và bài kế tiếp tồn tại, dùng đường dẫn tương đối.

## Tài liệu quản trị

- [x] `README.md`
- [x] `PROGRESS.md`

## 00-huong-dan

- [x] `00-huong-dan/roadmap.md`
- [ ] `00-huong-dan/01-cach-su-dung-bo-tai-lieu.md`
- [ ] `00-huong-dan/02-phuong-phap-hoc-problem-first.md`
- [ ] `00-huong-dan/03-cai-dat-c-cpp-toolchain.md`
- [ ] `00-huong-dan/04-cai-dat-dotnet-9.md`
- [ ] `00-huong-dan/05-chon-va-cai-dat-ide.md`
- [ ] `00-huong-dan/06-cai-dat-git-docker-database-nodejs.md`
- [ ] `00-huong-dan/07-terminal-va-he-thong-file.md`
- [ ] `00-huong-dan/08-kiem-tra-moi-truong.md`
- [ ] `00-huong-dan/09-cach-chay-debug-va-doc-loi.md`
- [ ] `00-huong-dan/10-ke-hoach-hoc-va-xay-portfolio.md`

## 01-nen-tang-lap-trinh

- [x] `01-nen-tang-lap-trinh/01-bai-toan-thuat-toan-va-pseudocode.md`
- [x] `01-nen-tang-lap-trinh/02-chuong-trinh-c-dau-tien.md`
- [x] `01-nen-tang-lap-trinh/03-bien-hang-so-kieu-du-lieu.md`
- [x] `01-nen-tang-lap-trinh/04-bo-nho-bien-va-pham-vi.md`
- [x] `01-nen-tang-lap-trinh/05-toan-tu-va-bieu-thuc.md`
- [x] `01-nen-tang-lap-trinh/06-nhap-xuat-voi-stdio.md`
- [x] `01-nen-tang-lap-trinh/07-dieu-kien-if-switch.md`
- [x] `01-nen-tang-lap-trinh/08-vong-lap-for-while-do-while.md`
- [x] `01-nen-tang-lap-trinh/09-ham-tham-so-gia-tri-tra-ve.md`
- [x] `01-nen-tang-lap-trinh/10-ngan-xep-loi-goi-ham.md`
- [x] `01-nen-tang-lap-trinh/11-mang-mot-chieu.md`
- [x] `01-nen-tang-lap-trinh/12-mang-hai-chieu.md`
- [x] `01-nen-tang-lap-trinh/13-chuoi-ky-tu.md`
- [x] `01-nen-tang-lap-trinh/14-debug-va-kiem-thu-chuong-trinh-c.md`
- [x] `01-nen-tang-lap-trinh/15-du-an-console-quan-ly-diem.md`

## 02-c-chuyen-sau

- [x] `02-c-chuyen-sau/01-dia-chi-bo-nho-va-con-tro.md`
- [x] `02-c-chuyen-sau/02-con-tro-va-bien.md`
- [x] `02-c-chuyen-sau/03-con-tro-voi-mang-va-chuoi.md`
- [x] `02-c-chuyen-sau/04-con-tro-cap-hai.md`
- [x] `02-c-chuyen-sau/05-con-tro-ham-va-callback.md`
- [x] `02-c-chuyen-sau/06-stack-heap-va-vong-doi-bo-nho.md`
- [x] `02-c-chuyen-sau/07-cap-phat-dong-malloc-calloc-realloc-free.md`
- [x] `02-c-chuyen-sau/08-loi-bo-nho-va-undefined-behavior.md`
- [x] `02-c-chuyen-sau/09-struct-enum-typedef.md`
- [x] `02-c-chuyen-sau/10-union-bit-field-va-bo-nho.md`
- [x] `02-c-chuyen-sau/11-file-io.md`
- [x] `02-c-chuyen-sau/12-preprocessor-header-va-macro.md`
- [x] `02-c-chuyen-sau/13-qua-trinh-bien-dich-linking-makefile.md`
- [x] `02-c-chuyen-sau/14-xu-ly-loi-va-lap-trinh-phong-thu.md`
- [x] `02-c-chuyen-sau/15-du-an-c-quan-ly-kho.md`

## 03-cpp

- [x] `03-cpp/01-tu-c-sang-cpp20.md`
- [x] `03-cpp/02-reference-const-va-vong-doi-doi-tuong.md`
- [x] `03-cpp/03-class-object-encapsulation.md`
- [x] `03-cpp/04-constructor-destructor-va-bo-nho.md`
- [x] `03-cpp/05-copy-move-rule-of-zero-five.md`
- [x] `03-cpp/06-ke-thua-va-da-hinh.md`
- [x] `03-cpp/07-abstract-class-va-interface-trong-cpp.md`
- [x] `03-cpp/08-template-va-generic-programming.md`
- [x] `03-cpp/09-stl-container.md`
- [x] `03-cpp/10-iterator-algorithm-va-lambda.md`
- [x] `03-cpp/11-exception-va-raii.md`
- [x] `03-cpp/12-smart-pointer-va-quyen-so-huu.md`
- [x] `03-cpp/13-move-semantics-va-perfect-forwarding.md`
- [x] `03-cpp/14-du-an-cpp-quan-ly-thu-vien.md`

## 04-csharp-co-ban

- [x] `04-csharp-co-ban/01-dotnet-9-va-chuong-trinh-csharp.md`
- [x] `04-csharp-co-ban/02-cu-phap-bien-va-kieu-du-lieu.md`
- [x] `04-csharp-co-ban/03-toan-tu-dieu-kien-vong-lap.md`
- [x] `04-csharp-co-ban/04-method-parameter-va-return.md`
- [x] `04-csharp-co-ban/05-stack-heap-value-type-reference-type.md`
- [x] `04-csharp-co-ban/06-array-string-index-va-range.md`
- [x] `04-csharp-co-ban/07-class-object-constructor.md`
- [x] `04-csharp-co-ban/08-property-encapsulation-va-access-modifier.md`
- [x] `04-csharp-co-ban/09-inheritance-polymorphism.md`
- [x] `04-csharp-co-ban/10-abstract-class-va-interface.md`
- [x] `04-csharp-co-ban/11-struct-enum-va-tuple.md`
- [x] `04-csharp-co-ban/12-exception-va-xu-ly-loi.md`
- [x] `04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md`
- [x] `04-csharp-co-ban/14-project-solution-namespace-va-assembly.md`
- [x] `04-csharp-co-ban/15-debug-va-diagnostics-co-ban.md`
- [x] `04-csharp-co-ban/16-du-an-console-csharp-quan-ly-cong-viec.md`

## 05-csharp-nang-cao

- [x] `05-csharp-nang-cao/01-generics-va-constraints.md`
- [x] `05-csharp-nang-cao/02-delegate-action-func-predicate.md`
- [x] `05-csharp-nang-cao/03-event-va-event-handler.md`
- [x] `05-csharp-nang-cao/04-lambda-closure-va-bo-nho.md`
- [x] `05-csharp-nang-cao/05-extension-method.md`
- [x] `05-csharp-nang-cao/06-nullable-reference-type.md`
- [x] `05-csharp-nang-cao/07-record-init-required-va-immutability.md`
- [x] `05-csharp-nang-cao/08-pattern-matching.md`
- [x] `05-csharp-nang-cao/09-async-await-task-va-state-machine.md`
- [x] `05-csharp-nang-cao/10-cancellation-timeout-va-exception-bat-dong-bo.md`
- [x] `05-csharp-nang-cao/11-parallelism-concurrency-va-thread-safety.md`
- [x] `05-csharp-nang-cao/12-idisposable-gc-va-quan-ly-tai-nguyen.md`
- [x] `05-csharp-nang-cao/13-reflection-attribute-va-dynamic.md`
- [x] `05-csharp-nang-cao/14-span-memory-va-lap-trinh-hieu-nang.md`
- [x] `05-csharp-nang-cao/15-covariance-va-contravariance.md`
- [x] `05-csharp-nang-cao/16-expression-tree.md`
- [x] `05-csharp-nang-cao/17-serialization-system-text-json.md`
- [x] `05-csharp-nang-cao/18-do-luong-va-toi-uu-hieu-nang.md`
- [x] `05-csharp-nang-cao/19-du-an-xu-ly-du-lieu-bat-dong-bo.md`

## 06-oop-va-thiet-ke

- [x] `06-oop-va-thiet-ke/01-mo-hinh-hoa-doi-tuong.md`
- [x] `06-oop-va-thiet-ke/02-encapsulation-abstraction-inheritance-polymorphism.md`
- [x] `06-oop-va-thiet-ke/03-composition-over-inheritance.md`
- [x] `06-oop-va-thiet-ke/04-single-responsibility.md`
- [x] `06-oop-va-thiet-ke/05-open-closed.md`
- [x] `06-oop-va-thiet-ke/06-liskov-substitution.md`
- [x] `06-oop-va-thiet-ke/07-interface-segregation.md`
- [x] `06-oop-va-thiet-ke/08-dependency-inversion.md`
- [x] `06-oop-va-thiet-ke/09-coupling-va-cohesion.md`
- [x] `06-oop-va-thiet-ke/10-dependency-injection-va-inversion-of-control.md`
- [x] `06-oop-va-thiet-ke/11-clean-code-ten-ham-va-cau-truc.md`
- [x] `06-oop-va-thiet-ke/12-code-smell-va-refactoring.md`
- [x] `06-oop-va-thiet-ke/13-design-by-contract-va-invariant.md`
- [x] `06-oop-va-thiet-ke/14-du-an-refactor-ung-dung-csharp.md`

## 07-cau-truc-du-lieu-giai-thuat

- [x] `07-cau-truc-du-lieu-giai-thuat/01-big-o-thoi-gian-va-bo-nho.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/02-de-quy-va-call-stack.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/03-mang-va-dynamic-array.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/04-linked-list.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/05-stack-queue-va-deque.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/06-hash-table-va-hash-function.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/07-tree-va-binary-search-tree.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/08-heap-va-priority-queue.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/09-trie.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/10-graph-va-cach-bieu-dien.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/11-bfs-va-dfs.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/12-shortest-path-va-minimum-spanning-tree.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/13-sorting.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/14-searching.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/15-greedy.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/16-backtracking.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/17-dynamic-programming.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md`
- [x] `07-cau-truc-du-lieu-giai-thuat/19-du-an-engine-tim-duong.md`

## 08-sql-va-csdl

- [x] `08-sql-va-csdl/01-mo-hinh-quan-he-va-cai-dat-sql-server.md`
- [x] `08-sql-va-csdl/02-thiet-ke-schema-table-key-constraint.md`
- [x] `08-sql-va-csdl/03-kieu-du-lieu-va-null.md`
- [x] `08-sql-va-csdl/04-crud-select-insert-update-delete.md`
- [x] `08-sql-va-csdl/05-filter-sort-va-pagination.md`
- [x] `08-sql-va-csdl/06-ham-scalar-case-va-xu-ly-null.md`
- [x] `08-sql-va-csdl/07-group-by-aggregate-va-having.md`
- [x] `08-sql-va-csdl/08-inner-left-right-full-cross-join.md`
- [x] `08-sql-va-csdl/09-subquery-va-correlated-subquery.md`
- [x] `08-sql-va-csdl/10-set-operator-union-intersect-except.md`
- [x] `08-sql-va-csdl/11-cte-va-recursive-cte.md`
- [x] `08-sql-va-csdl/12-window-function.md`
- [x] `08-sql-va-csdl/13-view-stored-procedure-function-trigger.md`
- [x] `08-sql-va-csdl/14-mo-hinh-er-va-quan-he.md`
- [x] `08-sql-va-csdl/15-chuan-hoa-1nf-2nf-3nf-bcnf.md`
- [x] `08-sql-va-csdl/16-denormalization-va-du-lieu-lich-su.md`
- [x] `08-sql-va-csdl/17-index-btree-clustered-nonclustered.md`
- [x] `08-sql-va-csdl/18-covering-filtered-composite-index.md`
- [x] `08-sql-va-csdl/19-transaction-va-acid.md`
- [x] `08-sql-va-csdl/20-isolation-level-mvcc-lock-deadlock.md`
- [x] `08-sql-va-csdl/21-execution-plan-va-statistics.md`
- [x] `08-sql-va-csdl/22-toi-uu-truy-van-va-sargability.md`
- [x] `08-sql-va-csdl/23-bao-mat-phan-quyen-va-sql-injection.md`
- [x] `08-sql-va-csdl/24-backup-restore-va-migration-du-lieu.md`
- [x] `08-sql-va-csdl/25-du-an-csdl-thuong-mai-dien-tu.md`

## 09-linq-va-ef-core

- [x] `09-linq-va-ef-core/01-linq-query-syntax-va-method-syntax.md`
- [x] `09-linq-va-ef-core/02-where-select-va-selectmany.md`
- [x] `09-linq-va-ef-core/03-ordering-partitioning-va-distinct.md`
- [x] `09-linq-va-ef-core/04-aggregate-groupby-va-tolookup.md`
- [x] `09-linq-va-ef-core/05-join-va-groupjoin.md`
- [x] `09-linq-va-ef-core/06-deferred-execution-va-materialization.md`
- [x] `09-linq-va-ef-core/07-ienumerable-va-iqueryable.md`
- [x] `09-linq-va-ef-core/08-expression-tree-query-provider-va-sql-translation.md`
- [x] `09-linq-va-ef-core/09-composition-va-dynamic-query.md`
- [x] `09-linq-va-ef-core/10-loi-linq-va-toi-uu.md`
- [x] `09-linq-va-ef-core/11-ef-core-10-dbcontext-va-entity.md`
- [x] `09-linq-va-ef-core/12-convention-data-annotation-va-fluent-api.md`
- [x] `09-linq-va-ef-core/13-migration-code-first-va-seeding.md`
- [x] `09-linq-va-ef-core/14-crud-change-tracking-va-unit-of-work.md`
- [x] `09-linq-va-ef-core/15-quan-he-one-to-one-one-to-many-many-to-many.md`
- [x] `09-linq-va-ef-core/16-eager-explicit-va-lazy-loading.md`
- [x] `09-linq-va-ef-core/17-n-plus-one-projection-va-split-query.md`
- [x] `09-linq-va-ef-core/18-transaction-va-concurrency-token.md`
- [x] `09-linq-va-ef-core/19-global-query-filter-va-interceptor.md`
- [x] `09-linq-va-ef-core/20-raw-sql-va-stored-procedure.md`
- [x] `09-linq-va-ef-core/21-performance-no-tracking-compiled-query-bulk-update.md`
- [x] `09-linq-va-ef-core/22-testing-ef-core-voi-sqlite-va-testcontainers.md`
- [x] `09-linq-va-ef-core/23-repository-pattern-co-nen-dung.md`
- [x] `09-linq-va-ef-core/24-du-an-data-access-cho-web-api.md`

## 10-web-nen-tang

- [ ] `10-web-nen-tang/01-internet-dns-tcp-tls-va-trinh-duyet.md`
- [ ] `10-web-nen-tang/02-http-request-va-response.md`
- [ ] `10-web-nen-tang/03-http-method-status-code-va-header.md`
- [ ] `10-web-nen-tang/04-json-serialization-va-content-negotiation.md`
- [ ] `10-web-nen-tang/05-cookie-session-va-web-storage.md`
- [ ] `10-web-nen-tang/06-rest-resource-uri-va-api-contract.md`
- [ ] `10-web-nen-tang/07-pagination-filtering-versioning-va-idempotency.md`
- [ ] `10-web-nen-tang/08-error-response-problem-details-va-openapi.md`
- [ ] `10-web-nen-tang/09-same-origin-policy-va-cors.md`
- [ ] `10-web-nen-tang/10-xac-thuc-bam-mat-khau-va-session.md`
- [ ] `10-web-nen-tang/11-jwt-access-token-va-refresh-token.md`
- [ ] `10-web-nen-tang/12-oauth2-va-openid-connect.md`
- [ ] `10-web-nen-tang/13-phan-quyen-rbac-abac-va-policy.md`
- [ ] `10-web-nen-tang/14-owasp-top-10-va-threat-modeling.md`
- [ ] `10-web-nen-tang/15-xss-csrf-sql-injection-va-ssrf.md`
- [ ] `10-web-nen-tang/16-https-secret-security-header-va-rate-limit.md`
- [ ] `10-web-nen-tang/17-thiet-ke-api-quan-ly-don-hang.md`

## 11-aspnet-core-backend

- [ ] `11-aspnet-core-backend/01-khoi-tao-aspnet-core-9.md`
- [ ] `11-aspnet-core-backend/02-program-host-va-vong-doi-ung-dung.md`
- [ ] `11-aspnet-core-backend/03-configuration-options-va-secret.md`
- [ ] `11-aspnet-core-backend/04-dependency-injection-va-service-lifetime.md`
- [ ] `11-aspnet-core-backend/05-middleware-pipeline.md`
- [ ] `11-aspnet-core-backend/06-routing-model-binding-va-model-validation.md`
- [ ] `11-aspnet-core-backend/07-minimal-api.md`
- [ ] `11-aspnet-core-backend/08-controller-api.md`
- [ ] `11-aspnet-core-backend/09-dto-mapping-va-problem-details.md`
- [ ] `11-aspnet-core-backend/10-exception-handling-va-filter.md`
- [ ] `11-aspnet-core-backend/11-logging-structured-logging-va-correlation-id.md`
- [ ] `11-aspnet-core-backend/12-tich-hop-ef-core.md`
- [ ] `11-aspnet-core-backend/13-authentication-jwt-va-authorization-policy.md`
- [ ] `11-aspnet-core-backend/14-openapi-versioning-va-rate-limiting.md`
- [ ] `11-aspnet-core-backend/15-output-cache-va-distributed-cache.md`
- [ ] `11-aspnet-core-backend/16-httpclientfactory-va-resilience.md`
- [ ] `11-aspnet-core-backend/17-background-service-va-hang-doi-noi-bo.md`
- [ ] `11-aspnet-core-backend/18-signalr.md`
- [ ] `11-aspnet-core-backend/19-grpc-va-protobuf.md`
- [ ] `11-aspnet-core-backend/20-health-check-metrics-va-readiness.md`
- [ ] `11-aspnet-core-backend/21-file-upload-va-streaming.md`
- [ ] `11-aspnet-core-backend/22-hieu-nang-pooling-va-native-aot.md`
- [ ] `11-aspnet-core-backend/23-du-an-web-api-production.md`

## 12-frontend

### Nền tảng chung — bắt buộc cho cả hai nhánh

- [ ] `12-frontend/01-html-semantic-va-cau-truc-trang.md`
- [ ] `12-frontend/02-form-validation-va-accessibility.md`
- [ ] `12-frontend/03-css-selector-box-model-va-cascade.md`
- [ ] `12-frontend/04-flexbox-grid-va-responsive-design.md`
- [ ] `12-frontend/05-javascript-bien-kieu-du-lieu-va-ham.md`
- [ ] `12-frontend/06-javascript-object-array-va-module.md`
- [ ] `12-frontend/07-dom-event-va-form.md`
- [ ] `12-frontend/08-promise-async-await-va-event-loop.md`
- [ ] `12-frontend/09-fetch-http-va-xu-ly-loi.md`
- [ ] `12-frontend/10-browser-storage-cookie-va-security.md`
- [ ] `12-frontend/11-typescript-type-interface-union-va-generic.md`
- [ ] `12-frontend/12-typescript-narrowing-module-va-tsconfig.md`
- [ ] `12-frontend/13-chon-nhanh-react-hoac-angular.md`

### Nhánh A — React

- [ ] `12-frontend/14-react-jsx-component-va-props.md`
- [ ] `12-frontend/15-react-state-event-va-controlled-form.md`
- [ ] `12-frontend/16-react-hook-useeffect-va-custom-hook.md`
- [ ] `12-frontend/17-react-router-va-layout.md`
- [ ] `12-frontend/18-react-context-reducer-va-state-management.md`
- [ ] `12-frontend/19-react-tanstack-query-va-server-state.md`
- [ ] `12-frontend/20-react-api-auth-va-refresh-token.md`
- [ ] `12-frontend/21-testing-react.md`
- [ ] `12-frontend/22-du-an-react-spa-quan-ly-cong-viec.md`

### Nhánh B — Angular

- [ ] `12-frontend/23-angular-cli-standalone-component-va-project-structure.md`
- [ ] `12-frontend/24-angular-template-binding-directive-va-pipe.md`
- [ ] `12-frontend/25-angular-component-input-output-va-lifecycle.md`
- [ ] `12-frontend/26-angular-service-di-rxjs-va-observable.md`
- [ ] `12-frontend/27-angular-reactive-form-va-validation.md`
- [ ] `12-frontend/28-angular-router-guard-va-resolver.md`
- [ ] `12-frontend/29-angular-httpclient-interceptor-auth-va-refresh-token.md`
- [ ] `12-frontend/30-angular-signals-rxjs-va-state-management.md`
- [ ] `12-frontend/31-testing-angular.md`
- [ ] `12-frontend/32-du-an-angular-spa-quan-ly-cong-viec.md`

### Hoàn thiện frontend — áp dụng cho framework đã chọn

- [ ] `12-frontend/33-css-framework-va-design-system.md`
- [ ] `12-frontend/34-performance-accessibility-va-build.md`
- [ ] `12-frontend/35-frontend-architecture-va-so-sanh-react-angular.md`
- [ ] `12-frontend/36-checkpoint-frontend-production-ready.md`

## 13-fullstack-tich-hop

- [ ] `13-fullstack-tich-hop/01-thiet-ke-contract-frontend-backend.md`
- [ ] `13-fullstack-tich-hop/02-cau-hinh-cors-va-moi-truong.md`
- [ ] `13-fullstack-tich-hop/03-api-client-va-xu-ly-loi-thong-nhat.md`
- [ ] `13-fullstack-tich-hop/04-dang-nhap-jwt-cookie-va-refresh-token.md`
- [ ] `13-fullstack-tich-hop/05-validation-end-to-end.md`
- [ ] `13-fullstack-tich-hop/06-upload-download-file.md`
- [ ] `13-fullstack-tich-hop/07-signalr-websocket-realtime.md`
- [ ] `13-fullstack-tich-hop/08-docker-compose-fullstack.md`
- [ ] `13-fullstack-tich-hop/09-crud-backend-aspnet-core.md`
- [ ] `13-fullstack-tich-hop/10-crud-frontend-react-hoac-angular.md`
- [ ] `13-fullstack-tich-hop/11-kiem-thu-va-trien-khai-ung-dung-crud.md`
- [ ] `13-fullstack-tich-hop/12-du-an-fullstack-quan-ly-ban-hang.md`

## 14-testing-chat-luong

- [ ] `14-testing-chat-luong/01-chien-luoc-testing-va-test-pyramid.md`
- [ ] `14-testing-chat-luong/02-unit-test-voi-xunit.md`
- [ ] `14-testing-chat-luong/03-assertion-theory-fixture-va-test-data.md`
- [ ] `14-testing-chat-luong/04-mocking-stub-fake-voi-moq.md`
- [ ] `14-testing-chat-luong/05-thiet-ke-code-de-test.md`
- [ ] `14-testing-chat-luong/06-integration-test-webapplicationfactory.md`
- [ ] `14-testing-chat-luong/07-integration-test-database-testcontainers.md`
- [ ] `14-testing-chat-luong/08-api-contract-test.md`
- [ ] `14-testing-chat-luong/09-end-to-end-test-voi-playwright.md`
- [ ] `14-testing-chat-luong/10-tdd-red-green-refactor.md`
- [ ] `14-testing-chat-luong/11-code-coverage-va-mutation-testing.md`
- [ ] `14-testing-chat-luong/12-static-analysis-format-va-warning.md`
- [ ] `14-testing-chat-luong/13-code-review-checklist.md`
- [ ] `14-testing-chat-luong/14-performance-load-va-stress-test.md`
- [ ] `14-testing-chat-luong/15-quality-gate-trong-ci.md`
- [ ] `14-testing-chat-luong/16-du-an-xay-test-suite.md`

## 15-devops-trien-khai

- [ ] `15-devops-trien-khai/01-git-branch-merge-rebase-va-conflict.md`
- [ ] `15-devops-trien-khai/02-git-reset-revert-reflog-bisect-cherry-pick.md`
- [ ] `15-devops-trien-khai/03-trunk-based-gitflow-va-pull-request.md`
- [ ] `15-devops-trien-khai/04-semantic-versioning-changelog-va-release.md`
- [ ] `15-devops-trien-khai/05-container-image-volume-va-network.md`
- [ ] `15-devops-trien-khai/06-dockerfile-dotnet-multi-stage.md`
- [ ] `15-devops-trien-khai/07-docker-compose-frontend-backend-database.md`
- [ ] `15-devops-trien-khai/08-bao-mat-va-toi-uu-image.md`
- [ ] `15-devops-trien-khai/09-ci-cd-nguyen-ly-va-pipeline.md`
- [ ] `15-devops-trien-khai/10-github-actions-build-test-publish.md`
- [ ] `15-devops-trien-khai/11-gitlab-ci-build-test-publish.md`
- [ ] `15-devops-trien-khai/12-quan-ly-secret-artifact-va-container-registry.md`
- [ ] `15-devops-trien-khai/13-trien-khai-iis.md`
- [ ] `15-devops-trien-khai/14-trien-khai-linux-systemd-nginx.md`
- [ ] `15-devops-trien-khai/15-trien-khai-container-va-database-migration.md`
- [ ] `15-devops-trien-khai/16-blue-green-canary-va-rollback.md`
- [ ] `15-devops-trien-khai/17-monitoring-logging-va-alerting.md`
- [ ] `15-devops-trien-khai/18-prometheus-va-grafana.md`
- [ ] `15-devops-trien-khai/19-du-an-pipeline-production.md`

## 16-design-pattern

- [ ] `16-design-pattern/01-khi-nao-dung-design-pattern.md`
- [ ] `16-design-pattern/02-singleton.md`
- [ ] `16-design-pattern/03-factory-method.md`
- [ ] `16-design-pattern/04-abstract-factory.md`
- [ ] `16-design-pattern/05-builder.md`
- [ ] `16-design-pattern/06-prototype.md`
- [ ] `16-design-pattern/07-adapter.md`
- [ ] `16-design-pattern/08-bridge.md`
- [ ] `16-design-pattern/09-composite.md`
- [ ] `16-design-pattern/10-decorator.md`
- [ ] `16-design-pattern/11-facade.md`
- [ ] `16-design-pattern/12-flyweight.md`
- [ ] `16-design-pattern/13-proxy.md`
- [ ] `16-design-pattern/14-chain-of-responsibility.md`
- [ ] `16-design-pattern/15-command.md`
- [ ] `16-design-pattern/16-interpreter.md`
- [ ] `16-design-pattern/17-iterator.md`
- [ ] `16-design-pattern/18-mediator.md`
- [ ] `16-design-pattern/19-memento.md`
- [ ] `16-design-pattern/20-observer.md`
- [ ] `16-design-pattern/21-state.md`
- [ ] `16-design-pattern/22-strategy.md`
- [ ] `16-design-pattern/23-template-method.md`
- [ ] `16-design-pattern/24-visitor.md`
- [ ] `16-design-pattern/25-pattern-trong-dotnet-va-aspnet-core.md`
- [ ] `16-design-pattern/26-antipattern-va-overengineering.md`
- [ ] `16-design-pattern/27-du-an-refactor-bang-design-pattern.md`

## 17-kien-truc-phan-mem

- [ ] `17-kien-truc-phan-mem/01-quality-attribute-va-architectural-driver.md`
- [ ] `17-kien-truc-phan-mem/02-layered-va-n-layer-architecture.md`
- [ ] `17-kien-truc-phan-mem/03-hexagonal-onion-va-clean-architecture.md`
- [ ] `17-kien-truc-phan-mem/04-modular-monolith.md`
- [ ] `17-kien-truc-phan-mem/05-ddd-strategic-design-va-bounded-context.md`
- [ ] `17-kien-truc-phan-mem/06-ddd-ubiquitous-language-va-context-map.md`
- [ ] `17-kien-truc-phan-mem/07-ddd-entity-value-object-va-aggregate.md`
- [ ] `17-kien-truc-phan-mem/08-repository-domain-service-va-domain-event.md`
- [ ] `17-kien-truc-phan-mem/09-application-service-use-case-va-boundary.md`
- [ ] `17-kien-truc-phan-mem/10-cqrs.md`
- [ ] `17-kien-truc-phan-mem/11-event-sourcing.md`
- [ ] `17-kien-truc-phan-mem/12-monolith-vs-microservices.md`
- [ ] `17-kien-truc-phan-mem/13-phan-ra-microservice-theo-domain.md`
- [ ] `17-kien-truc-phan-mem/14-api-contract-va-service-communication.md`
- [ ] `17-kien-truc-phan-mem/15-du-lieu-phan-tan-saga-va-outbox.md`
- [ ] `17-kien-truc-phan-mem/16-event-driven-architecture.md`
- [ ] `17-kien-truc-phan-mem/17-resilience-timeout-retry-va-circuit-breaker.md`
- [ ] `17-kien-truc-phan-mem/18-security-trong-kien-truc.md`
- [ ] `17-kien-truc-phan-mem/19-architecture-test-va-fitness-function.md`
- [ ] `17-kien-truc-phan-mem/20-migration-strangler-fig.md`
- [ ] `17-kien-truc-phan-mem/21-case-study-clean-architecture.md`
- [ ] `17-kien-truc-phan-mem/22-case-study-microservices-don-hang.md`

## 18-thiet-ke-he-thong

- [ ] `18-thiet-ke-he-thong/01-quy-trinh-system-design-va-uoc-luong.md`
- [ ] `18-thiet-ke-he-thong/02-latency-throughput-availability-sla-slo.md`
- [ ] `18-thiet-ke-he-thong/03-vertical-horizontal-scaling-va-stateless.md`
- [ ] `18-thiet-ke-he-thong/04-load-balancing-va-service-discovery.md`
- [ ] `18-thiet-ke-he-thong/05-cache-aside-write-through-write-behind.md`
- [ ] `18-thiet-ke-he-thong/06-redis-data-type-expiration-va-eviction.md`
- [ ] `18-thiet-ke-he-thong/07-cache-invalidation-va-cache-stampede.md`
- [ ] `18-thiet-ke-he-thong/08-cdn-object-storage-va-static-content.md`
- [ ] `18-thiet-ke-he-thong/09-database-replication-va-read-write-splitting.md`
- [ ] `18-thiet-ke-he-thong/10-partitioning-sharding-va-rebalancing.md`
- [ ] `18-thiet-ke-he-thong/11-cap-pacelc-va-consistency-model.md`
- [ ] `18-thiet-ke-he-thong/12-message-queue-backpressure-va-idempotency.md`
- [ ] `18-thiet-ke-he-thong/13-distributed-id-va-clock.md`
- [ ] `18-thiet-ke-he-thong/14-rate-limiting.md`
- [ ] `18-thiet-ke-he-thong/15-distributed-lock-va-leader-election.md`
- [ ] `18-thiet-ke-he-thong/16-search-full-text-va-indexing.md`
- [ ] `18-thiet-ke-he-thong/17-resilience-degradation-va-disaster-recovery.md`
- [ ] `18-thiet-ke-he-thong/18-capacity-planning-va-cost.md`
- [ ] `18-thiet-ke-he-thong/19-case-study-url-shortener.md`
- [ ] `18-thiet-ke-he-thong/20-case-study-chat-realtime.md`
- [ ] `18-thiet-ke-he-thong/21-case-study-news-feed.md`
- [ ] `18-thiet-ke-he-thong/22-case-study-ecommerce.md`

## 19-cong-nghe-hien-dai

- [ ] `19-cong-nghe-hien-dai/01-cloud-service-model-va-shared-responsibility.md`
- [ ] `19-cong-nghe-hien-dai/02-cloud-iam-network-compute-va-storage.md`
- [ ] `19-cong-nghe-hien-dai/03-managed-database-cache-va-messaging.md`
- [ ] `19-cong-nghe-hien-dai/04-trien-khai-dotnet-len-azure.md`
- [ ] `19-cong-nghe-hien-dai/05-infrastructure-as-code-terraform-va-bicep.md`
- [ ] `19-cong-nghe-hien-dai/06-twelve-factor-app.md`
- [ ] `19-cong-nghe-hien-dai/07-kubernetes-architecture-va-kubectl.md`
- [ ] `19-cong-nghe-hien-dai/08-pod-deployment-va-replicaset.md`
- [ ] `19-cong-nghe-hien-dai/09-service-ingress-va-network-policy.md`
- [ ] `19-cong-nghe-hien-dai/10-configmap-secret-va-persistent-volume.md`
- [ ] `19-cong-nghe-hien-dai/11-probe-resource-limit-va-hpa.md`
- [ ] `19-cong-nghe-hien-dai/12-helm-kustomize-va-gitops.md`
- [ ] `19-cong-nghe-hien-dai/13-rabbitmq-exchange-queue-va-routing.md`
- [ ] `19-cong-nghe-hien-dai/14-kafka-topic-partition-va-consumer-group.md`
- [ ] `19-cong-nghe-hien-dai/15-delivery-semantics-va-idempotent-consumer.md`
- [ ] `19-cong-nghe-hien-dai/16-schema-evolution-va-schema-registry.md`
- [ ] `19-cong-nghe-hien-dai/17-api-gateway-va-backend-for-frontend.md`
- [ ] `19-cong-nghe-hien-dai/18-service-mesh.md`
- [ ] `19-cong-nghe-hien-dai/19-opentelemetry-log-metric-va-trace.md`
- [ ] `19-cong-nghe-hien-dai/20-observability-dashboard-alert-va-slo.md`
- [ ] `19-cong-nghe-hien-dai/21-cloud-security-cost-va-disaster-recovery.md`
- [ ] `19-cong-nghe-hien-dai/22-du-an-trien-khai-microservices-kubernetes.md`

## 20-ky-nang-architect

- [ ] `20-ky-nang-architect/01-vai-tro-va-trach-nhiem-software-architect.md`
- [ ] `20-ky-nang-architect/02-khai-thac-requirement-va-rang-buoc.md`
- [ ] `20-ky-nang-architect/03-quality-attribute-scenario.md`
- [ ] `20-ky-nang-architect/04-phan-tich-tradeoff-va-atam.md`
- [ ] `20-ky-nang-architect/05-danh-gia-cong-nghe-va-proof-of-concept.md`
- [ ] `20-ky-nang-architect/06-architecture-decision-record.md`
- [ ] `20-ky-nang-architect/07-c4-context-container-component-code.md`
- [ ] `20-ky-nang-architect/08-uml-sequence-class-state-deployment.md`
- [ ] `20-ky-nang-architect/09-viet-tai-lieu-kien-truc.md`
- [ ] `20-ky-nang-architect/10-threat-modeling-va-risk-register.md`
- [ ] `20-ky-nang-architect/11-capacity-cost-va-technical-roadmap.md`
- [ ] `20-ky-nang-architect/12-build-vs-buy-va-vendor-lock-in.md`
- [ ] `20-ky-nang-architect/13-architecture-review-va-governance.md`
- [ ] `20-ky-nang-architect/14-modernize-legacy-system.md`
- [ ] `20-ky-nang-architect/15-giao-tiep-voi-stakeholder.md`
- [ ] `20-ky-nang-architect/16-mentoring-va-dan-dat-ky-thuat.md`
- [ ] `20-ky-nang-architect/17-incident-postmortem-va-hoc-tu-su-co.md`
- [ ] `20-ky-nang-architect/18-quan-ly-technical-debt.md`
- [ ] `20-ky-nang-architect/19-case-study-ra-quyet-dinh-kien-truc.md`
- [ ] `20-ky-nang-architect/20-portfolio-va-phong-van-architect.md`

## 21-du-an-thuc-hanh

- [ ] `21-du-an-thuc-hanh/01-cach-lam-du-an-va-definition-of-done.md`
- [ ] `21-du-an-thuc-hanh/02-du-an-c-console-quan-ly-kho.md`
- [ ] `21-du-an-thuc-hanh/03-du-an-cpp-engine-quan-ly-tai-nguyen.md`
- [ ] `21-du-an-thuc-hanh/04-du-an-csharp-console-quan-ly-chi-tieu.md`
- [ ] `21-du-an-thuc-hanh/05-du-an-aspnet-core-web-api-quan-ly-cong-viec.md`
- [ ] `21-du-an-thuc-hanh/06-du-an-fullstack-thuong-mai-dien-tu.md`
- [ ] `21-du-an-thuc-hanh/07-du-an-realtime-chat.md`
- [ ] `21-du-an-thuc-hanh/08-du-an-devops-trien-khai-production.md`
- [ ] `21-du-an-thuc-hanh/09-du-an-microservices-dat-hang.md`
- [ ] `21-du-an-thuc-hanh/10-capstone-saas-da-tenant.md`
- [ ] `21-du-an-thuc-hanh/11-tieu-chi-review-portfolio-va-kien-truc.md`

## Project gate theo cấp

| Gate | Thời điểm | Project chính | Điều kiện nổi bật |
|---|---|---|---|
| A — Người mới | Sau module `03` | `21/02–03` | C nhiều file, file I/O, memory sạch; C++ dùng RAII/STL |
| B — Data/.NET | Sau module `09` | `04/16`, `08/25`, `09/24`, rồi `21/04` | SQL, migration, transaction, query plan và EF performance |
| C — Junior | Sau module `14` | `11/23`, `12/22` hoặc `12/32`, `13/12`, rồi `21/05–07` | API + React/Angular + auth + validation + test end-to-end |
| D — Middle | Sau module `16` | `15/19`, `16/27`, rồi `21/08` | Container, CI/CD, monitoring, rollback và refactor có lý do |
| E — Senior | Sau module `19` | `17/22`, `19/22`, rồi `21/09` | Broker, Redis, gRPC, idempotency, resilience, tracing và Kubernetes |
| F — Architect | Sau module `20` | `21/10–11` | Requirement, C4, ADR, threat model, PoC, cost và migration plan |

## Lịch sử cập nhật

- `2026-09-22`: hoàn thành module `09-linq-va-ef-core` (`24/24` bài) theo Lesson Authoring Standard v2; baseline .NET 10/C# 14/EF Core 10.0.12/SQL Server 2025; thêm Entry/Exit test, rubric, TL;DR, mục `Khi nào KHÔNG dùng`, scale notes, bài judgment liên module, retrieval practice, sample CommerceLab Data Access và CI migration/provider-real smoke test.
- `2026-09-22`: hoàn thành toàn bộ module `08-sql-va-csdl` (`25/25` bài); verifier chạy từng lab trên SQL Server 2025 trong Docker, kiểm tra cấu trúc tám phần/cross-link và build toàn bộ MkDocs; capstone cuối module là CSDL thương mại điện tử có schema, constraint, index, transaction, security, backup/migration và query tuning.
- `2026-09-22`: mở rộng module `12-frontend` thành hai lựa chọn song song React/Angular sau 12 bài nền tảng HTML/CSS/JavaScript/TypeScript; Module 13 chấp nhận framework đã chọn. Tổng manifest tăng từ `410` lên `421` file.
- `2026-09-21`: hoàn thành toàn bộ module `07-cau-truc-du-lieu-giai-thuat` (`19/19` bài); bổ sung CI kiểm tra cấu trúc tám phần, cross-link, build warnings-as-errors và run toàn bộ sample .NET 9; project cuối module là Route Engine dùng weighted graph, priority queue và Dijkstra.
- `2026-07-31`: hoàn thành toàn bộ module `06-oop-va-thiet-ke` (`14/14` bài); build/run 14 sample .NET 9 với `Nullable` bật và warnings-as-errors, đối chiếu từng dòng output, kiểm tra failure path của các bài Liskov/contract, và dựng dự án refactor 10 file có characterization harness so sánh bản cũ với bản mới.
- `2026-07-31`: hoàn thành toàn bộ module `01-nen-tang-lap-trinh` (`15/15` bài), `02-c-chuyen-sau` (`15/15` bài) và `03-cpp` (`14/14` bài); build/run 44 lời giải chính bằng C11/C++20 với warnings-as-errors, đối chiếu output, kiểm tra failure path, Makefile, ASan/UBSan, ownership/lifetime và audit chéo toàn bộ prerequisite/cross-link.
- `2026-07-30`: hoàn thành toàn bộ module `05-csharp-nang-cao` (`19/19` bài); build/run 19 project .NET 9 với warnings-as-errors, đối chiếu output, audit tuyến prerequisite/memory model/cross-link và kiểm tra failure path của dự án batch JSON bất đồng bộ.
- `2026-07-30`: hoàn thành toàn bộ module `04-csharp-co-ban` (`16/16` bài); build/run code .NET 9, audit format, memory model, cross-link và các failure path của project JSON.
- `2026-07-30`: tạo scaffold, roadmap 5 cấp và manifest ban đầu để review; chưa viết bài học.
