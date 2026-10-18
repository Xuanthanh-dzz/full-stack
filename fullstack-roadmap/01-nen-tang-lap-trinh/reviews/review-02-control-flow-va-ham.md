# Spaced Review 02 — Input, control flow và lời gọi

> Sau bài 10; làm lại sau 3 ngày và trước capstone. Câu 4–5 kéo lại cụm 01–05 thay cho module trước chưa có.

## Retrieval

1. Cụm mới: vì sao một lần getchar không đọc được số 12 như một integer?
2. Cụm mới: cần biết gì để chứng minh while sẽ kết thúc?
3. Cụm mới: lời gọi lồng nhau giữ state nào khi đang chờ return?
4. Ôn nền: gán parameter số có thay biến caller không? Liên hệ copy ở bài 04.
5. Ôn nền: build xanh nhưng công thức cho tỷ lệ 0 có mâu thuẫn không? Giải thích hai loại kiểm chứng.

## Dự đoán output

1. `int total=0; for(int i=1;i<4;i++){total+=i;}` — total cuối bao nhiêu, bao nhiêu lượt cộng?
2. Một hàm in n trước khi gọi lại với n-1, dừng tại 0; với n=2, vẽ cả thứ tự output và thứ tự các lời gọi kết thúc.

## Debug

Menu đọc ký tự tới newline nhưng input kết thúc ngay, vòng lặp tiếp tục. Trace kết quả getchar sau EOF, ghi điều kiện dừng còn thiếu và ca regression. Không chữa bằng giới hạn thời gian tùy tiện bên trong business logic.

## Judgment liên module

Chuẩn bị đệ quy Module 07: đếm ngược từ 100000 nên dùng loop hay recursion? Nêu state cần giữ và loại chi phí tăng theo input. Khi chưa biết giới hạn stack, có nên thử chạy tới crash để kết luận “an toàn dưới mốc này” không?

## Self-score

10 điểm: retrieval 5, dự đoán 2, debug 1, judgment 2 (state 1, lựa chọn theo quy mô 1). Viết lý do trước khi mở bài.

- Dưới 7: ôn [input](../06-nhap-xuat-voi-stdio.md), [loop](../08-vong-lap-for-while-do-while.md) và [hàm](../09-ham-tham-so-gia-tri-tra-ve.md).
- 7–8: làm [Failure Lab 02](../failure-labs/02-sentinel-thanh-diem.md), quay lại sau 3 ngày.
- 9–10: tiếp tục; dùng [call stack](../10-ngan-xep-loi-goi-ham.md) để đối chiếu sơ đồ.
