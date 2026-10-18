# Con trỏ với mảng và chuỗi

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Mảng chứa các phần tử; con trỏ có thể chỉ tới phần tử nhưng không tự mang chiều dài mảng.
- Dùng pointer + count để hàm xử lý dãy, hoặc mượn vị trí trong chuỗi.
- Đi ra ngoài biên hoặc coi sizeof(pointer) là kích thước mảng làm contract sai.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- giải thích khi nào tên mảng được chuyển thành pointer tới phần tử đầu;
- duyệt mảng bằng chỉ số hoặc pointer mà không vượt giới hạn;
- hiểu quan hệ giữa `values[index]` và `*(values + index)`;
- xử lý chuỗi C qua `const char *` và ký tự kết thúc `'\0'`;
- phân biệt mảng ký tự có thể sửa với string literal không được sửa.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mảng giống dãy ô đánh số. Con trỏ là ngón tay chỉ một ô; nó không biết dãy dài bao nhiêu. Muốn nhờ hàm cộng dãy, bạn cần đưa cả vị trí ô đầu và số ô được phép đọc.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| count | số phần tử hợp lệ cho thao tác | 4 phần tử quantities |
| pointer arithmetic | dịch vị trí theo đơn vị phần tử cùng mảng | values + i |
| one-past | vị trí ngay sau phần tử cuối, không được đọc | values + count |
| borrowed pointer | con trỏ mượn dữ liệu do nơi khác giữ sống | suffix nằm trong chuỗi ban đầu |
| sizeof | số byte của kiểu/object ở biểu thức đang xét | mảng thật khác tham số pointer |

### Ví dụ nhỏ — tính tay trước

Với [2, 5, 1], p trỏ ô 0: *p = 2, *(p + 1) = 5. Tổng chạy là 0 → 2 → 7 → 8. p + 3 chỉ là mốc kết thúc, không có phần tử thứ tư để đọc.

Hệ thống kho cần:

1. tính tổng các số lượng trong một mảng;
2. tìm vị trí ký tự `'-'` trong mã sản phẩm như `"BOOK-2026"`.

Hàm không biết kích thước mảng chỉ từ một pointer. Vì vậy, contract phải truyền cả pointer tới phần tử đầu và giới hạn cần duyệt.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. main giữ mảng [4, 7, 3, 6]; sum nhận địa chỉ ô đầu và count = 4.
2. Vòng lặp duyệt i = 0..3, kiểm tra cộng không tràn, total đổi 0 → 4 → 11 → 14 → 20.
3. Hàm tìm ký tự duyệt BOOK-2026 tới dấu - ở chỉ số 4 rồi trả địa chỉ bên trong chuỗi.
4. Không có bản sao suffix hay cấp phát mới. Cộng/tìm tuyến tính theo số phần tử được duyệt; state phụ là biến chạy và tổng, kích thước cố định.

### Mini-check

Nếu count = 0, cần đọc values[0] không? Vì sao contract có thể cho phép values = NULL trong ca này?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Mảng thật | chứa liên tiếp các phần tử | sizeof biết tổng byte tại nơi còn kiểu mảng; không thay bằng pointer để suy chiều dài |
| Pointer + count | địa chỉ và giới hạn do caller cung cấp | không copy dãy; caller phải cung cấp biên đúng |
| Chuỗi C | dãy char kết thúc bằng byte 0 | tìm kết thúc phải duyệt; không dùng với buffer chưa có terminator |

### Misconception check

**Đúng hay sai?** Tham số int values[] giữ toàn bộ kích thước mảng caller.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: trong tham số hàm nó được điều chỉnh thành pointer.

</details>

**Đúng hay sai?** Có thể tạo và dereference pointer one-past.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Chỉ tạo mốc/so sánh trong điều kiện chuẩn cho phép; không được dereference.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** duyệt bằng chỉ số đúng biên.

- **Working Developer — dùng khi làm việc:** truyền count và ghi rõ borrow.

- **Deep Dive — có thể quay lại sau:** điều kiện hợp lệ của phép trừ/so sánh pointer.

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

## 7. Khi nào KHÔNG dùng

Không dùng strlen để đo buffer nhị phân có byte 0 bên trong. Không bỏ count rồi đoán biên bằng sizeof ở callee; giữ chiều dài tường minh đơn giản hơn tìm lỗi vượt mảng.

## 8. Production notes & scale check

Với bốn số, một vòng lặp là đủ. Với hàng triệu số, vẫn đo số lượt duyệt và kiểm tra tràn; chưa cần cấu trúc phức tạp. Kết quả tìm là mượn: không free, không giữ lâu hơn chuỗi nguồn. Test count 0, không tìm thấy, phần tử cuối và phép cộng sát INT_MAX.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Đưa hàm tổng Module 01 sang API dùng pointer + count: ai đảm bảo count không lớn hơn mảng thật? Viết tiền điều kiện, test biên và giải thích vì sao callee không thể tự phát hiện mọi caller nói sai.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Tại sao p + 1 không nhất thiết tăng địa chỉ một byte?
2. Vẽ suffix và chuỗi nguồn mà không nhân đôi dữ liệu.
3. Phân biệt tạo mốc kết thúc với đọc mốc đó.

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi biết tên mảng thường chuyển thành pointer tới phần tử đầu.
- [ ] Tôi luôn truyền số phần tử cùng pointer mảng.
- [ ] Tôi giải thích được `values[index]` và `*(values + index)`.
- [ ] Tôi không dereference one-past-the-end pointer.
- [ ] Tôi phân biệt mảng ký tự có thể sửa với string literal.

**Bài prerequisite:** [Con trỏ và biến](./02-con-tro-va-bien.md)

**Bài tiếp theo:** [Con trỏ cấp hai](./04-con-tro-cap-hai.md)
