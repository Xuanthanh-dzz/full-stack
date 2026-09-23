# Module 08 — SQL và cơ sở dữ liệu

25 bài từ dữ liệu quan hệ tới checkout và vận hành có bằng chứng. SQL Server 2025/T-SQL; query chạy ở server, client gửi lệnh và nhận rowset. Giữ tách biệt logical query processing với physical execution plan.

| Cụm | Failure Lab | Review |
|---|---|---|
| 01–05 | [NULL/CHECK](./failure-labs/01-null-check.md) | [Review01](./reviews/review-01.md) |
| 06–10 | [LEFT JOIN](./failure-labs/02-left-join.md) | [Review02](./reviews/review-02.md) |
| 11–15 | [Ranking](./failure-labs/03-rank.md) | [Review03](./reviews/review-03.md) |
| 16–20 | [Rollback](./failure-labs/04-rollback.md) | [Review04](./reviews/review-04.md) |
| 21–25 | [Injection](./failure-labs/05-injection.md) | [Review05](./reviews/review-05.md) |

Kết thúc bằng [PR Review](./pr-review-labs/01-report.md). Career checkpoint Junior Data/Backend nằm sau Module 09, không tạo thêm mốc ở08.

## Kiểm chứng

Verifier dùng container riêng có label `fullstack.module08.verifier=1`; không nhận container ứng dụng. Xem workflow `.github/workflows/verify-module-08.yml` và hướng dẫn `samples/module-08/README.md` trong repository. Mỗi lesson có manifest SQL trong section3: bài20 gồm setup+2 sessions; bài24 gồm migration+backup+restore. Không chọn block dài nhất.

Gate thực thi SQL, kiểm contracts và tái hiện5lab. Human review vẫn phải xét khả năng giải thích grain, NULL, cost, isolation và judgment; không coi tất cả bài tập mở rộng là đã làm. [Tiến độ](../PROGRESS.md).
