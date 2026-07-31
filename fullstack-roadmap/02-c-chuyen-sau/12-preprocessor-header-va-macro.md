# Preprocessor, header và macro

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- giải thích preprocessor xử lý directive trước compiler;
- tạo header có include guard;
- dùng `#include`, `#define`, `#if` và `-D` ở mức an toàn;
- viết macro có ngoặc đầy đủ và nhận ra nguy cơ đánh giá đối số nhiều lần;
- ưu tiên `static inline` cho logic có kiểu khi phù hợp;
- hiểu header được include vào một translation unit, chưa phải một module được link riêng.

## 2. Bài toán mở đầu

Capacity tối đa và hàm chuẩn hóa số lượng đang bị lặp trong source code. Ta muốn:

- đặt contract dùng chung trong `inventory_limits.h`;
- tránh lỗi include header hai lần;
- tính số phần tử của một mảng thật;
- bật trace khi build debug mà không sửa source.

Bài này vẫn chỉ biên dịch một file `.c`. Bài sau mới tách nhiều translation unit và link chúng.

## 3. Lời giải bằng code

Tạo `inventory_limits.h`:

```c
#ifndef INVENTORY_LIMITS_H
#define INVENTORY_LIMITS_H

#include <stddef.h>

#define INVENTORY_CAPACITY 4U
#define ARRAY_COUNT(array) (sizeof(array) / sizeof((array)[0]))

#ifndef TRACE_ENABLED
#define TRACE_ENABLED 0
#endif

#if TRACE_ENABLED
#include <stdio.h>
#define TRACE(message) fprintf(stderr, "TRACE: %s\n", (message))
#else
#define TRACE(message) ((void)0)
#endif

static inline int clamp_quantity(int quantity)
{
    return quantity < 0 ? 0 : quantity;
}

#endif
```

Tạo `main.c` trong cùng thư mục:

```c
#include <stdio.h>

#include "inventory_limits.h"
/* The include guard makes this deliberate second include harmless. */
#include "inventory_limits.h"

_Static_assert(INVENTORY_CAPACITY == 4U, "Capacity demo must be 4");

int main(void)
{
    int quantities[INVENTORY_CAPACITY] = {-3, 3, 7, -1};

    TRACE("Bat dau chuan hoa");

    for (size_t index = 0; index < ARRAY_COUNT(quantities); ++index) {
        quantities[index] = clamp_quantity(quantities[index]);
    }

    printf("So phan tu: %zu\n", ARRAY_COUNT(quantities));
    printf(
        "So luong: %d %d %d %d\n",
        quantities[0],
        quantities[1],
        quantities[2],
        quantities[3]
    );
    return 0;
}
```

Header được include hai lần có chủ đích để chứng minh include guard ngăn định nghĩa lặp.

Build mặc định:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o preprocessor-demo
./preprocessor-demo
```

Output trên standard output:

```text
So phan tu: 4
So luong: 0 3 7 0
```

Build bật trace bằng định nghĩa từ command line:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror \
  -DTRACE_ENABLED=1 main.c -o preprocessor-trace
./preprocessor-trace
```

Khi đó standard error có thêm:

```text
TRACE: Bat dau chuan hoa
```

Standard output vẫn giữ hai dòng như trên.

## 4. Giải thích cơ chế

### Preprocessor chạy trước compiler

Pipeline rút gọn:

```text
main.c
  │
  ├─ preprocessor: #include, #define, #if
  ▼
translation unit sau tiền xử lý
  │
  ├─ compiler kiểm tra cú pháp/kiểu và sinh code
  ▼
object code
```

`#include "inventory_limits.h"` về bản chất yêu cầu preprocessor chèn nội dung header tại vị trí directive. Nó không gọi runtime và không tạo allocation.

### Include guard

Lần include đầu:

1. `INVENTORY_LIMITS_H` chưa được định nghĩa;
2. nội dung giữa `#define` và `#endif` được giữ;
3. macro guard được định nghĩa.

Lần include thứ hai, điều kiện `#ifndef` sai nên toàn bộ thân bị bỏ qua. Nhờ đó `static inline` và các khai báo không xuất hiện lặp trong cùng translation unit.

Tên guard nên duy nhất và gắn với project/header.

### Object-like macro

```c
#define INVENTORY_CAPACITY 4U
```

thay token `INVENTORY_CAPACITY` bằng `4U` trước compile. Macro không có kiểu riêng; suffix `U` làm literal có kiểu unsigned phù hợp với ý nghĩa capacity.

### Function-like macro

```c
#define ARRAY_COUNT(array) (sizeof(array) / sizeof((array)[0]))
```

Ngoặc bảo vệ biểu thức khi được chèn vào ngữ cảnh khác. Macro chỉ đúng khi đối số là một object mảng tại nơi gọi. Nếu đối số đã là pointer, kết quả là tỉ lệ kích thước pointer/phần tử, không phải số phần tử.

Với mảng fixed-size `quantities` của sample, hai toán hạng `sizeof` không đánh giá lại mảng, nên đối số không chạy hai lần. Không suy rộng điều đó cho VLA (mảng có kích thước runtime) hoặc expression có side effect: nếu chưa phân tích contract cụ thể, không truyền chúng vào macro này.

### `static inline`

`clamp_quantity` dùng function có kiểu:

