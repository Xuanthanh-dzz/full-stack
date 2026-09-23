# Denormalization và dữ liệu lịch sử

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Snapshot lịch sử giữ fact tại thời điểm nghiệp vụ; dữ liệu dẫn xuất lưu thêm cần quy tắc đồng bộ.
- Dùng khi hóa đơn phải giữ giá cũ hoặc workload đã chứng minh cần đọc nhanh hơn.
- Đừng tự đồng bộ snapshot theo catalog mới; cũng đừng để aggregate copy lệch source of truth.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt denormalization có chủ đích với duplication lỗi;
- giữ historical snapshot cho order/invoice;
- hiểu audit/history table;
- cân nhắc precomputed aggregate;
- biết khi nào không nên denormalize;
- ghi lại trade-off và source of truth.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Hóa đơn đã ghi giá mua1200000 không được đổi thành1500000 chỉ vì cửa hàng tăng giá hôm nay. Đây là hai sự thật ở hai thời điểm, khác với tổng tiền được lưu thêm để đỡ cộng lại mỗi lần.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| historical fact | giá trị đúng tại thời điểm sự kiện | UnitPriceSnapshot |
| derived aggregate | giá trị tính từ các row khác | Order.TotalAmount |
| source of truth | nguồn có quyền quyết định giá trị | items hoặc quy tắc chốt đơn |
| consistency | các bản biểu diễn tuân cùng rule | tổng đơn khớp dòng hàng |

### Ví dụ nhỏ — tính tay trước

Product Keyboard Pro1200000 được copy vào item. Sau UPDATE catalog thành Keyboard Pro2/1500000, item vẫn có tên cũ/1200000. Hai mức giá khác nhau là đúng lịch sử.

Product hiện tại:

```text
Name = Keyboard Pro 2
Price = 1,500,000
```

Nhưng order năm trước đã mua:

```text
Keyboard Pro
1,200,000
```

Nếu invoice chỉ join sang Product hiện tại, lịch sử sẽ bị viết lại.

Vì vậy production database đôi lúc **cố ý lưu duplicate**.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_16') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_16
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_16;
END;
GO

CREATE DATABASE CommerceLab08_16;
GO
USE CommerceLab08_16;
GO

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL
);

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    OrderedAt datetime2(0) NOT NULL
);

CREATE TABLE dbo.OrderItems
(
    OrderId int NOT NULL,
    ProductId int NOT NULL,
    ProductNameSnapshot nvarchar(160) NOT NULL,
    UnitPriceSnapshot decimal(19,4) NOT NULL,
    Quantity int NOT NULL,
    CONSTRAINT PK_OrderItems PRIMARY KEY (OrderId, ProductId),
    CONSTRAINT FK_OrderItems_Orders
        FOREIGN KEY (OrderId) REFERENCES dbo.Orders(OrderId),
    CONSTRAINT FK_OrderItems_Products
        FOREIGN KEY (ProductId) REFERENCES dbo.Products(ProductId)
);
GO

INSERT INTO dbo.Products VALUES
(1,N'Keyboard Pro',1200000);

INSERT INTO dbo.Orders VALUES
(1001,'2025-09-01');

INSERT INTO dbo.OrderItems
(
    OrderId,
    ProductId,
    ProductNameSnapshot,
    UnitPriceSnapshot,
    Quantity
)
SELECT
    1001,
    ProductId,
    Name,
    Price,
    1
FROM dbo.Products
WHERE ProductId = 1;
GO

UPDATE dbo.Products
SET
    Name = N'Keyboard Pro 2',
    Price = 1500000
WHERE ProductId = 1;
GO

SELECT
    p.Name AS CurrentName,
    p.Price AS CurrentPrice,
    oi.ProductNameSnapshot,
    oi.UnitPriceSnapshot
FROM dbo.OrderItems AS oi
JOIN dbo.Products AS p
    ON p.ProductId = oi.ProductId
