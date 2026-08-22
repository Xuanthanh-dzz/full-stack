# Mảng và dynamic array

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích vì sao mảng cho phép truy cập theo chỉ số ở `O(1)` nhờ bộ nhớ **liền kề**;
- nêu giới hạn của mảng cố định: kích thước không đổi sau khi tạo;
- mô tả cách một **dynamic array** (chính là `List<T>`) tăng dung lượng bằng cách **gấp đôi capacity**;
- giải thích vì sao thêm vào cuối là `O(1)` **amortized** dù đôi lúc phải copy toàn bộ;
- suy ra vì sao chèn/xóa ở giữa là `O(n)` do phải dịch phần tử;
- chọn giữa mảng cố định và `List<T>` theo bài toán.

## 2. Bài toán mở đầu

Bạn viết chương trình đọc điểm thi của một lớp. Vấn đề: **không biết trước lớp có bao nhiêu học sinh**. Dùng mảng cố định thì phải đoán:

- Khai báo `new int[30]` — lớp có 45 em thì tràn.
- Khai báo `new int[1000]` cho chắc — lớp có 20 em thì phí 980 ô nhớ, và vẫn có thể tràn nếu một ngày có 1001 em.

Mảng cố định (`int[]`, đã học ở [module 01, bài 11](../01-nen-tang-lap-trinh/11-mang-mot-chieu.md)) rất nhanh khi truy cập nhưng không co giãn được. `List<T>` (module 04) giải quyết đúng chỗ đau này: thêm bao nhiêu cũng được, nó tự lớn lên. Câu hỏi của bài: *nó lớn lên bằng cách nào, và cái giá là gì?* Ta sẽ tự dựng một dynamic array để nhìn rõ cơ chế bên trong `List<T>`.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `ArrayDemo` với cấu hình `.csproj` chuẩn của module (như bài [01](./01-big-o-thoi-gian-va-bo-nho.md)), rồi thay `Program.cs`:

```csharp
namespace ArrayDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Mảng cố định: truy cập theo chỉ số là O(1) ==");
        int[] fixedArray = { 10, 20, 30, 40 };
        Console.WriteLine($"fixedArray[2] = {fixedArray[2]} (không cần duyệt, tính địa chỉ trực tiếp)");
        Console.WriteLine($"Length = {fixedArray.Length} (không đổi sau khi tạo)");

        Console.WriteLine();
        Console.WriteLine("== DynamicArray tự viết: capacity tăng gấp đôi ==");
        var list = new DynamicArray<int>();
        for (int i = 1; i <= 9; i++)
        {
            list.Add(i * 100);
        }
        Console.WriteLine($"Sau khi thêm 9 phần tử: Count={list.Count}, Capacity={list.Capacity}");
        Console.WriteLine($"Phần tử tại chỉ số 4: {list[4]}");

        Console.WriteLine();
        Console.WriteLine("== Chèn giữa phải dịch phần tử: O(n) ==");
        list.InsertAt(0, -1);
        Console.WriteLine($"Sau InsertAt(0, -1): [{list}]");
        list.RemoveAt(3);
        Console.WriteLine($"Sau RemoveAt(3):     [{list}]");
    }
}

internal sealed class DynamicArray<T>
{
    private T[] _items = new T[1]; // backing array, ban đầu chứa được 1 phần tử
    public int Count { get; private set; }
    public int Capacity => _items.Length;

    public T this[int index]
    {
        get
        {
            if ((uint)index >= (uint)Count)
            {
                throw new IndexOutOfRangeException();
            }
            return _items[index]; // O(1): truy cập trực tiếp
        }
    }

    public void Add(T value)
    {
        if (Count == _items.Length)
        {
            Grow(); // hết chỗ -> cấp mảng lớn gấp đôi rồi copy
        }
        _items[Count] = value;
        Count++;
    }

    private void Grow()
    {
        int newCapacity = _items.Length * 2;
        var bigger = new T[newCapacity];
        Array.Copy(_items, bigger, Count); // copy O(n) khi phình
        Console.WriteLine($"  [grow] capacity {_items.Length} -> {newCapacity}");
        _items = bigger;
    }

    public void InsertAt(int index, T value)
    {
        if (Count == _items.Length)
        {
            Grow();
        }
        // dịch mọi phần tử từ index sang phải một ô: O(n)
        for (int i = Count; i > index; i--)
        {
            _items[i] = _items[i - 1];
        }
        _items[index] = value;
        Count++;
    }

    public void RemoveAt(int index)
    {
        // dịch mọi phần tử sau index sang trái một ô: O(n)
        for (int i = index; i < Count - 1; i++)
        {
            _items[i] = _items[i + 1];
        }
        Count--;
    }

    public override string ToString()
    {
        return string.Join(", ", _items.Take(Count));
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Mảng cố định: truy cập theo chỉ số là O(1) ==
fixedArray[2] = 30 (không cần duyệt, tính địa chỉ trực tiếp)
Length = 4 (không đổi sau khi tạo)

== DynamicArray tự viết: capacity tăng gấp đôi ==
  [grow] capacity 1 -> 2
  [grow] capacity 2 -> 4
  [grow] capacity 4 -> 8
  [grow] capacity 8 -> 16
Sau khi thêm 9 phần tử: Count=9, Capacity=16
Phần tử tại chỉ số 4: 500

== Chèn giữa phải dịch phần tử: O(n) ==
Sau InsertAt(0, -1): [-1, 100, 200, 300, 400, 500, 600, 700, 800, 900]
Sau RemoveAt(3):     [-1, 100, 200, 400, 500, 600, 700, 800, 900]
```

