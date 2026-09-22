# Tree và binary search tree

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

## 3. Lời giải bằng code

```bash
mkdir BinarySearchTreeDemo
cd BinarySearchTreeDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

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
        return TraverseInOrder(_root);
    }

    private static IEnumerable<T> TraverseInOrder(Node? node)
    {
        if (node is null)
        {
            yield break;
        }

        foreach (T value in TraverseInOrder(node.Left))
        {
            yield return value;
        }

        yield return node.Value;

        foreach (T value in TraverseInOrder(node.Right))
        {
            yield return value;
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

## 4. Giải thích cơ chế

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

Call-stack space phụ thuộc height:

```text
O(h)
```

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt binary tree và BST.
- [ ] Tôi giải thích invariant trái < node < phải.
- [ ] Tôi search/insert được BST.
- [ ] Tôi biết complexity phụ thuộc height.
- [ ] Tôi giải thích được cây lệch làm `O(log n)` thành `O(n)`.
- [ ] Tôi hiểu inorder của BST cho thứ tự tăng dần.

Điều hướng:

- Bài trước: [Hash table và hash function](./06-hash-table-va-hash-function.md)
- Bài tiếp theo: [Heap và priority queue](./08-heap-va-priority-queue.md)
