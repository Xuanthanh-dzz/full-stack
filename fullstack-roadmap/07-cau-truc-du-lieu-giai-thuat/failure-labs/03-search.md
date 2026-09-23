# Failure Lab — Binary search trên dữ liệu chưa sort

Sau bài 15; .NET SDK 9.0.121, net9.0, C# 13. Chạy trong thư mục tạm.

## Bối cảnh

Tra cứu 4 trong danh sách giữ thứ tự nhập; không được báo mất phần tử đang có.

## Code lỗi

Lưu đoạn độc lập sau vào Program.cs:

```csharp
int[] values = [4, 1, 3];
Console.WriteLine($"index={Search(values, 4)}");
static int Search(int[] values, int key)
{
    int lo = 0, hi = values.Length - 1;
    while (lo <= hi)
    {
        int mid = lo + (hi - lo) / 2;
        if (values[mid] == key) return mid;
        if (values[mid] < key) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}
```

## Triệu chứng

Output hiện tại `index=-1`. Ghi output mong muốn trước khi sửa.

## Cách tái hiện

Tạo project với `dotnet new console --framework net9.0`, thay Program.cs, chạy `dotnet run -c Release`. Ghi SDK, stdout/stderr và exit code. Chạy lại Debug để phân biệt contract runtime với assert.

## Acceptance criteria

- Tìm được index trong danh sách gốc, giữ nguyên input. Chọn scan hoặc index phụ theo số queries; không sort tại chỗ rồi trả index sai nghĩa.
- Có test đỏ với bản lỗi và xanh với bản sửa.
- Giải thích nơi state sống, ai được sửa và chi phí thay đổi.
- Không đổi expected để che bug; giữ lỗi và diff trong submission.

## Hints

1. Đáp án index thuộc thứ tự nào? Điều kiện cho phép bỏ nửa trái đã đúng chưa?
2. Tìm dòng đầu tiên actual lệch contract, trước khi sửa các dòng sau.
3. Chọn giải pháp nhỏ nhất, nêu một điều kiện khiến phải xét lại.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] Trace trước/sau và root cause.
- [ ] Diff nhỏ cùng regression test.
- [ ] Trade-off, evidence và giới hạn.

[Bản đồ](../index.md).
