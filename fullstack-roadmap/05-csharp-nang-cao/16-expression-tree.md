# Expression tree

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt delegate thực thi với expression tree mô tả code như dữ liệu;
- đọc các node `Lambda`, `AndAlso`, `MemberAccess`, `Constant` và `Parameter`;
- tạo `Expression<Func<T, bool>>` từ lambda expression;
- dựng expression tree bằng factory API ở runtime;
- compile tree thành delegate và kiểm tra kết quả;
- hiểu expression tree là object graph immutable trên managed heap;
- nhận ra closure, method call và node không hỗ trợ có thể cản translation;
- không thực thi expression đến từ nguồn chưa tin cậy nếu chưa validate.

## 2. Bài toán mở đầu

Một hệ thống duyệt đơn có rule:

```text
đơn đang active và total từ 1.000.000 VND
```

Nếu rule chỉ là `Func<Order, bool>`, ta gọi được nhưng khó đi qua cấu trúc để log, kiểm tra hoặc chuyển cho một engine khác. Ta cần đồng thời:

- nhìn được rule gồm phép `>=`, `&&` và member nào;
- chạy rule trong process để kiểm thử;
- dựng một rule ngưỡng khác từ cấu hình runtime;
- không nhầm “cây dữ liệu mô tả code” với source code string tùy ý.

