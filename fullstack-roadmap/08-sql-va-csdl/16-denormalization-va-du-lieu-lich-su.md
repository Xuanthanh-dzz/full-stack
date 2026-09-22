# Denormalization và dữ liệu lịch sử

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt denormalization có chủ đích với duplication lỗi;
- giữ historical snapshot cho order/invoice;
- hiểu audit/history table;
- cân nhắc precomputed aggregate;
- biết khi nào không nên denormalize;
- ghi lại trade-off và source of truth.

## 2. Bài toán mở đầu

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

## 3. Lời giải bằng SQL

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

## 4. Giải thích cơ chế

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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt current state và historical fact.
- [ ] Tôi hiểu snapshot có chủ đích.
- [ ] Tôi xác định source of truth.
- [ ] Tôi biết denormalized aggregate cần consistency.
- [ ] Tôi không denormalize theo cảm tính.
- [ ] Tôi hiểu audit/history khác current table.

Điều hướng:

- Bài trước: [Chuẩn hóa](./15-chuan-hoa-1nf-2nf-3nf-bcnf.md)
- Bài tiếp theo: [Index B-tree, clustered và nonclustered](./17-index-btree-clustered-nonclustered.md)
