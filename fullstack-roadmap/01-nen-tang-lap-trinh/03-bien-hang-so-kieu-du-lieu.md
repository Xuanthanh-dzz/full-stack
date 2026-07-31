# Biến, hằng số và kiểu dữ liệu

## 1. Mục tiêu

Sau bài này, bạn có thể:

- khai báo, khởi tạo, đọc và cập nhật một biến;
- dùng `const` cho giá trị không được thay đổi;
- chọn `int`, `double`, `char` và `bool` cho dữ liệu cơ bản;
- dùng đúng format phổ biến của `printf`;
- nhận ra conversion có thể làm mất dữ liệu.

## 2. Bài toán mở đầu

Kho còn `24` hộp. Một đơn hàng lấy đi `7` hộp. Chương trình cần giữ lại cả dữ liệu ban đầu lẫn kết quả để in:

```text
Ma kho: A
Ton dau: 24
Da xuat: 7
Ton cuoi: 17
Ty le con lai: 70.83%
Con hang: 1
```

Nếu ghi thẳng mọi con số vào `printf`, mỗi thay đổi phải sửa ở nhiều nơi. Ta cần đặt tên cho dữ liệu và để máy tính kết quả.

## 3. Lời giải bằng code

Tạo file `inventory.c`:

```c
#include <stdbool.h>
#include <stdio.h>

int main(void)
{
    const char warehouse_code = 'A';
    const int opening_stock = 24;
    const int shipped = 7;

    int remaining = opening_stock - shipped;

    /* Cast trước phép chia để không mất phần thập phân. */
    double remaining_rate = (double)remaining / opening_stock * 100.0;
    bool in_stock = remaining > 0;

    printf("Ma kho: %c\n", warehouse_code);
    printf("Ton dau: %d\n", opening_stock);
    printf("Da xuat: %d\n", shipped);
    printf("Ton cuoi: %d\n", remaining);
    printf("Ty le con lai: %.2f%%\n", remaining_rate);
    printf("Con hang: %d\n", in_stock);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror inventory.c -o inventory
./inventory
```

Output:

```text
Ma kho: A
Ton dau: 24
Da xuat: 7
Ton cuoi: 17
Ty le con lai: 70.83%
Con hang: 1
```

Theo quy ước của C, giá trị `bool` đúng in qua `%d` là `1`, sai là `0`. Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

## 4. Giải thích cơ chế

### 4.1. Khai báo và khởi tạo

```c
int remaining = opening_stock - shipped;
```

Dòng này gồm:

- `int`: kiểu của dữ liệu;
- `remaining`: tên biến;
- `=`: khởi tạo bằng giá trị của expression bên phải;
- expression được tính trước, sau đó kết quả `17` được lưu cho `remaining`.

Một biến nên được khởi tạo ngay khi khai báo. Đọc một local variable chưa được khởi tạo tạo hành vi không xác định; compiler không luôn cứu được bạn.

### 4.2. `const` bảo vệ ý định

```c
const int opening_stock = 24;
```

Sau khi khởi tạo, code không được gán lại `opening_stock`. `const` phù hợp khi giá trị trong lần chạy đó không nên đổi. Nó giúp compiler phát hiện thao tác trái ý định:

```c
/* opening_stock = 30; */ /* Sai: object này là const. */
```

`remaining` không có `const` vì về mặt mô hình nó có thể được cập nhật ở bước sau.

### 4.3. Mỗi type quy định tập giá trị và phép toán

| Type | Dữ liệu trong bài | Format `printf` |
|---|---|---|
| `int` | số hộp nguyên | `%d` |
| `double` | tỷ lệ có phần thập phân | `%f`, ví dụ `%.2f` |
| `char` | một mã ký tự | `%c` |
| `bool` | đúng hoặc sai | `%d` |

`bool`, `true`, `false` được cung cấp qua standard header `<stdbool.h>` trong C11.

Expression `remaining > 0` so sánh hai giá trị: nó tạo `true` khi số
hộp còn lại lớn hơn 0 và `false` trong trường hợp ngược lại. Bài 05 sẽ hệ
thống hóa toàn bộ toán tử so sánh; ở đây quy tắc này đủ để tạo biến
`in_stock`.

### 4.4. Conversion có chủ đích

```c
(double)remaining
```

Đây là cast: tạo giá trị `double` tương ứng với `remaining` cho expression. Nhờ ít nhất một toán hạng là `double`, phép chia giữ phần thập phân:

```text
17 / 24                  -> 0       (chia int)
(double)17 / 24          -> 0.7083... (chia double)
```

Cast không thay type đã khai báo của `remaining`; biến đó vẫn là `int`.

## 5. Kiến thức nền

### Identifier

Tên biến là identifier:

