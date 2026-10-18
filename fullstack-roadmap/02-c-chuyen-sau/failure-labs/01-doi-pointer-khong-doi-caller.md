# Failure Lab — Đổi con trỏ nhưng caller không nhận kết quả

Cụm 01–05. Làm trong thư mục tạm riêng; code sau cố ý có lỗi. Không chạy trên file dữ liệu thật.

## Bối cảnh

Một hàm chọn ô lớn hơn nhận bản sao pointer kết quả. Reviewer thấy phép gán hợp lệ nhưng caller vẫn giữ ô đầu.

## Code lỗi

Lưu thành `bug.c`:

```c
#include <stdio.h>
static void select_second(const int *values, const int *selected)
{
    selected = values + 1;
    printf("Trong ham: %d\n", *selected);
}
int main(void)
{
    int values[] = {3, 9};
    const int *selected = values;
    select_second(values, selected);
    printf("Caller: %d\n", *selected);
    return 0;
}
```

## Triệu chứng

Trong hàm in 9 nhưng caller in 3. Yêu cầu là caller phải nhận địa chỉ ô chứa 9, không chỉ nhận bản sao số 9.

## Cách tái hiện

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror bug.c -o bug
./bug
```

Ghi compiler, lệnh, exit status, stdout/stderr. Chạy bản lỗi trước khi sửa để chứng minh regression có ý nghĩa.

## Acceptance criteria

- Caller nhận đúng địa chỉ phần tử, không tạo bản sao hoặc dùng global.
- Quy định và test input NULL/không đủ phần tử; thất bại không đổi output.
- Giải thích vòng đời của kết quả mượn.

## Hints

1. Vẽ hai object pointer ở caller và callee.
2. Phép gán selected thay object nào?
3. So sánh trả pointer với nhận địa chỉ của pointer output.

## Checklist điều tra

- [ ] Vẽ object, owner/borrow và thời điểm state thay đổi.
- [ ] Chỉ đúng câu lệnh gây lỗi bằng evidence.
- [ ] Viết expected behavior trước khi sửa.
- [ ] Nộp diff nhỏ và kết quả test cả ca lỗi lẫn hợp lệ.

Quay lại [bản đồ Module 02](../index.md).