WHERE oi.OrderId = 1001;
GO
```

### Walkthrough — execution / state / cost

1. INSERT SELECT đọc giá/tên tại thời điểm statement và ghi snapshot vào item.
2. UPDATE catalog không đụng cột snapshot vì không có rule tự lan truyền.
3. JOIN cuối đặt current và historical cạnh nhau để thấy hai ý nghĩa.
4. Server giữ thêm cột/index/log; snapshot không cần refresh theo catalog, còn aggregate dẫn xuất cần protocol cập nhật hoặc tái dựng.

### Mini-check

Sửa tên catalog có nên sửa tên trên hóa đơn đã phát hành không; nếu hóa đơn gõ sai cần quy trình nào riêng?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Current state và historical fact

Product table trả lời dữ liệu hiện tại.

OrderItems trả lời khách đã mua gì và giá nào tại thời điểm đó.

Hai câu hỏi khác nhau nên duplication là hợp lệ.

### Denormalized aggregate

Có thể lưu `Orders.TotalAmount` dù tính được từ OrderItems.

Lợi ích: đọc nhanh, report đơn giản.

Chi phí: phải giữ consistency.

### Source of truth

Mỗi field denormalized phải có rule rõ source of truth và derived copy.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| historical snapshot | fact theo thời điểm | không refresh theo current state |
| cached aggregate | giá trị dẫn xuất để đọc nhanh | cần rebuild/validation và freshness policy |
| normalized current data | một nơi cho fact hiện tại | đọc có thể cần join |

### Misconception check

**Đúng hay sai?** Mọi duplication đều là lỗi thiết kế.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phải xét thời điểm và ngữ nghĩa của fact.

</details>

**Đúng hay sai?** Snapshot column tự ngăn người dùng UPDATE nó.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần quyền hoặc application contract bảo vệ.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** current/history.

- **Working Developer — dùng khi làm việc:** source of truth và repair.

- **Deep Dive — có thể quay lại sau:** read model khi đo được bottleneck.

### History table

Audit có thể lưu entity id, old/new value, actor, time và reason.

### Read model

Hệ thống lớn có thể denormalize read model mạnh để query nhanh, nhưng phải đo workload trước.

### Denormalization không miễn phí

Mỗi copy thêm storage, update path, consistency risk và migration complexity.

## 6. Lỗi thường gặp

### Denormalize trước khi có bottleneck

Làm schema phức tạp không cần thiết.

### Không document source of truth

Hai cột duplicate rồi không biết cột nào đúng.

### Recompute invoice từ catalog hiện tại

Làm sai lịch sử.

### Audit nhưng không lưu actor/time

Không đủ giá trị điều tra.

## 7. Khi nào KHÔNG dùng

Không denormalize theo dự đoán bottleneck. Không dùng cached total làm nguồn đúng khi không ai chịu trách nhiệm đồng bộ với items.

## 8. Production notes & scale check

Gate xác nhận snapshot còn nguyên sau đổi catalog. Sample một writer không chứng minh giá được khóa xuyên nhiều statement checkout; cần xác định điểm chốt giá. Audit cần actor/time/reason theo yêu cầu thật, không chỉ có old/new value.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Thiết kế snapshot shipping address trong Order.

### Bài 2

Thêm Order.TotalAmount và viết transaction cập nhật nó.

### Bài 3

Thiết kế ProductPriceHistory.

### Bài 4

Viết ADR: vì sao OrderItem cần ProductNameSnapshot.

### Bài 5

Nêu 3 trường hợp không nên denormalize.

## 10. Bài tập tích hợp liên module — Judgment

So object copy Module 05 và snapshot graph Module 07: copy dữ liệu tại thời điểm nào tạo contract đúng? Nêu khác biệt giữa immutable history và cache có thể thay thế.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Hai giá khác nhau có thể cùng đúng không?
2. Ai được sửa snapshot?
3. Aggregate copy cần rule gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt current state và historical fact.
- [ ] Tôi hiểu snapshot có chủ đích.
- [ ] Tôi xác định source of truth.
- [ ] Tôi biết denormalized aggregate cần consistency.
- [ ] Tôi không denormalize theo cảm tính.
- [ ] Tôi hiểu audit/history khác current table.

Điều hướng:

- Bài trước: [Chuẩn hóa](./15-chuan-hoa-1nf-2nf-3nf-bcnf.md)
- Bài tiếp theo: [Index B-tree, clustered và nonclustered](./17-index-btree-clustered-nonclustered.md)
