# Con trỏ và biến

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- C truyền đối số bằng giá trị, kể cả khi giá trị được truyền là một con trỏ.
- Dùng tham số con trỏ để hàm sửa dữ liệu caller hoặc trả thêm kết quả.
- Đổi bản sao con trỏ không đổi con trỏ caller; dereference sai vẫn gây lỗi bộ nhớ.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- truyền địa chỉ của biến vào hàm để hàm sửa object của bên gọi;
- giải thích vì sao bản thân pointer vẫn được truyền bằng giá trị;
- dùng `NULL` để biểu diễn “không trỏ tới object nào” và kiểm tra trước khi dereference;
- dùng `const int *` khi hàm chỉ được đọc object đích;
- phân biệt việc đổi giá trị object đích với việc đổi địa chỉ chứa trong pointer.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bạn đưa cho người khác bản sao tờ giấy ghi địa chỉ nhà. Họ có thể đến nhà sửa cửa, nhưng viết địa chỉ khác lên bản giấy của họ không đổi bản bạn giữ. Hàm nhận pointer cũng vậy.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| caller | hàm đang gọi hàm khác | main gọi order_ascending |
| callee | hàm được gọi | order_ascending |
| output parameter | tham số chỉ vùng nhận kết quả | low và high |
| const int * | con trỏ chỉ cho phép đọc int qua đường truy cập này | hàm in không được sửa số |
| NULL | giá trị con trỏ rỗng, không chỉ tới object | được kiểm tra trước *low |

### Ví dụ nhỏ — tính tay trước

a = 8, b = 3. Hàm nhận &a và &b, giữ tạm 8, ghi 3 vào a rồi ghi 8 vào b. Caller thấy a = 3, b = 8 vì cả hai lần ghi dùng địa chỉ của caller.

Một màn hình nhập hai mức tồn kho nhưng người dùng có thể nhập ngược: giới hạn thấp lại lớn hơn giới hạn cao. Ta cần hàm sắp xếp hai biến theo thứ tự tăng dần.

Hàm C chỉ nhận bản sao tham số. Hàm sau không thể sửa biến của `main`:

```c
void order_wrong(int left, int right)
{
    int temporary = left;
    left = right;
    right = temporary;
}
```

Ta sẽ truyền địa chỉ của hai biến để hàm truy cập đúng object của bên gọi.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.c`:

```c
#include <limits.h>
#include <stdio.h>

static int order_ascending(int *left, int *right)
{
    /* Validate both borrowed pointers before the first dereference. */
    if (left == NULL || right == NULL) {
        return 0;
    }

    if (*left > *right) {
        int temporary = *left;
        *left = *right;
        *right = temporary;
    }

    return 1;
}

static void print_range(const int *low, const int *high)
{
    if (low == NULL || high == NULL) {
        printf("Khoang khong hop le\n");
        return;
    }

    printf("Khoang ton kho: %d..%d\n", *low, *high);
}

