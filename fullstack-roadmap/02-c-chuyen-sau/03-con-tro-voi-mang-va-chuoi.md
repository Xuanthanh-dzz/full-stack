# Con trỏ với mảng và chuỗi

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- giải thích khi nào tên mảng được chuyển thành pointer tới phần tử đầu;
- duyệt mảng bằng chỉ số hoặc pointer mà không vượt giới hạn;
- hiểu quan hệ giữa `values[index]` và `*(values + index)`;
- xử lý chuỗi C qua `const char *` và ký tự kết thúc `'\0'`;
- phân biệt mảng ký tự có thể sửa với string literal không được sửa.

## 2. Bài toán mở đầu

Hệ thống kho cần:

1. tính tổng các số lượng trong một mảng;
2. tìm vị trí ký tự `'-'` trong mã sản phẩm như `"BOOK-2026"`.

Hàm không biết kích thước mảng chỉ từ một pointer. Vì vậy, contract phải truyền cả pointer tới phần tử đầu và giới hạn cần duyệt.

## 3. Lời giải bằng code

Tạo `main.c`:

```c
#include <limits.h>
#include <stddef.h>
#include <stdio.h>

static int sum_quantities(
    const int *values,
    size_t count,
    int *result
)
{
    if (result == NULL || (values == NULL && count > 0)) {
        return 0;
    }

    int total = 0;

    /* The pointer does not carry a length; count is part of the contract. */
    for (size_t index = 0; index < count; ++index) {
        if (values[index] < 0 || total > INT_MAX - values[index]) {
            return 0;
        }
        total += values[index];
    }

    *result = total;
    return 1;
}

static const char *find_character(const char *text, char target)
{
    if (text == NULL) {
        return NULL;
    }

    while (*text != '\0') {
        if (*text == target) {
            return text;
        }
        ++text;
    }

    return NULL;
}

int main(void)
{
    int quantities[] = {4, 7, 3, 6};
    size_t quantity_count = sizeof quantities / sizeof quantities[0];
    const char product_code[] = "BOOK-2026";
    int total = 0;

    if (!sum_quantities(quantities, quantity_count, &total)) {
        fprintf(stderr, "Khong tinh duoc tong\n");
        return 1;
    }
    printf("Tong so luong: %d\n", total);

    const char *separator = find_character(product_code, '-');
    if (separator != NULL) {
        size_t position = (size_t)(separator - product_code);
        printf("Dau '-' o vi tri: %zu\n", position);
        printf("Phan sau dau '-': %s\n", separator + 1);
    }

    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o pointer-array
./pointer-array
```

Output:

```text
Tong so luong: 20
Dau '-' o vi tri: 4
Phan sau dau '-': 2026
```

## 4. Giải thích cơ chế

### Mảng là một object gồm các phần tử liên tiếp

Khai báo:

```c
int quantities[] = {4, 7, 3, 6};
```

tạo một object mảng gồm bốn object `int` liên tiếp:

```text
quantities

phần tử       [0]       [1]       [2]       [3]
giá trị        4         7         3         6
địa chỉ        A       A+1       A+2       A+3
             ┌─────┬─────────┬─────────┬─────────┐
             │  4  │    7    │    3    │    6    │
             └─────┴─────────┴─────────┴─────────┘
```

`A+1` trong sơ đồ nghĩa là địa chỉ phần tử kế tiếp, không nhất thiết tăng đúng một byte. Pointer arithmetic tự tăng theo `sizeof(int)`.

Trong hầu hết biểu thức, tên mảng `quantities` được chuyển thành `&quantities[0]`, có kiểu `int *`.

### Hàm nhận pointer và số phần tử

Khai báo:

```c
static int sum_quantities(
    const int *values,
    size_t count,
    int *result
);
```

nhận:

- `values`: địa chỉ phần tử đầu;
- `count`: số phần tử được phép đọc.
- `result`: object của bên gọi nhận tổng khi hàm thành công.

Trong hàm không còn thông tin để dùng `sizeof values` tính số phần tử: `values` chỉ là một pointer. `count` là một phần bắt buộc của contract. Hàm còn từ chối quantity âm và kiểm tra `total > INT_MAX - values[index]` trước phép cộng để không signed overflow.

### Chỉ số là phép toán pointer

Với pointer `values`:

```c
values[index]
```

tương đương:

```c
*(values + index)
```

Compiler tính địa chỉ phần tử thứ `index`, rồi dereference. Điều kiện an toàn trong vòng lặp là `index < count`.

### Chuỗi C và con trỏ đang di chuyển

`product_code` là mảng:

```text
B  O  O  K  -  2  0  2  6  \0
^
text
```

Trong `find_character`, tham số `text` là bản sao pointer. `++text` làm bản sao này trỏ sang ký tự kế, không đổi mảng và không đổi pointer nào ở `main`.

Khi tìm thấy `'-'`, hàm trả địa chỉ của ký tự nằm **bên trong** mảng `product_code`:

