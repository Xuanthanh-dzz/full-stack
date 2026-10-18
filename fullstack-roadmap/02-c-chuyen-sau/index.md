# Module 02 — C: con trỏ, quyền sở hữu và dữ liệu bền qua lần chạy

15 bài giữ C11 và chương trình cũ. Bắt đầu từ [con trỏ](./01-dia-chi-bo-nho-va-con-tro.md); đọc Beginner core trước, Working Developer sau khi tự trace được, Deep Dive để quay lại khi có câu hỏi cụ thể.

## Entry check

Từ Module 01, tự viết hàm tổng mảng có count; phân biệt scope, giá trị trả về, input sai và EOF. Build với warning nghiêm ngặt, chạy một test có expected output. Chưa cần biết malloc hoặc C++.

## Cadence đánh giá

| Cụm | Failure Lab | Spaced Review |
|---|---|---|
| 01–05 | [Pointer caller](./failure-labs/01-doi-pointer-khong-doi-caller.md) | [Pointer/contract](./reviews/review-01-pointer-va-contract.md) |
| 06–10 | [Alias sau free](./failure-labs/02-alias-sau-free.md) | [Vòng đời/ownership](./reviews/review-02-lifetime-va-ownership.md) |
| 11–15 | [Load mất state](./failure-labs/03-load-lam-mat-state.md) | [Build/file/commit](./reviews/review-03-build-file-va-commit.md) |

Cuối module làm [PR Review](./pr-review-labs/01-inventory-ownership.md) trước khi chuyển C++. Artifact bổ trợ không tăng lesson completed.

## Exit check

Không nhìn code: vẽ owner/borrow của một kho hai sản phẩm; trace add thất bại ở từng allocation, remove phần tử giữa và load lỗi. Chạy lại sanitizer, giải thích vì sao PASS chưa chứng minh mọi input an toàn. Đo số lượt so sánh mã trong validate trước khi kết luận complexity.

## Rubric capstone

| Nhóm | Điểm | Evidence |
|---|---:|---|
| Correctness | 25 | thêm/xóa/bán/tổng/roundtrip |
| Data và contract | 15 | count/capacity, mã duy nhất, miền số |
| Failure handling | 15 | allocation failure, file hỏng, state cũ giữ nguyên |
| Tests | 15 | assertion cụ thể và sanitizer |
| Cost | 10 | tìm mã, tăng buffer, validate trùng |
| Safety | 10 | owner/borrow, cleanup, path contract |
| Readability | 5 | header/source và trách nhiệm rõ |
| Reproducibility | 5 | compiler, Makefile, input/output |

## Kiểm chứng

Từ repository root, dùng Python và compiler hỗ trợ C11:

```bash
python scripts/verify_module_02.py --report /tmp/module02.json
python scripts/verify_module_02.py --sanitize --report /tmp/module02-sanitizers.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict
```

Dependency tài liệu ở `requirements-docs.txt`. Gate trích đúng bộ source phần 3, so output, chạy contract và tái hiện ba lỗi cố ý. Các fragment giải thích và bài tập không phải tất cả là chương trình độc lập; giới hạn evidence ghi tại `samples/module-02/README.md` trong repository. Maintainer vẫn phải review chất lượng giải thích và bài tập độc lập. [PROGRESS](../PROGRESS.md).
