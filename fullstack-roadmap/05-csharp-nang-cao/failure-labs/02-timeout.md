# Failure Lab — Timeout nhưng producer vẫn sửa state

Sau bài 10. SDK9.0.121 / net9.0 / C#13; chạy trong thư mục tạm.

## Bối cảnh

Caller muốn timeout là yêu cầu ngừng trước commit; chỉ ngừng chờ chưa đáp ứng contract.

## Code lỗi

Lưu đoạn tái hiện độc lập sau vào Program.cs của project tạm:

```csharp
var producer=new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
int saved=0;
async Task Work(){await producer.Task;saved++;}
Task work=Work();
try{await work.WaitAsync(TimeSpan.Zero);}catch(TimeoutException){}
producer.SetResult();
await work;
Console.WriteLine($"saved={saved}");
```

## Triệu chứng

Output hiện tại: `saved=1`. Ghi expected theo contract trước khi sửa.

## Cách tái hiện

Tạo console project bằng `dotnet new console --framework net9.0`, thay Program.cs bằng code trên, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code; không cần network hoặc timing ngẫu nhiên.

## Acceptance criteria

- Đáp ứng contract trong Bối cảnh, có assertion trạng thái trước/sau.
- Test phải bắt lỗi của bản gốc rồi pass bản sửa.
- Không nuốt exception hoặc bỏ ownership để che lỗi.
- Giải thích nơi execution chạy, state được giữ và chi phí bản sửa.

## Hints

1. Phân biệt waiting task và underlying task; chọn token checkpoint trước mutation và vẫn await cleanup/completion.
2. Chỉ ra câu lệnh đầu tiên khiến actual lệch expected.
3. Chọn sửa nhỏ, kiểm tra cả đường thành công và đường lỗi.

## Checklist điều tra

- [ ] Hypothesis và evidence trước sửa.
- [ ] Trace state/lifetime và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Nêu metric hoặc log cần theo dõi trong ứng dụng thật.

[Bản đồ](../index.md).