```text
product_code ──► 'B'
separator    ──────────────► '-'
```

Pointer `separator` không sở hữu một chuỗi mới. Nó chỉ mượn địa chỉ trong mảng còn sống ở `main`.

### Hiệu hai pointer trong cùng mảng

```c
separator - product_code
```

cho số phần tử giữa hai pointer khi cả hai trỏ vào cùng mảng. Kết quả bằng `4`. Không trừ hai pointer thuộc hai object mảng khác nhau.

## 5. Kiến thức nền

### `size_t`

`size_t` là kiểu số nguyên không âm dùng cho kích thước và chỉ số object. Header `<stddef.h>` định nghĩa kiểu này; `%zu` là format đúng của `printf`.

### Những trường hợp tên mảng không chuyển thành pointer

Hai trường hợp quan trọng:

```c
sizeof quantities
&quantities
```

- `sizeof quantities` là tổng số byte của cả mảng.
- `&quantities` là pointer tới **toàn bộ mảng**, không phải pointer tới một `int`.

Vì vậy phép tính số phần tử phải đặt nơi `quantities` vẫn là mảng:

```c
sizeof quantities / sizeof quantities[0]
```

### One-past-the-end pointer

C cho phép tạo pointer ngay sau phần tử cuối để làm mốc kết thúc:

```c
const int *end = quantities + quantity_count;
```

Có thể so sánh hoặc dùng nó để dừng vòng lặp, nhưng không được dereference `*end`.

### Mảng ký tự và string literal

Mảng có thể sửa:

```c
char editable[] = "ABC";
editable[0] = 'X';
```

Pointer tới string literal nên là chỉ-đọc:

```c
const char *label = "ABC";
```

Không ghi qua `label`. String literal không phải vùng lưu trữ cho phép chương trình sửa.

### `const` lan truyền contract

`find_character` không sửa chuỗi, nên nhận và trả `const char *`. Pointer trả về trỏ vào chính vùng dữ liệu chỉ đọc theo contract; bên gọi không nên cast bỏ `const`.

## 6. Lỗi thường gặp

### Dùng `sizeof` trên tham số pointer

Sai:

```c
static size_t count_items(const int values[])
{
    return sizeof values / sizeof values[0];
}
```

Trong tham số hàm, `const int values[]` được điều chỉnh thành pointer. Truyền `count` riêng.

### Lỗi lệch một đơn vị

Sai:

```c
for (size_t index = 0; index <= count; ++index)
```

Khi `index == count`, pointer nằm sau cuối mảng và không được dereference. Dùng `index < count`.

### Trả pointer vào mảng đã hết lifetime

Không tạo mảng cục bộ trong hàm rồi trả địa chỉ phần tử của nó. Khi hàm kết thúc, mảng không còn sống. Trong ví dụ chính, mảng thuộc `main`, nên còn sống sau khi `find_character` trả về.

### Sửa string literal

Đoạn sau có undefined behavior và **không được chạy**:

```c
char *text = "ABC";
text[0] = 'X';
```

Dùng `char text[] = "ABC"` nếu cần vùng nhớ có thể sửa.

### Quên ký tự `'\0'`

Vòng lặp chuỗi dựa vào `'\0'`. Nếu buffer không có terminator trong phạm vi hợp lệ, vòng lặp sẽ đọc vượt giới hạn. Khi tự xây chuỗi, luôn dành một phần tử cho `'\0'`.

## 7. Bài tập

### Bài 1 — Tìm giá trị lớn nhất

Viết hàm nhận `const int *values`, `size_t count` và trả giá trị lớn nhất qua output parameter.

**Gợi ý:** từ chối `NULL` và `count == 0`.

### Bài 2 — Đếm ký tự

Viết hàm đếm số lần một ký tự xuất hiện trong chuỗi.

**Gợi ý:** dừng trước `'\0'`; không cần gọi `strlen` trong mỗi vòng lặp.

### Bài 3 — Duyệt bằng cặp pointer

Viết lại hàm tính tổng với `current` và `end` thay vì chỉ số.

**Gợi ý:** điều kiện là `current != end`; `end` không được dereference.

### Bài 4 — Tách tiền tố mã

Với `"BOOK-2026"`, in các ký tự trước `'-'` mà không sửa chuỗi nguồn.

**Gợi ý:** dùng pointer bắt đầu và pointer kết thúc; in từng ký tự trong khoảng nửa mở `[begin, end)`.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi biết tên mảng thường chuyển thành pointer tới phần tử đầu.
- [ ] Tôi luôn truyền số phần tử cùng pointer mảng.
- [ ] Tôi giải thích được `values[index]` và `*(values + index)`.
- [ ] Tôi không dereference one-past-the-end pointer.
- [ ] Tôi phân biệt mảng ký tự có thể sửa với string literal.

**Bài prerequisite:** [Con trỏ và biến](./02-con-tro-va-bien.md)

**Bài tiếp theo:** [Con trỏ cấp hai](./04-con-tro-cap-hai.md)