- gồm chữ cái, chữ số và `_`;
- không bắt đầu bằng chữ số;
- phân biệt hoa/thường;
- không được trùng keyword như `int`, `return`;
- nên diễn tả vai trò: `remaining_rate` rõ hơn `x`.

Lộ trình dùng `snake_case` cho tên biến và hàm C.

### Literal

Literal là giá trị viết trực tiếp trong source:

- `24` có type số nguyên phù hợp, trong trường hợp này dùng như `int`;
- `100.0` là `double`;
- `'A'` là character constant;
- `"Ma kho: "` là string literal;
- `true` là giá trị boolean từ `<stdbool.h>`.

Dấu nháy đơn biểu diễn một ký tự; dấu nháy kép biểu diễn chuỗi ký tự.

### Kích thước và miền giá trị

Chuẩn C không bắt buộc `int` luôn có đúng 32 bit trên mọi hệ thống. `<limits.h>` cung cấp `INT_MIN`, `INT_MAX`; `<float.h>` mô tả giới hạn kiểu floating-point. Khi domain có thể vượt giới hạn, phải chọn type và validate phù hợp.

### Số thực không biểu diễn chính xác mọi số thập phân

`double` dùng biểu diễn nhị phân nên nhiều giá trị như `0.1` chỉ được xấp xỉ. Bài này in tỷ lệ với hai chữ số. Với tiền, thường lưu số đơn vị nhỏ nhất bằng integer (ví dụ đồng) thay vì trông chờ so sánh `double` tuyệt đối.

## 6. Lỗi thường gặp

### Dùng biến trước khi khởi tạo

```c
int remaining;
printf("%d\n", remaining); /* Sai. */
```

Hãy gán một giá trị hợp lệ trước lần đọc đầu tiên.

### Nhầm `=` với ý nghĩa “bằng nhau”

Trong khai báo, `=` đưa giá trị vào biến. Operator so sánh bằng `==` sẽ học ở bài 05.

### Dùng sai format

`%d` không dùng cho `double`; `%f` không dùng cho `int`. `printf` là variadic function nên format sai có thể gây hành vi không xác định.

### Quên cast trước phép chia

`double rate = remaining / opening_stock;` thực hiện chia `int` trước rồi mới đổi kết quả sang `double`. Cast một toán hạng trước dấu `/`.

### Gán số thực về `int` và mất phần lẻ

`int value = 3.9;` làm mất phần thập phân. Với cờ hiện tại compiler có thể cảnh báo trong nhiều tình huống; đừng cast chỉ để làm warning biến mất nếu việc mất dữ liệu không có chủ đích.

### Dùng `char` cho cả một tên

`char` giữ một ký tự. Chuỗi ký tự cần một mảng `char`, sẽ học ở bài 13.

## 7. Bài tập

### Bài 1 — Hồ sơ sản phẩm

Khai báo mã khu vực kiểu `char`, số lượng kiểu `int`, giá trung bình kiểu `double` và trạng thái còn hàng kiểu `bool`; in tất cả.

**Gợi ý:** ghép `%c`, `%d`, `%.2f`, `%d` đúng thứ tự argument.

### Bài 2 — Cập nhật tồn kho

Thêm biến `received = 10` và tính tồn cuối bằng tồn đầu cộng nhập, trừ xuất.

**Gợi ý:** chỉ giá trị nào không đổi trong kịch bản mới dùng `const`.

### Bài 3 — Tỷ lệ đã xuất

Tính phần trăm hàng đã xuất với hai chữ số thập phân.

**Gợi ý:** cast `shipped` sang `double` trước phép chia.

### Bài 4 — Khảo sát chia nguyên

In cả `17 / 24` và `(double)17 / 24`; giải thích hai output trước khi chạy.

**Gợi ý:** dùng `%d` cho kết quả đầu và `%.4f` cho kết quả sau.

### Bài 5 — Tìm giới hạn

Include `<limits.h>` rồi in `INT_MIN` và `INT_MAX`.

**Gợi ý:** hai macro này có type tương thích với `%d`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi khai báo và khởi tạo được biến với tên có nghĩa.
- [ ] Tôi biết khi nào dùng `const`.
- [ ] Tôi chọn được `int`, `double`, `char` hoặc `bool` cho dữ liệu đơn giản.
- [ ] Tôi ghép đúng type với format `printf`.
- [ ] Tôi giải thích được vì sao cast phải xảy ra trước phép chia nguyên.
- [ ] Tôi không đọc local variable chưa được khởi tạo.

Điều hướng:

- Prerequisite: [Chương trình C đầu tiên](./02-chuong-trinh-c-dau-tien.md)
- Bài tiếp theo: [Bộ nhớ, biến và phạm vi](./04-bo-nho-bien-va-pham-vi.md)
