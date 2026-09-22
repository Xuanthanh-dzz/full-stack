# Failure Lab — RAII cleanup nhưng dữ liệu đã đổi

Sau bài 14. Code cố ý lỗi, chạy trong thư mục tạm riêng.

## Bối cảnh

Output size=0 dù yêu cầu replace thất bại phải giữ old. Không leak không đồng nghĩa strong guarantee.

## Code lỗi

Lưu `bug.cpp`:

```cpp
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
static void replace(std::vector<std::string>& items) {
    items.clear();
    throw std::runtime_error{"invalid file"};
}
int main() {
    std::vector<std::string> items{"old"};
    try { replace(items); }
    catch (const std::exception&) { std::cout << "size=" << items.size() << '\n'; }
}
```

## Triệu chứng

Output size=0 dù yêu cầu replace thất bại phải giữ old. Không leak không đồng nghĩa strong guarantee.

## Cách tái hiện

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -O0 -g -fsanitize=address,undefined -fno-omit-frame-pointer bug.cpp -o bug
./bug
```

Giữ warning làm evidence. Bản lỗi bỏ Werror để chạy sanitizer; bản sửa phải build lại với `-Werror`. Ghi compiler, stdout/stderr, exit status và trace trước khi sửa.

## Acceptance criteria

- Thất bại giữ đủ state cũ, thành công thay toàn bộ state.
- Không nuốt lỗi hoặc in thành công sau rejection.
- Test ít nhất lỗi trước/sau khi tạo một phần dữ liệu mới; giải thích commit và cleanup.

## Hints

1. Tìm state mutation đầu tiên.
2. RAII của vector bảo đảm gì khi throw?
3. Đặt dữ liệu ứng viên ở đâu trước commit?

## Checklist điều tra

- [ ] Vẽ owner/borrow và state trước/sau thao tác.
- [ ] Chỉ câu lệnh đầu tiên phá contract.
- [ ] Viết expected behavior và regression trước bản sửa.
- [ ] Nộp diff nhỏ, lệnh tái hiện và bằng chứng bản sửa.

[Bản đồ module](../index.md).
