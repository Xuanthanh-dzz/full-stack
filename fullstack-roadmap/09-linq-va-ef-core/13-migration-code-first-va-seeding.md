# Migration, Code First và seeding

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/.NET major update, provider breaking change, migration/query behavior change, sample CI failure

## TL;DR

- Migration là versioned schema change; generated migration phải được review/test, không phải truth bất khả sai.
- Local dev có thể dùng `dotnet ef database update`; production nên chọn script/bundle/deployment job theo governance.
- EF Core 10 hỗ trợ `UseSeeding`/`UseAsyncSeeding`; seed runtime phải idempotent và không biến app startup thành schema-admin.

## 1. Mục tiêu

- cài `dotnet-ef` 10.0.12;
- tạo migration và inspect Up/Down;
- generate idempotent SQL script/bundle;
- phân biệt `EnsureCreated` với Migrations;
- chọn seeding strategy;
- tách deployment identity khỏi runtime identity.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Code model thay đổi không tự làm database schema thay đổi. Migration là **bản ghi có version về cách đưa schema từ trạng thái cũ sang trạng thái mới**.

Ví dụ bạn thêm `OrderNumber` vào C#. Database hiện tại chưa có column này. Migration sẽ chứa operation tương ứng như `AddColumn`, tạo index, constraint...

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| migration | một bước thay đổi schema có version |
| model snapshot | ảnh chụp model EF dùng để so thay đổi |
| `Up` | cách đi từ schema cũ → mới |
| `Down` | cách rollback migration khi khả thi |
| idempotent script | script biết migration nào đã apply |
| seeding | đưa dữ liệu khởi tạo/reference vào DB |
| backfill | điền dữ liệu cho column/structure mới |

Migration không phải magic backup hay zero-downtime mechanism. Nó chỉ là cách **mô tả và apply schema evolution**.

Đổi property `Product.Name` hoặc relationship có thể làm EF generate migration destructive. Nếu CI/app tự apply mà không review, một rename có thể bị hiểu thành drop + add và mất dữ liệu.

## 3. Lời giải chạy được

Local workflow:

~~~bash
dotnet tool install dotnet-ef --version 10.0.12 --tool-path ./.tools
export COMMERCE_DB='Server=localhost;Database=CommerceLab09;...'
./.tools/dotnet-ef migrations add InitialCreate \
  --project samples/module-09/CommerceLab.Data

./.tools/dotnet-ef migrations script --idempotent \
  --project samples/module-09/CommerceLab.Data \
  --output artifacts/module09-migrations.sql
~~~

General-purpose seed có thể đặt trong `UseSeeding`/`UseAsyncSeeding`; project sample giữ `SeedData.SeedAsync` để demo/test explicit và dễ kiểm soát.

### Walkthrough: thêm `OrderNumber`

~~~text
Bước 1: sửa C# model
Order.OrderNumber

Bước 2: dotnet ef migrations add AddOrderNumber

Bước 3: EF so
current model
vs
previous model snapshot

Bước 4: sinh migration operations
AddColumn(OrderNumber)
CreateIndex(...) nếu cấu hình

Bước 5: review migration

Bước 6: generate SQL/apply

Bước 7: __EFMigrationsHistory ghi migration đã chạy
~~~

Điểm nguy hiểm: EF thấy property cũ biến mất và property mới xuất hiện có thể hiểu là **drop + add**, dù ý định thật của bạn là rename. Vì vậy generated migration luôn phải review.

## 4. Cơ chế hoạt động

### `EnsureCreated` vs Migrations

| | `EnsureCreated` | Migrations |
|---|---|---|
| Mục tiêu | tạo schema nhanh | evolve schema qua version |
| Model history | không | có |
| Production evolution | không phù hợp | phù hợp |
| Test/demo DB tạm | tiện | được nhưng nặng hơn |

### Local dev vs production

~~~text
Local:
model → migration → database update

Production:
model → reviewed migration
      → tested SQL/bundle
      → backup/rollback plan
      → deployment identity apply
~~~

