# Module 07 — Cấu trúc dữ liệu và giải thuật

19 bài từ đếm công việc tới route engine. Học theo thứ tự; luôn xác định input, invariant, output và chi phí trước chọn thuật toán.

| Cụm | Failure Lab | Review |
|---|---|---|
| 01–05 | [Queue](./failure-labs/01-queue.md) | [Review01](./reviews/review-01.md) |
| 06–10 | [Hash key](./failure-labs/02-hash.md) | [Review02](./reviews/review-02.md) |
| 11–15 | [Search](./failure-labs/03-search.md) | [Review03](./reviews/review-03.md) |
| 16–19 | [Alias](./failure-labs/04-alias.md) | [Review04](./reviews/review-04.md) |

Kết thúc bằng [PR Review](./pr-review-labs/01-route.md).

## Kiểm chứng

SDK9.0.121, từ repository root:

```bash
python scripts/verify_module_07.py --report artifacts/module07-release.json
python scripts/verify_module_07.py --configuration Debug --report artifacts/module07-debug.json
python -m mkdocs build --strict --site-dir /tmp/fullstack-site
```

Gate chạy19sample, contracts độc lập và 4lab lỗi. Stopwatch không được dùng làm ngưỡng pass/fail; heap hòa không hứa FIFO. Không chứng nhận mọi bài tập, benchmark, MST implementation hoặc concurrency. Human review tiếp tục kiểm beginner clarity. [Tiến độ](../PROGRESS.md).
