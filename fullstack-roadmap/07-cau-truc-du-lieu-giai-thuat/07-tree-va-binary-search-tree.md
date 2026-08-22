# Tree và binary search tree

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng đúng thuật ngữ cây: root, node, child, parent, leaf, subtree, height, depth;
- phát biểu **tính chất BST**: mọi node bên trái nhỏ hơn, bên phải lớn hơn node hiện tại;
- cài đặt `Insert`, `Contains`, `Min`, `Max` và các phép **duyệt** cây bằng đệ quy;
- giải thích vì sao **in-order traversal** cho ra dãy đã sắp xếp;
- lý giải vì sao BST cân đối cho thao tác `O(log n)` còn cây suy biến tụt về `O(n)`;
- biết vì sao cần cây tự cân bằng và khi nào chọn BST thay cho hash table.

## 2. Bài toán mở đầu

Bài [06](./06-hash-table-va-hash-function.md) cho ta tra cứu `O(1)`, nhưng đánh mất **thứ tự**: duyệt một `Dictionary` không ra dãy sắp xếp, và không có cách hỏi "phần tử nhỏ nhất lớn hơn 65 là gì?". Còn nếu giữ dữ liệu trong một mảng đã sắp xếp thì tra cứu nhanh (`O(log n)` bằng tìm nhị phân, bài [14](./14-searching.md)) nhưng **chèn** một phần tử mới lại là `O(n)` vì phải dịch chỗ.

Ta muốn một cấu trúc vừa **giữ thứ tự** vừa cho chèn/tìm nhanh. **Binary search tree** làm được: mỗi lần so sánh loại bỏ một nửa cây còn lại, nên tìm và chèn đều `O(log n)` khi cây cân đối, mà in-order vẫn cho dãy sắp xếp bất cứ lúc nào. Bài này dựng BST và chỉ ra cả sức mạnh lẫn cái bẫy suy biến của nó.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `BstDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace BstDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Dựng BST và duyệt in-order (ra thứ tự tăng dần) ==");
        var tree = new BinarySearchTree<int>();
        int[] values = { 50, 30, 70, 20, 40, 60, 80 };
        foreach (int v in values)
        {
            tree.Insert(v);
        }
        Console.WriteLine($"Chèn theo thứ tự: [{string.Join(", ", values)}]");
        Console.WriteLine($"In-order:         [{string.Join(", ", tree.InOrder())}]");
        Console.WriteLine($"Chiều cao cây: {tree.Height()}  (cây cân đối)");
        Console.WriteLine($"Min = {tree.Min()}, Max = {tree.Max()}");

        Console.WriteLine();
        Console.WriteLine("== Cấu trúc cây (nhìn nghiêng, phải ở trên) ==");
        tree.Print();

        Console.WriteLine();
        Console.WriteLine("== Tìm kiếm: đi trái/phải theo so sánh ==");
        foreach (int target in new[] { 40, 65 })
        {
            Console.WriteLine($"  Contains({target}) = {tree.Contains(target)}");
        }

        Console.WriteLine();
        Console.WriteLine("== Bẫy: chèn dữ liệu đã sắp xếp -> cây suy biến ==");
        var degenerate = new BinarySearchTree<int>();
        foreach (int v in new[] { 1, 2, 3, 4, 5, 6, 7 })
        {
            degenerate.Insert(v);
        }
        Console.WriteLine("Chèn [1,2,3,4,5,6,7] theo thứ tự tăng dần:");
        Console.WriteLine($"Chiều cao cây: {degenerate.Height()}  (suy biến như linked list -> O(n))");
    }
}

internal sealed class TreeNode<T>
{
    public T Value { get; }
    public TreeNode<T>? Left { get; set; }
    public TreeNode<T>? Right { get; set; }

    public TreeNode(T value)
    {
        Value = value;
    }
}

internal sealed class BinarySearchTree<T> where T : IComparable<T>
{
    private TreeNode<T>? _root;

    public void Insert(T value)
    {
        _root = InsertInto(_root, value);
    }

    // Đệ quy: đi xuống đúng nhánh, tạo node ở chỗ trống.
    private static TreeNode<T> InsertInto(TreeNode<T>? node, T value)
    {
        if (node is null)
        {
            return new TreeNode<T>(value); // chỗ trống -> node mới
        }
        int cmp = value.CompareTo(node.Value);
        if (cmp < 0)
        {
            node.Left = InsertInto(node.Left, value);   // nhỏ hơn -> trái
        }
        else if (cmp > 0)
        {
            node.Right = InsertInto(node.Right, value); // lớn hơn -> phải
        }
        // cmp == 0: đã có, bỏ qua (BST này không nhận trùng)
        return node;
    }

    public bool Contains(T value)
    {
        TreeNode<T>? node = _root;
        while (node is not null)
        {
            int cmp = value.CompareTo(node.Value);
            if (cmp == 0) return true;
            node = cmp < 0 ? node.Left : node.Right; // loại nửa cây mỗi bước
        }
        return false;
    }

    public IEnumerable<T> InOrder()
    {
        return InOrderFrom(_root);
    }

    // In-order: trái -> gốc -> phải, cho ra thứ tự tăng dần.
    private static IEnumerable<T> InOrderFrom(TreeNode<T>? node)
    {
        if (node is null)
        {
            yield break;
        }
        foreach (T v in InOrderFrom(node.Left)) yield return v;
        yield return node.Value;
        foreach (T v in InOrderFrom(node.Right)) yield return v;
    }

    public T Min()
    {
        TreeNode<T> node = _root ?? throw new InvalidOperationException("Cây rỗng.");
        while (node.Left is not null) node = node.Left; // trái nhất
        return node.Value;
    }

    public T Max()
    {
        TreeNode<T> node = _root ?? throw new InvalidOperationException("Cây rỗng.");
        while (node.Right is not null) node = node.Right; // phải nhất
        return node.Value;
    }

    public int Height() => HeightOf(_root);

    private static int HeightOf(TreeNode<T>? node)
    {
        if (node is null) return 0;
        return 1 + Math.Max(HeightOf(node.Left), HeightOf(node.Right));
    }

    public void Print() => PrintNode(_root, 0);

    private static void PrintNode(TreeNode<T>? node, int depth)
    {
        if (node is null) return;
        PrintNode(node.Right, depth + 1);
        Console.WriteLine($"{new string(' ', depth * 4)}{node.Value}");
        PrintNode(node.Left, depth + 1);
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Dựng BST và duyệt in-order (ra thứ tự tăng dần) ==
Chèn theo thứ tự: [50, 30, 70, 20, 40, 60, 80]
In-order:         [20, 30, 40, 50, 60, 70, 80]
Chiều cao cây: 3  (cây cân đối)
Min = 20, Max = 80

== Cấu trúc cây (nhìn nghiêng, phải ở trên) ==
        80
    70
        60
50
        40
    30
        20

== Tìm kiếm: đi trái/phải theo so sánh ==
  Contains(40) = True
  Contains(65) = False

== Bẫy: chèn dữ liệu đã sắp xếp -> cây suy biến ==
Chèn [1,2,3,4,5,6,7] theo thứ tự tăng dần:
Chiều cao cây: 7  (suy biến như linked list -> O(n))
```

