# Failure Lab — Capture chung biến vòng lặp

Sau bài 05. SDK9.0.121 / net9.0 / C#13; chạy trong thư mục tạm.

## Bối cảnh

Mỗi callback phải nhớ index của lượt đăng ký, kể cả khi gọi sau khi loop kết thúc.

## Code lỗi

Lưu đoạn tái hiện độc lập sau vào Program.cs của project tạm:

```csharp
var callbacks = new List<Func<int>>();
for (int i=0;i<3;i++) callbacks.Add(()=>i);
var results = new List<int>();
foreach (var callback in callbacks) results.Add(callback());
Console.WriteLine(string.Join(",", results));
```

## Triệu chứng

Output hiện tại: `3,3,3`. Ghi expected theo contract trước khi sửa.

## Cách tái hiện

Tạo console project bằng `dotnet new console --framework net9.0`, thay Program.cs bằng code trên, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code; không cần network hoặc timing ngẫu nhiên.

## Acceptance criteria

- Đáp ứng contract trong Bối cảnh, có assertion trạng thái trước/sau.
- Test phải bắt lỗi của bản gốc rồi pass bản sửa.
- Không nuốt exception hoặc bỏ ownership để che lỗi.
- Giải thích nơi execution chạy, state được giữ và chi phí bản sửa.

## Hints

1. Vẽ storage i chung; so sánh copy local trong body và dùng parameter tường minh.
2. Chỉ ra câu lệnh đầu tiên khiến actual lệch expected.
3. Chọn sửa nhỏ, kiểm tra cả đường thành công và đường lỗi.

## Checklist điều tra

- [ ] Hypothesis và evidence trước sửa.
- [ ] Trace state/lifetime và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Nêu metric hoặc log cần theo dõi trong ứng dụng thật.

[Bản đồ](../index.md).
