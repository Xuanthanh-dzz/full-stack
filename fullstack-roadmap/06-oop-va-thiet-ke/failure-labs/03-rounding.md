# Failure Lab — Refactor đổi thứ tự làm tròn

Sau bài 14; .NET SDK9.0.121, net9.0, C#13. Chạy trong thư mục tạm.

## Bối cảnh

Giữ kết quả tiền của legacy cho mọi ca trong miền VND đã chốt.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
decimal subtotal = 10m;
decimal legacy = decimal.Round(subtotal * .05m, 0) + decimal.Round(subtotal * .03m, 0);
decimal changed = decimal.Round(subtotal * (.05m + .03m), 0);
Console.WriteLine($"same={legacy == changed}");
```

## Triệu chứng

Output hiện tại `same=False`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Giữ thứ tự tính/làm tròn đã cam kết; thêm case đúng midpoint và case không midpoint.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. 0.5 ToEven ra bao nhiêu? Không lấy ngẫu nhiên toàn số lớn mà bỏ biên.
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
