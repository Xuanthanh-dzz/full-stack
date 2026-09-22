# Failure Lab — Biến cancellation thành kết quả thành công

Sau bài 19. SDK9.0.121 / net9.0 / C#13; chạy trong thư mục tạm.

## Bối cảnh

Cancellation phải đi lên caller với task Canceled; lỗi một file mới được chuyển thành result.

## Code lỗi

Lưu đoạn tái hiện độc lập sau vào Program.cs của project tạm:

```csharp
using var source=new CancellationTokenSource();source.Cancel();
Console.WriteLine(await Process(source.Token));
static async Task<string> Process(CancellationToken token)
{
 try{await Task.Delay(1,token);return "done";}
 catch(Exception){return "completed with file error";}
}
```

## Triệu chứng

Output hiện tại: `completed with file error`. Ghi expected theo contract trước khi sửa.

## Cách tái hiện

Tạo console project bằng `dotnet new console --framework net9.0`, thay Program.cs bằng code trên, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code; không cần network hoặc timing ngẫu nhiên.

## Acceptance criteria

- Đáp ứng contract trong Bối cảnh, có assertion trạng thái trước/sau.
- Test phải bắt lỗi của bản gốc rồi pass bản sửa.
- Không nuốt exception hoặc bỏ ownership để che lỗi.
- Giải thích nơi execution chạy, state được giữ và chi phí bản sửa.

## Hints

1. Đọc exception hierarchy; tách cancellation dự kiến và input failure, giữ token và trạng thái Task.
2. Chỉ ra câu lệnh đầu tiên khiến actual lệch expected.
3. Chọn sửa nhỏ, kiểm tra cả đường thành công và đường lỗi.

## Checklist điều tra

- [ ] Hypothesis và evidence trước sửa.
- [ ] Trace state/lifetime và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Nêu metric hoặc log cần theo dõi trong ứng dụng thật.

[Bản đồ](../index.md).
