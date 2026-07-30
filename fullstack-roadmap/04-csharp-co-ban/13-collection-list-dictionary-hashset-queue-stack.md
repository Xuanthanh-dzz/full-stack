# Collection: List, Dictionary, HashSet, Queue và Stack

## 1. Mục tiêu

Sau bài này, bạn có thể:

- chọn collection theo thao tác chính thay vì chọn theo thói quen;
- dùng `List<T>`, `Dictionary<TKey,TValue>`, `HashSet<T>`, `Queue<T>` và `Stack<T>`;
- giải thích thứ tự của list/queue/stack và không dựa vào thứ tự của hash collection;
- dùng `TryGetValue`, `TryAdd`, `TryDequeue` và `TryPop` cho trường hợp “không có dữ liệu” bình thường;
- hiểu equality và hash code quyết định key/phần tử có trùng trong hash collection hay không;
- ước lượng độ phức tạp căn bản của các thao tác phổ biến;
- vẽ được việc nhiều collection cùng giữ reference tới một object trên managed heap.

## 2. Bài toán mở đầu

Một kho hàng nhận đơn theo thứ tự thời gian và cần:

- giữ danh sách đơn để xuất báo cáo theo thứ tự đăng ký;
- tìm đơn nhanh theo `orderId`, không phân biệt hoa/thường;
- thu thập tập mã sản phẩm không trùng;
- xử lý đơn theo nguyên tắc vào trước, ra trước;
- hoàn tác lần xử lý gần nhất.

Một collection duy nhất không làm tốt tất cả các thao tác đó. Dùng `List<Order>` để tìm ID sẽ phải duyệt tuần tự; dùng `Dictionary` lại không diễn đạt hàng đợi FIFO hay lịch sử LIFO. Ta phối hợp năm cấu trúc, mỗi cấu trúc có một trách nhiệm rõ ràng.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir CollectionDemo
cd CollectionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay toàn bộ `Program.cs`:

