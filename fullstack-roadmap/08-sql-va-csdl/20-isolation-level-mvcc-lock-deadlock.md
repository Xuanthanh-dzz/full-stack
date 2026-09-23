# Isolation level, MVCC, lock và deadlock

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Isolation quy định cách transaction nhìn thấy và tương tác với thay đổi đồng thời.
- Dùng locks hoặc row versions theo guarantee cần cho thao tác.
- RCSI giảm reader–writer blocking nhưng không xóa writer conflicts hoặc deadlock.

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

### Trực giác 60 giây

Hai người giữ hai ngăn tủ khác nhau rồi cùng chờ ngăn người kia đang giữ thì không ai tiến được. Cho người đọc xem bản cũ có thể giúp họ khỏi chờ, nhưng hai người đang sửa vẫn phải phối hợp.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| blocking | chờ tài nguyên đang bị giữ xung đột | writer chờ writer |
| deadlock | vòng chờ không ai tự tiến được | A giữ1 chờ2,B giữ2 chờ1 |
| row versioning | giữ bản row phù hợp cho reader | RCSI |
| RCSI | READ COMMITTED đọc snapshot theo statement | không phải snapshot toàn transaction |

### Ví dụ nhỏ — tính tay trước

Stock 1=99,Stock 2=100 sau setup. A trừ1 ở product1 rồi chờ2; B trừ1 ở product2 rồi chờ1. Khi tạo được cycle, một transaction bị lỗi1205 và rollback; survivor trừ mỗi sản phẩm một lần.

Hai request checkout cùng lúc:

```text
A: update Product 1 rồi Product 2
B: update Product 2 rồi Product 1
```

A giữ lock Product 1 chờ Product 2.

B giữ lock Product 2 chờ Product 1.

Đó là cycle: deadlock.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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
USE CommerceLab08_20;
GO
BEGIN TRAN;
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 1;
WAITFOR DELAY '00:00:05';
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 2;
COMMIT;
```

Session B:

```sql
USE CommerceLab08_20;
GO
BEGIN TRAN;
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 2;
WAITFOR DELAY '00:00:05';
UPDATE dbo.Inventory SET Stock = Stock - 1 WHERE ProductId = 1;
COMMIT;
```

Một session có thể bị chọn làm deadlock victim.

### Walkthrough — execution / state / cost

1. Setup bật READ_COMMITTED_SNAPSHOT trong database lab riêng rồi thực hiện update mẫu.
2. Hai script phải chạy trên hai session cùng database; một session chạy tuần tự không tái hiện deadlock.
3. Detector chọn victim, rollback toàn transaction đó; code gọi cần xử lý lỗi và retry cả đơn vị công việc nếu phù hợp.
4. Version store giữ dữ liệu cũ tốn storage/cleanup; vị trí tempdb hay persistent version store phụ thuộc cấu hình ADR. Writers vẫn cần phối hợp ghi và có thể chờ nhau.

### Mini-check

SELECT lần1 dưới RCSI thấy99; writer commit98 trước SELECT lần2: có thể thấy98 không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| locking READ COMMITTED | tránh dirty read bằng cơ chế khóa đọc theo cấu hình | có thể blocking và non-repeatable read |
| RCSI | snapshot tại đầu mỗi statement | hai SELECT trong transaction có thể khác |
| SNAPSHOT | view theo transaction sau khi bắt đầu đọc dữ liệu | phải bật/cấu hình riêng, có update conflict |

### Misconception check

**Đúng hay sai?** NOLOCK nghĩa là không có khóa nào và dữ liệu chính xác hơn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể dirty/inconsistent read và vẫn có schema locks.

</details>

**Đúng hay sai?** RCSI giữ cùng ảnh chụp qua mọi SELECT trong transaction.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: RCSI theo statement, khác SNAPSHOT.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** hai-session trace.

- **Working Developer — dùng khi làm việc:** RCSI/locks và rollback.

- **Deep Dive — có thể quay lại sau:** snapshot conflict/ADR theo workload.

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

## 7. Khi nào KHÔNG dùng

Không thêm NOLOCK như cách chữa blocking mặc định. Không retry vô hạn hay chỉ chạy lại statement cuối sau deadlock victim.

## 8. Production notes & scale check

Gate dùng hai sqlcmd sessions, kiểm một lỗi1205 và state survivor; thêm reader RCSI thấy giá trị committed khi writer đang giữ thay đổi chưa commit. Không cố định victim danh tính hoặc thời gian detector. Không tuyên bố đã kiểm mọi isolation anomaly chỉ từ demo này.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Từ cycle detection Module 07 và lifetime Module 06: vẽ wait-for graph của hai session, chỉ rõ state lock sống tới lúc nào. Đề xuất cùng access order trước khi thêm retry phức tạp.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Blocking khác deadlock thế nào?
2. RCSI snapshot theo đơn vị nào?
3. Victim cần retry phạm vi nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt blocking và deadlock.
- [ ] Tôi biết isolation level chính.
- [ ] Tôi hiểu dirty/non-repeatable/phantom.
- [ ] Tôi hiểu row versioning ở mức khái niệm.
- [ ] Tôi không dùng NOLOCK theo thói quen.
- [ ] Tôi giảm deadlock bằng transaction ngắn và access order nhất quán.

Điều hướng:

- Bài trước: [Transaction và ACID](./19-transaction-va-acid.md)
- Bài tiếp theo: [Execution plan và statistics](./21-execution-plan-va-statistics.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/04-rollback.md)
- [Spaced Review](./reviews/review-04.md)
