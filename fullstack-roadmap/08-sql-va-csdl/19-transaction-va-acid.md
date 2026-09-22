# Transaction và ACID

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng BEGIN/COMMIT/ROLLBACK;
- hiểu Atomicity, Consistency, Isolation, Durability;
- dùng TRY/CATCH và XACT_STATE;
- thiết kế transaction boundary theo business operation;
- tránh transaction quá dài;
- hiểu external side effect không được rollback bởi DB.

## 2. Bài toán mở đầu

Checkout cần:

1. tạo Order;
2. tạo OrderItems;
3. trừ Stock;
4. ghi trạng thái payment.

Nếu bước 3 lỗi nhưng 1–2 đã commit, database ở trạng thái nửa vời.

Transaction làm nhóm thay đổi thành all-or-nothing.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_19') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_19
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_19;
END;
GO

CREATE DATABASE CommerceLab08_19;
GO
USE CommerceLab08_19;
GO

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Stock int NOT NULL
        CONSTRAINT CK_Products_Stock CHECK (Stock >= 0)
);

CREATE TABLE dbo.Orders
(
    OrderId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    Status varchar(20) NOT NULL
);
GO

INSERT INTO dbo.Products VALUES (1, 5);
GO

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    INSERT INTO dbo.Orders (Status)
    VALUES ('Pending');

    DECLARE @OrderId int = SCOPE_IDENTITY();
    DECLARE @Quantity int = 3;

    UPDATE dbo.Products
    SET Stock = Stock - @Quantity
    WHERE ProductId = 1
      AND Stock >= @Quantity;

    IF @@ROWCOUNT <> 1
        THROW 50001, 'Not enough stock.', 1;

    COMMIT TRANSACTION;

    SELECT @OrderId AS OrderId, Stock
    FROM dbo.Products
    WHERE ProductId = 1;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO

SELECT * FROM dbo.Orders;
SELECT * FROM dbo.Products;
GO
```

## 4. Giải thích cơ chế

### Atomicity

Tất cả statement thành công cùng nhau hoặc rollback.

### Consistency

Transaction chuyển database giữa các state thỏa invariant.

### Isolation

Concurrent transaction tương tác theo isolation level.

### Durability

Sau COMMIT thành công, thay đổi được bảo toàn theo guarantee của database/storage.

### XACT_ABORT

Giúp nhiều runtime error làm transaction được xử lý an toàn hơn.

## 5. Kiến thức nền

### Transaction boundary

Bao đúng business unit.

Không giữ transaction khi chờ user, HTTP, email hoặc upload dài.

### External side effects

Database transaction không rollback email hoặc HTTP call đã gửi.

### Optimistic update stock

```sql
UPDATE ...
WHERE Stock >= @Quantity
```

và kiểm tra `@@ROWCOUNT` giúp tránh read-then-write race đơn giản.

## 6. Lỗi thường gặp

### Quên rollback trong catch

Connection có thể giữ transaction mở.

### Transaction quá rộng

Lock lâu, blocking tăng.

### Gọi payment API trong transaction DB dài

Giữ lock khi chờ network.

### Nghĩ ACID tự xóa mọi concurrency bug

Isolation/access pattern vẫn quan trọng.

## 7. Bài tập

### Bài 1

Cố mua quantity 10 khi stock 5 và xác nhận Order không được tạo.

### Bài 2

Thêm OrderItems vào transaction.

### Bài 3

Tạo transfer balance giữa hai account.

### Bài 4

Giải thích boundary cho checkout + email.

### Bài 5

Viết pattern TRY/CATCH chuẩn dùng lại cho procedure.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng BEGIN/COMMIT/ROLLBACK.
- [ ] Tôi giải thích được ACID.
- [ ] Tôi dùng TRY/CATCH + XACT_STATE.
- [ ] Tôi giữ transaction ngắn.
- [ ] Tôi không giả định DB transaction rollback external side effect.
- [ ] Tôi thiết kế boundary theo business operation.

Điều hướng:

- Bài trước: [Covering, filtered và composite index](./18-covering-filtered-composite-index.md)
- Bài tiếp theo: [Isolation level, MVCC, lock và deadlock](./20-isolation-level-mvcc-lock-deadlock.md)
