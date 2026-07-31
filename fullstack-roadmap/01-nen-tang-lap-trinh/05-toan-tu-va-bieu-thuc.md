# Toán tử và biểu thức

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng operator số học, so sánh, logic và assignment;
- phân biệt chia nguyên với chia số thực;
- dự đoán thứ tự đánh giá theo precedence cơ bản;
- dùng ngoặc để biểu diễn ý định rõ ràng;
- tránh overflow và side effect khó đọc trong biểu thức.

## 2. Bài toán mở đầu

Một đơn hàng có:

- `3` sản phẩm, mỗi sản phẩm `120000` VND;
- giảm giá cố định `20000` VND;
- phí giao hàng `15000` VND;
- miễn phí giao hàng nếu tiền sau giảm giá ít nhất `300000` VND.

Chương trình cần tính các con số và hai điều kiện:

```text
Tam tinh: 360000
Sau giam gia: 340000
Duoc mien phi giao hang: 1
Tong thanh toan: 340000
Don hang hop le: 1
```

Ta chưa dùng `if`; giá trị điều kiện được in trực tiếp dưới dạng `1` hoặc `0`.

## 3. Lời giải bằng code

Tạo file `operators.c`:

```c
#include <stdbool.h>
#include <stdio.h>

int main(void)
{
    const int quantity = 3;
    const int unit_price = 120000;
    const int discount = 20000;
    const int shipping_fee = 15000;
    const int free_shipping_threshold = 300000;

    int subtotal = quantity * unit_price;
    int discounted_total = subtotal - discount;
    bool has_free_shipping =
        discounted_total >= free_shipping_threshold;

    /* Dùng phép nhân boolean chỉ để quan sát giá trị 0/1 của điều kiện. */
    int payable = discounted_total +
        shipping_fee * !has_free_shipping;

    bool valid_order =
        quantity > 0 &&
        unit_price > 0 &&
        discount >= 0 &&
        discount <= subtotal;

    printf("Tam tinh: %d\n", subtotal);
    printf("Sau giam gia: %d\n", discounted_total);
    printf("Duoc mien phi giao hang: %d\n", has_free_shipping);
    printf("Tong thanh toan: %d\n", payable);
    printf("Don hang hop le: %d\n", valid_order);

    printf("17 / 5 = %d\n", 17 / 5);
    printf("17 %% 5 = %d\n", 17 % 5);
    printf("17.0 / 5.0 = %.1f\n", 17.0 / 5.0);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror operators.c -o operators
./operators
```

Output:

```text
Tam tinh: 360000
Sau giam gia: 340000
Duoc mien phi giao hang: 1
Tong thanh toan: 340000
Don hang hop le: 1
17 / 5 = 3
17 % 5 = 2
17.0 / 5.0 = 3.4
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

## 4. Giải thích cơ chế

### 4.1. Operator số học

| Operator | Ý nghĩa | Ví dụ |
|---|---|---|
| `+` | cộng | `subtotal + fee` |
| `-` | trừ hoặc đổi dấu | `subtotal - discount` |
| `*` | nhân | `quantity * unit_price` |
| `/` | chia | `17 / 5` |
| `%` | phần dư số nguyên | `17 % 5` |

Nếu cả hai toán hạng của `/` là integer, kết quả là integer và phần lẻ bị bỏ về phía 0. Nếu toán hạng phù hợp là floating-point, phép chia tạo số thực.

### 4.2. Operator so sánh

```c
discounted_total >= free_shipping_threshold
```

Các operator `==`, `!=`, `<`, `<=`, `>`, `>=` tạo kết quả đúng/sai. Đừng nhầm `==` (so sánh bằng nhau) với `=` (assignment).

### 4.3. Operator logic

- `!condition`: phủ định;
- `left && right`: đúng khi cả hai đúng;
- `left || right`: đúng khi ít nhất một bên đúng.

C dùng **short-circuit**:

- với `&&`, nếu vế trái sai thì vế phải không được đánh giá;
- với `||`, nếu vế trái đúng thì vế phải không được đánh giá.

Đặc tính này sau này giúp chỉ thực hiện phép tính nguy hiểm khi điều kiện bảo vệ đã đúng.

Trong sample, `!has_free_shipping` là `0` khi được miễn phí, nên:

```text
shipping_fee * 0 = 0
```

Đây là cách minh họa operator, không phải cách diễn đạt dễ đọc nhất trong production. Sau bài 07, nên dùng `if` để chọn phí giao hàng.

### 4.4. Assignment và cập nhật

```c
balance = balance - 10;
balance -= 10;
```

Hai dòng trên có tác dụng tương đương trong tình huống đơn giản. C còn có `+=`, `*=`, `/=`, `%=`. `++count` tăng một; `--count` giảm một.

Ở code production cho người đọc mới, không ghép nhiều lần tăng/assignment vào cùng expression. Tách thành statement rõ thứ tự.

## 5. Kiến thức nền

### Precedence và associativity

Một phần thứ tự phổ biến:

```text
cao hơn:  ()  unary ! -
          * / %
          + -
          < <= > >=
          == !=
          &&
          ||
