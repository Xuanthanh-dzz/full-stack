# Spaced Review — sau bài 15

Lượt 1 sau cụm; lượt 2 sau 2–3 ngày; lượt 3 sau một tuần. Đóng tài liệu ở lượt retrieval, sau đó mới chạy ví dụ để đối chiếu. Ghi câu còn nhầm và bằng chứng sửa hiểu lầm, không chỉ điểm.

## Retrieval

1. Nhắc lại output parameter: khi load thất bại caller được giữ state nào?
2. So sánh EOF bình thường và lỗi đọc file.
3. Giải thích vì sao header đổi có thể đòi rebuild nhiều object.
4. Trace parse 12x với errno/end pointer và contract digits-only.
5. Vẽ ownership transfer khi remove rồi load thành công.

## Dự đoán output

1. Kho cũ có A:7; kho tạm đọc B:2 rồi gặp record sai. Theo contract capstone, kho nào còn sống và dữ liệu cuối là gì?
2. count = capacity = 4, add mã trùng: có cần tăng count hay cấp thêm buffer không? Trace thứ tự validation.

## Debug

Một PR tuyên bố total O(n) vì vòng cộng chỉ chạy n lần. Đọc inventory_validate và đếm số so sánh mã khi n = 4 rồi n = 8; sửa kết luận cho cả hàm.

## Judgment liên module

Liên hệ capstone điểm Module 01 và kho C: khi một người dùng vài chục record, file text có đủ không? Nêu driver cụ thể về đồng thời/độ bền khiến cần thay cơ chế lưu, không chỉ thêm công cụ.

## Self-score

Mỗi retrieval 0–2 điểm (10), mỗi prediction 0–2 (4), debug 0–3, judgment 0–3: tổng 20. Đúng kết quả nhưng không giải thích state/vòng đời chỉ được một nửa điểm. Từ 16 điểm và không còn lỗi ownership nghiêm trọng thì đi tiếp; dưới mức đó quay lại bài liên quan rồi tự làm biến thể khác.

Nộp một trang: câu trả lời ban đầu, trace, kết quả kiểm chứng, quyết định kỹ thuật và lý do. [Bản đồ module](../index.md).
