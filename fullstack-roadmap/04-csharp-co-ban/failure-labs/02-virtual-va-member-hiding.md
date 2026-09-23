# Failure Lab — Gọi qua base cho phí sai

Sau bài 10. Baseline .NET SDK 9.0.121 / C# 13 / net9.0. Code cố ý lỗi; dùng thư mục tạm riêng.

## Bối cảnh

Cùng loại Express nhưng phí qua base khác gọi trực tiếp. Requirement: mọi cách gọi qua contract Shipping phải nhận phí Express.

## Code lỗi

Thay Program.cs của console project bằng:

```csharp
Shipping a = new Express();
Console.WriteLine($"base={a.Fee()}, direct={new Express().Fee()}");
class Shipping { public virtual decimal Fee() => 25m; }
class Express : Shipping { public new decimal Fee() => 55m; }
```

## Triệu chứng

Output lỗi đã tái hiện: `base=25, direct=55`. Ghi expected trước khi sửa và giải thích vì sao không chấp nhận output hiện tại.

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

- Phí qua base và trực tiếp cùng 55; Shipping thường vẫn 25.
- Không sửa bằng cast tại từng caller hoặc so tên type.
- Giải thích static type, runtime type, hiding và override bằng trace.

## Hints

1. Biến a có static type nào?
2. new member ở đây khác new object như thế nào?
3. Member nào thực sự tham gia virtual dispatch?

## Checklist điều tra

- [ ] Vẽ state và alias trước/sau lời gọi.
- [ ] Chỉ câu lệnh đầu tiên làm kết quả lệch contract.
- [ ] Viết test bắt lỗi gốc rồi sửa nhỏ.
- [ ] Nộp expected/actual, diff và bằng chứng bản sửa.

[Bản đồ module](../index.md).
