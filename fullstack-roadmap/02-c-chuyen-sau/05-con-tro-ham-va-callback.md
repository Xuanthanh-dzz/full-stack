# Con trỏ hàm và callback

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- lưu địa chỉ của một hàm trong function pointer;
- truyền function pointer làm callback cho một hàm khác;
- đọc khai báo `int (*rule)(int)`;
- kiểm tra callback `NULL` trước khi gọi;
- nhận ra khi callback giúp tách phần ổn định khỏi chính sách có thể thay đổi.

## 2. Bài toán mở đầu

Quy trình tính tiền luôn giống nhau:

1. nhận đơn giá;
2. áp dụng chính sách giá;
3. nhân với số lượng.

Nhưng chính sách giá có thể là giữ nguyên hoặc giảm 10%. Ta không muốn chép lại toàn bộ hàm tính tổng cho mỗi chính sách. Thay vào đó, hàm tính tổng nhận một callback: địa chỉ của hàm thực hiện chính sách.

## 3. Lời giải bằng code

Tạo `main.c`:

```c
#include <limits.h>
#include <stdio.h>

static int regular_price(int unit_price)
{
    return unit_price;
}

static int ten_percent_off(int unit_price)
{
    int whole_hundreds = unit_price / 100;
    int remainder = unit_price % 100;
    return whole_hundreds * 90 + remainder * 90 / 100;
}

static int calculate_line_total(
    int unit_price,
    int quantity,
    int (*price_rule)(int)
)
{
    if (unit_price < 0 || quantity < 0 || price_rule == NULL) {
        return -1;
    }

    /* This callback runs synchronously and is not retained after the call. */
    int adjusted_price = price_rule(unit_price);
    if (adjusted_price < 0
        || (quantity > 0 && adjusted_price > INT_MAX / quantity)) {
        return -1;
    }

    return adjusted_price * quantity;
}

static void print_total(
    const char *label,
    int unit_price,
    int quantity,
    int (*price_rule)(int)
)
{
    int total = calculate_line_total(unit_price, quantity, price_rule);

    if (total < 0) {
        printf("%s: du lieu khong hop le\n", label);
        return;
    }

    printf("%s: %d xu\n", label, total);
}

int main(void)
{
    int (*selected_rule)(int) = regular_price;

    print_total("Gia thuong", 1000, 3, selected_rule);

    selected_rule = ten_percent_off;
    print_total("Giam 10 phan tram", 1000, 3, selected_rule);

    print_total("Khong co callback", 1000, 3, NULL);
    return 0;
}
```

Ví dụ dùng đơn vị “xu” nguyên để bài tập trung vào function pointer, không đưa sai số số thực vào phép tính tiền.

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o function-pointer
./function-pointer
```

Output:

```text
Gia thuong: 3000 xu
Giam 10 phan tram: 2700 xu
Khong co callback: du lieu khong hop le
```

## 4. Giải thích cơ chế

### Hàm cũng có địa chỉ

Code đã biên dịch của `regular_price` và `ten_percent_off` nằm trong vùng chứa lệnh của chương trình. Tên hàm trong biểu thức có thể chuyển thành pointer tới hàm đó:

```c
int (*selected_rule)(int) = regular_price;
```

Đọc từ tên `selected_rule`:

1. `(*selected_rule)`: `selected_rule` là pointer;
2. `(int)`: nó trỏ tới hàm nhận một `int`;
3. `int` bên trái: hàm trả một `int`.

Dấu ngoặc là bắt buộc. `int *selected_rule(int)` sẽ là khai báo một hàm trả về `int *`, hoàn toàn khác.

### Truyền callback vẫn là truyền bằng giá trị

Lời gọi:

```c
calculate_line_total(1000, 3, selected_rule);
```

chép địa chỉ hàm vào tham số cục bộ `price_rule`.

```text
selected_rule ──► ten_percent_off
                       ▲
