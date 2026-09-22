# Hệ thống Assessment, Review và Career Checkpoint

Tài liệu này biến roadmap từ bộ bài học thành hệ thống học có kiểm chứng.

## 1. Bốn lớp đánh giá

~~~text
Trong bài
→ Retrieval practice

Sau 4–6 bài
→ Spaced Review

Sau cụm kỹ năng
→ Failure Lab / PR Review Lab

Sau mốc nghề nghiệp
→ Career Checkpoint
~~~

Mỗi lớp kiểm tra năng lực khác nhau:

- **Retrieval:** nhớ và giải thích.
- **Spaced Review:** giữ kiến thức sau một khoảng cách.
- **Failure Lab:** debug dưới thông tin không đầy đủ.
- **PR Review:** đọc code người khác và đánh giá rủi ro.
- **Career Checkpoint:** tích hợp build + debug + review + judgment.

## 2. Failure Lab

Failure Lab phải có bug thật sự hợp lý:

- output sai;
- query count tăng;
- race condition;
- tracking state stale;
- security/config mistake;
- resource leak;
- migration/transaction sai.

Không đặt solution đầy đủ cùng trang.

Người học phải ghi lại:

1. hypothesis ban đầu;
2. evidence thu được;
3. root cause;
4. fix nhỏ nhất;
5. regression test;
6. điều gì sẽ monitor ở production.

## 3. Spaced Review

Review không được chỉ hỏi bài vừa học.

Tỷ lệ gợi ý:

| Nguồn | Tỷ lệ |
|---|---:|
| Cụm vừa học | 50% |
| Module trước | 30% |
| Judgment/debugging | 20% |

Nếu dưới 70%, quay lại các bài được review map chỉ ra.

## 4. PR Review Lab

Mỗi finding cần ghi:

~~~text
Severity: blocker / high / medium / low
Location:
Problem:
Impact:
Evidence:
Suggested smallest fix:
~~~

Rubric:

| Nhóm | Câu hỏi |
|---|---|
| Correctness | Có sai logic/invariant không? |
| Performance | Query/algorithm có scale không? |
| Security | Input/permission/secret có rủi ro không? |
| Maintainability | Abstraction có đáng không? |
| Operability | Có log/metrics/retry/migration concern không? |

## 5. Career checkpoints

### Sau Module 05 — C# Foundation

Người học phải có thể viết/debug/test ứng dụng C# vừa, dùng async/cancellation/resource đúng và giải thích memory/reference/GC ở mức developer.

### Sau Module 09 — Junior Data/Backend

Người học phải có thể thiết kế schema vừa, chọn đúng SQL/LINQ/EF Core, đọc generated SQL/plan cơ bản, tránh N+1/tracking misuse, xử lý transaction/concurrency và viết relational integration test.

### Sau Module 13 — Full-stack Junior

Người học phải có thể build API + React hoặc Angular, auth/validation/error handling end-to-end và deploy một hệ thống nhỏ.

### Sau Module 15 — Production-ready Developer

Người học phải có thể vận hành testing, CI/CD, Docker, rollback, logging/metrics/health và secret/config.

### Sau Module 18 — Senior/System Design

Người học phải có thể tìm architectural drivers, estimate scale, chọn storage/cache/queue, thiết kế consistency/failure handling và viết ADR.

### Sau Module 20 — Architect

Người học phải có thể cân trade-off business/technical, thiết kế evolutionary architecture, migration/risk plan và dẫn dắt technical decision mà không pattern worship.

## 6. Mức đánh giá

### Chưa đạt

Cần hướng dẫn chi tiết, không tự debug/giải thích được.

### Đạt

Tự hoàn thành task chuẩn, giải thích được lựa chọn chính.

### Vững

Xử lý edge case, đo trade-off, review người khác và đề xuất giải pháp đơn giản phù hợp bối cảnh.

Checkpoint dùng để quyết định **bài nào cần ôn tiếp**, không dùng để xếp hạng con người.