```csharp
using System;
using System.Collections.Generic;

namespace CollectionDemo;

public enum OrderStatus
{
    Pending,
    Processed
}

// Immutable key: equality và hash code không đổi sau khi được thêm vào HashSet.
public sealed class ProductCode : IEquatable<ProductCode>
{
    public string Value { get; }

    public ProductCode(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        Value = value.Trim().ToUpperInvariant();
    }

    public bool Equals(ProductCode? other) =>
        other is not null &&
        StringComparer.Ordinal.Equals(Value, other.Value);

    public override bool Equals(object? obj) =>
        obj is ProductCode other && Equals(other);

    public override int GetHashCode() =>
        StringComparer.Ordinal.GetHashCode(Value);

    public override string ToString() => Value;
}

public sealed class Order
{
    public string Id { get; }
    public IReadOnlyList<ProductCode> ProductCodes { get; }
    public OrderStatus Status { get; private set; } = OrderStatus.Pending;

    public Order(string id, ProductCode[] productCodes)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentNullException.ThrowIfNull(productCodes);

        Id = id;
        // Clone tách khỏi input; wrapper chặn downcast về array rồi sửa ô.
        ProductCodes = Array.AsReadOnly((ProductCode[])productCodes.Clone());
    }

    public void MarkProcessed() => Status = OrderStatus.Processed;

    public void RestoreStatus(OrderStatus status) => Status = status;
}

public sealed class StatusChange
{
    public Order Order { get; }
    public OrderStatus PreviousStatus { get; }

    public StatusChange(Order order, OrderStatus previousStatus)
    {
        Order = order;
        PreviousStatus = previousStatus;
    }
}

public sealed class Warehouse
{
    private readonly List<Order> _registrationOrder = [];

    private readonly Dictionary<string, Order> _ordersById =
        new(StringComparer.OrdinalIgnoreCase);

    private readonly HashSet<ProductCode> _knownProductCodes = [];
    private readonly Queue<Order> _pendingOrders = [];
    private readonly Stack<StatusChange> _history = [];
    private readonly IReadOnlyList<Order> _ordersView;

    public Warehouse()
    {
        // Wrapper chỉ đọc giữ cùng backing list nhưng không thể cast về List<Order>.
        _ordersView = _registrationOrder.AsReadOnly();
    }

    public IReadOnlyList<Order> Orders => _ordersView;
    public int UniqueProductCount => _knownProductCodes.Count;
    public int PendingCount => _pendingOrders.Count;

    public bool Register(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        // Trùng ID là normal flow nên trả bool, không ném exception.
        if (!_ordersById.TryAdd(order.Id, order))
        {
            return false;
        }

        _registrationOrder.Add(order);
        _pendingOrders.Enqueue(order);

        foreach (ProductCode productCode in order.ProductCodes)
        {
            _knownProductCodes.Add(productCode); // false nếu value đã tồn tại.
        }

        return true;
    }

    public bool TryFind(string orderId, out Order? order) =>
        _ordersById.TryGetValue(orderId, out order);

    public bool TryProcessNext(out Order? processedOrder)
    {
        if (!_pendingOrders.TryDequeue(out processedOrder))
        {
            return false;
        }

        _history.Push(new StatusChange(processedOrder, processedOrder.Status));
        processedOrder.MarkProcessed();
        return true;
    }

    public bool TryUndoLastProcessing()
    {
        if (!_history.TryPop(out StatusChange? change))
        {
            return false;
        }

        change.Order.RestoreStatus(change.PreviousStatus);

        // Quyết định nghiệp vụ: đơn hoàn tác trở lại cuối hàng đợi.
        _pendingOrders.Enqueue(change.Order);
        return true;
    }
}

internal static class Program
{
    private static void Main()
    {
        var warehouse = new Warehouse();

        var first = new Order(
            "ORD-001",
            [new ProductCode("sku-a"), new ProductCode("SKU-B")]);

        var second = new Order(
            "ORD-002",
            [new ProductCode("SKU-B"), new ProductCode("sku-c")]);

        Console.WriteLine($"Register first: {warehouse.Register(first)}");
        Console.WriteLine($"Register second: {warehouse.Register(second)}");

        // Dictionary dùng comparer không phân biệt hoa/thường.
        var duplicateId = new Order("ord-001", [new ProductCode("SKU-X")]);
        Console.WriteLine($"Register duplicate ID: {warehouse.Register(duplicateId)}");

        Console.WriteLine($"Unique products: {warehouse.UniqueProductCount}");

        if (warehouse.TryFind("ord-002", out Order? found) && found is not null)
        {
            Console.WriteLine($"Found: {found.Id}");
        }

        warehouse.TryProcessNext(out Order? processedFirst);
        warehouse.TryProcessNext(out Order? processedSecond);
        Console.WriteLine($"Processed FIFO: {processedFirst?.Id}, {processedSecond?.Id}");

        warehouse.TryUndoLastProcessing();
        Console.WriteLine("Order report:");

        foreach (Order order in warehouse.Orders)
        {
            Console.WriteLine($"- {order.Id}: {order.Status}");
        }

        Console.WriteLine($"Pending after undo: {warehouse.PendingCount}");
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Kết quả:

```text
Register first: True
Register second: True
Register duplicate ID: False
Unique products: 3
Found: ORD-002
Processed FIFO: ORD-001, ORD-002
Order report:
- ORD-001: Processed
- ORD-002: Pending
Pending after undo: 1
```

## 4. Giải thích cơ chế

### Mỗi collection giải một kiểu truy cập

| Collection | Vai trò trong ví dụ | Quy tắc chính |
|---|---|---|
| `List<Order>` | báo cáo theo thứ tự đăng ký | có index, giữ thứ tự chèn |
| `Dictionary<string, Order>` | tìm theo ID | key duy nhất, tra bằng hash |
| `HashSet<ProductCode>` | loại mã sản phẩm trùng | chỉ giữ phần tử unique theo equality |
| `Queue<Order>` | hàng đợi xử lý | FIFO: enqueue sau, dequeue trước |
| `Stack<StatusChange>` | lịch sử hoàn tác | LIFO: push sau, pop trước |

`TryProcessNext` lấy `ORD-001` trước `ORD-002`. Hai thay đổi được push lên stack theo thứ tự đó; lần `TryUndoLastProcessing` đầu tiên pop thay đổi của `ORD-002`.

### Một object được nhiều collection cùng tham chiếu

`Order` là class. Mỗi lần `new Order(...)` tạo một object riêng trên managed heap. Khi đăng ký `first`, các collection sao chép **reference** đến cùng object, không clone `Order`:

```text
Warehouse object (heap)
│
├─ _registrationOrder ─> List backing array ─┐
├─ _ordersById ────────> Dictionary entries ─┼──> Order ORD-001 object
├─ _pendingOrders ─────> Queue backing array ┘       │
└─ _history ───────────> Stack backing array         ├─ Status
                                                     └─ ProductCodes array
