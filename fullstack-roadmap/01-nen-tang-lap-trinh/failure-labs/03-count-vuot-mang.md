# Failure Lab 03 — Báo cáo đọc quá phần tử cuối

> Sau bài 15 · C11 + AddressSanitizer/UBSan · Kết hợp mảng, vòng lặp và evidence debug.

## Bối cảnh

Một công cụ báo cáo giữ ba điểm đã nhập. Bản sửa vòng lặp đôi khi in tổng lạ; có máy vẫn có vẻ chạy bình thường. Lab chỉ chạy trong thư mục tạm bằng sanitizer, không dùng dữ liệu thật.

## Code lỗi

Lưu `lab.c`:

```c
#include <stdio.h>
int main(void)
{
    int scores[] = {8, 7, 9};
    int count = 3;
    int total = 0;
    for (int index = 0; index <= count; index++) {
        total += scores[index];
    }
    printf("Total: %d\n", total);
    return 0;
}
```

## Triệu chứng

Sanitizer báo truy cập ngoài vùng mảng. Không có một output “sai nhưng cố định” để dự đoán: vượt biên là undefined behavior, tức chuẩn C không bảo đảm kết quả.

## Cách tái hiện

Trong thư mục chứa `lab.c`:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror -O0 -g \
  -fsanitize=address,undefined -fno-sanitize-recover=all lab.c -o lab
./lab
```

Ghi diagnostic đầu tiên, dòng source, index và miền hợp lệ. Nếu toolchain không hỗ trợ sanitizer, ghi gate chưa chạy; không coi lần chạy không crash là pass.

## Acceptance criteria

- Sau sửa, tổng là 24 và không có sanitizer finding.
- Chạy thêm một phần tử; mô tả contract cho count 0 trước khi thử.
- Giải thích tại sao tăng capacity không phải cách sửa biên duyệt.
- Chứng minh mọi lần truy cập có `0 <= index < count <= capacity`.
- Giữ ca bắt lỗi trong verifier; không chỉ nhìn output bằng mắt.

## Hints

1. Liệt kê index thật sự được thân loop sử dụng.
2. Count là số lượng hay index cuối?
3. Mảng C có tự từ chối index sai không?

## Checklist điều tra

- [ ] Input và compiler được ghi lại.
- [ ] Phân biệt count với capacity.
- [ ] Tìm lần đọc sai đầu tiên, không suy luận từ tổng sau UB.
- [ ] Chạy lại output test và sanitizer sau sửa.

Ôn [mảng](../11-mang-mot-chieu.md), [debug](../14-debug-va-kiem-thu-chuong-trinh-c.md). Nộp evidence trước/sau cùng giải thích state và cost.
