# Isolation level, MVCC, lock và deadlock

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả dirty read, non-repeatable read và phantom;
- biết isolation level phổ biến của SQL Server;
- hiểu lock/blocking ở mức thực hành;
- hiểu row-versioning isolation ở mức khái niệm;
- phân biệt blocking với deadlock;
- giảm deadlock bằng access order và transaction ngắn;
- hiểu retry không thay thế việc sửa root cause.

## 2. Bài toán mở đầu

Hai request checkout cùng lúc:

```text
A: update Product 1 rồi Product 2
B: update Product 2 rồi Product 1
```

A giữ lock Product 1 chờ Product 2.

B giữ lock Product 2 chờ Product 1.

Đó là cycle: deadlock.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_20') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_20
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_20;
END;
GO

CREATE DATABASE CommerceLab08_20;
GO

ALTER DATABASE CommerceLab08_20
SET READ_COMMITTED_SNAPSHOT ON
WITH ROLLBACK IMMEDIATE;
GO

USE CommerceLab08_20;
GO

CREATE TABLE dbo.Inventory
(
    ProductId int NOT NULL
        CONSTRAINT PK_Inventory PRIMARY KEY,
    Stock int NOT NULL
);
GO

INSERT INTO dbo.Inventory VALUES
(1,100),
(2,100);
GO

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

BEGIN TRANSACTION;

UPDATE dbo.Inventory
SET Stock = Stock - 1
WHERE ProductId = 1;

COMMIT TRANSACTION;
GO

SELECT ProductId, Stock
FROM dbo.Inventory
ORDER BY ProductId;
GO
```

Deadlock lab cần hai session riêng.

Session A:

```sql
BEGIN TRAN;
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 1;
WAITFOR DELAY '00:00:05';
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 2;
COMMIT;
```

Session B:

```sql
BEGIN TRAN;
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 2;
WAITFOR DELAY '00:00:05';
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 1;
COMMIT;
```

Một session có thể bị chọn làm deadlock victim.

## 4. Giải thích cơ chế

### Lock và blocking

Session khác cần lock xung đột sẽ chờ.

Blocking không nhất thiết là bug.

### Deadlock

Deadlock cần cycle:

```text
A holds X, waits Y
B holds Y, waits X
```

SQL Server phát hiện cycle và rollback một victim.

### Isolation levels

Các level thường gặp:

- READ UNCOMMITTED;
- READ COMMITTED;
- REPEATABLE READ;
- SNAPSHOT;
- SERIALIZABLE.

### Row versioning

READ_COMMITTED_SNAPSHOT/SNAPSHOT có thể cho reader đọc version phù hợp thay vì chờ writer trong nhiều trường hợp.

Writer-writer conflict vẫn tồn tại.

## 5. Kiến thức nền

### Dirty read

Đọc dữ liệu chưa commit.

### Non-repeatable read

Cùng row, đọc hai lần thấy giá trị khác do transaction khác commit.

### Phantom

Chạy predicate hai lần thấy tập row thay đổi.

### Retry

Retry deadlock victim phải có giới hạn, logging và idempotency phù hợp.

## 6. Lỗi thường gặp

### NOLOCK để fix blocking

Có thể đọc dữ liệu không nhất quán.

### Access order khác nhau

Tăng nguy cơ deadlock.

### Giữ transaction khi chờ network

Kéo dài lock lifetime.

### Nghĩ snapshot không có conflict

Writer conflict vẫn có.

## 7. Bài tập

### Bài 1

Chạy deadlock lab bằng hai terminal.

### Bài 2

Sửa hai transaction cùng update ProductId theo thứ tự tăng.

### Bài 3

So READ COMMITTED với READ_COMMITTED_SNAPSHOT.

### Bài 4

Viết retry pseudocode cho error 1205.

### Bài 5

Nêu khi nào blocking là behavior đúng.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt blocking và deadlock.
- [ ] Tôi biết isolation level chính.
- [ ] Tôi hiểu dirty/non-repeatable/phantom.
- [ ] Tôi hiểu row versioning ở mức khái niệm.
- [ ] Tôi không dùng NOLOCK theo thói quen.
- [ ] Tôi giảm deadlock bằng transaction ngắn và access order nhất quán.

Điều hướng:

- Bài trước: [Transaction và ACID](./19-transaction-va-acid.md)
- Bài tiếp theo: [Execution plan và statistics](./21-execution-plan-va-statistics.md)
