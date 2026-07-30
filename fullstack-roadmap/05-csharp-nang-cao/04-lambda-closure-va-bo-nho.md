# Lambda, closure và bộ nhớ

## 1. Mục tiêu

Sau bài này, bạn có thể:

- viết expression lambda và statement lambda phù hợp với delegate target type;
- phân biệt parameter của lambda với local variable bị capture;
- giải thích closure giữ **variable storage**, không chụp một bản sao value tại thời điểm tạo;
- dự đoán lifetime của captured local sau khi method đã return;
- tạo nhiều closure có state độc lập và tránh lỗi capture biến vòng `for`;
- dùng `static` lambda để compiler cấm capture ngoài ý muốn;
- vẽ rõ stack frame, closure object, delegate object, target và object được tham chiếu.

## 2. Bài toán mở đầu

Màn hình sản phẩm cần tạo filter từ cấu hình runtime. Người dùng đổi giá tối thiểu, filter hiện có phải dùng giá mới. Ta còn cần:

- hai counter độc lập dùng cùng logic;
- một danh sách action in đúng index `0`, `1`, `2`;
- một filter tồn kho thuần, không được vô tình giữ state bên ngoài.

Named method phù hợp khi behavior có tên ổn định. Nhưng các rule ngắn, chỉ dùng tại call site sẽ tạo nhiều method rời và khó truyền state cấu hình. Lambda cung cấp cú pháp ngắn để tạo delegate; khi lambda dùng local bên ngoài, compiler bảo toàn local đó bằng closure.

Điểm quan trọng không phải viết `=>` thật ngắn. Ta phải biết chính xác variable nào được capture, object nào được tạo và vì sao value có thể thay đổi sau khi delegate đã được tạo.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name ClosureDemo --framework net9.0 --use-program-main
cd ClosureDemo
```

Thay `ClosureDemo.csproj` bằng:

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
namespace ClosureDemo;

internal static class Program
{
    private static void Main()
    {
        var products = new List<Product>
        {
            new Product("Keyboard", price: 600m, stock: 3),
            new Product("Monitor", price: 900m, stock: 0),
            new Product("Cable", price: 100m, stock: 20)
        };

        decimal minimumPrice = 500m;

        // Lambda capture variable minimumPrice.
        Func<Product, bool> minimumPriceFilter =
            product => product.Price >= minimumPrice;

        PrintMatches("Minimum 500", products, minimumPriceFilter);

        // Closure đọc cùng storage, nên delegate thấy value 800 mới.
        minimumPrice = 800m;
        PrintMatches("Minimum 800", products, minimumPriceFilter);

        Func<int> counterA = CounterFactory.Create();
        Func<int> counterB = CounterFactory.Create();
        Console.WriteLine($"Counter A: {counterA()}, {counterA()}");
        Console.WriteLine($"Counter B: {counterB()}");

        var printers = new List<Action>();
        for (int i = 0; i < 3; i++)
        {
            // Tạo storage riêng cho từng iteration thay vì capture chung i.
            int index = i;
            printers.Add(() => Console.WriteLine($"Index: {index}"));
        }

        foreach (Action print in printers)
        {
            print();
        }

        // static lambda bị compiler cấm đọc local/this bên ngoài.
        Func<Product, bool> inStock = static product => product.Stock > 0;
        Console.WriteLine($"In-stock count: {CountMatches(products, inStock)}");
    }

    private static void PrintMatches(
        string label,
        IReadOnlyList<Product> products,
        Func<Product, bool> predicate)
    {
        var names = new List<string>();
        foreach (Product product in products)
        {
            if (predicate(product))
            {
                names.Add(product.Name);
            }
        }

        Console.WriteLine($"{label}: {string.Join(", ", names)}");
    }

    private static int CountMatches(
        IReadOnlyList<Product> products,
        Func<Product, bool> predicate)
    {
        int count = 0;
        foreach (Product product in products)
        {
            if (predicate(product))
            {
                count++;
            }
        }

        return count;
    }
}

internal static class CounterFactory
{
    public static Func<int> Create()
    {
        int count = 0;

        // Statement lambda có block và return tường minh.
        return () =>
        {
            count++;
            return count;
        };
    }
}

internal sealed class Product
{
    public string Name { get; }
    public decimal Price { get; }
    public int Stock { get; }

    public Product(string name, decimal price, int stock)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);

        if (price < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(price));
        }

        if (stock < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(stock));
        }

        Name = name.Trim();
        Price = price;
        Stock = stock;
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả chính xác:

```text
Minimum 500: Keyboard, Monitor
Minimum 800: Monitor
Counter A: 1, 2
Counter B: 1
Index: 0
Index: 1
Index: 2
In-stock count: 2
```

## 4. Giải thích cơ chế

### 4.1 Lambda được convert thành delegate

Trong:

```csharp
Func<Product, bool> filter = product => product.Price >= minimumPrice;
```

target type `Func<Product,bool>` cho compiler biết:

- parameter `product` có type `Product`;
- lambda phải trả `bool`;
- kết quả conversion là một delegate có thể được invoke như method.

`product => expression` là expression lambda; kết quả expression trở thành return value. Lambda nhiều statement dùng block:

```csharp
() =>
{
    count++;
    return count;
}
```

### 4.2 Parameter không phải captured variable

Trong filter:

- `product` là parameter mới cho mỗi invocation;
- `minimumPrice` được khai báo ở scope bên ngoài và được lambda dùng, nên bị capture.

Mỗi lần `predicate(product)` chạy, caller truyền một reference `Product` vào parameter. Parameter tồn tại trong invocation hiện tại. Ngược lại, captured storage của `minimumPrice` phải sống cùng delegate lâu hơn frame `Main` thông thường.

### 4.3 Closure giữ variable, không giữ snapshot value

Sau khi tạo delegate, code gán:

```csharp
minimumPrice = 800m;
```

Filter đọc `800`, vì code bên ngoài và lambda cùng truy cập **một storage logic**. Có thể hình dung compiler biến code thành dạng tương đương sau (tên thật là implementation detail):

```csharp
sealed class DisplayClass
{
    public decimal MinimumPrice;

