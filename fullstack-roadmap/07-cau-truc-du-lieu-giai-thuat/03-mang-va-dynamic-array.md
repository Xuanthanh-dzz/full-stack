# Mảng và dynamic array

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Dynamic array giữ buffer liên tiếp và Count logic riêng Capacity.
- Dùng khi cần index và append; preallocate khi có ước lượng hợp lý.
- Resize có lần O(n); insert/remove đầu phải dịch nhiều slot.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích mảng lưu phần tử liên tiếp và vì sao truy cập theo index có complexity `O(1)`;
- phân biệt fixed-size array với dynamic array;
- giải thích cơ chế resize của `List<T>` ở mức khái niệm;
- phân biệt `Count` và `Capacity`;
- phân tích complexity của đọc theo index, append, insert, remove và search;
- giải thích khái niệm amortized `O(1)`;
- tự cài đặt một dynamic array đơn giản để hiểu cơ chế bên trong;
- chọn `T[]` hay `List<T>` dựa trên yêu cầu thay vì thói quen.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một kệ4ô đang có 3món còn chỗ để thêm. Hết ô thì chuyển sang kệ lớn hơn; không phải tự kéo giãn chính kệ cũ. Giá chuyển kệ được chia trên nhiều lần thêm.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| backing array | buffer thực chứa slot | _items |
| Count | số slot có dữ liệu logic | index hợp lệ dưới Count |
| Capacity | số slot đã cấp | có thể lớn hơn Count |
| resize | cấp buffer mới rồi copy | EnsureCapacity |

### Ví dụ nhỏ — tính tay trước

Capacity = 2; thêm 10, 20, 30 khiến buffer tăng lên 4 và copy 2 phần tử cũ. Insert(1,15) dịch 30 rồi 20 sang phải. Remove(20) dịch 30 sang trái và xóa slot dư. Cuối cùng Count = 3, Capacity = 4.

Giả sử cần lưu danh sách sản phẩm được người dùng thêm vào giỏ hàng.

Nếu dùng array:

```csharp
Product[] items = new Product[3];
```

bạn phải biết trước số lượng tối đa. Khi người dùng thêm sản phẩm thứ tư, array hiện tại không thể "nở" thêm.

Một cách thủ công là:

1. tạo array mới lớn hơn;
2. copy dữ liệu cũ;
3. thêm phần tử mới;
4. bỏ reference tới array cũ.

Đó chính là ý tưởng cốt lõi phía sau **dynamic array**.

Trong .NET, `List<T>` là collection dynamic array quen thuộc. Nhưng nếu chỉ dùng mà không hiểu capacity/resize, bạn khó giải thích tại sao:

- append thường rất nhanh nhưng đôi lúc đắt;
- insert ở đầu danh sách là `O(n)`;
- remove giữa danh sách phải dịch phần tử;
- pre-allocate capacity đôi khi giảm allocation đáng kể.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
mkdir DynamicArrayDemo
cd DynamicArrayDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `DynamicArrayDemo.csproj` bằng:

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

Thay `Program.cs`:

