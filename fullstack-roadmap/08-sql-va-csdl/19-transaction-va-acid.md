# Transaction và ACID

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Transaction nhóm thay đổi để commit hoặc rollback cùng nhau.
- Chọn boundary theo invariant của một thao tác nghiệp vụ.
- Transaction không tự sửa logic sai hoặc rollback side effect ngoài database.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng BEGIN/COMMIT/ROLLBACK;
- hiểu Atomicity, Consistency, Isolation, Durability;
- dùng TRY/CATCH và XACT_STATE;
- thiết kế transaction boundary theo business operation;
- tránh transaction quá dài;
- hiểu external side effect không được rollback bởi DB.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Ghi đơn rồi trừ kho là hai dòng trong một công việc. Nếu kho không đủ, xóa mọi dấu vết của công việc chưa thành công trong database; không để lại đơn lẻ loi chỉ vì INSERT đã chạy trước.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| atomicity | toàn bộ thay đổi trong transaction cùng commit hoặc rollback | order và stock |
| commit | công bố transaction thành công theo guarantee engine | COMMIT |
| rollback | hủy thay đổi chưa commit của transaction | ROLLBACK |
| XACT_STATE | trạng thái transaction:0,1,-1 | catch quyết định rollback |

### Ví dụ nhỏ — tính tay trước

Kho có 5 món. Đặt 3 món: ghi đơn, trừ kho còn 2 rồi commit. Đặt 10 món từ cùng dữ liệu ban đầu: lệnh trừ kho tác động 0 row, báo lỗi và rollback cả đơn; kho vẫn là 5. Giá trị identity có thể đã cấp dù row bị rollback.

Checkout cần:

1. tạo Order;
2. tạo OrderItems;
3. trừ Stock;
4. ghi trạng thái payment.

Nếu bước 3 lỗi nhưng 1–2 đã commit, database ở trạng thái nửa vời.

Transaction làm nhóm thay đổi thành all-or-nothing.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. SET XACT_ABORT ON cùng TRY/CATCH thiết lập đường xử lý lỗi runtime.
2. BEGIN TRANSACTION mở boundary; INSERT chưa là thành công business cuối.
3. UPDATE có điều kiện Stock>=Quantity và kiểm @@ROWCOUNT ngay sau lệnh.
4. COMMIT lưu thay đổi; catch rollback khi `XACT_STATE()` khác 0 rồi rethrow. Lock/log tồn tại theo engine/isolation; giữ transaction chờ network làm tăng blocking.

### Mini-check

Email đã gửi rồi SQL rollback: dữ liệu nào được trả lại, dữ liệu nào không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| statement đơn | một thao tác ghi theo tập | chưa nhóm nhiều bước nghiệp vụ |
| transaction DB | nhóm thay đổi trong database | không bao trùm email/HTTP |
| optimistic concurrency token | phát hiện version bị đổi | khác với conditional stock UPDATE ở sample |

### Misconception check

**Đúng hay sai?** ACID Consistency tự hiểu mọi rule nghiệp vụ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: code và constraints phải diễn đạt invariant.

</details>

**Đúng hay sai?** Rollback trả identity counter về số trước.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể có gap, không dùng identity làm số chứng từ liên tục.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** commit/rollback trace.

- **Working Developer — dùng khi làm việc:** failure state và boundary.

- **Deep Dive — có thể quay lại sau:** retry/outbox khi side effect thực sự yêu cầu.

### Transaction boundary

Bao đúng business unit.

Không giữ transaction khi chờ user, HTTP, email hoặc upload dài.

### External side effects

Database transaction không rollback email hoặc HTTP call đã gửi.

### Conditional atomic update stock

```sql
UPDATE ...
WHERE Stock >= @Quantity
```

và kiểm tra `@@ROWCOUNT` giúp tránh read-then-write race đơn giản. Đây là cập nhật có điều kiện trong một statement; không có nghĩa SQL Server bỏ write lock hay đây đã là optimistic concurrency bằng rowversion.

## 6. Lỗi thường gặp

### Quên rollback trong catch

Connection có thể giữ transaction mở.

### Transaction quá rộng

Lock lâu, blocking tăng.

### Gọi payment API trong transaction DB dài

Giữ lock khi chờ network.

### Nghĩ ACID tự xóa mọi concurrency bug

Isolation/access pattern vẫn quan trọng.

## 7. Khi nào KHÔNG dùng

Không mở transaction chờ người dùng quyết định hoặc gọi payment API chậm. Không thêm transaction rộng cho read-only một statement nếu không có yêu cầu snapshot liên statement.

## 8. Production notes & scale check

Gate kiểm thành công, nhánh thiếu kho rollback order/stock và không để transaction mở. Sample quantity là hằng dương; tham số từ ngoài cần validate dương/khác NULL. Durability vẫn phụ thuộc cấu hình delayed durability và storage; không suy ra crash recovery đã được test.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So commit point của file writer Module 06: database rollback bao những state nào mà File.Move không bao? Chọn boundary nhỏ cho checkout, để notification ở bước có contract riêng.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. XACT_STATE=-1 cho phép commit không?
2. Tại sao kiểm ROWCOUNT ngay?
3. Identity gap có nghĩa mất row không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng BEGIN/COMMIT/ROLLBACK.
- [ ] Tôi giải thích được ACID.
- [ ] Tôi dùng TRY/CATCH + XACT_STATE.
- [ ] Tôi giữ transaction ngắn.
- [ ] Tôi không giả định DB transaction rollback external side effect.
- [ ] Tôi thiết kế boundary theo business operation.

Điều hướng:

- Bài trước: [Covering, filtered và composite index](./18-covering-filtered-composite-index.md)
- Bài tiếp theo: [Isolation level, MVCC, lock và deadlock](./20-isolation-level-mvcc-lock-deadlock.md)
