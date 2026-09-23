# Tree và binary search tree

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- BST tổ chức thứ tự để tìm bằng cách bỏ một nhánh.
- Dùng khi cần ordering/range; complexity phụ thuộc chiều cao h.
- BST không tự cân bằng; dữ liệu sort có thể tạo chuỗi dài.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả tree bằng node, root, parent, child, leaf, depth và height;
- phân biệt binary tree với binary search tree;
- cài đặt BST cơ bản bằng C#;
- thực hiện insert, search và inorder traversal;
- phân tích complexity theo chiều cao cây;
- giải thích vì sao BST lệch có thể suy giảm từ `O(log n)` xuống `O(n)`;
- liên hệ tree với cấu trúc thư mục, DOM, index và hệ thống phân cấp.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mỗi biển chỉ đường ghi số mốc: nhỏ hơn đi trái, lớn hơn đi phải. Biển đúng giúp bỏ cả nhánh; nếu mọi biển chỉ sang phải thì vẫn phải đi qua từng biển.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| root | node đầu tiên của cây | _root |
| height | số cạnh dài nhất xuống lá | h |
| BST invariant | mọi giá trị trái nhỏ hơn, phải lớn hơn | CompareTo |
| inorder | trái rồi node rồi phải | sequence tăng dần |

### Ví dụ nhỏ — tính tay trước

Insert 3,1,4,2 → root 3, trái 1 có phải 2, phải 4. Tìm2 đi3→1→2; thêm 2 lần nữa trả false, Count vẫn 4.

Ta cần lưu một tập số và thường xuyên:

- thêm giá trị;
- kiểm tra một giá trị có tồn tại;
- duyệt dữ liệu theo thứ tự tăng dần.

Nếu dùng list chưa sort, search là `O(n)`.
Nếu giữ list luôn sort, search bằng binary search là `O(log n)`, nhưng insert giữa list phải dịch phần tử: `O(n)`.

Binary search tree tổ chức dữ liệu theo quan hệ:

```text
left < node < right
```

để search và insert có thể đi xuống một nhánh thay vì scan toàn bộ — miễn là cây không bị lệch quá mức.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir BinarySearchTreeDemo
cd BinarySearchTreeDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

Project `.csproj` tạo ở bước trên dùng cấu hình sau:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <LangVersion>13</LangVersion>
  </PropertyGroup>
</Project>
```

Mã Program.cs:

```csharp
namespace BinarySearchTreeDemo;

public sealed class BinarySearchTree<T>
    where T : IComparable<T>
{
    private sealed class Node(T value)
    {
        public T Value { get; } = value;
        public Node? Left { get; set; }
        public Node? Right { get; set; }
    }

    private Node? _root;

    public int Count { get; private set; }

    public bool Add(T value)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (_root is null)
        {
            _root = new Node(value);
            Count++;
            return true;
        }

        Node current = _root;

        while (true)
        {
            int comparison = value.CompareTo(current.Value);

            if (comparison == 0)
            {
                return false;
            }

            if (comparison < 0)
            {
                if (current.Left is null)
                {
                    current.Left = new Node(value);
                    Count++;
                    return true;
                }

                current = current.Left;
            }
            else
            {
                if (current.Right is null)
                {
                    current.Right = new Node(value);
                    Count++;
                    return true;
                }

                current = current.Right;
            }
        }
    }

    public bool Contains(T value)
    {
        ArgumentNullException.ThrowIfNull(value);
        Node? current = _root;

        while (current is not null)
        {
            int comparison = value.CompareTo(current.Value);

            if (comparison == 0)
            {
                return true;
            }

            current = comparison < 0
                ? current.Left
                : current.Right;
        }

        return false;
    }

    public IEnumerable<T> InOrder()
    {
        var pending = new Stack<Node>();
        Node? current = _root;
        while (current is not null || pending.Count > 0)
        {
            while (current is not null)
            {
                pending.Push(current);
                current = current.Left;
            }

            current = pending.Pop();
            yield return current.Value;
            current = current.Right;
        }
    }

}

internal static class Program
{
    private static void Main()
    {
        var tree = new BinarySearchTree<int>();

        foreach (int value in new[] { 8, 3, 10, 1, 6, 14, 4, 7, 13 })
        {
            tree.Add(value);
        }

        Console.WriteLine(string.Join(", ", tree.InOrder()));
        Console.WriteLine($"Count = {tree.Count}");
        Console.WriteLine($"Contains 7 = {tree.Contains(7)}");
        Console.WriteLine($"Contains 9 = {tree.Contains(9)}");
    }
}
```

Output:

```text
1, 3, 4, 6, 7, 8, 10, 13, 14
Count = 9
Contains 7 = True
Contains 9 = False
```

### Walkthrough — execution / state / cost

1. Add đi từ root, so CompareTo và chỉ tạo node tại link rỗng.
2. Contains dùng cùng relation, không duyệt nhánh chắc chắn ngoài mục tiêu.
3. InOrder đẩy đường trái lên Stack, pop rồi sang phải; yield trả từng value.
4. Mỗi node push/pop một lần nên traversal O(n), pending stack O(h). Search/insert O(h); build cây lệch bằng n insert có thể O(n²).

### Mini-check

Insert1..5: tổng số lần so sánh tăng thế nào dù mỗi insert chỉ đi một nhánh?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Thuật ngữ

Với cây:

```text
        8
      /   \
     3     10
    / \      \
   1   6      14
      / \     /
     4   7   13
