# Failure Lab — Alias còn trỏ vào vùng đã giải phóng

Cụm 06–10. Làm trong thư mục tạm riêng; code sau cố ý có lỗi. Không chạy trên file dữ liệu thật.

## Bối cảnh

Code giải phóng owner, đặt owner về NULL rồi nghĩ rằng alias cũng an toàn.

## Code lỗi

Lưu thành `bug.c`:

```c
#include <stdio.h>
#include <stdlib.h>
int main(void)
{
    int *owner = malloc(sizeof *owner);
    if (owner == NULL) return 2;
    *owner = 42;
    int *alias = owner;
    free(owner);
    owner = NULL;
    if (alias != NULL) printf("Gia tri: %d\n", *alias);
    return 0;
}
```

## Triệu chứng

AddressSanitizer báo heap-use-after-free tại lần đọc *alias. Không đặt expected output của bản không sanitizer vì thao tác đã là UB.

## Cách tái hiện

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -O0 -g -fsanitize=address -fno-omit-frame-pointer bug.c -o bug
./bug
```

Lab lỗi cố ý bỏ `-Werror` để compiler có thể cảnh báo use-after-free mà vẫn tạo executable cho AddressSanitizer. Giữ nguyên warning làm bằng chứng; bản sửa phải build lại với `-Werror`.

Ghi compiler, lệnh, exit status, stdout/stderr. Chạy bản lỗi trước khi sửa để chứng minh regression có ý nghĩa.

## Acceptance criteria

- Không dereference sau free; owner chỉ được giải phóng một lần.
- Giữ được nghiệp vụ đọc 42 tại thời điểm hợp lệ, không chỉ xóa hết chức năng.
- Báo cáo stack trace cấp phát/giải phóng/truy cập và chạy lại sanitizer.

## Hints

1. NULL check chứng minh điều gì và không chứng minh điều gì?
2. Đánh dấu thời điểm allocation kết thúc vòng đời.
3. Chọn đổi thứ tự sử dụng hay sao chép giá trị; giải thích quyền sở hữu.

## Checklist điều tra

- [ ] Vẽ object, owner/borrow và thời điểm state thay đổi.
- [ ] Chỉ đúng câu lệnh gây lỗi bằng evidence.
- [ ] Viết expected behavior trước khi sửa.
- [ ] Nộp diff nhỏ và kết quả test cả ca lỗi lẫn hợp lệ.

Quay lại [bản đồ Module 02](../index.md).
