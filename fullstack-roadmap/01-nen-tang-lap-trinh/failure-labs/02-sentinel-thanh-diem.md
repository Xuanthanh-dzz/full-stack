# Failure Lab 02 — Báo lỗi nhưng vẫn xếp loại

> Sau bài 10 · C11 · Kết hợp contract hàm, control flow và trace lời gọi.

## Bối cảnh

Hàm tính điểm báo lỗi bằng số âm. Màn hình báo cáo lại hiển thị học sinh “chưa đạt”, khiến input lỗi bị hiểu là kết quả học tập hợp lệ.

## Code lỗi

Lưu `lab.c`:

```c
#include <stdio.h>
double average(int first, int second)
{
    if (first < 0 || first > 10 || second < 0 || second > 10) {
        return -1.0;
    }
    return (first + second) / 2.0;
}
char grade(double value)
{
    if (value >= 5.0) {
        return 'P';
    }
    return 'F';
}
int main(void)
{
    double value = average(8, 11);
    printf("Grade: %c\n", grade(value));
    return 0;
}
```

## Triệu chứng

Output là `Grade: F` và status 0 dù điểm 11 ngoài miền. Hàm `average` đã phát hiện lỗi; lỗi bị mất ở ranh giới caller.

## Cách tái hiện

Trong thư mục chứa `lab.c`:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror -O0 -g lab.c -o lab
./lab
```

Đặt breakpoint trước `grade(value)` hoặc ghi trace các giá trị return bằng tay. Thay từng cặp: `(8,11)`, `(8,6)`, `(0,0)`; ghi cả stdout/stderr/status.

## Acceptance criteria

- Điểm sai không tạo grade; caller báo lỗi qua stderr và status khác 0.
- `(0,0)` vẫn là input hợp lệ, không bị nhận nhầm là failure.
- Hàm tính không tự in hoặc kết thúc chương trình; giữ khả năng tái sử dụng.
- Có test cho ca sai và hai ca hợp lệ; giải thích tại sao sửa ngưỡng grade không chữa root cause.

## Hints

1. Sentinel là dữ liệu nghiệp vụ hay tín hiệu về kết quả tính?
2. Caller đang kiểm tra gì giữa hai lời gọi?
3. Ai quyết định có được đi tiếp sang bước xếp loại?

## Checklist điều tra

- [ ] Ghi contract của cả hai hàm.
- [ ] Vẽ value trở về main trước khi gọi grade.
- [ ] Kiểm tra status ngoài output.
- [ ] Phân biệt điểm 0 hợp lệ với sentinel âm.

Nộp bug report và regression cases; ôn [hàm](../09-ham-tham-so-gia-tri-tra-ve.md) và [call stack](../10-ngan-xep-loi-goi-ham.md).
