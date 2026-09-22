# Failure Lab 01 — Tỷ lệ giảm giá bằng 0

> Sau bài 05 · C11 · Kết hợp contract bài 01, type bài 03 và operator bài 05.

## Bối cảnh

Một quầy nhỏ cần báo tỷ lệ đã bán. Với tồn đầu 4, đã bán 1, báo cáo phải ghi 25.0%. Đây là bản rút gọn từ lỗi báo cáo; chưa có input bàn phím.

## Code lỗi

Lưu thành `lab.c` trong thư mục tạm riêng:

```c
#include <stdio.h>
int main(void)
{
    const int opening = 4;
    const int sold = 1;
    double percent = sold / opening * 100.0;
    printf("Sold: %.1f%%\n", percent);
    return 0;
}
```

## Triệu chứng

Build không warning, exit status 0, nhưng stdout là `Sold: 0.0%`. Khách hàng không chấp nhận việc sửa riêng chuỗi output thành 25.0 vì số liệu sẽ thay đổi.

## Cách tái hiện

Trong thư mục chứa `lab.c`:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror lab.c -o lab
./lab
```

Tính tay trước với `(opening,sold)=(4,1)`, `(3,2)`, `(4,4)`. Ghi type và giá trị của từng biểu thức trung gian, rồi đối chiếu stdout. Chưa chạy ca mẫu số 0; bài 07 mới cung cấp guard cho ca đó.

## Acceptance criteria

- Sửa phép tính cho cả ba cặp; không hard-code kết quả.
- Giữ số hộp là số nguyên, giải thích chỗ chuyển type.
- Chứng minh sửa lỗi bằng output và exit status; compile pass riêng chưa đủ.
- Viết thêm một ca trước đây fail, giữ làm regression case.
- Ghi rõ contract chưa nhận tồn đầu 0; nêu kiểm tra cần thêm sau bài 07.

## Hints

1. `sold / opening` được tính theo type nào?
2. Biến nhận kết quả là `double` có thay đổi phép chia đã chạy không?
3. Chuyển một toán hạng trước phép chia khác chuyển kết quả ở điểm nào?

## Checklist điều tra

- [ ] Kỳ vọng được tính độc lập từ yêu cầu.
- [ ] Đã ghi giá trị trước và sau mỗi phép toán.
- [ ] Đã thử ca có phần lẻ, không chỉ ca chia hết.
- [ ] Đã ghi compiler và lệnh tái hiện.

Nộp giả thuyết → evidence → nguyên nhân → thay đổi nhỏ nhất → ca regression. Ôn [type](../03-bien-hang-so-kieu-du-lieu.md) và [operator](../05-toan-tu-va-bieu-thuc.md).
