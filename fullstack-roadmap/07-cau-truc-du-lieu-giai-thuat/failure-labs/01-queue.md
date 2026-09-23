# Failure Lab — Hàng đợi bằng RemoveAt(0)

Sau bài 05; .NET SDK9.0.121, net9.0, C#13. Chạy trong thư mục tạm.

## Bối cảnh

Lấy1000 việc theo FIFO, tránh dời lại toàn bộ phần còn lại mỗi lần.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
var jobs = Enumerable.Range(0, 1000).ToList();
long shifts = 0;
while (jobs.Count > 0)
{
    shifts += jobs.Count - 1;
    jobs.RemoveAt(0);
}
Console.WriteLine($"shifts={shifts}");
```

## Triệu chứng

Output hiện tại `shifts=499500`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Giữ FIFO, mỗi job xử lý đúng một lần; số bước lấy tăng tuyến tính theo n. So n và 2n bằng bộ đếm, không chỉ stopwatch.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. RemoveAt(0) phải dời bao nhiêu phần tử? Queue có giữ cùng contract không?
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