thấp hơn: =
```

Do đó `a + b * c` nhân trước rồi cộng. Tuy nhiên, đừng bắt người đọc thuộc bảng để hiểu nghiệp vụ:

```c
int subtotal = quantity * unit_price;
int payable = discounted_total + shipping_fee;
```

Biến trung gian vừa làm rõ ý định vừa giúp debugger quan sát state.

### Conversion trong biểu thức

Khi `int` tham gia phép tính với `double`, giá trị `int` được chuyển phù hợp để tính `double`. Conversion từ miền rộng về miền hẹp có thể mất dữ liệu. Chỉ cast khi bạn mô tả được giá trị bị mất hoặc được giữ.

### Overflow

Nếu `quantity * unit_price` vượt miền biểu diễn của `int`, signed integer overflow trong C tạo hành vi không xác định. Production code phải chọn type đủ rộng và kiểm tra biên trước phép tính. Module 02 sẽ đi sâu cách kiểm tra dựa trên giới hạn type.

### Đào sâu (có thể quay lại sau)

Thứ tự **nhóm operator** do precedence không đồng nghĩa mọi toán hạng có thứ tự thực thi trái sang phải. Trong C, không nên viết expression có nhiều side effect lên cùng state, ví dụ:

```c
/* Không viết: hành vi không xác định. */
/* int result = count++ + count++; */
```

Tách thành nhiều statement. Đây là quy tắc an toàn hơn việc cố ghi nhớ toàn bộ quy tắc sequencing.

## 6. Lỗi thường gặp

### Viết `=` thay vì `==`

Assignment có thể tạo một giá trị hợp lệ trong expression, nên lỗi không phải lúc nào cũng dừng compile. Trong điều kiện, kiểm tra kỹ mục đích.

### Chia nguyên rồi mới gán vào `double`

`double average = total / count;` vẫn chia nguyên nếu hai biến là `int`. Dùng `(double)total / count`.

### Chia hoặc lấy dư cho 0

Với integer, `/ 0` và `% 0` là lỗi runtime/undefined behavior. Phải kiểm tra divisor trước.

### Tin rằng ngoặc sửa được overflow

`(double)(quantity * unit_price)` cast sau khi phép nhân `int` đã xảy ra. Nếu cần, conversion phải xảy ra trước phép tính.

### Biểu thức quá dài

Nhiều operator lồng nhau làm khó audit type, biên và logic. Đặt tên cho kết quả trung gian theo nghiệp vụ.

### Dùng so sánh bằng tuyệt đối cho kết quả `double`

Sai số biểu diễn có thể khiến kết quả tính toán không đúng bit với literal mong đợi. Khi so sánh số thực tính toán, thường dùng một tolerance phù hợp domain.

## 7. Bài tập

### Bài 1 — Chẵn hay lẻ

Với một integer cố định, in `1` nếu chẵn và `0` nếu lẻ.

**Gợi ý:** so sánh phần dư khi chia `2` với `0`.

### Bài 2 — Điều kiện hợp lệ

Tạo `age` và in kết quả của điều kiện tuổi nằm trong đoạn từ `18` đến `65`, kể cả hai đầu.

**Gợi ý:** ghép hai phép so sánh bằng `&&`.

### Bài 3 — Chuyển giây

Đổi `3672` giây thành giờ, phút còn lại và giây còn lại.

**Gợi ý:** dùng `/` và `%` từng bước, đặt biến trung gian.

### Bài 4 — So sánh chia nguyên/số thực

Tính trung bình của `8`, `9`, `10` theo cả hai cách và giải thích type của từng expression.

**Gợi ý:** tổng này chia hết; hãy đổi một giá trị để lộ khác biệt.

### Bài 5 — Refactor biểu thức

Tách một expression thanh toán dài thành ít nhất ba biến mang tên nghiệp vụ.

**Gợi ý:** mỗi biến đại diện một bước trong pseudocode.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được operator số học, so sánh và logic.
- [ ] Tôi phân biệt `=` với `==`.
- [ ] Tôi dự đoán đúng `17 / 5`, `17 % 5` và `17.0 / 5.0`.
- [ ] Tôi giải thích được short-circuit.
- [ ] Tôi dùng ngoặc và biến trung gian để code rõ hơn.
- [ ] Tôi biết signed integer overflow không chỉ là “quay vòng”.

Điều hướng:

- Prerequisite: [Bộ nhớ, biến và phạm vi](./04-bo-nho-bien-va-pham-vi.md)
- Bài tiếp theo: [Nhập xuất với stdio](./06-nhap-xuat-voi-stdio.md)