int main(void)
{
    int low_stock = 30;
    int high_stock = 10;

    printf("Truoc khi sap xep: %d..%d\n", low_stock, high_stock);

    if (!order_ascending(&low_stock, &high_stock)) {
        printf("Khong the sap xep\n");
        return 1;
    }

    printf("Sau khi sap xep: %d..%d\n", low_stock, high_stock);
    print_range(&low_stock, &high_stock);

    printf(
        "Goi voi NULL: %s\n",
        order_ascending(NULL, &high_stock) ? "thanh cong" : "bi tu choi"
    );

    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o pointer-variable
./pointer-variable
```

Output:

```text
Truoc khi sap xep: 30..10
Sau khi sap xep: 10..30
Khoang ton kho: 10..30
Goi voi NULL: bi tu choi
```

### Walkthrough — execution / state / cost

1. main giữ 30 và 10; các đối số là địa chỉ của hai biến này.
2. order_ascending nhận bản sao hai địa chỉ, kiểm tra NULL trước khi đọc dữ liệu.
3. Vì 30 > 10, biến tạm giữ 30; hai lần ghi qua pointer đổi caller thành 10 và 30.
4. Hàm in đọc qua const int *; không sở hữu và không giải phóng dữ liệu. Số phép đọc/ghi cố định, không phụ thuộc kích thước input ngoài hai số.

### Mini-check

Nếu low và high cùng trỏ một int thì hàm sắp xếp có cần tạo hai int mới không? Trace điều kiện so sánh.

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Trước khi gọi hàm

Dùng mô hình stack frame phổ biến để trace (chuẩn C không bắt buộc vị trí vật lý này), trong `main`:

```text
low_stock = 30             high_stock = 10
địa chỉ L                  địa chỉ H
┌──────────────┐           ┌───────────────┐
│ int: 30      │           │ int: 10       │
└──────────────┘           └───────────────┘
```

Lời gọi:

```c
order_ascending(&low_stock, &high_stock);
```

tính hai giá trị địa chỉ `L` và `H`, rồi truyền **bản sao của hai địa chỉ** vào hàm.

### Trong stack frame của hàm

Tham số `left` và `right` là hai object pointer cục bộ:

```text
Stack frame order_ascending          Stack frame main

left = L  ─────────────────────────► low_stock = 30
right = H ─────────────────────────► high_stock = 10
```

C vẫn truyền tham số bằng giá trị:

- bản sao của số `30` không được truyền;
- bản sao của địa chỉ `L` được truyền;
- dereference `*left` cho phép truy cập object tại `L`.

Khi hàm gán:

```c
*left = *right;
```

object `low_stock` trong frame của `main` bị sửa. Nếu hàm chỉ viết `left = right`, nó chỉ đổi pointer cục bộ `left`.

### `NULL` và kiểm tra đầu vào

`NULL` là null pointer constant: giá trị dùng để chỉ pointer không trỏ tới object nào. So sánh pointer với `NULL` là hợp lệ; dereference `NULL` là undefined behavior.

Hàm kiểm tra:

```c
if (left == NULL || right == NULL) {
    return 0;
}
```

trước mọi `*left` hoặc `*right`. Giá trị trả về `1` báo thành công, `0` báo đầu vào không hợp lệ. Bài 14 sẽ xây dựng hệ thống mã lỗi chi tiết hơn.

### `const` bảo vệ object đích

Khai báo:

```c
static void print_range(const int *low, const int *high)
```

nghĩa là hàm được đọc `*low`, nhưng compiler không cho hàm gán `*low = ...`. Pointer cục bộ `low` vẫn có thể được gán để trỏ nơi khác; điều bị bảo vệ ở đây là object nhìn qua pointer đó.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| int value | bản sao một số | rẻ, rõ; ưu tiên nếu chỉ đọc một int |
| int *value | bản sao địa chỉ, có thể sửa đích | cần contract NULL/vòng đời; dùng output parameter |
| const int *value | đọc đích qua con trỏ | không làm đích bất biến qua mọi alias; dùng API chỉ đọc |

### Misconception check

**Đúng hay sai?** C có truyền tham chiếu khi tham số là int *.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: C vẫn sao chép giá trị con trỏ; thao tác gián tiếp mới sửa caller.

</details>

**Đúng hay sai?** const int * ngăn mọi đoạn code khác sửa int.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ hạn chế ghi qua đường truy cập đó.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace bản sao địa chỉ và ghi qua *.

- **Working Developer — dùng khi làm việc:** thiết kế contract output không đổi khi lỗi.

- **Deep Dive — có thể quay lại sau:** phân tích alias và giới hạn của NULL check.

### Ba dạng `const` thường gặp

```c
const int *read_only_target = &value;
int * const fixed_pointer = &value;
const int * const fixed_read_only = &value;
```

- `const int *`: không sửa `int` qua pointer này; pointer có thể trỏ chỗ khác.
- `int * const`: pointer phải giữ nguyên địa chỉ sau khi khởi tạo; có thể sửa `int`.
- `const int * const`: không đổi địa chỉ và không sửa `int` qua pointer.

Trong tham số hàm, dạng đầu phổ biến nhất. Nó ghi rõ contract “hàm chỉ đọc”.

### Pointer cùng kiểu

Một `int *` phải trỏ tới `int`; một `double *` phải trỏ tới `double`. Không cast pointer để che lỗi không tương thích. Kiểu pointer giúp compiler chọn kích thước và cách diễn giải object khi dereference.

### Pointer có thể làm output parameter

Khi hàm cần trả thêm một kết quả, bên gọi tạo biến và truyền địa chỉ:

```c
static int try_divide(int dividend, int divisor, int *result)
{
    if (divisor == 0 || result == NULL
        || (dividend == INT_MIN && divisor == -1)) {
        return 0;
    }

    *result = dividend / divisor;
    return 1;
}
```

Hàm trả `1/0` để báo trạng thái; kết quả phép chia được ghi vào `*result`. Ngoài chia cho `0`, hàm từ chối `INT_MIN / -1` vì kết quả không biểu diễn được bằng `int`. Chỉ đọc `result` ở bên gọi khi hàm báo thành công.

### Contract phải nói rõ pointer có bắt buộc hay không

Một API nhận pointer cần quy định:

- `NULL` có được phép không;
- hàm chỉ đọc hay có thể sửa object đích;
- object phải còn sống trong bao lâu;
- ai sở hữu và giải phóng tài nguyên nếu có.

Ở bài này, `left` và `right` bắt buộc khác `NULL`; hàm có thể sửa hai `int`; quyền sở hữu vẫn thuộc `main`.

## 6. Lỗi thường gặp

### Truyền giá trị thay vì địa chỉ

Sai:

```c
order_ascending(low_stock, high_stock);
```

Hàm yêu cầu `int *`. Đúng:

```c
order_ascending(&low_stock, &high_stock);
```

### Quên `*` trong hàm

```c
left = right;
```

chỉ làm pointer cục bộ `left` trỏ cùng nơi với `right`. Muốn sửa object:

```c
*left = *right;
```

### Kiểm tra `NULL` sau khi dereference

Sai thứ tự:

```c
int value = *pointer;
if (pointer == NULL) {
    return;
}
```

Phải kiểm tra trước mọi dereference.

### Ghi qua pointer chỉ-đọc

Nếu hàm nhận `const int *value`, không cast bỏ `const` để ghi. Hãy sửa contract của hàm nếu nó thật sự cần quyền ghi, hoặc giữ hàm chỉ đọc.

### Trả địa chỉ của biến cục bộ

Không trả `&temporary` khi `temporary` là biến cục bộ của hàm. Object hết lifetime lúc hàm kết thúc. Bài [Stack, heap và vòng đời bộ nhớ](./06-stack-heap-va-vong-doi-bo-nho.md) sẽ phân tích lỗi này đầy đủ.

## 7. Khi nào KHÔNG dùng

Không dùng output parameter cho một phép tính chỉ trả một giá trị và không có trạng thái lỗi cần tách. Không dùng con trỏ có quyền ghi cho hàm chỉ in; quyền đọc đủ sẽ làm contract rõ hơn.

## 8. Production notes & scale check

Với hai số, tối ưu thêm không có lợi đáng kể; ưu tiên ca NULL và alias cùng object. API thực phải nói khi thất bại output có giữ nguyên không. NULL check không chứng minh mọi pointer khác NULL đều hợp lệ.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Tăng tồn kho

Viết `int add_stock(int *quantity, int amount)`. Từ chối `NULL` và `amount < 0`; nếu hợp lệ thì cộng vào object đích.

**Gợi ý:** kiểm tra mọi điều kiện trước `*quantity += amount`, kể cả `*quantity > INT_MAX - amount` để tránh signed overflow.

### Bài 2 — Chia có kiểm tra

Hoàn thiện `try_divide` trong phần kiến thức nền và gọi với mẫu số hợp lệ, bằng `0`, cùng output pointer `NULL`.

**Gợi ý:** không sửa biến kết quả khi hàm thất bại.

### Bài 3 — Tìm số nhỏ hơn

Viết hàm chỉ đọc hai `int` qua `const int *` và trả về giá trị nhỏ hơn qua output parameter.

**Gợi ý:** hàm có ba pointer cần kiểm tra.

### Bài 4 — Vẽ stack frame

Vẽ stack ngay trước và trong lời gọi `add_stock(&quantity, 5)`.

**Gợi ý:** phải có object `quantity`, pointer tham số và mũi tên từ pointer tới object.

## 10. Bài tập tích hợp liên module — Judgment

Module 01 đã dùng giá trị trả về. Thiết kế phép chia cần trả thương và báo mẫu số 0: so sánh sentinel với trạng thái thành công + output parameter; chỉ ra ca INT_MIN / -1 và giá trị output khi lỗi.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vì sao gán low = NULL trong hàm không đổi pointer caller?
2. const đặt trước int hạn chế thao tác nào?
3. Nêu hai ca kiểm thử ngoài a > b.

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được “C truyền bản sao của địa chỉ”.
- [ ] Tôi biết lúc nào dùng `&variable` và lúc nào dùng `*pointer`.
- [ ] Tôi kiểm tra `NULL` trước khi dereference.
- [ ] Tôi dùng `const int *` cho tham số chỉ đọc.
- [ ] Tôi phân biệt đổi pointer với đổi object đích.

**Bài prerequisite:** [Địa chỉ bộ nhớ và con trỏ](./01-dia-chi-bo-nho-va-con-tro.md)

**Bài tiếp theo:** [Con trỏ với mảng và chuỗi](./03-con-tro-voi-mang-va-chuoi.md)