```

- `8`: root;
- `3` và `10`: child của 8;
- `8`: parent của 3 và 10;
- `1`, `4`, `7`, `13`: leaf;
- depth: khoảng cách từ root tới node;
- height: độ dài đường đi dài nhất xuống leaf.

### Quy tắc BST

Mỗi node thỏa:

```text
mọi value bên trái < node.Value
mọi value bên phải > node.Value
```

Vì vậy search 7:

```text
7 < 8  -> trái
7 > 3  -> phải
7 > 6  -> phải
7 == 7 -> found
```

Không cần xem các node ở nhánh phải của 8.

### Complexity phụ thuộc height

Nếu cây gần cân bằng:

```text
height ≈ log2(n)
```

Search/insert trung bình tốt:

```text
O(log n)
```

Nếu insert dữ liệu đã sort:

```text
1
 \
  2
   \
    3
     \
      4
       \
        5
```

height trở thành `n`.

Search/insert suy giảm thành:

```text
O(n)
```

### Inorder traversal

Thứ tự:

```text
left -> node -> right
```

Với BST, inorder tạo sequence tăng dần.

Traversal phải thăm mọi node:

```text
O(n)
```

Sample dùng stack tường minh có tối đa h node đang chờ; không dùng đệ quy qua nhiều iterator lồng nhau. Kiểu iterator lồng `foreach/yield` có thể chuyển tiếp mỗi value qua nhiều ancestor, làm tăng chi phí theo độ sâu. Extra space của bản hiện tại:

```text
O(h)
```

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| BST không cân bằng | giữ ordering bằng links | O(h), worst O(n) mỗi lookup |
| balanced tree | giữ h gần log n | thêm rotation; dùng thư viện nếu đủ |
| hash table | exact membership | average O(1), không có ordering tự nhiên |

### Misconception check

**Đúng hay sai?** Cây có hai con mỗi node thì chắc cao log n.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tối đa hai con vẫn cho phép chỉ một nhánh dài.

</details>

**Đúng hay sai?** CompareTo==0 mà Equals false vẫn thêm được vào sample.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample coi comparison0 là duplicate.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** đường đi và ordering.

- **Working Developer — dùng khi làm việc:** worst case và comparator.

- **Deep Dive — có thể quay lại sau:** balanced tree khi có driver.

### Binary tree không đồng nghĩa BST

Binary tree chỉ nói:

> mỗi node có tối đa hai child.

Nó không bắt buộc quan hệ thứ tự.

BST thêm invariant ordering.

### Balanced BST

Các cây như AVL hoặc Red-Black Tree duy trì height gần `O(log n)` bằng rotation/rebalancing.

Trong ứng dụng thường không tự implement nếu runtime/library đã có abstraction phù hợp.

### Tree trong phần mềm thật

Tree xuất hiện ở:

- filesystem;
- menu phân cấp;
- organization chart;
- AST của compiler;
- DOM;
- B-tree/B+ tree trong database index;
- routing/tree-based search.

Không phải mọi tree đều là binary tree.

## 6. Lỗi thường gặp

### Gọi BST là O(log n) tuyệt đối

BST thường chỉ đạt `O(log n)` khi height được kiểm soát.

Unbalanced BST có worst case `O(n)`.

### Quên policy duplicate

BST phải quyết định:

- cấm duplicate;
- lưu count;
- cho duplicate sang một phía;
- hoặc dùng collection tại node.

Sample trả `false` khi duplicate.

### Dùng recursion với tree cực sâu

Traversal recursive đẹp và tự nhiên nhưng tree lệch hàng trăm nghìn node có thể gây stack overflow.

### Dùng BST khi Dictionary phù hợp hơn

Nếu nhu cầu chỉ là exact-key lookup, hash table thường đơn giản và average `O(1)`.

BST hữu ích khi cần ordering/range traversal.

## 7. Khi nào KHÔNG dùng

Không dùng BST tự viết khi chỉ exact lookup. Không coi cây nhị phân là cùng cấu trúc B-tree của database.

## 8. Production notes & scale check

Gate so với SortedSet trên input seed cố định và trùng; kiểm null và duyệt cây lệch có độ sâu vừa phải. InOrder đã đổi từ iterator đệ quy lồng foreach sang stack để không chuyển tiếp value qua từng ancestor. Keys không được đổi phần tham gia CompareTo khi đã lưu; không mutate trong iterator.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Min và Max

Viết:

```csharp
T Min()
T Max()
```

**Gợi ý:** đi hết trái hoặc hết phải.

### Bài 2 — Preorder và Postorder

Cài:

```text
preorder: node-left-right
postorder: left-right-node
```

### Bài 3 — Height

Tính height của tree.

Phân tích time complexity.

### Bài 4 — Dữ liệu sort

Insert 1..20 theo thứ tự tăng dần. Vẽ tree và giải thích hiệu năng.

### Bài 5 — Range query

Trả các value nằm trong `[min, max]` mà không cần duyệt những nhánh chắc chắn ngoài range.

## 10. Bài tập tích hợp liên module — Judgment

Từ invariant Module06, nơi nào giữ ordering và vì sao get-only reference chưa bảo đảm object T bất biến? Với100key nhỏ và ít query, chọn sorted array hay tree.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Search phụ thuộc n hay h?
2. Policy duplicate là gì?
3. Iterator giữ state nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt binary tree và BST.
- [ ] Tôi giải thích invariant trái < node < phải.
- [ ] Tôi search/insert được BST.
- [ ] Tôi biết complexity phụ thuộc height.
- [ ] Tôi giải thích được cây lệch làm `O(log n)` thành `O(n)`.
- [ ] Tôi hiểu inorder của BST cho thứ tự tăng dần.

Điều hướng:

- Bài trước: [Hash table và hash function](./06-hash-table-va-hash-function.md)
- Bài tiếp theo: [Heap và priority queue](./08-heap-va-priority-queue.md)
