# Module 04 — C# cơ bản: runtime, state và ứng dụng console

16 bài, baseline .NET SDK9.0.121 / net9.0 / C#13. Entry check từ Module03: phân biệt copy/alias, ownership, cleanup và rollback. Bắt đầu [bài01](./01-dotnet-9-va-chuong-trinh-csharp.md); Beginner core trước, Deep Dive có thể quay lại.

## Đánh giá theo cụm

| Cụm | Failure Lab | Review |
|---|---|---|
| 01–05 | [ref và overflow](./failure-labs/01-ref-va-overflow.md) | [Review01](./reviews/review-01.md) |
| 06–10 | [Virtual và hiding](./failure-labs/02-virtual-va-member-hiding.md) | [Review02](./reviews/review-02.md) |
| 11–16 | [Shallow copy và Save](./failure-labs/03-shallow-copy-va-save.md) | [Review03](./reviews/review-03.md) |

Cuối module làm [PR Review](./pr-review-labs/01-todo.md). Exit check: chạy todo qua restart, kiểm tra input/JSON/file lỗi, trace alias và giải thích điểm commit. Chưa cần tự thiết kế framework nhiều tầng.

## Rubric capstone

| Nhóm | Điểm | Evidence |
|---|---:|---|
| Correctness | 25 | add/list/done/remove qua restart |
| Contract/state | 20 | lỗi giữ state trước persistence |
| Memory/alias | 15 | snapshot và candidate đúng |
| Failure tests | 15 | JSON, duplicate, I/O, ID exhaustion |
| Scale/judgment | 10 | single writer, O(n), durability giới hạn |
| Readability | 10 | trách nhiệm rõ, không thêm tầng vô cớ |
| Reproducibility | 5 | SDK, input, exit/output |

## Kiểm chứng

Từ repository root, cài SDK9.0.121; verifier tạo global.json trong thư mục tạm để pin SDK:

```bash
python scripts/verify_module_04.py --report /tmp/module04-release.json
python scripts/verify_module_04.py --configuration Debug --report /tmp/module04-debug.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict --site-dir /tmp/fullstack-site
```

Có thể chọn executable bằng --dotnet /path/to/dotnet. Runtime/globalization cần hỗ trợ en-US để oracle format ổn định. Bản vá9.0.121 thay9.0.119 sau chạy lại samples; không đổi net9.0/C#13. Verifier không chứng nhận breakpoint/Watch đã thao tác trong IDE, mọi bài tập mở rộng, crash durability hay chất lượng giảng dạy. Maintainer review riêng. Artifact không tăng [lesson completed](../PROGRESS.md).
