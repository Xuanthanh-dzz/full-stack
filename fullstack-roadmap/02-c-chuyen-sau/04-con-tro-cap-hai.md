# Con trỏ cấp hai

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Con trỏ cấp hai cho phép hàm cập nhật một object vốn là con trỏ.
- Dùng khi cần trả vị trí được chọn hoặc thay địa chỉ mà caller giữ.
- Mỗi tầng * cần object hợp lệ; const ở các tầng không hoán đổi tùy ý.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- đọc kiểu `int **` theo từng lớp pointer;
- truyền địa chỉ của một biến pointer để hàm đổi nơi pointer của bên gọi trỏ tới;
- dùng `const int **` đúng contract trong một bài toán tìm kiếm;
- vẽ ba lớp: object dữ liệu, pointer cấp một và pointer cấp hai;
- kiểm tra `NULL` ở đúng từng cấp trước khi dereference.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Muốn người khác đổi tờ giấy ghi địa chỉ của bạn, bạn phải chỉ nơi đặt chính tờ giấy ấy. int * chỉ tới một int; int ** chỉ tới một object int * để có thể thay giá trị của object đó.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| pointer cấp hai | con trỏ chỉ tới một object con trỏ | out_selected |
| borrow | mượn dữ liệu, không nhận quyền giải phóng | selected chỉ phần tử mảng |
| const int ** | con trỏ tới object const int * | ghi địa chỉ kết quả, không ghi phần tử qua nó |

### Ví dụ nhỏ — tính tay trước

Mảng [3, 9], selected = NULL. Truyền &selected: hàm ghi địa chỉ ô 1 vào selected; sau return *selected = 9. Mảng vẫn do caller giữ, không có int mới được tạo.

Ta có mảng số lượng tồn kho và muốn một hàm chọn phần tử lớn nhất. Hàm không cần sao chép giá trị; nó cần làm pointer `selected` ở `main` trỏ thẳng tới phần tử được chọn.

Nếu tham số chỉ là `const int *result`, hàm nhận bản sao của pointer. Gán lại bản sao đó không đổi pointer ở `main`. Muốn sửa **object pointer** của bên gọi, hàm cần địa chỉ của object pointer ấy: một pointer cấp hai.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.c`:

```c
#include <stddef.h>
#include <stdio.h>

static int select_largest(
    const int *values,
    size_t count,
    const int **result
)
{
    if (values == NULL || count == 0 || result == NULL) {
        return 0;
    }

    size_t largest_index = 0;

    for (size_t index = 1; index < count; ++index) {
        if (values[index] > values[largest_index]) {
            largest_index = index;
        }
    }

    /* *result is the caller's selected pointer, not the selected int. */
    *result = &values[largest_index];
    return 1;
}