```csharp
namespace DynamicArrayDemo;

public sealed class SimpleDynamicArray<T>
{
    private const int DefaultCapacity = 4;
    private T[] _items;

    public SimpleDynamicArray(int capacity = DefaultCapacity)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(capacity);
        _items = capacity == 0 ? [] : new T[capacity];
    }

    public int Count { get; private set; }

    public int Capacity => _items.Length;

    public T this[int index]
    {
        get
        {
            EnsureValidIndex(index);
            return _items[index];
        }
        set
        {
            EnsureValidIndex(index);
            _items[index] = value;
        }
    }

    public void Add(T item)
    {
        EnsureCapacity(checked(Count + 1));

        _items[Count] = item;
        Count++;
    }

    public void Insert(int index, T item)
    {
        if ((uint)index > (uint)Count)
        {
            throw new ArgumentOutOfRangeException(nameof(index));
        }

        EnsureCapacity(checked(Count + 1));

        for (int i = Count; i > index; i--)
        {
            _items[i] = _items[i - 1];
        }

        _items[index] = item;
        Count++;
    }

    public bool Remove(T item)
    {
        int index = IndexOf(item);

        if (index < 0)
        {
            return false;
        }

        RemoveAt(index);
        return true;
    }

    public void RemoveAt(int index)
    {
        EnsureValidIndex(index);

        for (int i = index; i < Count - 1; i++)
        {
            _items[i] = _items[i + 1];
        }

        Count--;
        _items[Count] = default!;
    }

    public int IndexOf(T item)
    {
        var comparer = EqualityComparer<T>.Default;

        for (int i = 0; i < Count; i++)
        {
            if (comparer.Equals(_items[i], item))
            {
                return i;
            }
        }

        return -1;
    }

    public T[] ToArray()
    {
        var result = new T[Count];
        Array.Copy(_items, result, Count);
        return result;
    }

    private void EnsureCapacity(int required)
    {
        if (required <= _items.Length)
        {
            return;
        }

        int newCapacity = _items.Length == 0
            ? DefaultCapacity
            : checked(_items.Length * 2);

        if (newCapacity < required)
        {
            newCapacity = required;
        }

        var newItems = new T[newCapacity];
        Array.Copy(_items, newItems, Count);
        _items = newItems;
    }

    private void EnsureValidIndex(int index)
    {
        if ((uint)index >= (uint)Count)
        {
            throw new ArgumentOutOfRangeException(nameof(index));
        }
    }
}

internal static class Program
{
    private static void Main()
    {
        var numbers = new SimpleDynamicArray<int>(capacity: 2);

        Print(numbers, "initial");

        numbers.Add(10);
        numbers.Add(20);
        Print(numbers, "after 2 Add");

        numbers.Add(30);
        Print(numbers, "after resize");

        numbers.Insert(1, 15);
        Print(numbers, "after Insert");

        numbers.Remove(20);
        Print(numbers, "after Remove");

        Console.WriteLine($"numbers[1] = {numbers[1]}");
        Console.WriteLine($"IndexOf(30) = {numbers.IndexOf(30)}");
    }

    private static void Print<T>(
        SimpleDynamicArray<T> values,
        string label)
    {
        Console.WriteLine(
            $"{label,-14} Count={values.Count}, " +
            $"Capacity={values.Capacity}, " +
            $"Values=[{string.Join(", ", values.ToArray())}]");
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
initial        Count=0, Capacity=2, Values=[]
after 2 Add    Count=2, Capacity=2, Values=[10, 20]
after resize   Count=3, Capacity=4, Values=[10, 20, 30]
after Insert   Count=4, Capacity=4, Values=[10, 15, 20, 30]
after Remove   Count=3, Capacity=4, Values=[10, 15, 30]
numbers[1] = 15
IndexOf(30) = 2
```

Sample cố tình viết dynamic array tối giản để nhìn rõ cơ chế. Trong code ứng dụng, ưu tiên `List<T>` thay vì tự viết collection này.

### Walkthrough — execution / state / cost

1. Add kiểm capacity trước khi ghi slot và tăng Count.
2. Resize cấp/copy xong mới đổi _items, input reference elements không deep clone.
3. Insert dịch từ phải sang trái; RemoveAt dịch trái rồi clear phần dư.
4. Đọc index O(1), search O(n); n lần append có tổng chi phí O(n) theo phân tích amortized. ToArray cấp phát và copy O(n). Buffer cũ có thể chờ GC nên bộ nhớ đỉnh lớn hơn buffer mới.

### Mini-check

Vì sao Insert phải dịch ngược còn RemoveAt dịch xuôi để không ghi đè dữ liệu chưa copy?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Array lưu các slot liên tiếp

Với `int[]`:

```text
index:    0       1       2       3
        +-------+-------+-------+-------+
value:  |  10   |  20   |  30   |  40   |
        +-------+-------+-------+-------+
           ^               ^
           |               |
        base          base + offset
```

Để đọc `array[i]`, runtime không cần đi qua các phần tử trước đó. Địa chỉ có thể được tính từ:

```text
base address + i * element size
```

Vì vậy truy cập theo index là `O(1)`.

### Array có kích thước cố định

Sau:

```csharp
var values = new int[4];
```

managed array có đúng 4 slot.

