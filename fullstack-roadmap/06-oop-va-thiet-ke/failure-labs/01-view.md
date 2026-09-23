# Failure Lab — View đọc được nhưng dữ liệu vẫn bị sửa

Sau bài 05; .NET SDK9.0.121, net9.0, C#13. Chạy trong thư mục tạm.

## Bối cảnh

Đơn đã đặt có ít nhất một dòng; caller chỉ được đọc Lines.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
var order = new Order();
((List<string>)order.Lines).Clear();
Console.WriteLine($"lines={order.Lines.Count}");
sealed class Order
{
    private readonly List<string> _lines = new() { "SKU-A" };
    public IReadOnlyList<string> Lines => _lines;
}
```

## Triệu chứng

Output hiện tại `lines=0`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Không cho sửa collection qua API đọc; giữ view sống hoặc snapshot theo quyết định có giải thích.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. Kiểm runtime type khác kiểu khai báo. So wrapper với copy, tính cả cost và alias phần tử.
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
