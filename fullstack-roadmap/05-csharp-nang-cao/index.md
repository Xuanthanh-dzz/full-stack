# Module 05 — C# nâng cao

19 bài, SDK9.0.121 / net9.0 / C#13. Entry check: trace copy/alias, validation và lỗi lưu của [capstone Module04](../04-csharp-co-ban/16-du-an-console-csharp-quan-ly-cong-viec.md). Bắt đầu [generics](./01-generics-va-constraints.md); học Beginner core trước Deep Dive.

## Đánh giá theo cụm

| Cụm | Failure Lab | Review |
|---|---|---|
| 01–05 | [Capture](./failure-labs/01-capture.md) | [01](./reviews/review-01.md) |
| 06–10 | [Timeout](./failure-labs/02-timeout.md) | [02](./reviews/review-02.md) |
| 11–15 | [Dispose](./failure-labs/03-dispose.md) | [03](./reviews/review-03.md) |
| 16–19 | [Cancel](./failure-labs/04-cancel.md) | [04](./reviews/review-04.md) |

Exit check: hoàn thành [PR Review](./pr-review-labs/01-batch.md) và [C# Foundation](./career-checkpoint/index.md), trace task/resource/state, phân biệt lỗi input với cancellation và bảo vệ report cũ khi ghi lỗi.

## Rubric capstone

Correctness25, async/cancellation20, ownership15, failure tests15, scale/judgment10, readability10, reproducibility5: tổng100. Nộp source, SDK, lệnh, expected/actual, JSON và object/task graph; không chấm theo số pattern.

## Kiểm chứng

```bash
python scripts/verify_module_05.py --report /tmp/module05-release.json
python scripts/verify_module_05.py --configuration Debug --report /tmp/module05-debug.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict --site-dir /tmp/fullstack-site
```

Verifier pin SDK9.0.121 trong thư mục tạm; --dotnet chọn executable riêng. Build/run source chính, contracts và lab không chứng nhận mọi bài tập, thao tác IDE, AOT hoặc crash durability. Maintainer review và checkpoint người học là gate riêng. Không tăng số lesson completed trong [PROGRESS](../PROGRESS.md).