int main(void)
{
    const int quantities[] = {8, 15, 6, 12};
    const int *selected = NULL;

    if (!select_largest(
            quantities,
            sizeof quantities / sizeof quantities[0],
            &selected
        )) {
        printf("Khong chon duoc phan tu\n");
        return 1;
    }

    printf("So luong lon nhat: %d\n", *selected);
    printf(
        "Da chon phan tu thu hai: %s\n",
        selected == &quantities[1] ? "co" : "khong"
    );

    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o pointer-to-pointer
./pointer-to-pointer
```

Output:

```text
So luong lon nhat: 15
Da chon phan tu thu hai: co
```

### Walkthrough — execution / state / cost

1. main tạo mảng và biến selected; select_largest nhận mảng, count và địa chỉ selected.
2. Hàm từ chối input không hợp lệ trước khi ghi output; với dữ liệu mẫu, quét tới giá trị lớn nhất 15.
3. *out_selected nhận địa chỉ ô chứa 15; caller đọc qua selected để in.
4. Dữ liệu và con trỏ kết quả sống trong caller. Quét n phần tử tốn O(n), state phụ cố định; không malloc, không free.

### Mini-check

Khi hàm gán *out_selected, object nào thay đổi: mảng, selected hay bản sao out_selected trong callee?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Đọc khai báo từ tên biến ra ngoài

```c
const int **result;
```

Đọc theo từng lớp:

1. `result` là pointer;
2. nó trỏ tới một pointer;
3. pointer ở lớp trong trỏ tới `const int`.

Trong ví dụ:

```text
Stack frame select_largest       Stack frame main

result ────────────────────────► selected ─────────────┐
                                                      │
quantities: [8] [15] [6] [12]                        │
                   ▲                                  │
                   └──────────────────────────────────┘
```

`result` trỏ tới object pointer `selected`. Sau phép gán:

```c
*result = &values[largest_index];
```

- `result` vẫn trỏ tới `selected`;
- `*result` chính là object `selected`;
- object `selected` được gán địa chỉ của `quantities[1]`.

### Vì sao lời gọi dùng `&selected`

`selected` có kiểu `const int *`. Do đó:

```c
&selected
```

có kiểu `const int **`, đúng kiểu tham số `result`.

Nếu truyền chỉ `selected`, hàm nhận `const int *` và chỉ có thể đọc phần tử hoặc đổi bản sao pointer trong frame của hàm.

### Hai lần dereference

Với một `int **numbers`:

- `numbers` là địa chỉ của object pointer;
- `*numbers` là pointer cấp một;
- `**numbers` là object `int` cuối cùng.

Trong hàm chính, ta chỉ dùng `*result` để đổi pointer cấp một, không dùng `**result` để sửa phần tử. `const` cũng ngăn việc sửa phần tử qua chuỗi pointer này.

### Lifetime của pointer được trả qua output

`selected` trỏ vào mảng `quantities` thuộc `main`. Mảng còn sống tới cuối `main`, nên dereference `selected` sau lời gọi là hợp lệ.

Hàm không tạo object mới và không chuyển ownership. Nó trả một **borrowed pointer**: pointer mượn vùng nhớ của mảng nguồn. Bên gọi không được giải phóng pointer đó và không được dùng nó sau khi mảng nguồn hết lifetime.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Trả một int | sao chép giá trị được chọn | caller không phụ thuộc vòng đời mảng; không cho biết vị trí gốc |
| Trả const int * | trả địa chỉ mượn | không copy phần tử; phụ thuộc nguồn còn sống |
| const int ** output | ghi con trỏ kết quả của caller | tách status khỏi kết quả; nhiều tầng hơn, chỉ dùng khi cần contract đó |

### Misconception check

**Đúng hay sai?** const int ** nghĩa là không thể đổi con trỏ output.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể ghi *out_selected là một const int *; const hạn chế int ở đích cuối.

</details>

**Đúng hay sai?** int ** luôn chuyển an toàn sang const int **.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể mở đường gán địa chỉ const object vào int * rồi ghi trái phép; compiler phải bảo vệ kiểu.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** vẽ từng tầng địa chỉ.

- **Working Developer — dùng khi làm việc:** giữ kiểu const đúng ở từng tầng.

- **Deep Dive — có thể quay lại sau:** giải thích vì sao chuyển đổi const nhiều tầng bị hạn chế.

### Mỗi cấp pointer là một object riêng

Ví dụ:

```c
int value = 42;
int *first_level = &value;
int **second_level = &first_level;
```

Sơ đồ:

```text
second_level ──► first_level ──► value
   int **           int *          int
```

Ba object có ba địa chỉ riêng. “Cấp hai” không có nghĩa dữ liệu `value` bị nhân đôi.

### Kiểm tra `NULL` theo đường truy cập

Trước `*second_level`, `second_level` phải khác `NULL`.

Trước `**second_level`, cả hai điều kiện phải đúng:

```c
if (second_level != NULL && *second_level != NULL) {
    printf("%d\n", **second_level);
}
```

Toán tử `&&` đánh giá từ trái sang phải và dừng khi vế trái sai, nên `*second_level` chỉ được đọc sau khi pointer ngoài hợp lệ.

### Output parameter thay đổi pointer

Mẫu tổng quát:

```c
int find_value(
    const int *values,
    size_t count,
    const int **result
);
```

Mẫu này cho phép:

- giá trị trả về báo thành công/thất bại;
- `*result` nhận pointer tới số tìm thấy;
- không sao chép phần tử.

Từ bài [Struct, enum và typedef](./09-struct-enum-typedef.md), ta sẽ dùng cùng mẫu với kiểu dữ liệu sản phẩm.

### Không phải mọi API đều cần pointer cấp hai

Nếu chỉ sửa object `int`, dùng `int *`. Nếu chỉ đọc mảng, dùng `const int *`. Chỉ dùng `T **` khi cần truy cập hoặc thay đổi một object có kiểu `T *`, hoặc khi cấu trúc dữ liệu thật sự có hai lớp pointer.

## 6. Lỗi thường gặp

### Truyền sai cấp pointer

Hàm cần `const int **result`, nên đối số là `&selected`, không phải `selected`.

Compiler warning về kiểu pointer không tương thích thường chỉ ra lỗi thiết kế thật. Không cast để làm warning biến mất.

### Dereference thiếu hoặc thừa một cấp

```c
result = &values[largest_index];
```

là sai kiểu và chỉ định đổi pointer cục bộ. Dòng đúng để sửa `selected` là:

```c
*result = &values[largest_index];
```

### Không kiểm tra output parameter

Nếu `result == NULL`, `*result = ...` dereference null pointer. Kiểm tra trước.

### Giữ borrowed pointer quá lâu

Không trả qua `result` địa chỉ của biến cục bộ trong `select_largest`. Cũng không dùng pointer vào một mảng sau khi mảng hết lifetime.

### Chuyển `T **` tùy tiện

Không thể coi mọi pointer cấp hai là tương thích. Đặc biệt, không truyền `int **` vào nơi nhận `const int **` bằng cast; phép chuyển đó có thể cho phép ghi một pointer không phù hợp vào object của bên gọi. Hãy khai báo object pointer của bên gọi đúng kiểu contract ngay từ đầu, như `const int *selected`.

## 7. Khi nào KHÔNG dùng

Không dùng hai tầng pointer nếu chỉ trả một số nhỏ và không cần phân biệt trạng thái lỗi. Không dùng ép kiểu để dập warning int **/const int **; sửa kiểu object trung gian và contract.

## 8. Production notes & scale check

Quét vài chục phần tử dùng vòng lặp đủ rõ. API nên nói output giữ nguyên khi lỗi và borrow có hiệu lực bao lâu. Test mảng rỗng, out_selected = NULL và maximum ở đầu/cuối; sanitizer không thay thế việc review const/ownership.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Chọn số nhỏ nhất

Viết `select_smallest` theo mẫu bài chính và làm `selected` trỏ tới phần tử nhỏ nhất.

**Gợi ý:** khởi tạo chỉ số nhỏ nhất bằng `0`, bắt đầu duyệt từ `1`.

### Bài 2 — Tìm ký tự cuối

Viết hàm nhận chuỗi, ký tự đích và `const char **result`; trả pointer tới lần xuất hiện cuối cùng.

**Gợi ý:** mỗi lần gặp ký tự đích, cập nhật `*result`; đặt `*result = NULL` trước khi duyệt.

### Bài 3 — Đổi chỗ hai pointer

Viết hàm đổi chỗ hai biến `int *` của bên gọi.

**Gợi ý:** tham số của hàm có kiểu `int **`; biến tạm có kiểu `int *`.

### Bài 4 — Vẽ ba lớp bộ nhớ

Vẽ trạng thái của `result`, `selected` và mảng trước/sau dòng `*result = &values[largest_index]`.

**Gợi ý:** không gộp `result` và `selected` thành một hộp.

## 10. Bài tập tích hợp liên module — Judgment

So với tìm điểm cao nhất Module 01, khi nào trả bản sao điểm tốt hơn trả địa chỉ? Xét caller cần giữ kết quả sau khi thay mảng; nêu chi phí và vòng đời của mỗi lựa chọn.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ ba object mảng/selected/out_selected.
2. Có phải hai dấu * đồng nghĩa hai vùng cấp phát động?
3. Làm sao trả status mà vẫn đưa ra vị trí được chọn?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi đọc được `const int **result` theo từng lớp.
- [ ] Tôi giải thích được vì sao lời gọi truyền `&selected`.
- [ ] Tôi biết `*result` sửa object pointer nào.
- [ ] Tôi kiểm tra `NULL` ở từng cấp trước khi dereference.
- [ ] Tôi hiểu pointer trả về trong bài là borrowed pointer.

**Bài prerequisite:** [Con trỏ với mảng và chuỗi](./03-con-tro-voi-mang-va-chuoi.md)

**Bài tiếp theo:** [Con trỏ hàm và callback](./05-con-tro-ham-va-callback.md)
