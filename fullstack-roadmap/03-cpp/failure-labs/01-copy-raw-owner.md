# Failure Lab — Copy hai owner cho một allocation

Sau bài 05. Code cố ý lỗi, chạy trong thư mục tạm riêng.

## Bối cảnh

Copy mặc định chỉ sao chép địa chỉ. Khi ra scope, hai destructor giải phóng cùng allocation. ASan phải báo attempting double-free.

## Code lỗi

Lưu `bug.cpp`:

```cpp
#include <cstddef>
struct Buffer {
    int* data = new int[2]{4, 7};
    ~Buffer() { delete[] data; }
};
int main() {
    Buffer first;
    Buffer second = first;
    return second.data[0] == 4 ? 0 : 1;
}
```

## Triệu chứng

Copy mặc định chỉ sao chép địa chỉ. Khi ra scope, hai destructor giải phóng cùng allocation. ASan phải báo attempting double-free.

## Cách tái hiện

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -O0 -g -fsanitize=address,undefined -fno-omit-frame-pointer bug.cpp -o bug
./bug
```

Giữ warning làm evidence. Bản lỗi bỏ Werror để chạy sanitizer; bản sửa phải build lại với `-Werror`. Ghi compiler, stdout/stderr, exit status và trace trước khi sửa.

## Acceptance criteria

- Copy phải có semantics được công bố: độc lập hoặc bị cấm tại compile-time.
- Giữ nghiệp vụ lưu/đọc hai số; không sửa bằng bỏ destructor để leak.
- Test copy/move/cleanup và giải thích lựa chọn Rule of Zero.

## Hints

1. Vẽ hai object và số allocation thật.
2. Destructor mỗi object nghĩ mình có quyền gì?
3. So sánh member tự quản lý, deep copy và cấm copy.

## Checklist điều tra

- [ ] Vẽ owner/borrow và state trước/sau thao tác.
- [ ] Chỉ câu lệnh đầu tiên phá contract.
- [ ] Viết expected behavior và regression trước bản sửa.
- [ ] Nộp diff nhỏ, lệnh tái hiện và bằng chứng bản sửa.

[Bản đồ module](../index.md).
