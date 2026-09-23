# Spaced Review — sau bài 10

Đóng tài liệu khi trả lời; sau đó đối chiếu và làm một biến thể mới.

## Retrieval

1. Nhắc lại alias bài 05 trong array class và array struct.
2. Range array tạo view hay copy?
3. Constructor/required/init bảo vệ những phần nào của invariant?
4. Upcast C# khác slicing C++ như thế nào?
5. Abstract class và interface khả năng khác nhau ở đâu?

## Dự đoán output

1. string s="sale"; string t=s.ToUpperInvariant(); s và t là gì? A😀B.Length bao nhiêu?
2. Với `ShippingMethod x = new ExpressShipping(2)`, `x.CalculateFee(2.5m)` trả gì và implementation nào chạy?

## Debug

Transfer trừ A rồi Deposit vào B=decimal.MaxValue thất bại. Chứng minh mất bảo toàn và sửa mà không thêm transaction framework.

## Judgment liên module

Hai gateway demo chỉ in log. Nếu sau Charge thì Send lỗi, kết quả đơn nên báo thế nào? Phân biệt state nghiệp vụ, log và bằng chứng provider thật.

## Self-score

Retrieval 5 × 2, prediction 2 × 2, debug 3, judgment 3: tổng 20. Kết quả đúng thiếu trace state/cost nhận tối đa nửa điểm. Từ 16 điểm và không còn nhầm alias/commit thì đi tiếp; nếu chưa đạt, đọc phần liên quan rồi làm ví dụ khác. Nộp câu trả lời, trace và test expected/actual.

[Bản đồ module](../index.md).
