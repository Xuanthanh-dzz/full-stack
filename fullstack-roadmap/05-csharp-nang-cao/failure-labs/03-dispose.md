# Failure Lab — Đóng dependency đang được mượn

Sau bài 15. SDK9.0.121 / net9.0 / C#13; chạy trong thư mục tạm.

## Bối cảnh

Helper chỉ mượn stream để ghi một byte; caller còn cần dùng stream sau khi helper return.

## Code lỗi

Lưu đoạn tái hiện độc lập sau vào Program.cs của project tạm:

```csharp
using var stream=new MemoryStream();
WriteBorrowed(stream);
try{stream.WriteByte(2);}catch(ObjectDisposedException){Console.WriteLine("owner cannot write");}
static void WriteBorrowed(Stream stream){using(stream){stream.WriteByte(1);}}
```

## Triệu chứng

Output hiện tại: `owner cannot write`. Ghi expected theo contract trước khi sửa.

## Cách tái hiện

Tạo console project bằng `dotnet new console --framework net9.0`, thay Program.cs bằng code trên, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code; không cần network hoặc timing ngẫu nhiên.

## Acceptance criteria

- Đáp ứng contract trong Bối cảnh, có assertion trạng thái trước/sau.
- Test phải bắt lỗi của bản gốc rồi pass bản sửa.
- Không nuốt exception hoặc bỏ ownership để che lỗi.
- Giải thích nơi execution chạy, state được giữ và chi phí bản sửa.

## Hints

1. Đánh dấu owner và borrower; using có trách nhiệm gì khi helper không nhận ownership?
2. Chỉ ra câu lệnh đầu tiên khiến actual lệch expected.
3. Chọn sửa nhỏ, kiểm tra cả đường thành công và đường lỗi.

## Checklist điều tra

- [ ] Hypothesis và evidence trước sửa.
- [ ] Trace state/lifetime và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Nêu metric hoặc log cần theo dõi trong ứng dụng thật.

[Bản đồ](../index.md).
