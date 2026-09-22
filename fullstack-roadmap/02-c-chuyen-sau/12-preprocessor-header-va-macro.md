# Preprocessor, header và macro

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Preprocessor xử lý chỉ thị trước compiler; header chia sẻ khai báo, macro thay token.
- Dùng header guard, hằng cấu hình và hàm nhỏ đúng kiểu để chia sẻ code.
- Macro không hiểu kiểu như hàm và có thể đánh giá đối số nhiều lần; ARRAY_COUNT chỉ dùng với mảng thật.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- giải thích preprocessor xử lý directive trước compiler;
- tạo header có include guard;
- dùng `#include`, `#define`, `#if` và `-D` ở mức an toàn;
- viết macro có ngoặc đầy đủ và nhận ra nguy cơ đánh giá đối số nhiều lần;
- ưu tiên `static inline` cho logic có kiểu khi phù hợp;
- hiểu header được include vào một translation unit, chưa phải một module được link riêng.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Trước khi dịch, có một bước chuẩn bị văn bản: chèn nội dung header, bật/tắt khối code, thay tên macro. Đây không phải một hàm chạy lúc chương trình đang xử lý dữ liệu. Phân biệt hai thời điểm giúp hiểu vì sao đổi -D phải build lại.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| preprocessor | bước xử lý chỉ thị và token trước biên dịch | include, define, if |
| header guard | chốt tránh nội dung header bị chèn lặp trong một đơn vị dịch | ifndef/define/endif |
| macro | quy tắc thay token | ARRAY_COUNT |
| static inline | hàm có kiểu, định nghĩa dùng nội bộ đơn vị dịch | clamp_non_negative; không hứa compiler inline |
| stderr | luồng báo chẩn đoán riêng stdout | TRACE |

### Ví dụ nhỏ — tính tay trước

Đối số i++ truyền vào hàm được đánh giá một lần trước lời gọi; macro viết đối số hai chỗ có thể đánh giá hai lần. Với i = 2, đừng suy macro có cùng hành vi hàm chỉ vì tên trông giống lời gọi.

Capacity tối đa và hàm chuẩn hóa số lượng đang bị lặp trong source code. Ta muốn:

- đặt contract dùng chung trong `inventory_limits.h`;
- tránh lỗi include header hai lần;
- tính số phần tử của một mảng thật;
- bật trace khi build debug mà không sửa source.

Bài này vẫn chỉ biên dịch một file `.c`. Bài sau mới tách nhiều translation unit và link chúng.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Preprocessor chèn inventory_limits.h và chọn nhánh TRACE_ENABLED khi build, chưa có dữ liệu runtime.
2. main giữ mảng [-3, 3, 7, -1]; ARRAY_COUNT tính số phần tử tại nơi còn kiểu mảng.
3. clamp_non_negative lần lượt cho [0, 3, 7, 0]; mỗi lần là một hàm có kiểm tra kiểu.
4. Bản build TRACE_ENABLED=1 thêm một dòng stderr, stdout giữ nguyên. Runtime duyệt n phần tử, state mảng O(n); macro không tạo vùng nhớ tự thân.

### Mini-check

Đổi TRACE_ENABLED khi chương trình đã chạy có tác dụng không? Cần làm bước nào để nhánh mới tồn tại trong executable?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Macro | thay token trước compile | cần cho điều kiện compile; không dùng thay hàm chỉ để tối ưu tưởng tượng |
| static inline function | hàm có kiểm tra kiểu/đối số | phù hợp phép biến đổi nhỏ; inline không bắt buộc bỏ lời gọi |
| const object | giá trị có kiểu và storage theo khai báo | dễ debug; không thay mọi nhu cầu #if trong C |

### Misconception check

**Đúng hay sai?** Header guard ngăn mọi lỗi nhiều định nghĩa giữa các file .c.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ ngăn include lặp trong một đơn vị dịch; linkage vẫn cần thiết kế đúng.

</details>

**Đúng hay sai?** Từ khóa inline bảo đảm machine code không còn lời gọi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: đó không phải cam kết tối ưu của compiler.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** theo dõi include và cấu hình build.

- **Working Developer — dùng khi làm việc:** ưu tiên hàm có kiểu, kiểm tra stdout/stderr.

- **Deep Dive — có thể quay lại sau:** xem output tiền xử lý khi macro khó debug.

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

## 7. Khi nào KHÔNG dùng

Không dùng macro function cho phép tính thông thường khi static inline rõ kiểu và ít rủi ro hơn. Không gọi ARRAY_COUNT trên pointer trong callee. Không bật trace ghi dữ liệu nhạy cảm chỉ vì là debug build.

## 8. Production notes & scale check

Demo có một header và một source; hai cấu hình trace đều phải build/test. Giữ output nghiệp vụ ở stdout để script tiêu thụ ổn định, log ở stderr. Đừng tăng hệ cấu hình phức tạp cho một cờ; driver là có hai build mode thực sự cần kiểm tra.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Module 01 kiểm tra expected output bằng script. Nếu bật trace, làm sao giữ assertion nghiệp vụ ổn định mà vẫn lưu log? Nêu luồng output và hai lệnh build cần có trong CI.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Macro được xử lý lúc nào so với main?
2. Header guard giải quyết phạm vi trùng nào?
3. Vì sao ARRAY_COUNT đổi ý nghĩa khi nhận pointer?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi biết `#include` là chèn source ở bước tiền xử lý.
- [ ] Tôi tạo header có include guard và tự đủ dependency.
- [ ] Tôi không đặt side effect vào macro có thể bỏ qua/lặp lại.
- [ ] Tôi chỉ dùng `ARRAY_COUNT` với mảng thật.
- [ ] Tôi ưu tiên `static inline` cho logic có kiểu.

**Bài prerequisite:** [File I/O](./11-file-io.md)

**Bài tiếp theo:** [Quá trình biên dịch, linking và Makefile](./13-qua-trinh-bien-dich-linking-makefile.md)
