# Generics và constraints

## 1. Mục tiêu

Sau bài này, bạn có thể:

- nhận ra bài toán đang lặp cùng một thuật toán cho nhiều type;
- khai báo và sử dụng generic class, generic interface và generic method;
- phân biệt type parameter như `TEntity` với argument type cụ thể như `Product`;
- dùng constraint để compiler biết operation nào hợp lệ trên `T`;
- chọn đúng các constraint thường gặp: `class`, `struct`, `notnull`, base class, interface và `new()`;
- giải thích type safety, boxing và mô hình bộ nhớ của một closed generic type;
- tránh tạo generic abstraction khi các type không thực sự có cùng contract.

## 2. Bài toán mở đầu

Một ứng dụng kho cần lưu `Product` theo mã `string`, rồi sắp tới còn lưu `Warehouse` theo mã `int`. Cả hai đều cần ba thao tác giống nhau:

- thêm entity và từ chối ID trùng;
- tìm entity bắt buộc phải tồn tại;
- đếm số entity.

Nếu viết `ProductStore`, sao chép thành `WarehouseStore`, rồi tiếp tục sao chép cho từng type mới, logic kiểm tra trùng và tra cứu sẽ bị lặp. Nếu thay tất cả bằng `object`, compiler không còn biết object có ID kiểu gì và caller phải cast khi lấy dữ liệu ra.

Ta cần viết thuật toán lưu trữ một lần nhưng vẫn giữ type cụ thể ở compile time. Đó là bài toán của generics; constraints sẽ mô tả chính xác contract mà thuật toán cần.

## 3. Lời giải bằng code

Tạo project .NET 9:

```bash
dotnet new console --name GenericsDemo --framework net9.0 --use-program-main
cd GenericsDemo
```

Thay `GenericsDemo.csproj` bằng:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

Thay `Program.cs` bằng:

