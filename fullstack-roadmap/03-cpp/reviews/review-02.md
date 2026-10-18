# Spaced Review — sau bài 10

Làm ngay sau cụm, sau 2–3 ngày và sau một tuần. Đóng bài ở lượt đầu; lưu câu trả lời ban đầu trước khi chạy kiểm chứng.

## Retrieval

1. Nhắc lại reference: truyền derived thành base value khác base reference thế nào?
2. Vẽ hai interface nhìn cùng wallet.
3. Concept kiểu khác validation giá trị runtime thế nào?
4. Phân biệt size/capacity và invalidation.
5. Giải thích capture value/reference bằng vòng đời đã học.

## Dự đoán output

1. Map có A:2, đọc map[B] rồi hỏi size: dữ liệu thay thế nào?
2. Lambda capture threshold=5 theo value; đổi biến ngoài thành 9 rồi gọi: nó dùng ngưỡng nào?

## Debug

Comparator dùng >= trên total; tạo hai đơn cùng total và kiểm tra compare(x,x) thay vì chờ sort crash.

## Judgment liên module

So với tìm mã tuyến tính Module 02, có cần unordered_map cho 20 sản phẩm? Nêu workload, thứ tự output và chi phí giữ index.

## Self-score

Retrieval 5 × 2 điểm, prediction 2 × 2, debug 3, judgment 3: tổng 20. Chỉ đúng kết quả mà không giải thích state/cost nhận tối đa nửa điểm. Đạt từ 16 và không còn lỗi ownership nghiêm trọng thì đi tiếp; nếu chưa đạt, đọc lại phần liên quan rồi làm biến thể mới. Nộp trace, expected/actual và quyết định có driver.

[Bản đồ module](../index.md).