## 4. Giải thích cơ chế

### 4.1 Từ vựng về cây

Một cây gồm các **node** nối với nhau bằng con trỏ, xuất phát từ một node đặc biệt là **root** (gốc). Với cây ở trên (root là 50):

```text
              50            <- root, depth 0
          /       \
        30          70      <- depth 1
       /  \        /  \
     20    40    60    80   <- depth 2, đây là các leaf (không có con)
```

- **child / parent:** 30 và 70 là con của 50; 50 là cha của chúng.
- **leaf:** node không có con (20, 40, 60, 80).
- **subtree:** mỗi node cùng con cháu của nó tạo thành một cây con — nền tảng để đệ quy.
- **depth** của một node: số cạnh từ root xuống nó. **height** của cây: depth lớn nhất + 1 (số tầng). Cây trên có height 3.

Cây **nhị phân (binary)** là cây mà mỗi node có **tối đa hai con** (Left, Right) — đúng cấu trúc `TreeNode<T>`.

### 4.2 Tính chất BST và vì sao tìm kiếm nhanh

BST thêm một ràng buộc: với **mọi** node, toàn bộ cây con trái chứa giá trị **nhỏ hơn**, cây con phải chứa giá trị **lớn hơn**. Nhờ đó `Contains` không phải quét: mỗi lần so sánh chỉ cho **một** hướng đi và **loại bỏ nửa cây** còn lại.

Tìm `40` trong cây trên: `40 < 50` → sang trái (30); `40 > 30` → sang phải (40); khớp. Chỉ 3 bước cho 7 phần tử. Tổng quát, số bước bằng chiều cao cây. Cây cân đối có chiều cao `~log₂ n`, nên tìm và chèn là `O(log n)`.

### 4.3 In-order cho dãy đã sắp xếp