    public bool Filter(Product product)
    {
        return product.Price >= MinimumPrice;
    }
}
```

Compiler không bắt buộc sinh đúng source này, nhưng phải giữ semantics chia sẻ variable. Muốn snapshot value tại thời điểm tạo, tự copy sang một local không bị thay đổi sau đó rồi capture local copy đó.

### 4.4 Sơ đồ stack, heap, delegate target và closure

Ngay sau khi tạo `minimumPriceFilter`, mô hình đơn giản hóa:

```text
Main stack frame / registers                Managed heap
+------------------------------+            +-----------------------------+
| products ref -----------------+---------->| List<Product> H1            |
| minimumPriceFilter ref -------+-----+      | entries -> Product objects |
| closure access ---------------+--+  |      +-----------------------------+
+------------------------------+  |  |
                                  |  v
                                  | +-----------------------------+
                                  | | delegate object D1          |
                                  | | method: generated Filter    |
                                  | | target ref -----------------+---+
                                  | +-----------------------------+   |
                                  |                                   v
                                  +--------------------------->+------------------+
                                                               | closure H2       |
                                                               | minimumPrice=500 |
                                                               +------------------+
```

Sau `minimumPrice = 800m`, field/storage trong H2 thành `800`. D1 vẫn trỏ H2 nên lần invoke tiếp theo thấy value mới. Local captured không còn chỉ là storage ngắn hạn trong stack frame theo mô hình thông thường; compiler hoist state cần sống lâu vào closure object hoặc representation tương đương.

### 4.5 Mỗi lần gọi factory tạo state độc lập

Mỗi invocation `CounterFactory.Create()` có local `count` riêng. Hai lần gọi tạo hai closure state logic:

```text
counterA -> delegate DA -> closure HA { count = 2 }
counterB -> delegate DB -> closure HB { count = 1 }
```

`Create` đã return nhưng HA/HB còn reachable qua delegate, nên captured count tiếp tục tồn tại. Khi delegate và mọi reference tới closure không còn reachable, các object đó mới GC-eligible.

### 4.6 Capture trong vòng `for`

Nếu viết trực tiếp:

```csharp
for (int i = 0; i < 3; i++)
{
    printers.Add(() => Console.WriteLine(i));
}
```

các lambda capture cùng variable `i`. Khi gọi sau vòng lặp, `i` đã là `3`, nên thường in `3` ba lần. Code đúng tạo `int index = i` bên trong body; mỗi iteration có storage `index` riêng được closure tương ứng capture.

Với `foreach` trong C# hiện đại, iteration variable được tạo riêng cho mỗi iteration, nhưng các mutable local khác ở ngoài vòng vẫn có thể bị capture chung. Luôn hỏi “lambda đang giữ storage nào?”, đừng học thuộc một mẹo theo tên vòng lặp.

### 4.7 `static` lambda cấm capture

```csharp
Func<Product, bool> inStock = static product => product.Stock > 0;
```

Keyword `static` khiến compiler báo lỗi nếu lambda đọc local, parameter của method chứa nó hoặc `this`. Đây là cách biểu đạt behavior thuần theo input và ngăn closure ngoài ý muốn.

Non-capturing lambda không cần target closure.

### Đào sâu (có thể quay lại sau)

Lambda không phải một nominal type riêng như class/delegate đã khai báo. C# hiện đại có thể suy ra **natural delegate type** cho nhiều lambda đủ thông tin, nên một số câu `var f = ...` hợp lệ; không phải mọi lambda đều suy ra được. Ghi target delegate rõ như ví dụ vẫn làm contract input/output dễ đọc. Bài này chỉ dùng delegate, chưa dùng expression tree.

Delegate object D1 và closure target H2 là hai vai trò khác nhau. D1 nói “gọi method nào trên target nào”; H2 chứa captured state. Một closure có thể được nhiều delegate cùng tham chiếu nếu nhiều lambda trong cùng scope capture chung state.

Compiler có thể cache delegate instance để giảm allocation, nhưng đó là tối ưu implementation; code không nên dựa vào `ReferenceEquals` giữa các delegate được tạo từ lambda.

#### Closure và concurrency

Captured variable mutable là shared state nếu delegate được gọi từ nhiều thread. `count++` không atomic; counter demo chỉ chạy tuần tự. Concurrency cần synchronization hoặc thiết kế không chia sẻ mutable state, sẽ học ở bài thread safety.

#### Lambda không đồng nghĩa LINQ

Lambda chỉ là cú pháp tạo anonymous function để convert sang delegate/expression tree. Ví dụ dùng vòng lặp thường, chưa dùng LINQ. LINQ là API khác nhận delegate/expression và sẽ được học trong module riêng.

#### Allocation phải đo

Capturing lambda thường cần closure state và delegate; non-capturing lambda có thể được cache. JIT/compiler có quyền tối ưu nếu không đổi observable behavior. Khi hot path quan trọng, đo allocation bằng profiler/benchmark thay vì kết luận chỉ từ dấu `=>`.

## 5. Kiến thức nền

### Capture value type và reference type

Capture luôn nói về variable storage. Nếu variable chứa `int`, closure giữ storage chứa `int`. Nếu variable chứa reference `Customer`, closure giữ storage chứa reference; lambda và code ngoài có thể cùng mutate object đích hoặc gán variable sang object khác.

```text
closure.CustomerSlot -> Customer H1
```

Gán slot sang H2 làm lambda thấy H2 ở lần sau. Nó không tự deep-copy H1.

### Capture `this`

Lambda trong instance method dùng instance field/property sẽ capture `this`. Delegate từ đó giữ object hiện tại reachable. Với callback sống lâu, đây có thể giữ cả object graph lớn. Có thể copy đúng dữ liệu cần vào local nhỏ hoặc dùng static lambda nhận state qua parameter/API phù hợp.

## 6. Lỗi thường gặp

### Nghĩ closure chụp value ngay lúc tạo

Closure chia sẻ variable. Nếu variable bị gán sau đó, lambda đọc value mới. Muốn snapshot, tạo local copy có lifetime/ownership rõ.

### Capture trực tiếp biến `for`

Nhiều delegate giữ cùng `i`, nên kết quả sau vòng lặp không phải từng index. Tạo local `index` trong body như code chính.

### Tạo closure trong hot loop mà không đo

Mỗi iteration có thể tạo state/delegate mới. Trước tiên viết đúng; sau đó đo và cân nhắc static lambda, reuse delegate hoặc API truyền state.

### Dùng mutable closure như global state ẩn

Behavior nhìn như một function nhưng kết quả phụ thuộc state bên ngoài thay đổi khó thấy. Giới hạn scope, đặt tên factory rõ và tránh chia sẻ closure giữa request nếu không có synchronization.

### Không thể unsubscribe anonymous lambda tương đương

```csharp
publisher.Changed += (sender, data) => Handle(data);
publisher.Changed -= (sender, data) => Handle(data);
```

Hai expression thường tạo delegate khác nên phép trừ không tìm đúng entry. Nếu cần unsubscribe, lưu delegate vào biến/field rồi dùng lại cùng instance.

### Thêm `static` nhưng rồi bỏ vì compiler báo capture

Cảnh báo đó đang cho biết behavior phụ thuộc state ngoài. Quyết định có chủ đích: truyền state thành parameter, hoặc chấp nhận closure và tài liệu hóa lifetime; đừng đổi keyword mà không hiểu ownership.

## 7. Bài tập

### Bài 1 — Filter theo khoảng giá

Tạo lambda capture `minimum` và `maximum`, lọc list bằng vòng `foreach`. Đổi cả hai value rồi gọi lại cùng delegate.

**Gợi ý:** dự đoán output dựa trên shared storage, không dựa trên value lúc tạo delegate.

### Bài 2 — Ba counter độc lập

Gọi factory ba lần, invoke theo thứ tự xen kẽ và vẽ ba closure object cùng ba delegate object.

**Gợi ý:** mỗi invocation factory tạo captured local riêng.

### Bài 3 — Sửa lỗi vòng lặp

Viết bản lỗi capture trực tiếp `i`, dự đoán output, rồi sửa bằng local copy trong body.

**Gợi ý:** gọi action sau khi vòng lặp đã kết thúc để thấy rõ lifetime của `i`.

### Bài 4 — Capture reference

Capture biến `Account account`, mutate account, rồi gán variable sang `new Account`. Vẽ closure slot trước/sau và dự đoán object lambda dùng.

**Gợi ý:** tách “mutate object H1” khỏi “gán slot reference sang H2”.

### Bài 5 — Static lambda

Chuyển ba lambda sang `static`; ghi lại lambda nào compile và state nào phải truyền thành parameter.

**Gợi ý:** static lambda chỉ dùng parameter/local bên trong thân của chính nó và static member phù hợp.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được expression lambda và statement lambda theo delegate target.
- [ ] Tôi chỉ ra parameter nào local và variable nào bị capture.
- [ ] Tôi hiểu closure giữ variable storage, không phải snapshot mặc định.
- [ ] Tôi vẽ riêng delegate object và closure target object.
- [ ] Tôi giải thích được vì sao captured local sống sau khi method return.
- [ ] Tôi tránh capture chung biến `for` khi cần value từng iteration.
- [ ] Tôi dùng `static` lambda để ngăn capture ngoài ý muốn.

Điều hướng:

- Bài tiên quyết: [Event và event handler](./03-event-va-event-handler.md)
- Ôn mô hình bộ nhớ: [Stack, heap, value type và reference type](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md)
- Bài tiếp theo: [Extension method](./05-extension-method.md)