Bài này giới thiệu expression tree trực tiếp, không yêu cầu kiến thức LINQ query.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name ExpressionRuleDemo --framework net9.0 --use-program-main
cd ExpressionRuleDemo
```

Thay `ExpressionRuleDemo.csproj` bằng:

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
using System.Globalization;
using System.Linq.Expressions;

namespace ExpressionRuleDemo;

internal static class Program
{
    private static void Main()
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;

        Expression<Func<Order, bool>> approvalRule =
            order => order.Total >= 1_000_000m && order.IsActive;

        Console.WriteLine($"Rule text: {approvalRule}");
        Console.WriteLine("Tree:");
        PrintNode(approvalRule, indent: 0);

        // Compile một lần, dùng delegate nhiều lần.
        Func<Order, bool> approve = approvalRule.Compile();

        var first = new Order("A-01", 1_200_000m, true);
        var second = new Order("A-02", 2_000_000m, false);
        var third = new Order("A-03", 800_000m, true);

        Console.WriteLine($"Rule A-01: {approve(first)}");
        Console.WriteLine($"Rule A-02: {approve(second)}");
        Console.WriteLine($"Rule A-03: {approve(third)}");

        Expression<Func<Order, bool>> runtimeRule =
            BuildMinimumTotalRule(750_000m);
        Func<Order, bool> runtimePredicate = runtimeRule.Compile();

        Console.WriteLine($"Runtime rule: {runtimeRule}");
        Console.WriteLine($"Runtime rule A-03: {runtimePredicate(third)}");
    }

    private static Expression<Func<Order, bool>> BuildMinimumTotalRule(
        decimal minimumTotal)
    {
        ParameterExpression order = Expression.Parameter(
            typeof(Order),
            name: "order");

        MemberExpression total = Expression.Property(
            order,
            nameof(Order.Total));

        ConstantExpression threshold = Expression.Constant(
            minimumTotal,
            typeof(decimal));

        BinaryExpression comparison = Expression.GreaterThanOrEqual(
            total,
            threshold);

        return Expression.Lambda<Func<Order, bool>>(comparison, order);
    }

    private static void PrintNode(Expression node, int indent)
    {
        string prefix = new(' ', indent * 2);

        switch (node)
        {
            case LambdaExpression lambda:
                Console.WriteLine($"{prefix}Lambda ({lambda.Type.Name})");
                PrintNode(lambda.Body, indent + 1);
                break;

            case BinaryExpression binary:
                Console.WriteLine($"{prefix}{binary.NodeType}");
                PrintNode(binary.Left, indent + 1);
                PrintNode(binary.Right, indent + 1);
                break;

            case MemberExpression member:
                Console.WriteLine($"{prefix}MemberAccess ({member.Member.Name})");
                if (member.Expression is not null)
                {
                    PrintNode(member.Expression, indent + 1);
                }
                break;

            case ParameterExpression parameter:
                Console.WriteLine($"{prefix}Parameter ({parameter.Name})");
                break;

            case ConstantExpression constant:
                Console.WriteLine($"{prefix}Constant ({constant.Value})");
                break;

            default:
                Console.WriteLine($"{prefix}{node.NodeType} ({node.Type.Name})");
                break;
        }
    }
}

internal sealed record Order(string Id, decimal Total, bool IsActive);
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Các dòng chính trong output:

```text
Rule text: order => ((order.Total >= 1000000) AndAlso order.IsActive)
Tree:
Lambda (Func`2)
  AndAlso
    GreaterThanOrEqual
      MemberAccess (Total)
        Parameter (order)
      Constant (1000000)
    MemberAccess (IsActive)
      Parameter (order)
Rule A-01: True
Rule A-02: False
Rule A-03: False
Runtime rule: order => (order.Total >= 750000)
Runtime rule A-03: True
```

## 4. Giải thích cơ chế

### 4.1. Cùng cú pháp lambda, hai target type khác nhau

Compiler dùng target type để quyết định sản phẩm:

```csharp
Func<Order, bool> executable = order => order.IsActive;
Expression<Func<Order, bool>> data = order => order.IsActive;
```

- `Func<Order, bool>` là delegate có thể gọi ngay; body không được trình bày thành public object graph để visitor tùy ý phân tích.
- `Expression<Func<Order, bool>>` là object graph các node mô tả lambda tương thích.

Không phải mọi lambda đều chuyển thành expression tree. Ví dụ statement-bodied lambda và nhiều feature ngôn ngữ mới không có node tương ứng hoặc bị compiler cấm trong expression tree.

### 4.2. Cây của rule đầu tiên

```text
Lambda(order)
└── AndAlso                         // &&, có short-circuit
    ├── GreaterThanOrEqual          // >=
    │   ├── MemberAccess Total
    │   │   └── Parameter order
    │   └── Constant 1000000m
    └── MemberAccess IsActive
        └── Parameter order  (cùng parameter node logic)
```

`AndAlso` khác `And`: nó giữ semantics short-circuit của `&&`. Type của từng node phải khớp; hai nhánh của `AndAlso` phải tạo `bool`.

### 4.3. Expression tree là object graph immutable

Mô hình bộ nhớ rút gọn:

```text
approvalRule ref ──> LambdaExpression object
                       ├── Body ref ──> AndAlso node
                       │                 ├── Left ref  ──> >= node
                       │                 └── Right ref ──> Member node
                       └── Parameters ──> collection ──> Parameter node
                                                            ^
                       các Member node tham chiếu -----------┘
```

Các node nằm trên managed heap và có thể chia sẻ child node. API expression thiết kế immutable: muốn đổi threshold, tạo constant/tree mới hoặc dùng visitor tạo cây biến đổi; không sửa field nội bộ tại chỗ. Immutability giúp chia sẻ tree an toàn hơn nhưng không tự làm delegate/result thread-safe nếu code được gọi mutate state khác.

### 4.4. `Compile()` đổi data thành executable

`approvalRule.Compile()` tạo delegate thực thi semantics của tree. Compilation có chi phí, nên không compile lại cùng rule cho từng request. Cache theo tập rule có giới hạn và invalidation rõ.

Một số môi trường không cho sinh dynamic code. `Compile(preferInterpretation: true)` yêu cầu interpreter và có trade-off startup/throughput khác. Nếu target Native AOT, kiểm thử đúng publish mode; đừng giả định mọi node/compile mode hoạt động giống JIT.

### 4.5. Factory API dựng rule runtime

`BuildMinimumTotalRule` tạo lần lượt parameter, property access, constant, comparison và lambda. Factory kiểm tra type; dùng sai property hoặc operand type sẽ gây exception lúc dựng cây, sớm hơn lúc gọi delegate.

Parameter node truyền vào body phải là đúng node có trong parameter list. Chỉ tạo node khác cùng tên `"order"` không làm nó thành cùng biến; identity của node tham gia binding.

### 4.6. Expression tree không phải source string

Tree không tự parse C# và không tự serializable. Một engine có thể duyệt các node được cho phép rồi dịch sang ngôn ngữ khác, nhưng mỗi engine chỉ hỗ trợ một tập node/method nhất định. `Compile()` chạy code .NET; “dịch” là một operation riêng của provider.

Không nhận tree hoặc cấu hình method/type tùy ý từ nguồn chưa tin cậy rồi compile. Allowlist member/operator, giới hạn độ sâu/kích thước và tách authorization khỏi parsing.

## 5. Kiến thức nền

### Các node thường gặp

| Node/API | Ý nghĩa |
|---|---|
| `ParameterExpression` | biến/parameter có type và identity |
| `ConstantExpression` | literal hoặc reference constant |
| `MemberExpression` | đọc field/property |
| `BinaryExpression` | toán tử hai vế như `>=`, `AndAlso`, `Add` |
| `MethodCallExpression` | lời gọi method |
| `UnaryExpression` | convert, negate, not |
| `ConditionalExpression` | toán tử điều kiện |
| `LambdaExpression` | parameter list và body |

Luôn kiểm tra cả `NodeType` lẫn `.Type`; hai node cùng `NodeType` vẫn có operand/type khác nhau.

### Closure xuất hiện trong tree như thế nào?

Nếu lambda dùng local:

```csharp
decimal threshold = 1_000_000m;
Expression<Func<Order, bool>> rule = order => order.Total >= threshold;
```

compiler có thể biểu diễn `threshold` như member access trên một closure object được giữ trong `ConstantExpression`, không phải luôn là constant decimal trực tiếp. Engine dịch tree phải quyết định có đánh giá closure member hay từ chối. Muốn cấu trúc dự đoán được, dựng `Expression.Constant` tường minh như sample runtime.

### Visitor

`ExpressionVisitor` cung cấp traversal và trả node mới khi biến đổi. Visitor phải xử lý/allowlist node rõ ràng; fallback im lặng có thể làm rule mang semantics ngoài dự kiến.

### Equality của tree

Hai tree in giống nhau không mặc nhiên reference-equal hoặc structurally equal. Nếu cần cache theo cấu trúc, phải định nghĩa comparer/canonical form đúng cho node, member, constant và closure; đây là bài toán riêng, không dùng `.ToString()` làm key production.

## 6. Lỗi thường gặp

### Gọi `Compile()` trong mỗi iteration/request

Compilation lặp lại tạo overhead và có thể tăng allocation. Compile một lần khi rule thay đổi, cache có giới hạn, đo cả startup lẫn throughput.

### Tưởng mọi C# lambda đều thành expression tree

Expression tree API không biểu diễn toàn bộ ngôn ngữ C# hiện đại. Giữ lambda đơn giản hoặc dựng node factory thuộc tập engine hỗ trợ.

### Dịch mọi `MethodCallExpression` bằng tên method

Overload và declaring type mới xác định member. So sánh `MethodInfo`/contract allowlist, không chỉ string name.

### Nhầm `And` với `AndAlso`

`And` đánh giá cả hai vế; `AndAlso` short-circuit. Với null guard hoặc side effect, chọn sai node đổi hành vi.

### Capture object mutable ngoài ý muốn

Compiled delegate có thể giữ closure sống lâu và đọc state thay đổi theo thời gian. Truyền constant snapshot rõ ràng hoặc document live configuration semantics.

### Xem expression tree là dữ liệu an toàn mặc định

Tree có thể chứa method/constructor/member access. Validate allowlist, độ sâu và resource limits trước interpretation/compilation từ input ngoài.

## 7. Bài tập

### Bài 1 — Rule trạng thái

Tạo `Expression<Func<Order, bool>>` kiểm tra `IsActive` và `Total < 500_000m`, rồi in tree và compile.

**Gợi ý:** xác nhận `&&` thành `AndAlso`; test bốn tổ hợp biên.

### Bài 2 — Dựng equality bằng factory

Viết `BuildIdRule(string id)` dùng `Expression.Property`, `Expression.Constant` và `Expression.Equal`.

**Gợi ý:** parameter node trong body và parameter list phải cùng instance.

### Bài 3 — Đổi threshold bằng visitor

Viết visitor thay một `ConstantExpression` decimal cụ thể bằng constant mới, không mutate tree gốc.

**Gợi ý:** chỉ thay đúng type/value allowlist; so sánh output của tree cũ và mới.

### Bài 4 — Khảo sát closure

Tạo rule capture local `threshold`, in tree, đổi local sau khi compile rồi gọi delegate lại.

**Gợi ý:** tìm `Constant` chứa closure object và `MemberAccess`; ghi rõ snapshot hay live state bạn quan sát được.

### Bài 5 — Validator node

Viết visitor chỉ chấp nhận parameter, constant decimal, property `Order.Total` và các comparison cho phép.

**Gợi ý:** giới hạn độ sâu; ném lỗi khi gặp `MethodCallExpression` thay vì bỏ qua.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt delegate executable với expression object graph.
- [ ] Tôi đọc được node tree của một lambda đơn giản.
- [ ] Tôi dựng tree runtime với parameter identity và type đúng.
- [ ] Tôi compile một lần và hiểu trade-off interpreter/JIT/AOT.
- [ ] Tôi biết tree immutable và closure có thể xuất hiện như object/member access.
- [ ] Tôi chỉ cho engine xử lý tập node/member được hỗ trợ và tin cậy.

Điều hướng:

- Prerequisite: [Covariance và contravariance](./15-covariance-va-contravariance.md)
- Bài tiếp theo: [Serialization với `System.Text.Json`](./17-serialization-system-text-json.md)
