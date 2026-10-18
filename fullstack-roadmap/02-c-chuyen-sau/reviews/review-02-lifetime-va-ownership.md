# Spaced Review — sau bài 10

Lượt 1 sau cụm; lượt 2 sau 2–3 ngày; lượt 3 sau một tuần. Đóng tài liệu ở lượt retrieval, sau đó mới chạy ví dụ để đối chiếu. Ghi câu còn nhầm và bằng chứng sửa hiểu lầm, không chỉ điểm.

## Retrieval

1. Phân biệt scope và storage duration bằng static local.
2. Nhớ lại bài 03: alias trỏ phần tử mảng có còn dùng được sau realloc thành công?
3. Vẽ owner và hai borrow, đánh dấu thời điểm free.
4. So sánh copy struct chứa char[32] và char *.
5. Nhắc lại enum bài 09: tag và union phải giữ quan hệ nào?

## Dự đoán output

1. int a[] = {2, 4}; int *p = a; p[1] = p[0] + 5; dự đoán mảng.
2. malloc thành công, p được free rồi đọc *p: có được ghi một output số cố định làm đáp án không? Giải thích.

## Debug

Code dùng p = realloc(p, larger) rồi return khi p == NULL. Vẽ state khi allocation thất bại; thiết kế kiểm thử có kiểm soát thay vì đợi máy hết RAM.

## Judgment liên module

Kho chỉ có tối đa 8 sản phẩm: chọn mảng cố định hay cấp phát động. Liên hệ giới hạn 5 học sinh Module 01, nêu chi phí failure paths và điều kiện khiến quyết định đổi.

## Self-score

Mỗi retrieval 0–2 điểm (10), mỗi prediction 0–2 (4), debug 0–3, judgment 0–3: tổng 20. Đúng kết quả nhưng không giải thích state/vòng đời chỉ được một nửa điểm. Từ 16 điểm và không còn lỗi ownership nghiêm trọng thì đi tiếp; dưới mức đó quay lại bài liên quan rồi tự làm biến thể khác.

Nộp một trang: câu trả lời ban đầu, trace, kết quả kiểm chứng, quyết định kỹ thuật và lý do. [Bản đồ module](../index.md).