- compiler kiểm tra đối số/giá trị trả về;
- đối số được đánh giá đúng một lần;
- debugger và tooling hiểu như hàm;
- `static` cho mỗi translation unit một định nghĩa nội bộ hợp lệ.

`inline` cho phép compiler cân nhắc chèn thân hàm tại call site, nhưng không bắt buộc. Lợi ích chính ở đây là contract có kiểu, không phải lời hứa về hiệu năng.

### Conditional compilation

`-DTRACE_ENABLED=1` tương đương định nghĩa macro trước source. `#if TRACE_ENABLED` chọn một trong hai định nghĩa `TRACE`.

Khi tắt, `((void)0)` tạo một statement không làm gì và không đánh giá `message`. Không đặt side effect bắt buộc bên trong đối số trace vì nó sẽ biến mất ở build không trace.

## 5. Kiến thức nền

### `#include "..."` và `<...>`

- `"project_header.h"`: tìm theo quy tắc dành cho project/local header trước;
- `<stdio.h>`: tìm trong include path của implementation/toolchain.

Không dựa vào include bắc cầu. Header dùng `size_t` nên tự include `<stddef.h>`.

### Header nên chứa gì

Thường chứa:

- type dùng trong public contract;
- function declaration;
- hằng số compile-time cần chia sẻ;
- `static inline` nhỏ khi có lý do.

Tránh định nghĩa object global có external linkage trong header; mỗi translation unit include sẽ tạo định nghĩa trùng. Bài sau giải thích declaration/definition và linker.

### `_Static_assert`

`_Static_assert(condition, message)` kiểm tra điều kiện constant lúc compile. Nếu sai, build thất bại. Nó không tạo nhánh runtime.

### Macro nhiều statement

Khi buộc phải có macro nhiều statement, pattern phổ biến là:

```c
#define DO_BOTH(first, second) \
    do {                       \
        first;                 \
        second;                \
    } while (0)
```

Pattern giúp macro hành xử như một statement trong `if/else`. Tuy vậy, function thường an toàn và dễ debug hơn.

### Đào sâu (có thể quay lại sau)

Macro expansion làm việc trên token, không hiểu scope/type như compiler. Các toán tử `#` và `##` có thể stringify hoặc ghép token nhưng dễ tạo API khó đọc; chỉ dùng khi lợi ích build-time rõ ràng.

`#pragma once` được nhiều compiler hỗ trợ nhưng không nằm trong C11. Include guard chuẩn C vẫn là lựa chọn portable.

Các directive điều kiện quá dày tạo nhiều biến thể chương trình khó test. Mỗi tổ hợp macro quan trọng phải được build/test trong CI.

## 6. Lỗi thường gặp

### Macro thiếu ngoặc

Sai:

```c
#define DOUBLE(value) value + value
```

`2 * DOUBLE(3)` mở rộng thành `2 * 3 + 3`. Nếu vẫn dùng macro biểu thức, bọc từng đối số và toàn biểu thức.

### Đối số có side effect bị đánh giá hai lần

```c
#define SQUARE(value) ((value) * (value))
```

`SQUARE(index++)` tăng hai lần và còn có thể gây undefined behavior do thứ tự đánh giá. Không truyền side effect vào macro; ưu tiên function `static inline`.

### Dùng `ARRAY_COUNT` với pointer

Macro không thể tự phân biệt portable ở C11. Chỉ gọi ở scope còn biết object là mảng; truyền count vào hàm cùng pointer.

### Header phụ thuộc include order

Header phải include các standard header cần cho chính declaration của nó. Không ép caller include `<stddef.h>` trước.

### Side effect trong trace

`TRACE(save_data())` có thể chạy ở debug nhưng biến mất ở release. Tách side effect khỏi logging.

## 7. Bài tập

### Bài 1 — Header giới hạn

Tạo header chứa `MIN_QUANTITY`, `MAX_QUANTITY` và hàm `static inline` validate range.

**Gợi ý:** header tự include type cần thiết và có guard duy nhất.

### Bài 2 — Macro `MIN`

Viết macro có ngoặc rồi liệt kê lý do vẫn không gọi nó với `index++`.

**Gợi ý:** macro có thể đánh giá đối số nhiều hơn một lần.

### Bài 3 — Hai build mode

Thêm `DEBUG_VALIDATION`; build cả `0` và `1`, ghi output tương ứng.

**Gợi ý:** mọi tổ hợp cần compile sạch với warnings-as-errors.

### Bài 4 — Xem output preprocessor

Chạy `cc -E main.c` và tìm phần source đến từ header.

**Gợi ý:** output rất dài vì standard header; tìm tên `clamp_quantity`.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi biết `#include` là chèn source ở bước tiền xử lý.
- [ ] Tôi tạo header có include guard và tự đủ dependency.
- [ ] Tôi không đặt side effect vào macro có thể bỏ qua/lặp lại.
- [ ] Tôi chỉ dùng `ARRAY_COUNT` với mảng thật.
- [ ] Tôi ưu tiên `static inline` cho logic có kiểu.

**Bài prerequisite:** [File I/O](./11-file-io.md)

**Bài tiếp theo:** [Quá trình biên dịch, linking và Makefile](./13-qua-trinh-bien-dich-linking-makefile.md)