Không có thao tác thay đổi object array đó thành 8 slot. Muốn lớn hơn, bạn phải tạo array mới.

Dynamic array che giấu quy trình này.

### Count và Capacity khác nhau

Trong sample:

```text
Count    = số phần tử logic đang sử dụng
Capacity = số slot hiện có trong backing array
```

Sau khi thêm 3 phần tử vào capacity ban đầu 2:

```text
Count    = 3
Capacity = 4
```

Memory có thể hình dung:

```text
_items
  |
  v
+------+------+------+------+
| 10   | 20   | 30   | 0    |
+------+------+------+------+
  used   used   used   spare
```

Slot spare cho phép lần `Add` tiếp theo không cần allocation.

### Resize xảy ra như thế nào

Khi `Count == Capacity` và cần thêm phần tử:

```text
old array
+----+----+
| 10 | 20 |
+----+----+

        allocate new array

new array
+----+----+----+----+
|    |    |    |    |
+----+----+----+----+

        copy old elements

+----+----+----+----+
| 10 | 20 |    |    |
+----+----+----+----+

        append 30

+----+----+----+----+
| 10 | 20 | 30 |    |
+----+----+----+----+
```

Resize này tốn `O(n)` vì phải copy dữ liệu cũ.

### Vậy tại sao Add vẫn được gọi là amortized O(1)?

Nếu tăng capacity theo cấp số nhân, ví dụ:

```text
2 -> 4 -> 8 -> 16 -> 32 -> ...
```

không phải mọi `Add` đều copy.

Ví dụ thêm 8 phần tử:

```text
Add 1  no resize
Add 2  no resize
Add 3  resize 2 -> 4, copy 2
Add 4  no resize
Add 5  resize 4 -> 8, copy 4
Add 6  no resize
Add 7  no resize
Add 8  no resize
```

Tổng số phần tử copy qua nhiều lần resize:

```text
2 + 4 + 8 + ... < 2n
```

Chi phí tổng của `n` lần append vẫn tỷ lệ tuyến tính với `n`.

Do đó chi phí trung bình trên mỗi append là hằng số:

```text
amortized O(1)
```

Một lần `Add` cụ thể vẫn có thể là `O(n)`.

### Insert giữa danh sách là O(n)

Khi:

```csharp
numbers.Insert(1, 15);
```

từ:

```text
[10, 20, 30, _]
```

phải dịch:

```text
30 -> index 3
20 -> index 2
15 -> index 1
```

thành:

```text
[10, 15, 20, 30]
```

Số phần tử cần dịch phụ thuộc vị trí:

- insert cuối: gần `O(1)` amortized;
- insert đầu: `O(n)`;
- insert giữa: worst case `O(n)`.

### Remove cũng phải dịch

Remove index 1:

```text
before
[10, 15, 20, 30]

after logical remove
[10, 20, 30, ?]
```

Phần tử sau vị trí xóa phải dịch sang trái.

Do đó `RemoveAt` worst case là `O(n)`.

### Vì sao gán default sau RemoveAt?

Sau:

```csharp
Count--;
_items[Count] = default!;
```

nếu `T` là reference type, slot không còn sử dụng được xóa reference.

Nếu không, backing array có thể tiếp tục giữ reference tới object đã bị remove, khiến GC chưa thu hồi object dù collection logic không còn chứa nó.

Ví dụ:

```text
Count = 2

backing array:
[Customer A][Customer B][Customer C][null]
                         ^
                         |
              reference stale nếu không clear
```

Clear slot giúp tránh giữ object sống không cần thiết.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| array | kích thước cố định | indexO(1), ít metadata |
| dynamic array | dư capacity để append | amortizedO(1), resize/spare memory |
| linked nodes | thêm đầu bằng relink | không indexO(1), per-nodeallocation |

### Misconception check

**Đúng hay sai?** Capacity4 cho đọc index3 dù Count 3.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chưa phải phần tử logic.

</details>

**Đúng hay sai?** ToArray tách cả object trong slot.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ shallow copy slot/reference.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace buffer.

- **Working Developer — dùng khi làm việc:** amortized và alias.

- **Deep Dive — có thể quay lại sau:** allocation/GC profile khi nóng.

