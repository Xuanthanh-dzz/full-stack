# Spaced Review — sau bài 05

Đóng tài liệu khi trả lời; sau đó đối chiếu và làm một biến thể mới.

## Retrieval

1. Từ Module 03, copy value và copy owner/reference khác nhau thế nào?
2. SDK, runtime và target framework có vai trò gì?
3. Parse thành công còn thiếu kiểm tra nghiệp vụ nào?
4. Trace continue/break của đơn 4 và 7.
5. ref parameter khác copy reference class thế nào?

## Dự đoán output

1. int x=2; Inc(x); với Inc(int value){value++;} thì x cuối bằng gì? Đổi thành ref ở cả khai báo/lời gọi thì sao?
2. Coordinate b=a rồi b.X=9; Account d=c rồi d.Balance=9: biến nguồn nào thấy thay đổi?

## Debug

TryReserveItem trừ kho trước phép nhân decimal; input cận lớn làm lỗi. Viết expected stock trước/sau và chọn điểm commit.

## Judgment liên module

So sánh hóa đơn C Module 01 với C#: chọn kiểu tiền, cận input, parse/rounding và test, không chỉ thay cú pháp.

## Self-score

Retrieval 5 × 2, prediction 2 × 2, debug 3, judgment 3: tổng 20. Kết quả đúng thiếu trace state/cost nhận tối đa nửa điểm. Từ 16 điểm và không còn nhầm alias/commit thì đi tiếp; nếu chưa đạt, đọc phần liên quan rồi làm ví dụ khác. Nộp câu trả lời, trace và test expected/actual.

[Bản đồ module](../index.md).
