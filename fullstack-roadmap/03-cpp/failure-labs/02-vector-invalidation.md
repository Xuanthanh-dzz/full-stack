# Failure Lab — Reference qua lần vector tăng capacity

Sau bài 10. Code cố ý lỗi, chạy trong thư mục tạm riêng.

## Bối cảnh

reserve lớn hơn capacity hiện tại buộc reallocation; first trở thành dangling. ASan phải báo heap-use-after-free, không dự đoán output số.

## Code lỗi

Lưu `bug.cpp`:

```cpp
#include <iostream>
#include <vector>
int main() {
    std::vector<int> values{7};
    const int& first = values.front();
    values.reserve(values.capacity() + 1);
    std::cout << first << '\n';
}
```

## Triệu chứng

reserve lớn hơn capacity hiện tại buộc reallocation; first trở thành dangling. ASan phải báo heap-use-after-free, không dự đoán output số.

## Cách tái hiện

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -O0 -g -fsanitize=address,undefined -fno-omit-frame-pointer bug.cpp -o bug
./bug
```

Giữ warning làm evidence. Bản lỗi bỏ Werror để chạy sanitizer; bản sửa phải build lại với `-Werror`. Ghi compiler, stdout/stderr, exit status và trace trước khi sửa.

## Acceptance criteria

- Không giữ reference mất hiệu lực qua reallocation.
- Vẫn thêm được capacity và đọc đúng phần tử đầu theo requirement.
- So sánh giữ index, copy giá trị và lấy lại reference; chạy regression có reallocation thật.

## Hints

1. Capacity khác size thế nào?
2. Ai sở hữu int được first tham chiếu?
3. Nếu yêu cầu là đọc giá trị mới nhất, copy snapshot có đúng không?

## Checklist điều tra

- [ ] Vẽ owner/borrow và state trước/sau thao tác.
- [ ] Chỉ câu lệnh đầu tiên phá contract.
- [ ] Viết expected behavior và regression trước bản sửa.
- [ ] Nộp diff nhỏ, lệnh tái hiện và bằng chứng bản sửa.

[Bản đồ module](../index.md).
