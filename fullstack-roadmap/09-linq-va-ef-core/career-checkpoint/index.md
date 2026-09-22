# Career Checkpoint — Junior Data/Backend

> **Mốc:** sau Module 09  
> **Mục tiêu:** xác nhận người học có thể xử lý data-access work ở mức Junior mà không phụ thuộc tutorial từng bước.

## 1. Knowledge test — không nhìn tài liệu

1. `IEnumerable<T>` khác `IQueryable<T>` ở đâu?
2. Deferred execution có thể gây bug gì?
3. `AsEnumerable()` làm thay đổi execution location thế nào?
4. Khi nào projection tốt hơn `Include`?
5. N+1 và cartesian explosion khác nhau ra sao?
6. `DbContext` vì sao không nên singleton?
7. Change tracker làm gì?
8. Optimistic concurrency token phát hiện conflict bằng cách nào?
9. `ExecuteUpdate` bypass những gì?
10. Global query filter có phải authorization boundary không?
11. Khi nào raw SQL hợp lý?
12. Vì sao SQLite test chưa đủ cho SQL Server-specific query?
13. Generic Repository có thể trở thành abstraction thừa thế nào?
14. Khi query chậm, bạn kiểm tra C#, SQL hay index theo thứ tự nào?
15. Khi nào logic nên chạy SQL thay vì in-memory LINQ?

## 2. Build task

Trong 90–120 phút, không copy sample:

- thêm `OrderNumber` unique;
- tạo migration;
- viết query order history có keyset pagination;
- projection DTO không tracking;
- thêm integration test;
- generate SQL/migration artifact;
- ghi README cách chạy.

Acceptance:

- build warnings-as-errors;
- test pass;
- query có deterministic order;
- không hard-code secret;
- generated SQL có thể giải thích.

## 3. Debugging task

Chọn ngẫu nhiên **hai** Failure Lab:

- [Multiple enumeration](../failure-labs/01-multiple-enumeration-va-materialization.md)
- [`IQueryable` client-side filter](../failure-labs/02-iqueryable-client-side-filter.md)
- [N+1/cartesian explosion](../failure-labs/03-n-plus-one-va-cartesian-explosion.md)
- [Concurrency/stale state](../failure-labs/04-concurrency-va-stale-state.md)

Yêu cầu nộp:

1. hypothesis;
2. evidence;
3. root cause;
4. smallest fix;
5. regression test;
6. production metric cần monitor.

## 4. PR review task

Review một trong hai:

- [Order Search Service](../pr-review-labs/01-review-linq-search-service.md)
- [EF Production Risks](../pr-review-labs/02-review-ef-production-risks.md)

Yêu cầu tối thiểu 7 findings có severity và reasoning.

## 5. Judgment tasks

### Task A — SQL hay C#?

Dataset có 40 triệu OrderItems. Cần top 100 SKU doanh thu cao nhất rồi kiểm tra 100 SKU đó có nằm trong blacklist 50.000 phần tử.

Chọn nơi xử lý từng bước: SQL aggregate/index, EF query, LINQ in-memory, HashSet. Giải thích data locality, Big-O và network cost.

### Task B — abstraction

Team 3 người, một SQL Server, 50 request/s, một deployable. Chọn:

- `DbContext + application service`; hoặc
- Repository + Unit of Work + CQRS; hoặc
- microservice tách data domain.

Viết ADR 1 trang: drivers, decision, alternatives, cost, trigger để revisit.

## 6. Interview-style explanation

Không code, trả lời miệng 3–5 phút mỗi câu:

1. Vì sao LINQ nhìn giống nhau nhưng có thể chạy ở nơi khác nhau?
2. Kể một lần bạn sẽ chọn raw SQL thay EF LINQ.
3. Giải thích N+1 cho người chưa biết ORM.
4. Khi hai user sửa cùng row, bạn xử lý thế nào?
5. Vì sao thêm repository không tự động làm code dễ test hơn?

## 7. Competency matrix

| Năng lực | Chưa đạt | Đạt | Vững |
|---|---|---|---|
| LINQ/query composition | cần copy sample | tự viết query chuẩn | reasoning translation/cardinality |
| SQL/EF boundary | không biết query chạy đâu | xác định đúng execution location | chọn đúng tầng theo workload |
| Modeling/migration | cần hướng dẫn từng bước | map + migrate schema vừa | nhận ra migration risk/expand-contract |
| Performance | tối ưu theo cảm giác | dùng projection/log/plan | đo và trade-off query/index/app |
| Concurrency | blind last-write-wins | xử lý token/conflict | chọn policy theo business |
| Testing | chỉ unit/mock | relational integration test | provider-real strategy theo risk |
| Review | chỉ style issue | tìm correctness/perf/security issue | ưu tiên severity + smallest fix |
| Architecture judgment | pattern theo tutorial | chọn giải pháp đơn giản đủ tốt | nêu driver/trigger nâng cấp |

## 8. Remediation map

| Gap | Ôn lại |
|---|---|
| LINQ execution | bài 06–10 + Failure Lab 01–02 |
| EF modeling/tracking | bài 11–15 + Review 03 |
| Loading/performance | bài 16–17 + Failure Lab 03 |
| Transaction/concurrency | bài 18 + Failure Lab 04 |
| Raw SQL/security | bài 19–20 + PR Review 02 |
| Testing | bài 22 |
| Abstraction judgment | bài 23–24 + Review 05 |

## 9. Cách kết luận

- **Chưa đạt:** còn cần hướng dẫn chi tiết ở nhiều task; dùng remediation map rồi thử lại.
- **Đạt:** tự hoàn thành build/debug/review chuẩn và giải thích lựa chọn chính.
- **Vững:** xử lý edge case, đo trade-off, review có severity và đề xuất giải pháp nhỏ nhất phù hợp bối cảnh.

Checkpoint không xếp hạng con người; nó xác định gap để học tiếp.