### Complexity cơ bản của dynamic array

| Thao tác | Complexity |
|---|---:|
| `array[index]` | `O(1)` |
| `List<T>[index]` | `O(1)` |
| append cuối | amortized `O(1)` |
| insert đầu | `O(n)` |
| insert giữa | `O(n)` |
| remove đầu/giữa | `O(n)` |
| search theo value | `O(n)` |
| copy toàn collection | `O(n)` |

### Pre-allocation

Nếu biết trước gần đúng số phần tử:

```csharp
var rows = new List<OrderRow>(expectedRowCount);
```

có thể giảm số lần resize.

Điều này có ích khi:

- import file lớn;
- deserialize batch dữ liệu;
- build collection từ query có count biết trước;
- code chạy trong hot path đã được đo.

Không nên đoán capacity khổng lồ "cho nhanh" vì memory dư cũng có chi phí.

### Array hay List?

Dùng array khi:

- kích thước cố định;
- API yêu cầu array;
- cần representation đơn giản;
- cần tối ưu low-level đã được đo;
- dữ liệu không cần insert/remove thường xuyên.

Dùng `List<T>` khi:

- số phần tử thay đổi;
- cần API collection tiện dụng;
- thường append;
- muốn collection general-purpose dễ dùng.

### Contiguous memory và cache locality

Dynamic array giữ phần tử trong backing array liên tiếp về mặt layout của các slot.

Với value type nhỏ như `int`, các value nằm ngay trong array. CPU cache có thể đọc một block chứa nhiều phần tử kế tiếp, nên traversal tuần tự thường có locality tốt.

Với reference type:

```csharp
Customer[] customers;
```

array chứa các **reference** liên tiếp; các object `Customer` mà reference trỏ tới có thể nằm ở nhiều nơi khác nhau trên heap.

```text
array:
[ref A][ref B][ref C]

   |      |      |
   v      v      v
 obj A  obj B  obj C
 heap locations not necessarily adjacent
```

### Growth factor là implementation detail

Sample dùng nhân đôi capacity để giải thích amortized complexity.

Không nên viết business logic dựa trên giả định rằng mọi phiên bản `.NET List<T>` luôn tăng capacity đúng một hệ số cụ thể. Điều quan trọng là interface/behavior được document, không phải chi tiết growth strategy nội bộ.

### Array.Copy

`Array.Copy` thể hiện đúng ý định hơn loop thủ công khi cần copy block dữ liệu:

```csharp
Array.Copy(source, destination, count);
```

Complexity vẫn là `O(n)` theo số phần tử copy.

## 6. Lỗi thường gặp

### Nhầm Capacity với Count

Sai:

```csharp
for (int i = 0; i < list.Capacity; i++)
{
    Console.WriteLine(list[i]);
}
```

Index hợp lệ chỉ từ:

```text
0 .. Count - 1
```

Capacity chỉ là storage dự phòng.

### Nghĩ Add luôn O(1) tuyệt đối

Một append gây resize phải allocate + copy, nên lần đó là `O(n)`.

Cách phát biểu đúng:

> append vào dynamic array thường là amortized `O(1)`.

### Insert đầu List trong loop lớn

Ví dụ:

```csharp
foreach (Order order in orders)
{
    list.Insert(0, order);
}
```

Mỗi insert có thể dịch toàn bộ phần tử hiện có.

Lặp `n` lần có thể dẫn tới tổng chi phí `O(n²)`.

Nếu chỉ muốn đảo thứ tự:

- append bình thường rồi `Reverse`;
- hoặc chọn cấu trúc phù hợp hơn.

### Remove khi đang foreach

Thay đổi structural collection trong `foreach` thường làm enumerator invalid.

Ví dụ:

```csharp
foreach (int value in list)
{
    if (value < 0)
    {
        list.Remove(value);
    }
}
```

Nên dùng:

- `RemoveAll`;
- loop index từ cuối về đầu;
- tạo collection mới;
- hoặc cách khác phù hợp bài toán.

### Giữ reference stale trong implementation custom

Nếu tự viết collection cho reference type, xóa logic mà không clear slot có thể giữ object sống.

