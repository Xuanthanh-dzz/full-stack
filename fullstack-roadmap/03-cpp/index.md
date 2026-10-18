# Module 03 — C++20: object, ownership và thư viện chuẩn

14 bài giữ baseline C++20. Entry check: từ Module 02, vẽ owner/borrow, giải thích lifetime, build nhiều file và giữ state khi lỗi. Bắt đầu [bài 01](./01-tu-c-sang-cpp20.md); học Beginner core trước, Deep Dive có thể quay lại.

## Đánh giá theo cụm

| Cụm | Failure Lab | Review |
|---|---|---|
| 01–05 | [Copy owner](./failure-labs/01-copy-raw-owner.md) | [Review 01](./reviews/review-01.md) |
| 06–10 | [Vector invalidation](./failure-labs/02-vector-invalidation.md) | [Review 02](./reviews/review-02.md) |
| 11–14 | [RAII và rollback](./failure-labs/03-raii-khong-rollback.md) | [Review 03](./reviews/review-03.md) |

Cuối module làm [PR Review](./pr-review-labs/01-library.md). Exit check: tự thêm một loại tài liệu, trace ownership, kiểm tra duplicate/borrow/return/path lỗi và giải thích cost report. Không thêm shared ownership khi chưa có owner thứ hai.

## Rubric capstone

| Nhóm | Điểm | Evidence |
|---|---:|---|
| Correctness | 25 | mượn/trả và report đúng |
| Contract/state | 15 | validate trước commit |
| Ownership/safety | 20 | không leak/dangling, virtual destructor |
| Failure tests | 15 | duplicate, unknown ID, path lỗi |
| Cost/judgment | 10 | quét item × loan và driver index |
| Readability | 10 | operation và trách nhiệm rõ |
| Reproducibility | 5 | compiler/input/output |

## Kiểm chứng

Từ repository root:

```bash
python scripts/verify_module_03.py --report /tmp/module03.json
python scripts/verify_module_03.py --sanitize --report /tmp/module03-sanitizers.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict
```

Docs dependencies ở requirements-docs.txt. Gate compile/run chương trình chính, contract chọn lọc, compile rejection và tái hiện lab lỗi; không chứng minh mọi lời giải bài tập hay chất lượng giảng dạy. Maintainer review riêng. Artifact không tăng [lesson completed](../PROGRESS.md).