`InOrder` duyệt theo thứ tự **trái → gốc → phải** một cách đệ quy. Vì mọi thứ bên trái đều nhỏ hơn gốc và mọi thứ bên phải đều lớn hơn, thứ tự này in ra đúng dãy tăng dần — output `[20, 30, 40, 50, 60, 70, 80]` dù ta chèn vào theo thứ tự `[50, 30, 70, ...]`. Đây là một tính chất đẹp: BST **luôn** cho phép lấy dữ liệu đã sắp xếp trong `O(n)` mà không cần sắp xếp lại.

Ba kiểu duyệt theo chiều sâu (đổi vị trí "thăm gốc"):

- **In-order** (trái, gốc, phải): dãy sắp xếp.
- **Pre-order** (gốc, trái, phải): dùng khi cần sao chép/serialize cây.
- **Post-order** (trái, phải, gốc): dùng khi cần xử lý con trước cha (ví dụ giải phóng cây).

### 4.4 Cái bẫy: cây suy biến

Đây là điểm yếu chí mạng của BST cơ bản. Chèn `[1,2,3,4,5,6,7]` **theo thứ tự tăng dần**: mỗi số đều lớn hơn số trước nên luôn đi sang phải, tạo thành một chuỗi lệch hẳn:

```text
1
 \
  2
   \
    3
     \
      4  ...  (chiều cao = 7)
```

Cây "suy biến" thành đúng một linked list. Chiều cao bằng `n`, nên `Contains` và `Insert` tụt về `O(n)` — mất sạch lợi thế. BST chỉ nhanh **khi cân đối**, mà thứ tự chèn quyết định độ cân đối. Đây chính là động cơ cho cây tự cân bằng.

### Đào sâu (có thể quay lại sau)

- **Cây tự cân bằng.** AVL tree và red-black tree tự xoay (rotation) sau mỗi lần chèn/xóa để giữ chiều cao ở `O(log n)` **bảo đảm**, bất kể thứ tự chèn. Chúng phức tạp hơn nhiều; ý tưởng là "phát hiện lệch và xoay lại cho cân". Trong .NET, `SortedDictionary<K,V>` và `SortedSet<T>` được cài bằng cây cân bằng, cho `O(log n)` bảo đảm.
- **Xóa trong BST.** `Remove` phức tạp hơn `Insert`: xóa leaf thì dễ; xóa node một con thì nối con lên; xóa node hai con thì thay bằng phần tử kế vị in-order (nhỏ nhất của cây con phải). Đây là bài tập nâng cao ở cuối.
- **B-tree.** Khi dữ liệu nằm trên đĩa (cơ sở dữ liệu), người ta dùng B-tree — mỗi node chứa nhiều khóa và nhiều con — để giảm số lần đọc đĩa. Index của SQL Server chính là B-tree, bạn sẽ gặp ở [module 08](../08-sql-va-csdl/17-index-btree-clustered-nonclustered.md).

## 5. Kiến thức nền

### Đệ quy là ngôn ngữ tự nhiên của cây

Mỗi cây con lại là một cây, nên hầu hết thao tác cây viết đệ quy rất gọn: xử lý node hiện tại rồi gọi lại chính hàm đó cho `Left` và `Right`. `InsertInto`, `InOrderFrom`, `HeightOf` đều theo khuôn này. Base case luôn là `node is null` (cây rỗng). Đây là lý do bài [02 — đệ quy](./02-de-quy-va-call-stack.md) là tiên quyết.

### BST so với hash table

| Tiêu chí | Hash table | BST cân đối |
|---|---|---|
| Tìm theo khóa | `O(1)` trung bình | `O(log n)` |
| Giữ thứ tự sắp xếp | không | có (in-order) |
| Min / Max | `O(n)` (phải quét) | `O(log n)` |
| Truy vấn khoảng (range) | không | có |
| Worst case | `O(n)` | `O(n)` nếu không cân bằng |

Chọn hash table khi chỉ cần tra khóa nhanh. Chọn cây (cân bằng) khi cần **thứ tự**, min/max, hoặc truy vấn theo khoảng.

### Ràng buộc `IComparable<T>`

BST cần **so sánh** hai phần tử để quyết định trái/phải, nên `T` phải có `CompareTo` — chính constraint `where T : IComparable<T>` (đã học ở [module 05, bài 01](../05-csharp-nang-cao/01-generics-va-constraints.md)). `int`, `string`, `DateTime`... đều thỏa. Type tự viết cần implement `IComparable<T>` hoặc truyền một `IComparer<T>`.