```

Sau `processedOrder.MarkProcessed()`, đọc object qua list hoặc dictionary đều thấy `Processed`, vì các reference trỏ cùng object. Biến `duplicateId` lại trỏ tới một object khác dù `Id` giống về chữ; dictionary từ chối thêm key nên object đó không nằm trong các collection của `Warehouse`.

Các collection generic cũng là object trên heap và thường có backing storage riêng. Khi storage đầy, collection cấp phát storage lớn hơn rồi sao chép phần tử/reference. Vì vậy giữ `Capacity` quá lớn làm tốn memory, còn tăng từng phần tử vẫn có chi phí resize theo từng đợt.

### Hash, equality và bucket

`Dictionary`/`HashSet` dùng hai bước ý tưởng:

1. `GetHashCode` chọn vùng tìm kiếm (bucket).
2. `Equals` xác nhận hai key/value thực sự bằng nhau.

Hai object bằng nhau **phải** trả cùng hash code. Hai object có cùng hash code vẫn có thể không bằng nhau; collection xử lý collision bằng cách so sánh equality trong bucket.

`ProductCode("sku-b")` và `ProductCode("SKU-B")` cùng normalize thành `SKU-B`, có cùng equality và hash. `HashSet` chỉ giữ lần thêm đầu. Vì `Value` immutable, hash không thay đổi trong suốt thời gian phần tử ở set.

Dictionary ID nhận `StringComparer.OrdinalIgnoreCase` ngay lúc tạo, nên `ORD-001` và `ord-001` là cùng key. Comparer được khai báo tại collection rõ hơn việc rải `ToLower()` khắp code và tránh phụ thuộc culture.

## 5. Kiến thức nền

### API quan trọng

`List<T>`:

- `Add`, index `list[i]`, `Count`, `Remove`, `RemoveAt`, `Contains`;
- `Insert(0, value)` phải dời mọi phần tử sau nó;
- `Sort` thay đổi chính list; nếu thứ tự gốc quan trọng, hãy tạo bản sao trước.

`Dictionary<TKey,TValue>`:

- `Add` ném lỗi nếu key trùng;
- `TryAdd` trả `false` nếu key trùng;
- indexer `dictionary[key]` đọc key không có sẽ ném `KeyNotFoundException`, còn phép gán sẽ thêm hoặc ghi đè;
- `TryGetValue` là lựa chọn chuẩn khi không tìm thấy là bình thường.

`HashSet<T>`:

- `Add` trả `false` khi value đã tồn tại;
- hỗ trợ `UnionWith`, `IntersectWith`, `ExceptWith`, `IsSubsetOf`;
- không truy cập bằng index.

`Queue<T>` và `Stack<T>`:

- queue: `Enqueue`, `Dequeue`, `Peek`, cùng phiên bản `TryDequeue`/`TryPeek`;
- stack: `Push`, `Pop`, `Peek`, cùng phiên bản `TryPop`/`TryPeek`;
- `Dequeue`/`Pop` trên collection rỗng ném exception; `Try...` phù hợp cho trạng thái rỗng dự kiến.

### Độ phức tạp căn bản

Với `n` phần tử, các con số dưới đây là mô hình thường dùng của implementation .NET hiện tại:

| Thao tác | Thời gian thường kỳ vọng |
|---|---:|
| `List` đọc/ghi theo index | `O(1)` |
| `List.Add` | amortized `O(1)` |
| `List` tìm value, chèn/xóa giữa | `O(n)` |
| `Dictionary`/`HashSet` tìm, thêm, xóa | average `O(1)`, worst `O(n)` |
| `Queue.Enqueue`/`TryDequeue` | amortized `O(1)` |
| `Stack.Push`/`TryPop` | amortized `O(1)` |

“Amortized” nghĩa là đa số thao tác rẻ, thỉnh thoảng resize tốn `O(n)`, nhưng chia trên một chuỗi dài thì chi phí trung bình mỗi thao tác vẫn gần hằng số. Big-O không nói hết latency, allocation hay cache locality; module cấu trúc dữ liệu sẽ đi sâu hơn.

### Thứ tự enumeration

`List`, `Queue` và `Stack` có semantics thứ tự riêng (stack được enumerate từ đỉnh xuống). `HashSet` không cam kết thứ tự nghiệp vụ. Không dùng thứ tự enumerate của `Dictionary`/`HashSet` làm contract, kể cả khi một runtime cụ thể có vẻ ổn định. Khi output phải có thứ tự, hãy sort rõ ràng theo key/field.

### Generic collection và kiểu phần tử

`List<int>` có backing array chứa các `int` inline, không cần boxing mỗi phần tử như collection không generic cũ. `List<Order>` có backing array chứa các reference; từng `Order` là object riêng. Đây là lý do cần luôn hỏi: “collection chứa value hay chứa reference đến object nào?”.

### Read-only interface không tự tạo immutability

Chỉ khai báo một mutable `List<T>` hoặc array dưới type `IReadOnlyList<T>` không đủ bảo vệ backing collection: runtime object vẫn có thể bị downcast về type thật. Ví dụ dùng `AsReadOnly()`/`Array.AsReadOnly()` để trả wrapper chặn thao tác cấu trúc qua reference được công khai.

Wrapper đó vẫn là **shallow read-only**. `IReadOnlyList<Order>` ngăn caller `Add`, `Remove` hoặc thay ô, nhưng từng `Order` vẫn là cùng mutable object được nhiều collection tham chiếu. Sample giữ điều này để quan sát aliasing. Boundary production thường trả immutable read model/snapshot và không công khai mutation method tùy ý nếu trạng thái phải chỉ đổi qua `Warehouse`.

## 6. Lỗi thường gặp

### Chọn `List` rồi tìm tuyến tính liên tục

Nếu mỗi request đều tìm hàng nghìn phần tử theo ID, `List.Find`/vòng lặp là `O(n)`. Dùng dictionary khi key duy nhất và lookup là thao tác chính.

### Dùng indexer để kiểm tra key có tồn tại

`dictionary[key]` ném lỗi khi key không có. Tránh `ContainsKey` rồi lại indexer vì phải lookup hai lần; dùng `TryGetValue`.

### Override `Equals` nhưng quên `GetHashCode`

Hash collection có thể đặt hai value “bằng nhau” vào bucket khác. Luôn giữ contract: equal values có equal hash codes.

### Thay đổi key sau khi thêm vào hash collection

Nếu field tham gia hash bị đổi, collection tìm ở bucket mới trong khi entry còn ở bucket cũ. Thiết kế key immutable.

### Mong `HashSet` tự sắp xếp

Set bảo đảm uniqueness, không bảo đảm sorted order. Nếu cần cả tập hợp và thứ tự, sort lúc xuất hoặc chọn cấu trúc khác theo requirement.

### Vô tình chia sẻ collection mutable

Gán `List<Order> second = first;` chỉ sao chép reference; thêm qua `second` cũng làm `first` thấy thay đổi. Muốn list object riêng, tạo `new List<Order>(first)`. Lưu ý bản sao này vẫn là shallow copy: các reference `Order` bên trong vẫn dùng chung.

Đừng nghĩ cast một backing list sang `IReadOnlyList<T>` làm runtime object bất biến. Trả read-only wrapper hoặc snapshot; sau đó vẫn đánh giá riêng khả năng mutate từng element reference.

### Sửa collection trong `foreach`

Thêm/xóa trực tiếp vào collection đang enumerate thường gây `InvalidOperationException`. Thu thập thay đổi để áp dụng sau, hoặc dùng vòng lặp/index phù hợp.

## 7. Bài tập

### Bài 1 — Danh bạ theo số điện thoại

Lưu contact và tìm theo số điện thoại đã normalize.

Gợi ý: dùng `Dictionary<string, Contact>`; quyết định rõ số trùng thì từ chối hay cập nhật.

### Bài 2 — Loại tag trùng

Nhận nhiều tag không phân biệt hoa/thường, loại trùng rồi xuất theo alphabet.

Gợi ý: `HashSet<string>` với `StringComparer.OrdinalIgnoreCase`; copy sang list rồi sort khi xuất.

### Bài 3 — Hệ thống ticket FIFO

Thêm ticket vào queue, xử lý ticket đầu và không ném exception khi queue rỗng.

Gợi ý: dùng `TryDequeue`; in `Count` trước và sau thao tác.

### Bài 4 — Undo text editor

Mỗi lần thay nội dung, push trạng thái cũ vào `Stack<string>`; hỗ trợ undo nhiều lần.

Gợi ý: không push trạng thái khi nội dung mới bằng nội dung hiện tại.

### Bài 5 — Equality cho email

Tạo immutable `EmailAddress` implement `IEquatable<EmailAddress>`, sau đó dùng làm key dictionary.

Gợi ý: normalize phần domain một cách có chủ đích; viết test tay cho `Equals` và `GetHashCode` trước khi thêm vào collection.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi chọn được collection dựa trên lookup, uniqueness, FIFO hoặc LIFO.
- [ ] Tôi biết API `Try...` nào tránh exception cho normal flow.
- [ ] Tôi giải thích được average `O(1)`, `O(n)` và amortized `O(1)` ở mức cơ bản.
- [ ] Tôi giữ key dùng trong hash collection ở trạng thái immutable.
- [ ] Tôi không dựa vào thứ tự enumerate của hash collection.
- [ ] Tôi vẽ được nhiều collection cùng giữ reference tới một `Order` object.
- [ ] Tôi phân biệt shallow copy của list với clone từng object phần tử.
- [ ] Tôi đã build/run ví dụ bằng SDK .NET 9.

Bài prerequisite: [Exception và xử lý lỗi](./12-exception-va-xu-ly-loi.md).

Bài tiếp theo: [Project, solution, namespace và assembly](./14-project-solution-namespace-va-assembly.md).