price_rule ────────────┘
```

Hai object pointer riêng cùng chứa một địa chỉ hàm. Hàm `calculate_line_total` gọi callback bằng:

```c
price_rule(unit_price);
```

Cũng có thể viết `(*price_rule)(unit_price)`, nhưng dạng ngắn dễ đọc hơn.

### Chữ ký phải khớp

Callback yêu cầu chữ ký:

```c
int callback(int);
```

Cả `regular_price` và `ten_percent_off` đều:

- nhận đúng một `int`;
- trả về `int`.

Không truyền hàm có số lượng/kiểu tham số hoặc kiểu trả về khác. Gọi hàm qua function pointer không tương thích gây undefined behavior.

### Kiểm tra callback

`NULL` biểu diễn không có callback. `calculate_line_total` kiểm tra trước lời gọi gián tiếp. Không gọi `price_rule(...)` khi `price_rule == NULL`.

### Tách cơ chế khỏi chính sách

`calculate_line_total` giữ cơ chế cố định: validate, gọi chính sách, kiểm tra callback không trả giá âm, chống overflow rồi mới nhân số lượng. `ten_percent_off` tách `unit_price` thành phần trăm tròn và phần dư trước khi nhân; các phép nhân trung gian nhờ vậy không vượt miền `int`. Hai hàm callback chứa phần thay đổi. Muốn thêm chính sách mới, ta viết hàm cùng chữ ký mà không sửa thuật toán tổng quát.

## 5. Kiến thức nền

### Data pointer và function pointer

`int *` trỏ tới object dữ liệu kiểu `int`; `int (*)(int)` trỏ tới hàm. Không coi hai loại này là thay thế cho nhau và không cast giữa chúng trong code C11 portable.

### Callback chạy lúc nào

Trong ví dụ, callback chạy đồng bộ ngay bên trong `calculate_line_total`. Function pointer tự nó không tạo thread, không trì hoãn và không làm công việc bất đồng bộ.

### Context đi cùng callback

Một callback chỉ nhận tham số trong chữ ký. API C thường truyền thêm một data pointer để callback biết context:

```c
static void visit_value(
    int value,
    void (*visitor)(int value, void *context),
    void *context
);
```

`void *` là pointer có thể giữ địa chỉ object thuộc nhiều kiểu; callback phải biết contract để chuyển lại đúng kiểu trước khi dùng. Đây là mẫu nâng cao, chưa cần dùng trong chương trình chính. Không dereference `void *` trực tiếp vì nó chưa mô tả kiểu object.

### Khi nào callback đáng dùng

Callback phù hợp khi:

- thuật toán tổng quát ổn định;
- một bước có nhiều cách thực hiện;
- bên gọi cần cung cấp hành vi;
- các hàm lựa chọn có cùng contract.

Nếu chỉ có một hành vi đơn giản và không có nhu cầu thay thế, gọi hàm trực tiếp thường dễ đọc hơn.

### Đào sâu (có thể quay lại sau)

Function pointer không đảm bảo callback còn hợp lệ nếu đến từ code đã bị dỡ khỏi tiến trình, và không mang theo dữ liệu môi trường như closure ở một số ngôn ngữ khác. Trong C, context thường được truyền tách riêng bằng `void *`; lifetime và kiểu thật của object context là trách nhiệm của contract API.

Một số hệ thống dùng bảng function pointer để mô phỏng dispatch. Đây là nền tảng để hiểu đa hình trong C++, nhưng chưa cần cho lần đọc đầu.

## 6. Lỗi thường gặp

### Thiếu ngoặc trong khai báo

```c
int *rule(int);
```

khai báo hàm trả `int *`, không phải function pointer. Dạng đúng:

```c
int (*rule)(int);
```

### Gọi callback `NULL`

Luôn xác định `NULL` có hợp lệ theo contract không. Nếu không hợp lệ, từ chối trước khi gọi gián tiếp.

### Chữ ký gần giống nhưng không khớp

Không ép kiểu một hàm `long rule(long)` thành `int (*)(int)`. Compiler warning không phải thủ tục phiền toái; nó báo lời gọi có thể sai quy ước và cách diễn giải đối số.

### Callback dùng object đã hết lifetime

Nếu API giữ callback/context để gọi sau, object context phải sống đủ lâu. Ví dụ chính gọi ngay nên không giữ pointer sau khi hàm trả về.

### Tin rằng callback luôn trả kết quả hợp lệ

Callback là code do caller cung cấp. Hàm tổng quát vẫn phải validate kết quả theo contract và chống overflow trước phép nhân.

### Lạm dụng callback

Quá nhiều lớp callback làm luồng điều khiển khó theo dõi. Đặt tên theo mục đích, ghi rõ callback được gọi bao nhiêu lần, đồng bộ hay được giữ lại, và có được phép `NULL` hay không.

## 7. Bài tập

### Bài 1 — Hai chính sách phí

Viết callback `free_shipping` và `fixed_shipping`, rồi một hàm tính tổng nhận callback phí vận chuyển.

**Gợi ý:** chọn một chữ ký chung, chẳng hạn `int rule(int subtotal)`.

### Bài 2 — Chọn phép toán

Viết `calculate(a, b, operation)` với callback nhận hai `int`; thử cộng, trừ và nhân.

**Gợi ý:** kiểu tham số là `int (*operation)(int, int)`.

### Bài 3 — Duyệt mảng bằng callback

Viết hàm nhận mảng, số phần tử và callback biến đổi từng giá trị trước khi tính tổng.

**Gợi ý:** callback chỉ cần nhận một `int` và trả một `int`.

### Bài 4 — Callback với context

Mở rộng bài 3 để hệ số nhân nằm trong một object `int` được truyền qua `void *context`.

**Gợi ý:** trong callback, kiểm tra `context != NULL`, rồi chuyển về `const int *` trước khi dereference.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi đọc đúng khai báo `int (*rule)(int)`.
- [ ] Tôi hiểu function pointer chứa địa chỉ hàm, không chứa kết quả hàm.
- [ ] Tôi kiểm tra `NULL` trước khi gọi callback.
- [ ] Tôi không cast để ghép các chữ ký không tương thích.
- [ ] Tôi biết callback trong ví dụ chạy đồng bộ.

**Bài prerequisite:** [Con trỏ cấp hai](./04-con-tro-cap-hai.md)

**Bài tiếp theo:** [Stack, heap và vòng đời bộ nhớ](./06-stack-heap-va-vong-doi-bo-nho.md)