## 4. Giải thích cơ chế

### 4.1 Vì sao truy cập theo chỉ số là `O(1)`

Mảng lưu các phần tử **liền kề nhau** trong bộ nhớ. Nếu phần tử đầu ở địa chỉ `base` và mỗi phần tử chiếm `size` byte, thì phần tử thứ `i` nằm ở:

```text
địa chỉ(i) = base + i * size
```

Đây là một phép nhân và một phép cộng — hằng số thao tác, không phụ thuộc mảng dài bao nhiêu. Đó là lý do `fixedArray[2]` lấy được `30` ngay lập tức mà không cần duyệt qua `[0]` và `[1]`. Sơ đồ bộ nhớ:

```text
chỉ số:      0      1      2      3
          +------+------+------+------+
_items -> |  10  |  20  |  30  |  40  |   (các ô liền kề nhau)
          +------+------+------+------+
địa chỉ:  base  base+4 base+8 base+12   (int = 4 byte)
```

Chính tính liền kề này cũng làm mảng thân thiện với **CPU cache**: đọc một phần tử thường kéo theo các phần tử lân cận vào cache, nên duyệt tuần tự rất nhanh.

### 4.2 Dynamic array lớn lên bằng cách gấp đôi

`DynamicArray<T>` giữ một mảng nền `_items` và một `Count` (số phần tử thực sự đang dùng). Khi `Add` mà mảng nền đã đầy (`Count == _items.Length`), `Grow` cấp một mảng **gấp đôi**, copy dữ liệu cũ sang, rồi thay `_items`.

Output cho thấy chuỗi phình `1 → 2 → 4 → 8 → 16`. Thêm 9 phần tử chỉ phình 4 lần; sau lần cuối, capacity là 16 nên còn chỗ trống cho 7 phần tử nữa mà không phải copy lại. `List<T>` của .NET dùng đúng chiến lược gấp đôi này (bắt đầu từ 0, lần đầu thường nhảy lên 4).

### 4.3 `O(1)` amortized — trung bình hóa cái giá copy

Nhìn kỹ: đa số lần `Add` chỉ gán một ô và tăng `Count` — `O(1)`. Thỉnh thoảng một lần `Add` phải copy toàn bộ `n` phần tử — `O(n)`. Vậy rốt cuộc `Add` là gì?

