# Failure Lab — Mã yêu cầu bị giữ trong singleton

Sau bài 10; .NET SDK9.0.121, net9.0, C#13. Chạy trong thư mục tạm.

## Bối cảnh

Audit của yêu cầu thứ hai phải mang req-2, dù nơi gom log dùng chung.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
var log = new Audit("req-1");
RunSecondRequest(log, "req-2");
static void RunSecondRequest(Audit log, string requestId)
{
    _ = requestId;
    log.Write("second");
}
sealed class Audit(string requestId)
{
    public void Write(string message) => Console.WriteLine($"[{requestId}] {message}");
}
```

## Triệu chứng

Output hiện tại `[req-1] second`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Hai request có correlation ID riêng và log chung; test interleave hai request không lẫn ID.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. Vẽ singleton→request state. Xác định ai tạo message và ai sở hữu context.
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
