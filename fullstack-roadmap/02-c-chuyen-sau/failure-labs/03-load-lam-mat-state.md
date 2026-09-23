# Failure Lab — Nạp file hỏng làm mất dữ liệu cũ

Cụm 11–15. Làm trong thư mục tạm riêng; code sau cố ý có lỗi. Không chạy trên file dữ liệu thật.

## Bối cảnh

Người dùng đang có quantity 7. File chứa chữ; yêu cầu nạp lỗi phải giữ state cũ nhưng hàm xóa output ngay khi bắt đầu.

## Code lỗi

Lưu thành `bug.c`:

```c
#include <stdio.h>
static int load_quantity(const char *path, int *out)
{
    *out = 0;
    FILE *file = fopen(path, "r");
    if (file == NULL) return 0;
    int value;
    int ok = fscanf(file, "%d", &value) == 1;
    if (fclose(file) != 0) ok = 0;
    if (ok) *out = value;
    return ok;
}
int main(void)
{
    FILE *file = fopen("broken.txt", "w");
    if (file == NULL) return 2;
    if (fputs("oops\n", file) == EOF) { fclose(file); return 2; }
    if (fclose(file) != 0) return 2;
    int quantity = 7;
    int ok = load_quantity("broken.txt", &quantity);
    printf("ok=%d quantity=%d\n", ok, quantity);
    remove("broken.txt");
    return 0;
}
```

## Triệu chứng

Output ok=0 quantity=0 trái yêu cầu giữ quantity=7. Parser này còn chưa từ chối tiền tố `12x` hoặc số âm.

## Cách tái hiện

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror bug.c -o bug
./bug
```

Ghi compiler, lệnh, exit status, stdout/stderr. Chạy bản lỗi trước khi sửa để chứng minh regression có ý nghĩa.

## Acceptance criteria

- File hỏng/thiếu giữ nguyên output, file hợp lệ mới commit.
- Từ chối `12x`, số âm và số vượt miền; ghi rõ contract whitespace.
- Đóng file trên mọi đường đã mở; thêm regression test trạng thái trước/sau.

## Hints

1. Tìm lần ghi output đầu tiên và lần validation cuối cùng.
2. Tách biến ứng viên khỏi state chính.
3. Dùng contract parser bài 14; không chỉ kiểm tra fscanf == 1.

## Checklist điều tra

- [ ] Vẽ object, owner/borrow và thời điểm state thay đổi.
- [ ] Chỉ đúng câu lệnh gây lỗi bằng evidence.
- [ ] Viết expected behavior trước khi sửa.
- [ ] Nộp diff nhỏ và kết quả test cả ca lỗi lẫn hợp lệ.

Quay lại [bản đồ Module 02](../index.md).
