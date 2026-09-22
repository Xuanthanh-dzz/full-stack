# Spaced Review 01 — Dữ liệu và biểu thức

> Sau bài 05; làm lại sau 2–3 ngày và trước bài 10. Đóng tài liệu trong lượt đầu.

Module 01 chưa có module kỹ thuật trước: phần interleaving dùng kỹ năng đọc yêu cầu, tính tay và quy trình build của bài 01–02. Không giả định người học biết pointer, C# hay SQL.

## Retrieval

1. Cụm mới: một tỷ lệ còn hàng có nên dùng cùng type với số hộp không? Giải thích bằng 2/3.
2. Cụm mới: hai biến số được gán cùng giá trị có tự đổi cùng nhau không?
3. Cụm mới: tại sao thêm ngoặc không chữa được signed overflow?
4. Ôn nền: trước khi viết công thức giá vé, cần chốt ba thông tin gì với người yêu cầu?
5. Ôn nền: sau khi sửa source, làm sao biết chương trình đang chạy có chứa thay đổi đó?

## Dự đoán output

1. `int a=9; int b=a; a=2;` — in a và b được gì? Vẽ hai storage.
2. `double r=2/3;` và `double s=2.0/3;` — dự đoán hai giá trị được in với `%.2f`.

## Debug

Một phiếu hàng in “3 hộp” và “20000 đồng” vì developer chỉ sửa dòng số lượng. Viết input/output chứng minh lỗi; phân biệt sửa text demo với viết phép tính thật.

## Judgment liên module

Bạn phải chuyển quy tắc giá sang C# trong Module 04 sau này. Chọn artifact bàn giao: ảnh chụp output, source C hay pseudocode + ca kiểm tra? Chọn tối thiểu đủ dùng và bảo vệ lý do; chưa cần viết C#.

## Self-score

10 điểm: mỗi câu retrieval 1; mỗi dự đoán 1; debug 1; judgment 2 (contract 1, trade-off 1). Chỉ tự cho điểm khi có giải thích state/type hoặc bằng chứng, không chỉ chọn đáp án.

- Dưới 7: ôn [type](../03-bien-hang-so-kieu-du-lieu.md) và [operator](../05-toan-tu-va-bieu-thuc.md), rồi làm [Failure Lab 01](../failure-labs/01-tien-va-chia-nguyen.md).
- 7–8: làm lại câu sai sau 2 ngày bằng số khác.
- 9–10: tiếp tục, vẫn quay lại checkpoint ở lượt giãn cách.

Đối chiếu quy trình build với [bài 02](../02-chuong-trinh-c-dau-tien.md), contract với [bài 01](../01-bai-toan-thuat-toan-va-pseudocode.md).