Câu trả lời là **amortized `O(1)`**: chia đều chi phí copy qua toàn bộ các lần thêm, mỗi lần thêm gánh một phần hằng số. Lý do là cấp số nhân: để tới `n` phần tử, tổng số ô đã copy qua các lần phình là `1 + 2 + 4 + ... + n < 2n`, tức trung bình chưa tới **2 lần copy mỗi phần tử**. Nếu thay vì gấp đôi mà chỉ tăng thêm 1 ô mỗi lần đầy, tổng copy sẽ là `1 + 2 + ... + n ≈ n²/2` — biến `Add` thành `O(n)` mỗi lần. Gấp đôi là thứ giữ cho amortized ở `O(1)`.

### 4.4 Chèn/xóa ở giữa là `O(n)`

Vì phần tử phải liền kề, chèn vào giữa buộc mọi phần tử phía sau **dịch sang phải một ô**, và xóa buộc chúng dịch sang trái. `InsertAt(0, -1)` là trường hợp xấu nhất: chèn ở đầu phải dịch toàn bộ. Đó là `O(n)`.

Đây là điểm yếu cố hữu của cấu trúc dựa trên mảng, và cũng là động cơ để bài [04 — linked list](./04-linked-list.md) ra đời: linked list chèn/xóa ở một vị trí đã biết chỉ tốn `O(1)`, đổi lại mất khả năng truy cập `O(1)` theo chỉ số.

### Đào sâu (có thể quay lại sau)

- **`Capacity` so với `Count`.** `Count` là số phần tử thực; `Capacity` là số ô đã cấp. `Capacity >= Count` luôn đúng. Phần dư giữa hai số là bộ nhớ đã đặt trước nhưng chưa dùng.
- **Đặt trước capacity.** Nếu biết trước sẽ thêm khoảng `n` phần tử, `new List<T>(n)` (hoặc `EnsureCapacity`) cấp đủ ngay, tránh mọi lần phình giữa chừng. Đây là tối ưu đáng giá khi thêm số lượng lớn.
- **`Array.Copy` và bộ nhớ.** Lúc phình, cả mảng cũ và mảng mới cùng tồn tại một khoảnh khắc, nên đỉnh bộ nhớ có thể tới ~1,5 lần dữ liệu. Với mảng rất lớn đây là điều cần lưu ý.

## 5. Kiến thức nền

### Mảng cố định so với dynamic array

| Tiêu chí | Mảng cố định `T[]` | Dynamic array `List<T>` |
|---|---|---|
| Kích thước | cố định lúc tạo | co giãn tự động |
| Truy cập `[i]` | `O(1)` | `O(1)` |
| Thêm vào cuối | không (đã đầy là hết) | `O(1)` amortized |
| Chèn/xóa ở giữa | tự dịch thủ công, `O(n)` | `O(n)` |
| Bộ nhớ phụ | không | có thể dư (capacity > count) |

### Vì sao "amortized" khác "average"

- **Average** nói về phân bố đầu vào ngẫu nhiên.
- **Amortized** bảo đảm cho **một chuỗi thao tác**: dù kẻ xấu chọn đầu vào tệ nhất, tổng chi phí của `n` lần `Add` vẫn là `O(n)`, tức trung bình `O(1)` mỗi lần. Đây là bảo đảm mạnh hơn và không dựa vào giả định ngẫu nhiên.

### Khi nào dùng cái nào

- **Mảng cố định** khi số phần tử biết trước và không đổi (ví dụ 12 tháng, 7 ngày, bảng tra cứu). Gọn và nhanh nhất.
- **`List<T>`** cho mọi trường hợp còn lại khi cần một chuỗi có thể lớn lên và truy cập ngẫu nhiên nhanh. Đây là lựa chọn mặc định hằng ngày.

## 6. Lỗi thường gặp

### Đoán kích thước mảng cố định

Cấp `new int[1000]` "cho chắc" vừa phí bộ nhớ vừa vẫn có nguy cơ tràn. Khi số lượng chưa biết trước, dùng `List<T>` thay vì đoán.

### Chèn ở đầu `List<T>` trong vòng lặp

`list.Insert(0, x)` là `O(n)`; làm việc đó `n` lần là `O(n^2)`. Nếu cần thêm liên tục ở đầu, cân nhắc `LinkedList<T>` (bài [04](./04-linked-list.md)) hoặc thêm vào cuối rồi đảo mảng một lần.

