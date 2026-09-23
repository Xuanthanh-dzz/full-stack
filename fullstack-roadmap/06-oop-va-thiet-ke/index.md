# Module 06 — OOP và thiết kế

14 bài đi từ quyền sửa dữ liệu tới hợp đồng và refactor có bằng chứng. Học theo thứ tự trong menu; kiến trúc chỉ thêm khi có thay đổi hoặc failure cụ thể.

| Cụm | Failure Lab | Review |
|---|---|---|
| 01–05 | [View alias](./failure-labs/01-view.md) | [Review01](./reviews/review-01.md) |
| 06–10 | [Captive dependency](./failure-labs/02-captive.md) | [Review02](./reviews/review-02.md) |
| 11–14 | [Rounding](./failure-labs/03-rounding.md) | [Review03](./reviews/review-03.md) |

Kết thúc bằng [PR Review](./pr-review-labs/01-store.md); ôn [C# Foundation checkpoint](../05-csharp-nang-cao/career-checkpoint/index.md) khi còn hổng nền.

## Kiểm chứng

Từ repository root, SDK9.0.121:

```bash
python scripts/verify_module_06.py --report artifacts/module06-release.json
python scripts/verify_module_06.py --configuration Debug --report artifacts/module06-debug.json
python -m mkdocs build --strict --site-dir /tmp/fullstack-site
```

Verifier chạy code chính của14bài, contracts độc lập, compiler rejection và3lab lỗi. Không chứng nhận mọi lời giải bài tập, equivalence mọi input, concurrency hay crash durability. Human review vẫn phải kiểm khả năng người mới trace execution/state/cost. [Tiến độ](../PROGRESS.md).