Runtime app account không nhất thiết nên có quyền `ALTER TABLE`/`DROP`.

### Misconception check

**Đúng hay sai?** Migration được EF generate thì mặc định an toàn.

**Đáp án:** Sai. Tool không hiểu toàn bộ data semantics/zero-downtime requirement.

**Đúng hay sai?** `EnsureCreated` là cách nhanh hơn để production bỏ qua migration.

**Đáp án:** Sai. Nó không phải workflow schema evolution dài hạn.

### Mini-check

Nếu migration đổi nullable → NOT NULL trên 500GB data, câu hỏi đầu tiên nên là “command nào chạy?” hay “data/backfill/lock/downtime plan là gì?”

Đáp án: câu thứ hai.

Migration snapshot lưu model state; EF diff model hiện tại với snapshot để sinh operations.

`database update` apply pending migrations và ghi history table.

`UseSeeding`/`UseAsyncSeeding` chạy trong các operation initialization/migration phù hợp và được migration locking bảo vệ. Tooling/bundle vẫn dùng synchronous seeding path, nên khi dùng API này cần cấu hình cả sync/async theo guidance.

`EnsureCreated` tạo schema trực tiếp và không tương thích workflow Migrations lâu dài cho relational production.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** model change ≠ schema change; migration là versioned schema operation.

**Working developer:** review generated migration, script/bundle, seeding idempotent.

**Deep dive:** expand-contract, online schema change, long-running backfill và deployment permissions.

Module 08 đã học expand-contract, backup/restore và data migration. EF migration không thay các nguyên tắc đó.

Must know: schema migration và data backfill là hai concern có thể cần deploy nhiều bước.

Should know: migration bundle phù hợp automated deployment; SQL script phù hợp review/DBA-controlled flow.

## 6. Lỗi thường gặp

**Apply migration production ngay từ app startup không có governance.** Runtime identity phải có schema quyền cao và nhiều instance có thể cùng cạnh tranh.

**Không đọc generated migration.** Rename có thể thành drop/add.

**Dùng `HasData` cho dữ liệu lớn/dynamic.** Model-managed data có giới hạn và làm snapshot phình.

## 7. Khi nào KHÔNG dùng

Không dùng Migrations nếu database schema được DBA/khác team quản lý hoàn toàn và app chỉ database-first contract; lúc đó strategy phải thống nhất ownership.

Không `EnsureCreated` cho relational production dự định dùng Migrations.

Không seed business data thay đổi thường xuyên qua migration snapshot.

## 8. Production notes & scale check

Team nhỏ vẫn nên có deployment step riêng: generate/review migration → backup/rollback plan → apply một lần.

Runtime account không nên có `ALTER/DROP`; deployment account riêng có schema permission.

Data migration lớn cần batch/checkpoint/observability như Module 08, không nhét toàn bộ vào một migration transaction nếu gây downtime.

## 9. Bài tập kỹ thuật

1. Tạo migration thêm `OrderNumber` unique.
2. Inspect SQL script trước khi apply.
3. Viết seed idempotent cho một reference status.
4. Debug migration drop/add khi intent thật là rename.

## 10. Bài tập tích hợp liên module — Judgment

Production 500GB cần đổi nullable column thành NOT NULL. Chọn migration một bước hay expand-contract nhiều release? Nêu lock/backfill/rollback considerations.

## 11. Retrieval practice

1. Migration snapshot dùng để làm gì?
2. `EnsureCreated` khác Migrations ở đâu?
3. Vì sao migration generated phải review?
4. Khi nào script tốt hơn bundle?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi giải thích được behavior của EF Core thay vì chỉ nhớ API.
- [ ] Tôi phân biệt demo/local-dev với production.
- [ ] Tôi nêu được khi nào không nên dùng kỹ thuật.

- Bài trước: [Convention, Data Annotation và Fluent API](./12-convention-data-annotation-va-fluent-api.md)
- Bài tiếp theo: [CRUD, change tracking và Unit of Work](./14-crud-change-tracking-va-unit-of-work.md)