```csharp
namespace GenericsDemo;

internal static class Program
{
    private static void Main()
    {
        var products = new EntityStore<string, Product>(
            StringComparer.OrdinalIgnoreCase);

        products.Add(new Product("KB-01", "Keyboard", price: 750_000m, stock: 25));
        products.Add(new Product("MS-02", "Mouse", price: 320_000m, stock: 12));

        // Store giữ type Product; không cần cast object khi lấy ra.
        Product keyboard = products.GetRequired("kb-01");

        Console.WriteLine($"Product count: {products.Count}");
        Console.WriteLine(
            $"Found: {keyboard.Sku} | {keyboard.Name} | stock {keyboard.Stock}");

        int largerStock = GenericAlgorithms.GreaterOf(keyboard.Stock, 12);
        Console.WriteLine($"Larger stock: {largerStock}");

        // Cùng một generic class được đóng bằng cặp type khác.
        var warehouses = new EntityStore<int, Warehouse>(
            EqualityComparer<int>.Default);
        warehouses.Add(new Warehouse(7, "Da Nang"));

        Warehouse warehouse = warehouses.GetRequired(7);
        Console.WriteLine($"Warehouse: {warehouse.Id} | {warehouse.City}");

        // new() constraint cho phép generic code gọi new T().
        SequenceNumber sequence = ObjectFactory.Create<SequenceNumber>();
        Console.WriteLine($"First sequence: {sequence.Next()}");
    }
}

internal interface IEntity<TKey>
{
    TKey Id { get; }
}

internal sealed class EntityStore<TKey, TEntity>
    where TKey : notnull
    where TEntity : class, IEntity<TKey>
{
    private readonly Dictionary<TKey, TEntity> _items;

    public int Count => _items.Count;

    public EntityStore(IEqualityComparer<TKey> comparer)
    {
        ArgumentNullException.ThrowIfNull(comparer);
        _items = new Dictionary<TKey, TEntity>(comparer);
    }

    public void Add(TEntity entity)
    {
        ArgumentNullException.ThrowIfNull(entity);

        if (!_items.TryAdd(entity.Id, entity))
        {
            throw new InvalidOperationException(
                $"Entity with ID '{entity.Id}' already exists.");
        }
    }

    public TEntity GetRequired(TKey id)
    {
        if (!_items.TryGetValue(id, out var entity))
        {
            throw new KeyNotFoundException($"Entity with ID '{id}' was not found.");
        }

        return entity;
    }
}

internal static class GenericAlgorithms
{
    public static T GreaterOf<T>(T left, T right)
        where T : IComparable<T>
    {
        return left.CompareTo(right) >= 0 ? left : right;
    }
}

internal static class ObjectFactory
{
    public static T Create<T>() where T : new()
    {
        return new T();
    }
}

internal sealed class Product : IEntity<string>
{
    public string Sku { get; }
    public string Id => Sku;
    public string Name { get; }
    public decimal Price { get; }
    public int Stock { get; }

    public Product(string sku, string name, decimal price, int stock)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sku);
        ArgumentException.ThrowIfNullOrWhiteSpace(name);

        if (price < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(price));
        }

        if (stock < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(stock));
        }

        Sku = sku.Trim().ToUpperInvariant();
        Name = name.Trim();
        Price = price;
        Stock = stock;
    }
}

internal sealed class Warehouse : IEntity<int>
{
    public int Id { get; }
    public string City { get; }

    public Warehouse(int id, string city)
    {
        if (id <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(id));
        }

        ArgumentException.ThrowIfNullOrWhiteSpace(city);
        Id = id;
        City = city.Trim();
    }
}

internal sealed class SequenceNumber
{
    private int _current;

    public int Next()
    {
        _current = checked(_current + 1);
        return _current;
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả:

```text
Product count: 2
Found: KB-01 | Keyboard | stock 25
Larger stock: 25
Warehouse: 7 | Da Nang
First sequence: 1
```

## 4. Giải thích cơ chế

### 4.1 Type parameter và argument type

Trong khai báo:

```csharp
EntityStore<TKey, TEntity>
```

`TKey` và `TEntity` là **type parameter**: chỗ trống đại diện cho type. Tại call site:

```csharp
EntityStore<string, Product>
```

`string` và `Product` là **type argument**. Type đã điền đủ argument được gọi là closed constructed type. `EntityStore<,>` chưa điền type là open generic type và không thể dùng để tạo object trực tiếp.

Compiler kiểm tra xuyên suốt rằng dictionary nhận đúng key và entity. `products.GetRequired(...)` trả `Product`, không trả `object`, nên không cần cast và lỗi type xuất hiện lúc build thay vì muộn ở runtime.

### 4.2 Generic class và generic interface phối hợp

Constraint:

```csharp
where TEntity : class, IEntity<TKey>
```

nói rằng `TEntity` phải là reference type và implement `IEntity<TKey>`. Vì thế compiler cho phép generic code đọc `entity.Id`. Nếu bỏ `IEntity<TKey>`, compiler chỉ biết `TEntity` là một type chưa xác định và câu `entity.Id` không compile.

`Product : IEntity<string>` và `Warehouse : IEntity<int>` cung cấp cùng contract với key type khác nhau. Ta tái sử dụng logic lưu trữ vì hai type thật sự có chung operation mà store cần, không phải vì tên class trông giống nhau.

Constructor còn nhận `IEqualityComparer<TKey>`, tức strategy quyết định hai key có bằng nhau và tạo hash như thế nào. `StringComparer.OrdinalIgnoreCase` làm `"KB-01"` và `"kb-01"` là cùng key theo so sánh ordinal không phân biệt hoa/thường; `EqualityComparer<int>.Default` dùng equality mặc định của `int`. Store không tự ghi cứng policy equality cho mọi key type.

### 4.3 Constraint `notnull` của key

`Dictionary<TKey, TValue>` yêu cầu key không phải `null`. Constraint:

```csharp
where TKey : notnull
```

đưa yêu cầu đó vào API generic. Khi nullable analysis được bật, compiler cảnh báo nếu caller cố dùng một key type cho phép `null`. `notnull` là ràng buộc compile-time phục vụ phân tích; nó không thay thế validation dữ liệu ở mọi boundary. Nullable reference type sẽ được học đầy đủ ở [bài 06](./06-nullable-reference-type.md).

### 4.4 Generic method và interface constraint

`GreaterOf<T>` cần so sánh hai value nhưng không thể giả định mọi type có toán tử `>`:

```csharp
public static T GreaterOf<T>(T left, T right)
    where T : IComparable<T>
