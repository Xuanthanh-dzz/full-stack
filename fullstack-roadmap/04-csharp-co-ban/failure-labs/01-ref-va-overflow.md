# Failure Lab — Sửa tồn kho trước phép tính

Sau bài 05. Baseline .NET SDK 9.0.121 / C# 13 / net9.0. Code cố ý lỗi; dùng thư mục tạm riêng.

## Bối cảnh

Reserve thất bại do overflow, nhưng biến stock của caller đã giảm. Contract yêu cầu yêu cầu thất bại giữ kho cũ.

## Code lỗi

Thay Program.cs của console project bằng:

```csharp
int stock = 10;
try { Reserve(ref stock, 2, decimal.MaxValue); }
catch (OverflowException) { Console.WriteLine($"stock={stock}"); }
static decimal Reserve(ref int stock, int quantity, decimal price)
{
    stock -= quantity;
    return quantity * price;
}
```

## Triệu chứng

Output lỗi đã tái hiện: `stock=8`. Ghi expected trước khi sửa và giải thích vì sao không chấp nhận output hiện tại.

## Cách tái hiện

```bash
dotnet new console --framework net9.0 --name Repro
cd Repro
# Thay Program.cs bằng code trên.
dotnet build -c Release -warnaserror
dotnet run -c Release --no-build
```

Chạy cùng SDK baseline; ghi version, stdout/stderr và exit code. Verifier tự dựng source trên, không chạy trên dữ liệu cá nhân.

## Acceptance criteria

- Từ chối quantity/price ngoài miền trước mutation.
- Overflow không làm giảm kho; thành công vẫn trả đúng tiền và giảm đúng số lượng.
- Test quantity 0, thiếu kho, overflow và một đơn hợp lệ.

## Hints

1. ref nối tới biến nào?
2. Phép tính decimal có thể ném lỗi trước hay sau dòng trừ?
3. Chọn guard cận hoặc tính ứng viên trước commit; không nuốt lỗi.

## Checklist điều tra

- [ ] Vẽ state và alias trước/sau lời gọi.
- [ ] Chỉ câu lệnh đầu tiên làm kết quả lệch contract.
- [ ] Viết test bắt lỗi gốc rồi sửa nhỏ.
- [ ] Nộp expected/actual, diff và bằng chứng bản sửa.

[Bản đồ module](../index.md).
