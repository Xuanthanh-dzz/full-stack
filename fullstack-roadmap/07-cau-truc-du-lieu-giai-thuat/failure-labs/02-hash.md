# Failure Lab — Khóa đổi sau khi vào bảng hash

Sau bài 10; .NET SDK9.0.121, net9.0, C#13. Chạy trong thư mục tạm.

## Bối cảnh

Mã của key được dùng cho equality và hash; item đã thêm phải tìm được.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
var key = new Key { Id = 1 };
var set = new HashSet<Key> { key };
key.Id = 2;
Console.WriteLine($"found={set.Contains(key)}");
sealed class Key
{
    public int Id { get; set; }
    public override int GetHashCode() => Id;
    public override bool Equals(object? other) => other is Key k && k.Id == Id;
}
```

## Triệu chứng

Output hiện tại `found=False`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Giữ identity key ổn định khi ở trong set; có test key khác cùng giá trị và collision khác giá trị.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. Cùng object reference có đủ nếu bucket được chọn bằng hash mới không?
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