## 6. Lỗi thường gặp

### Chèn dữ liệu đã sắp xếp vào BST cơ bản

Đây là bẫy trong bài: dữ liệu vào theo thứ tự (hoặc gần thứ tự) làm cây suy biến `O(n)`. Nếu dữ liệu có thể đã sắp xếp, dùng cây tự cân bằng (`SortedSet<T>`/`SortedDictionary<K,V>`) thay vì BST tự viết.

### Quên trường hợp cây rỗng

Mọi thao tác phải xử lý `_root is null`. `Min`/`Max` trên cây rỗng nên ném lỗi rõ ràng thay vì `NullReferenceException`.

### Nhầm thứ tự trong ba kiểu duyệt

Muốn dãy sắp xếp phải là in-order (trái, gốc, phải). Đặt "thăm gốc" sai chỗ cho ra thứ tự khác. Ghi nhớ: vị trí của "gốc" trong tên nói lên khi nào thăm nó.

### Cho rằng BST luôn `O(log n)`

Chỉ đúng khi cân đối. Không có cơ chế cân bằng, một chuỗi chèn xấu đưa nó về `O(n)`. Đừng dựa vào `O(log n)` cho BST tự viết không cân bằng.

### Dùng `==` thay cho `CompareTo`

Với generic `T`, so sánh thứ tự phải qua `IComparable<T>.CompareTo`, không phải `<`/`>` (không áp dụng cho mọi `T`) hay `==` (chỉ biết bằng/khác, không biết lớn/nhỏ).

## 7. Bài tập

### Bài 1 — Đếm số node và số leaf

Thêm `int CountNodes()` và `int CountLeaves()` bằng đệ quy. Kiểm tra với cây trong bài (7 node, 4 leaf).

**Gợi ý:** số node = 1 + đếm trái + đếm phải; leaf là node có cả `Left` và `Right` là `null`.

### Bài 2 — Duyệt pre-order và post-order

Thêm `PreOrder()` và `PostOrder()`. In cả ba kiểu duyệt cho cây trong bài và so sánh thứ tự.

**Gợi ý:** chỉ đổi vị trí câu `yield return node.Value` so với hai lời gọi con.

### Bài 3 — Kiểm tra một cây có phải BST

Viết hàm nhận một cây nhị phân bất kỳ và trả `true` nếu nó thỏa tính chất BST. Cẩn thận: chỉ kiểm tra `Left < node < Right` cho từng node là **chưa đủ**.

**Gợi ý:** truyền xuống một khoảng `(min, max)` hợp lệ cho mỗi node; con trái thu hẹp `max`, con phải thu hẹp `min`.

### Bài 4 — Tìm chiều cao và độ cân bằng

Thêm hàm báo cây có "cân bằng" không: với **mọi** node, chênh lệch chiều cao hai cây con không quá 1. Dùng nó để xác nhận cây `[50,30,70,...]` cân bằng còn cây `[1..7]` thì không.

**Gợi ý:** tính chiều cao mỗi cây con một lần rồi so; tránh tính lại chiều cao nhiều lần thành `O(n^2)`.

### Bài 5 — Xóa node (nâng cao)

Cài `Remove(T value)` xử lý ba trường hợp: node là leaf, node có một con, node có hai con (thay bằng phần tử nhỏ nhất của cây con phải).

**Gợi ý:** trường hợp hai con là khó nhất — tìm phần tử kế vị in-order, chép giá trị nó lên node cần xóa, rồi xóa phần tử kế vị đó ở cây con phải.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng đúng các thuật ngữ root, leaf, subtree, height, depth.
- [ ] Tôi phát biểu và kiểm tra được tính chất BST.
- [ ] Tôi cài được `Insert`/`Contains` và giải thích vì sao mỗi bước loại nửa cây.
- [ ] Tôi giải thích được vì sao in-order cho dãy đã sắp xếp.
- [ ] Tôi chỉ ra được khi nào BST suy biến thành `O(n)` và vì sao cần cây cân bằng.
- [ ] Tôi biết `SortedSet`/`SortedDictionary` dùng cây cân bằng và khi nào chọn cây thay hash table.

Điều hướng:

- Bài prerequisite: [Hash table và hash function](./06-hash-table-va-hash-function.md)
- Ôn lại nền tảng: [Đệ quy và call stack](./02-de-quy-va-call-stack.md), [Linked list](./04-linked-list.md)
- Bài tiếp theo: [Heap và priority queue](./08-heap-va-priority-queue.md)