### Nhầm `Capacity` với `Count`

`list.Capacity` là chỗ đã cấp, không phải số phần tử. Vòng lặp `for (i = 0; i < list.Capacity; i++)` sẽ chạm cả những ô chưa dùng. Luôn duyệt tới `Count` (hoặc `list.Count`).

### Sửa collection trong khi `foreach`

Thêm/xóa phần tử của `List<T>` ngay trong `foreach` trên chính nó ném `InvalidOperationException`. Duyệt bằng chỉ số, hoặc gom thay đổi lại làm sau vòng lặp.

### Quên rằng phình làm dời địa chỉ

Sau khi `Grow`, backing array là một vùng nhớ **mới**; mọi tham chiếu tới mảng nền cũ (nếu có) đã lỗi thời. Đây là lý do không nên giữ con trỏ/tham chiếu trực tiếp vào phần tử của một dynamic array đang lớn lên.

## 7. Bài tập

### Bài 1 — Thêm phương thức `Contains`

Thêm `bool Contains(T value)` vào `DynamicArray<T>` bằng cách duyệt tuyến tính. Gọi tên độ phức tạp của nó.

**Gợi ý:** một vòng lặp qua `Count` phần tử — `O(n)`; dùng `EqualityComparer<T>.Default.Equals` để so sánh generic.

### Bài 2 — Đo số lần copy

Thêm bộ đếm `long` tăng mỗi khi `Array.Copy` chạy trong `Grow`. Thêm `1000` phần tử và in tổng số phần tử đã copy, rồi so với `2 * 1000`.

**Gợi ý:** tổng copy `< 2n` là bằng chứng thực nghiệm cho amortized `O(1)`.

### Bài 3 — `RemoveAt` giữ chỗ

Sau `RemoveAt`, ô cuối cùng vẫn giữ giá trị cũ (chỉ `Count` giảm). Với `T` là reference type, điều này giữ sống object không mong muốn. Sửa `RemoveAt` để gán `default` vào ô vừa bỏ trống.

**Gợi ý:** `_items[Count - 1] = default!;` sau khi dịch, trước khi giảm `Count`; đây chính là cách `List<T>` tránh rò rỉ tham chiếu.

### Bài 4 — So với `List<T>` thật

Viết chương trình thêm dần phần tử vào một `List<int>` và in `list.Capacity` sau mỗi lần thêm cho tới 20 phần tử. Ghi lại chuỗi capacity và so với chiến lược gấp đôi.

**Gợi ý:** `List<T>` bắt đầu từ 0, lần đầu nhảy lên 4 rồi gấp đôi; xác nhận bằng số thật.

### Bài 5 — Chọn cấu trúc

Cho ba tình huống: (a) lưu 12 giá trị doanh thu theo tháng; (b) hàng đợi log ghi liên tục không biết trước số lượng; (c) danh sách cần chèn thường xuyên vào giữa. Chọn mảng cố định, `List<T>`, hay gợi ý một cấu trúc khác, và giải thích.

**Gợi ý:** (c) là điểm yếu của cấu trúc mảng — hãy để dành lý do cho bài linked list.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được công thức địa chỉ khiến `array[i]` là `O(1)`.
- [ ] Tôi mô tả được cách dynamic array gấp đôi capacity khi đầy.
- [ ] Tôi chứng minh được thêm vào cuối là `O(1)` amortized nhờ cấp số nhân.
- [ ] Tôi biết chèn/xóa ở giữa là `O(n)` vì phải dịch phần tử.
- [ ] Tôi phân biệt `Count` và `Capacity`.
- [ ] Tôi chọn đúng giữa mảng cố định và `List<T>` cho một bài toán.

Điều hướng:

- Bài prerequisite: [Đệ quy và call stack](./02-de-quy-va-call-stack.md)
- Ôn lại nền tảng: [Mảng một chiều](../01-nen-tang-lap-trinh/11-mang-mot-chieu.md), [Collection: List, Dictionary, HashSet, Queue và Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Bài tiếp theo: [Linked list](./04-linked-list.md)
