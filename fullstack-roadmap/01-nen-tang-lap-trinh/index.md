# Module 01 — C nền tảng: học, chạy và giải thích

15 bài giữ C11, thứ tự cũ và các chương trình chính. Phần Beginner core đủ cho lượt đầu; Deep Dive có thể quay lại sau. Trước khi bắt đầu, cần compiler C hỗ trợ lệnh trong bài; phần hướng dẫn cài đặt Module 00 vẫn chưa hoàn tất.

## Entry check

Tự xác nhận: mở terminal, tạo file text, chuyển vào thư mục chứa file, chạy `cc --version`, tính tay tổng tiền từ số lượng và đơn giá. Nếu chưa làm được, ghi điểm cần hỗ trợ trước khi chạy bài đầu; không giả định đã học ngôn ngữ khác.

## Cadence đánh giá

| Cụm | Ôn giãn cách | Lab lỗi |
|---|---|---|
| 01–05 | [Review 01](./reviews/review-01-du-lieu-va-bieu-thuc.md) | [Chia nguyên](./failure-labs/01-tien-va-chia-nguyen.md) |
| 06–10 | [Review 02](./reviews/review-02-control-flow-va-ham.md) | [Sentinel bị mất](./failure-labs/02-sentinel-thanh-diem.md) |
| 11–15 | [Review 03](./reviews/review-03-state-va-debug.md) | [Biên mảng](./failure-labs/03-count-vuot-mang.md) |

Cuối module: [PR Review — Grade Import](./pr-review-labs/01-grade-import.md). Các artifact này không tăng số bài trong manifest. Vì đây là module kỹ thuật đầu tiên, review trộn kỹ năng nền/cụm trước, không đòi kiến thức module chưa học.

## Exit check

Không copy sample: nhận một tên và ba điểm, từ chối input sai, in trung bình. Chứng minh EOF giữa chừng không tạo record; trace storage của tên và caller/callee. Review một thay đổi dùng `<= count`, rồi giải thích vì sao loop phù hợp cho tối đa 5 record.

## Rubric capstone

| Nhóm | Điểm | Evidence |
|---|---:|---|
| Correctness | 25 | session thêm/liệt kê/tìm/thoát |
| Data/contract | 15 | count, capacity và miền điểm |
| Failure handling | 10 | EOF, dòng dài, input sai |
| Tests | 15 | expected output, status, regression |
| Performance | 10 | số lượt duyệt, bộ nhớ theo capacity |
| Safety | 10 | không vượt biên, terminator đúng |
| Readability | 10 | parsing/tính/in rõ trách nhiệm |
| Reproducibility | 5 | compiler, command, input |

Không đòi kiến trúc enterprise để lấy điểm.

## Kiểm chứng

Từ repository root:

```bash
python scripts/verify_module_01.py --report /tmp/module01.json
python scripts/verify_module_01.py --sanitize --report /tmp/module01-sanitizers.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict
```

Cài dependency docs từ `requirements-docs.txt` vào môi trường Python riêng. Verifier kiểm tra cấu trúc, liên kết, metadata, chương trình chính trích từ bài, output và một số contract/failure paths; không tự chứng minh toàn bộ chất lượng giảng dạy hoặc mọi lời giải bài tập. Maintainer review là gate riêng.

Bắt đầu tại [bài toán và pseudocode](./01-bai-toan-thuat-toan-va-pseudocode.md). Trạng thái retrofit toàn bộ Module 01–08 nằm trong [PROGRESS](../PROGRESS.md).