```

Constraint `IComparable<T>` cho compiler quyền gọi `left.CompareTo(right)`. `int`, `decimal`, `string` và nhiều type .NET đã implement contract này. Một type không implement sẽ bị từ chối ngay tại call site.

### 4.5 Constraint `new()`

Generic code chỉ được gọi `new T()` khi có:

```csharp
where T : new()
```

Type argument phải có public parameterless constructor và không được là abstract class. `new()` phải đứng cuối danh sách constraint. Factory minh họa cơ chế ngôn ngữ; trong code nghiệp vụ, một factory object/interface có contract tạo object đầy đủ thường rõ hơn việc ép mọi type có constructor rỗng.

### 4.6 Mô hình bộ nhớ

Sau khi thêm hai product, mô hình logic là:

```text
Main locals / registers                         Managed heap
+--------------------------+                    +---------------------------+
| products: reference -----+------------------->| EntityStore<string,       |
| keyboard: reference -----+-----------+        | Product> object H1        |
+--------------------------+           |        | _items: ref ----+         |
                                       |        +------------------|---------+
                                       |                           v
                                       |        +---------------------------+
                                       |        | Dictionary object H2      |
                                       |        | "KB-01" -> ref H3 -------+--+
                                       |        | "MS-02" -> ref H4        |  |
                                       |        +---------------------------+  |
                                       |                                       |
                                       +---------------------------------------+
                                                                               v
                                                    H3 Product { Sku, Name,
                                                                 Price, Stock }
