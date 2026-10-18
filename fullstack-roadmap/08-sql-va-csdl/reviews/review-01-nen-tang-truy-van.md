# Spaced Review — sau bài 05

Lượt 1 ngay sau cụm 01–05; lượt 2 sau 2–3 ngày; lượt 3 sau một tuần. Đóng tài liệu ở phần retrieval, sau đó mới chạy SQL trên container lab để đối chiếu. Ghi lại câu còn nhầm và bằng chứng đã sửa hiểu lầm, không chỉ ghi điểm.

## Retrieval

1. Vẽ table `Students`, `Courses`, `Enrollments` với primary key, foreign key và composite key; đặt tên constraint theo quy ước.
2. Giải thích vì sao `Email` cần `UNIQUE` dù `CustomerId` đã là primary key, và vì sao mã số thuế nullable cần filtered unique index thay vì `UNIQUE`.
3. Nêu ba nơi `NULL` làm kết quả khác trực giác: so sánh, aggregate và `NOT IN`.
4. Viết chuỗi thao tác an toàn để đổi giá một sản phẩm trên production, có `OUTPUT`.
5. So sánh offset và keyset pagination theo cost và độ ổn định khi dữ liệu thay đổi.

## Dự đoán output

1. Table có 3 hàng `Score`: `10`, `NULL`, `20`. Dự đoán `COUNT(*)`, `COUNT(Score)`, `AVG(Score)` và số hàng của `WHERE Score <> 10`.
2. Identity bắt đầu từ 1; insert 2 hàng hợp lệ, rồi một câu insert 2 hàng mà hàng thứ hai vi phạm `CHECK`, rồi insert 1 hàng hợp lệ. Dự đoán số hàng và id của hàng cuối.

## Debug

Báo cáo “doanh thu tháng 2” dùng `WHERE OrderedAt BETWEEN '2026-02-01' AND '2026-02-28' AND Status = 'Paid' OR Status = 'Refunded'`. Chỉ ra hai lỗi độc lập, đưa dữ liệu mẫu tối thiểu chứng minh từng lỗi và viết lại điều kiện.

## Judgment liên module

Validation C# (Module 06) đã kiểm tra giá không âm và email hợp lệ. Đồng nghiệp đề xuất bỏ `CHECK` và `UNIQUE` trong database để migration nhanh hơn. Viết quyết định ngắn: giữ hay bỏ từng ràng buộc, dựa trên số writer, chi phí mỗi lần ghi và hậu quả khi dữ liệu sai đã vào table.

## Self-score

Mỗi retrieval 0–2 điểm (10), mỗi prediction 0–2 (4), debug 0–3, judgment 0–3: tổng 20. Đúng kết quả nhưng không giải thích bằng tập hàng, `UNKNOWN` hoặc constraint chỉ được một nửa điểm. Từ 16 điểm và không còn nhầm `NULL`/precedence thì sang bài 06; dưới mức đó quay lại bài liên quan và tự làm một biến thể với dữ liệu khác.

Nộp một trang: câu trả lời ban đầu, trace, output kiểm chứng, quyết định kỹ thuật và lý do. Quay lại [bản đồ Module 08](../index.md).
