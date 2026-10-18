# Module 08 — SQL và cơ sở dữ liệu

25 bài SQL Server 2025 / T-SQL, từ mô hình quan hệ tới dự án CSDL thương mại điện tử. Bắt đầu từ [mô hình quan hệ và cài đặt SQL Server](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md); đọc Beginner core trước, Working Developer khi đã tự chạy được lab, Deep Dive để quay lại khi có câu hỏi cụ thể.

> **Trạng thái retrofit v4:** bài 01–06 đã theo Lesson Authoring Standard v4 và có checkpoint cụm 01–05. Bài 07–25 vẫn ở định dạng cũ, nội dung và lab vẫn chạy được; checkpoint các cụm sau sẽ thêm khi retrofit tới (xem [PROGRESS](../PROGRESS.md#retrofit-module-0108-khong-tang-lesson-completed)).

## Entry check

Không nhìn tài liệu, tự làm trong 30 phút:

1. Viết một class C# `Order` có `Customer` và danh sách `OrderLine`, rồi chỉ ra dữ liệu nào bị lặp nếu lưu mọi thứ trong một bảng tính phẳng.
2. Với `List<Product>`, viết bằng vòng lặp: lọc sản phẩm đang bán, sắp theo giá giảm dần, lấy phần tử 4–6.
3. Nêu khác nhau giữa `null` của reference type và `int?` trong C#.
4. Ước lượng Big-O của tìm một phần tử trong mảng chưa sắp và trong `Dictionary` (Module 07).

Nếu chưa làm được câu 2–3, ôn Module 04–05 trước; câu 4 cần cho phần index và tối ưu truy vấn.

## Cadence đánh giá

| Cụm | Failure Lab | Spaced Review |
|---|---|---|
| 01–05 | [Bộ lọc sản phẩm trả sai tập hàng](./failure-labs/01-bo-loc-san-pham-tra-sai-tap-hang.md) | [Nền tảng truy vấn](./reviews/review-01-nen-tang-truy-van.md) |
| 06–10 | chưa có — thêm khi retrofit tới bài 10 | chưa có |
| 11–15 | chưa có | chưa có |
| 16–20 | chưa có | chưa có |
| 21–25 | chưa có | chưa có |

Artifact bổ trợ không tăng lesson completed.

## Exit check

Không nhìn code: thiết kế schema cho đơn hàng có khách, sản phẩm, dòng đơn và thanh toán; viết query doanh thu theo tháng có khoảng thời gian nửa mở; chọn index cho trang danh sách đơn của một khách và chứng minh bằng execution plan; giải thích một deadlock giữa hai transaction. Mỗi câu trả lời phải kèm script chạy được trên container lab và output thật.

## Rubric capstone

| Nhóm | Điểm | Evidence |
|---|---:|---|
| Correctness | 25 | query trả đúng tập hàng, kể cả `NULL` và biên thời gian |
| Schema và constraint | 20 | key, foreign key, `CHECK`, `UNIQUE` có tên, nullable có lý do |
| Transaction và concurrency | 15 | ranh giới transaction, isolation level, xử lý xung đột |
| Index và cost | 15 | index theo access pattern, plan trước/sau |
| Security | 10 | parameter hóa, quyền tối thiểu |
| Migration và vận hành | 10 | script chạy lại được, backup/restore |
| Reproducibility | 5 | image, lệnh chạy, output |

## Kiểm chứng

Từ repository root, cần Docker và Python:

```bash
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=$MODULE08_SA_PASSWORD" \
  --name module08-sql -p 1433:1433 -d mcr.microsoft.com/mssql/server:2025-latest
MODULE08_SQL_CONTAINER=module08-sql python scripts/verify_module_08.py
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict
```

`MODULE08_SA_PASSWORD` là mật khẩu `sa` của container lab cục bộ, đặt trong biến môi trường của shell. Gate chạy block SQL lớn nhất của mỗi bài trên SQL Server 2025 sạch, kiểm tra section và link. Snippet giải thích, failure lab và bài tập không được gate chạy tự động; maintainer vẫn phải review chất lượng giải thích. [PROGRESS](../PROGRESS.md).
