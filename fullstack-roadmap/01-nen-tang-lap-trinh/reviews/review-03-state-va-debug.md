# Spaced Review 03 — State, chuỗi và debug

> Sau bài 15; làm lại sau một tuần, trước khi học sâu pointer Module 02.

## Retrieval

1. Cụm mới: tên 7 byte cần capacity nhỏ nhất bao nhiêu để là chuỗi C?
2. Cụm mới: tìm maximum trên count 0 thiếu tiền điều kiện nào?
3. Cụm mới: vì sao capstone giữ candidate trước khi ghi row chính?
4. Ôn cụm cũ: sentinel từ hàm tính phải được kiểm tra ở bước nào của caller?
5. Ôn cụm cũ: vì sao return 0 không chứng minh công thức trung bình đúng?

## Dự đoán output

1. Với mảng `[6,9,3]`, gán element index 1 thành 4. Trace tổng và maximum sau thay đổi.
2. Một danh sách đang có 2 học sinh; lần thêm thứ ba gặp EOF khi mới có hai điểm. Dự đoán count cuối và các row được list đọc.

## Debug

Bản sửa read_line ghi nội dung khi `length < capacity`, rồi đặt terminator ở `text[length]`. Dùng capacity 3 và dòng `ABC` để tìm lần ghi đầu tiên ngoài biên. Đề xuất evidence từ sanitizer và ca biên sau sửa; không cần chạy UB không có công cụ kiểm tra.

## Judgment liên module

Capstone cần giữ dữ liệu sau khi thoát. Chuẩn bị Module 02: chọn bổ sung file I/O vào ranh giới lưu trữ hay viết lại cả parser/tính điểm? Nêu invariant còn giữ và failure mode mới từ ghi file. Không yêu cầu API file trước khi học.

## Self-score

10 điểm: retrieval 5, dự đoán 2, debug 1, judgment 2 (invariant 1, failure mode/giải pháp nhỏ nhất 1).

- Dưới 7: ôn [mảng](../11-mang-mot-chieu.md), [chuỗi](../13-chuoi-ky-tu.md), [capstone](../15-du-an-console-quan-ly-diem.md).
- 7–8: làm [Failure Lab 03](../failure-labs/03-count-vuot-mang.md) và quay lại sau một tuần.
- 9–10: làm [PR review](../pr-review-labs/01-grade-import.md), tự bảo vệ lựa chọn trước người khác.

Đây là tự đánh giá kỹ năng, không phải chứng nhận năng lực production.
