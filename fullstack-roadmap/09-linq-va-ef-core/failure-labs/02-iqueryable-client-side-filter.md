# Failure Lab 02 — `AsEnumerable()` làm filter chạy sai tầng

## Bối cảnh

API search product chạy ổn ở dữ liệu dev vài nghìn row nhưng production có hàng triệu product thì timeout và memory tăng mạnh.

## Code lỗi

~~~csharp
var query = db.Products
    .Where(product => product.IsActive)
    .AsEnumerable()
    .Where(product => NormalizeSku(product.Sku) == requestedSku)
    .Take(20);

var result = query.ToList();
~~~

## Triệu chứng

- generated SQL chỉ có `IsActive`; không có filter SKU;
- app process nhận rất nhiều row;
- CPU/memory application tăng;
- database query có vẻ “nhanh” nhưng request chậm.

## Cách tái hiện

1. Seed ít nhất 100.000 product.
2. Bật SQL logging.
3. Chạy query và ghi số row database trả về.
4. So với query được thiết kế lại để filter gần data source.

## Acceptance criteria

- chỉ ra chính xác operator nào đổi execution location;
- đo row count trước/sau fix;
- đưa ra ít nhất ba lựa chọn: expression translatable, normalized indexed column, hoặc materialize có chủ đích;
- giải thích khi nào mỗi lựa chọn hợp lý.

## Hints

1. `AsEnumerable()` có execute ngay không?
2. Operator sau đó gọi `Enumerable.Where` hay `Queryable.Where`?
3. `NormalizeSku` có thể biến thành computed/normalized column không?
4. Search rule có thực sự cần chạy trong C# không?

## Checklist điều tra

- [ ] static type của source sau mỗi operator;
- [ ] generated SQL;
- [ ] rows read vs rows returned;
- [ ] index/SARGability;
- [ ] provider translation support;
- [ ] security của input/search rule.

## Liên module

- Module 08: SARGability và index.
- Module 09: `IEnumerable` vs `IQueryable`, expression tree.

Không có full solution trong trang này.
