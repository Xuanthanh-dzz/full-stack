# Failure Lab — Đáp án backtracking cùng trỏ một list

Sau bài 19; .NET SDK 9.0.121, net9.0, C# 13. Chạy trong thư mục tạm.

## Bối cảnh

Mỗi kết quả phải giữ lựa chọn tại lúc tìm thấy, dù current được dùng lại.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
var current = new List<int>();
var answers = new List<List<int>>();
current.Add(3);
answers.Add(current);
current.Clear();
current.Add(7);
answers.Add(current);
current.Clear();
Console.WriteLine($"lengths={string.Join(',', answers.Select(x => x.Count))}");
```

## Triệu chứng

Output hiện tại `lengths=0,0`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Đáp án cuối là[3] và[7], không đổi khi current tiếp tục sửa; giải thích cost copy theo tổng kích thước output.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. List.Add lưu reference hay snapshot? Copy ở bước nào đủ và ít tốn nhất?
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