Đây là lý do sample có:

```csharp
_items[Count] = default!;
```

### Tự viết collection trong production không cần thiết

Bài này yêu cầu tự implement để hiểu cơ chế, không phải để thay `List<T>`.

Collection chuẩn đã xử lý:

- API contract;
- validation;
- performance edge case;
- versioning/enumerator;
- compatibility;
- nhiều chi tiết mà sample không có.

## 7. Khi nào KHÔNG dùng

Không tự thay List<T> trong production chỉ vì viết demo được. Không cấp capacity cực lớn cho workload chưa biết số phần tử.

## 8. Production notes & scale check

Gate chạy chuỗi thao tác so List, biên index, remove không thấy và tính độc lập của bản sao. Sample không enumerator versioning/concurrency; checked bảo vệ cộng/growth số học, vẫn có thể thiếu memory.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Clear

Thêm method:

```csharp
public void Clear()
```

Yêu cầu:

- `Count` về 0;
- không giữ reference tới object cũ;
- có thể giữ lại capacity để tái sử dụng.

**Gợi ý:** dùng `Array.Clear`.

### Bài 2 — Contains

Viết:

```csharp
public bool Contains(T item)
```

dùng `EqualityComparer<T>.Default`.

Phân tích complexity.

**Gợi ý:** với backing array chưa sort, search phải scan từ đầu tới cuối.

### Bài 3 — EnsureCapacity công khai

Đổi method `EnsureCapacity` private hiện có thành API public, bổ sung guard capacity không âm (không khai báo hai method cùng signature):

```csharp
public void EnsureCapacity(int capacity)
```

Sau đó tạo chương trình thêm 100.000 phần tử:

- một lần không pre-allocate;
- một lần pre-allocate.

Không cần khẳng định tốc độ trước khi đo.

**Gợi ý:** ngoài time, có thể theo dõi số lần resize bằng counter trong implementation.

### Bài 4 — Insert đầu n lần

Viết chương trình:

```csharp
for (int i = 0; i < n; i++)
{
    values.Insert(0, i);
}
```

Phân tích tổng số lần dịch phần tử:

```text
0 + 1 + 2 + ... + (n - 1)
```

Suy ra Big-O tổng.

### Bài 5 — Chọn cấu trúc dữ liệu

Chọn giữa `T[]`, `List<T>`, `HashSet<T>` cho từng yêu cầu:

1. 7 ngày trong tuần, kích thước luôn cố định.
2. Danh sách item người dùng thêm dần vào giỏ.
3. Kiểm tra email đã tồn tại trong batch hay chưa.
4. Buffer 1.000 sensor reading cố định.
5. Danh sách kết quả query cần sort và render.

Giải thích lựa chọn bằng operation chính, không chỉ bằng câu "quen dùng".

## 10. Bài tập tích hợp liên module — Judgment

So vector C++ Module03: resize đổi buffer có nghĩa reference tới object C# trong slot bị invalid không? Phân biệt reference object với view vào storage.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Count và Capacity khác gì?
2. Một Add đắt nhất làm gì?
3. Vì sao clear slot sau remove?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được vì sao array index access là `O(1)`.
- [ ] Tôi phân biệt được `Count` và `Capacity`.
- [ ] Tôi mô tả được resize: allocate -> copy -> đổi backing array.
- [ ] Tôi giải thích được amortized `O(1)`.
- [ ] Tôi biết insert/remove giữa dynamic array là `O(n)`.
- [ ] Tôi biết vì sao implementation nên clear reference đã remove.
- [ ] Tôi biết khi nào nên pre-allocate capacity.
- [ ] Tôi chọn được array hay `List<T>` dựa trên operation của bài toán.
- [ ] Tôi hiểu sample tự viết collection chỉ phục vụ học cơ chế.

Điều hướng:

- Bài trước: [Đệ quy và call stack](./02-de-quy-va-call-stack.md)
- Ôn lại array: [Module 04 — Array, string, index và range](../04-csharp-co-ban/06-array-string-index-va-range.md)
- Ôn lại collection: [Module 04 — List, Dictionary, HashSet, Queue, Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Bài tiếp theo: [Linked list](./04-linked-list.md)
