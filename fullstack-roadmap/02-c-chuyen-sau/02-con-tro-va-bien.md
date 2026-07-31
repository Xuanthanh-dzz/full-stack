# Con trỏ và biến

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- truyền địa chỉ của biến vào hàm để hàm sửa object của bên gọi;
- giải thích vì sao bản thân pointer vẫn được truyền bằng giá trị;
- dùng `NULL` để biểu diễn “không trỏ tới object nào” và kiểm tra trước khi dereference;
- dùng `const int *` khi hàm chỉ được đọc object đích;
- phân biệt việc đổi giá trị object đích với việc đổi địa chỉ chứa trong pointer.

## 2. Bài toán mở đầu

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

## 3. Lời giải bằng code

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

## 4. Giải thích cơ chế

### Trước khi gọi hàm

Trong stack frame của `main`:

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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi giải thích được “C truyền bản sao của địa chỉ”.
- [ ] Tôi biết lúc nào dùng `&variable` và lúc nào dùng `*pointer`.
- [ ] Tôi kiểm tra `NULL` trước khi dereference.
- [ ] Tôi dùng `const int *` cho tham số chỉ đọc.
- [ ] Tôi phân biệt đổi pointer với đổi object đích.

**Bài prerequisite:** [Địa chỉ bộ nhớ và con trỏ](./01-dia-chi-bo-nho-va-con-tro.md)

**Bài tiếp theo:** [Con trỏ với mảng và chuỗi](./03-con-tro-voi-mang-va-chuoi.md)
