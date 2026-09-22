# Spaced Review — sau bài 05

Làm ngay sau cụm, sau 2–3 ngày và sau một tuần. Đóng bài ở lượt đầu; lưu câu trả lời ban đầu trước khi chạy kiểm chứng.

## Retrieval

1. So sánh reference C++ và pointer C về đổi đích và vòng đời.
2. Nhắc lại Module 02: copy raw owner khác copy dữ liệu thế nào?
3. Vẽ hai LoyaltyAccount và this qua từng lời gọi.
4. Dự đoán thứ tự dựng/hủy member theo khai báo.
5. Nêu lúc nên Rule of Zero thay tự viết năm special member.

## Dự đoán output

1. int x=3,y=8; int& r=x; r=y; x và y là gì, r còn gắn đâu?
2. Copy IntBuffer b=a rồi đổi b[0]; a đổi không? Move b sang c thì b.size theo contract mẫu là gì?

## Debug

Một getter trả const string& tới local. Test có lúc in đúng; dùng bằng chứng vòng đời để quyết định review.

## Judgment liên module

Kho C 20 record chuyển sang C++: chọn string/vector theo value hay raw owner tự viết. Nêu phần cleanup giảm và phần validation vẫn còn.

## Self-score

Retrieval 5 × 2 điểm, prediction 2 × 2, debug 3, judgment 3: tổng 20. Chỉ đúng kết quả mà không giải thích state/cost nhận tối đa nửa điểm. Đạt từ 16 và không còn lỗi ownership nghiêm trọng thì đi tiếp; nếu chưa đạt, đọc lại phần liên quan rồi làm biến thể mới. Nộp trace, expected/actual và quyết định có driver.

[Bản đồ module](../index.md).
