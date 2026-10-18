# Spaced Review — sau bài 05

Lượt 1 sau cụm; lượt 2 sau 2–3 ngày; lượt 3 sau một tuần. Đóng tài liệu ở lượt retrieval, sau đó mới chạy ví dụ để đối chiếu. Ghi câu còn nhầm và bằng chứng sửa hiểu lầm, không chỉ điểm.

## Retrieval

1. Vẽ riêng giá trị, địa chỉ và object qua một phép gán *p.
2. Nhắc lại truyền giá trị Module 01: vì sao pointer parameter vẫn là bản sao?
3. Viết contract pointer + count cho mảng rỗng.
4. Vẽ output pointer hai tầng và nguồn dữ liệu mượn.
5. Giải thích callback chạy ở đâu trong chương trình đồng bộ.

## Dự đoán output

1. int x = 4; int *p = &x; int *q = p; *q = 8; dự đoán x và *p.
2. Hàm nhận int *p rồi gán p = NULL; dự đoán pointer caller trước/sau.

## Debug

Hàm tổng dùng sizeof(values) / sizeof(values[0]) trong tham số int *values. Chỉ ra thông tin đã mất và đề xuất contract/test để bắt lỗi.

## Judgment liên module

Bạn chỉ cần chọn một trong hai công thức ít thay đổi cho bài hóa đơn Module 01. Chọn if hay callback, nêu driver thay đổi và cost đọc code.

## Self-score

Mỗi retrieval 0–2 điểm (10), mỗi prediction 0–2 (4), debug 0–3, judgment 0–3: tổng 20. Đúng kết quả nhưng không giải thích state/vòng đời chỉ được một nửa điểm. Từ 16 điểm và không còn lỗi ownership nghiêm trọng thì đi tiếp; dưới mức đó quay lại bài liên quan rồi tự làm biến thể khác.

Nộp một trang: câu trả lời ban đầu, trace, kết quả kiểm chứng, quyết định kỹ thuật và lý do. [Bản đồ module](../index.md).