```

`new EntityStore...` tạo store object H1; constructor tạo dictionary H2. Mỗi `new Product(...)` tạo product object riêng H3/H4. Dictionary giữ reference đến product, không nhúng hay clone product. Local `keyboard` và entry của dictionary cùng trỏ H3.

Với generic value type, dữ liệu có thể nằm inline theo context. Ví dụ `List<int>` giữ các `int` trong array nội bộ và không cần box từng phần tử thành `object`. .NET giữ thông tin về closed generic type ở runtime; JIT thường tạo code chuyên biệt cho value type và có thể chia sẻ code cho nhiều reference type. Đừng dựa vào chi tiết JIT cụ thể nếu chưa đo.

## 5. Kiến thức nền

### Các constraint thường gặp

| Constraint | Ý nghĩa chính |
|---|---|
| `where T : class` | `T` là non-nullable reference type trong nullable context |
| `where T : struct` | `T` là non-nullable value type |
| `where T : notnull` | `T` không nên nhận `null` theo nullable analysis |
| `where T : BaseType` | `T` kế thừa base class đó |
| `where T : IContract` | `T` implement interface đó |
| `where T : unmanaged` | `T` là unmanaged value type, không chứa managed reference |
| `where T : new()` | `T` có public parameterless constructor |

Có thể ghép constraint theo quy tắc thứ tự của C#: constraint về kind/base đứng trước, các interface tiếp theo, `new()` cuối. Chỉ thêm constraint mà thuật toán thực sự cần; constraint quá mạnh loại bỏ caller hợp lệ.

### Generic type khác overload

Overload tạo nhiều implementation được chọn theo parameter list. Generic tạo một thuật toán được type-check theo type parameter. Hai cơ chế có thể phối hợp nhưng không thay thế nhau. Nếu `int` cần thuật toán hoàn toàn khác `string`, overload hoặc strategy riêng có thể rõ hơn một generic chứa nhiều kiểm tra type.

### Invariance mặc định

Ngay cả khi `Dog : Animal`, `List<Dog>` không phải `List<Animal>`. Nếu cho phép, code nhận `List<Animal>` có thể thêm `Cat` vào list vốn chỉ chấp nhận `Dog`. Variance của generic interface sẽ được học ở bài riêng; ở đây hãy coi generic class mutable là invariant mặc định.

### Generics và boxing

`List<int>` biết element là `int`, nên lưu value trực tiếp trong array `int[]`. Collection cũ nhận `object` phải box từng `int`. Generics thường tránh cast và nhiều boxing, nhưng một generic operation chuyển `T` sang interface/`object` vẫn có thể box tùy constraint và cách JIT sinh code. Luôn đo khi hiệu năng quan trọng.

## 6. Lỗi thường gặp

### Dùng `object` rồi cast thay cho generic

API `object Add(object value)` mất type safety và có thể ném `InvalidCastException` muộn. Nếu input/output giữ cùng type logic, dùng `T` để compiler bảo toàn quan hệ đó.

### Quên constraint nhưng gọi member trên `T`

Compiler không cho `value.Id` chỉ vì mọi type hiện tại tình cờ có `Id`. Hãy tạo interface/base contract và constraint rõ ràng.

### Thêm `new()` chỉ để tạo object cho tiện

Constructor rỗng thường không đủ thiết lập invariant/dependency. Chỉ dùng `new()` khi đó thật sự là contract; nếu cần input, dùng factory object/interface hoặc thiết kế API khác.

### Nghĩ `notnull` là runtime guard

`notnull` không tự chèn `if (key is null)`. Nó chủ yếu điều khiển cảnh báo nullable tại compile time. Boundary nhận dữ liệu ngoài vẫn cần validation phù hợp.

### Tạo generic cho hai workflow khác bản chất

`Save<T>` chứa chuỗi `if (typeof(T) == ...)` dài thường cho thấy các type không có cùng contract. Tách strategy/implementation thay vì che khác biệt bằng một chữ `T`.

### Giả định mọi generic đều không allocation

Store, dictionary, array nội bộ và entity trong ví dụ vẫn là object. Generics giúp giữ type và có thể tránh boxing; nó không biến mọi thao tác thành zero-allocation.

## 7. Bài tập

### Bài 1 — Generic `Pair<TFirst, TSecond>`

Tạo class giữ hai value khác type, có get-only property và method `Swap` chỉ khi hai phía cùng type bằng một class `Pair<T>` riêng.

**Gợi ý:** phân biệt vì sao `Pair<TFirst,TSecond>` không thể luôn trả cùng type sau khi đảo nếu hai argument type khác nhau.

### Bài 2 — Kho khách hàng

Tạo `Customer : IEntity<Guid>`, lưu ba customer trong `EntityStore<Guid, Customer>` và thử thêm ID trùng.

**Gợi ý:** dự đoán exception trước khi chạy; không sửa generic store theo riêng `Customer`.

### Bài 3 — Giá trị nhỏ hơn

Viết `SmallerOf<T>` với constraint nhỏ nhất cần thiết, kiểm tra bằng `int`, `decimal` và `DateTime`.

**Gợi ý:** dùng `IComparable<T>`; không dùng `dynamic` hoặc kiểm tra `typeof`.

### Bài 4 — Factory có invariant

Phân tích vì sao `new()` không phù hợp để tạo `BankAccount` bắt buộc owner/opening balance. Thiết kế lại factory nhận các dữ liệu cần thiết mà chưa dùng lambda.

**Gợi ý:** một generic method có thể nhận object factory qua interface; so sánh độ rõ với constructor rỗng.

### Bài 5 — Vẽ object graph

Tạo một store chứa hai biến cùng trỏ một `Product`, rồi vẽ store, dictionary, entry, local và product object.

**Gợi ý:** mỗi `new` class/array có nhãn H riêng; assignment reference không thêm H.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt type parameter và type argument.
- [ ] Tôi viết được generic class, interface và method có type safety.
- [ ] Tôi thêm constraint vì operation cụ thể, không theo thói quen.
- [ ] Tôi giải thích được `class`, `struct`, `notnull`, interface và `new()` constraint.
- [ ] Tôi biết `List<int>` không phải `List<object>` và không mặc định covariant.
- [ ] Tôi vẽ được generic store, dictionary và entity reference trong bộ nhớ.
- [ ] Tôi hiểu generics có thể tránh boxing nhưng không bảo đảm zero-allocation.

Điều hướng:

- Bài tiên quyết: [Collection: List, Dictionary, HashSet, Queue và Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Ôn mô hình bộ nhớ: [Stack, heap, value type và reference type](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md)
- Bài tiếp theo: [Delegate, Action, Func và Predicate](./02-delegate-action-func-predicate.md)
