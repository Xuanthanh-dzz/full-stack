# Failure Lab — Copy list nhưng chia sẻ item

Sau bài 16. Baseline .NET SDK 9.0.121 / C# 13 / net9.0. Code cố ý lỗi; dùng thư mục tạm riêng.

## Bối cảnh

Save cố ý lỗi trước ghi; list cũ vẫn bị đổi vì hai list chứa cùng reference. GC không bảo đảm rollback nghiệp vụ.

## Code lỗi

Thay Program.cs của console project bằng:

```csharp
var items = new List<Todo> { new() { Done = false } };
var candidate = new List<Todo>(items);
try
{
    candidate[0].Done = true;
    Save(candidate);
}
catch (IOException) { Console.WriteLine($"old_done={items[0].Done}"); }
static void Save(IReadOnlyList<Todo> items) => throw new IOException("disk full");
class Todo { public bool Done { get; set; } }
```

## Triệu chứng

Output lỗi đã tái hiện: `old_done=True`. Ghi expected trước khi sửa và giải thích vì sao không chấp nhận output hiện tại.

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

- Save lỗi giữ toàn bộ state cũ; thành công công bố state mới.
- Snapshot trước thao tác giữ giá trị cũ sau thao tác.
- Test cả add/done/remove với lỗi trước persistence; nêu giới hạn nếu repository đã ghi rồi mới throw.

## Hints

1. Vẽ hai list và đếm số Todo object.
2. Copy container có clone element không?
3. Chỉ object nào cần tạo mới trước commit để tránh copy sâu vô cớ?

## Checklist điều tra

- [ ] Vẽ state và alias trước/sau lời gọi.
- [ ] Chỉ câu lệnh đầu tiên làm kết quả lệch contract.
- [ ] Viết test bắt lỗi gốc rồi sửa nhỏ.
- [ ] Nộp expected/actual, diff và bằng chứng bản sửa.

[Bản đồ module](../index.md).
