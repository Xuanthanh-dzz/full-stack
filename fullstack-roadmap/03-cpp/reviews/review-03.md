# Spaced Review — sau bài 14

Làm ngay sau cụm, sau 2–3 ngày và sau một tuần. Đóng bài ở lượt đầu; lưu câu trả lời ban đầu trước khi chạy kiểm chứng.

## Retrieval

1. Nhắc lại cleanup C: RAII thay được trách nhiệm nào và không thay rollback nào?
2. Vẽ unique owner, shared owner và weak observer.
3. Move unique_ptr khác vector<Book> reallocation về địa chỉ Book thế nào?
4. Tên tham số && là biểu thức loại gì trong thân?
5. Đếm các lượt quét loan khi report có I item và L loan.

## Dự đoán output

1. Một shared owner và một weak; owner.reset rồi weak.lock trả gì, object và control block khác nhau thế nào?
2. borrow A thành công, borrow A lần hai bị từ chối, return A: lịch sử loan còn hay bị xóa?

## Debug

PR move item vào vector rồi mới đọc item->id(). Trace owner trước/sau, đề xuất regression và sửa nhỏ.

## Judgment liên module

So với roundtrip kho C, report thư viện chưa đủ để restart. Chọn bước thêm persistence nhỏ nhất và failure contract; chưa thêm database nếu không có driver.

## Self-score

Retrieval 5 × 2 điểm, prediction 2 × 2, debug 3, judgment 3: tổng 20. Chỉ đúng kết quả mà không giải thích state/cost nhận tối đa nửa điểm. Đạt từ 16 và không còn lỗi ownership nghiêm trọng thì đi tiếp; nếu chưa đạt, đọc lại phần liên quan rồi làm biến thể mới. Nộp trace, expected/actual và quyết định có driver.

[Bản đồ module](../index.md).
