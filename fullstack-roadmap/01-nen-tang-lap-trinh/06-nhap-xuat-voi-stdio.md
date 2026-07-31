# Nhập xuất với stdio

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt standard input, standard output và standard error;
- dùng `printf`, `putchar` và `getchar`;
- đọc một ký tự rồi chuyển chữ số ASCII thành giá trị số;
- giải thích vì sao input luôn cần quy tắc hợp lệ;
- nhận biết giới hạn của chương trình chưa có validation.

## 2. Bài toán mở đầu

Quầy nước không muốn sửa source mỗi khi số cốc thay đổi. Người dùng sẽ gõ một chữ số từ `0` đến `9`; mỗi cốc giá `15000` VND. Với input `4`, chương trình in:

```text
Nhap so coc (0-9): 4
So coc: 4
Tong tien: 60000 VND
```

Bài này chỉ đọc **một ký tự**. Kiểm tra input sai cần điều kiện và sẽ được bổ sung ngay ở bài 07.

## 3. Lời giải bằng code

Tạo file `drink_order.c`:

```c
#include <stdio.h>

int main(void)
{
    const int unit_price = 15000;

    printf("Nhap so coc (0-9): ");

    /* Giữ kết quả ở int để type còn biểu diễn được giá trị đặc biệt EOF. */
    int input_character = getchar();

    int quantity = input_character - '0';
    int total = quantity * unit_price;

    printf("So coc: %d\n", quantity);
    printf("Tong tien: %d VND\n", total);

    return 0;
}
```

Compile rồi chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror drink_order.c -o drink_order
printf '4\n' | ./drink_order
```

Output:

```text
Nhap so coc (0-9): So coc: 4
Tong tien: 60000 VND
```

Khi chạy tương tác, ký tự `4` do terminal echo sẽ xuất hiện ngay sau prompt. Pipeline kiểm thử không echo input, nên output kiểm chứng ở trên không chứa dòng echo. Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

## 4. Giải thích cơ chế

### 4.1. Ba standard stream

Khi chương trình bắt đầu, môi trường thường cung cấp:

```text
standard input  (stdin)  --> dữ liệu chương trình đọc
standard output (stdout) <-- kết quả thông thường
standard error  (stderr) <-- diagnostic/lỗi
```

Terminal có thể là nguồn/đích, nhưng shell cũng có thể nối stream với file hoặc chương trình khác. Pipeline `printf '4\n' | ./drink_order` đưa text bên trái vào standard input của chương trình.

### 4.2. `getchar` trả mã của một ký tự

```c
int input_character = getchar();
```

`getchar()` đọc ký tự kế tiếp từ `stdin` và trả mã ký tự dưới dạng `int`. Nó dùng `int`, không dùng `char`, vì còn cần biểu diễn giá trị đặc biệt `EOF` khi hết input hoặc có lỗi.

Trong bộ mã ký tự mà C hỗ trợ, các chữ số `'0'` đến `'9'` có mã liên tiếp. Vì vậy:

```c
int quantity = input_character - '0';
```

đổi ký tự `'4'` thành số `4`.

### 4.3. Output có format và output một ký tự

`printf` tạo output theo format như các bài trước. Khi chỉ cần ghi một ký tự, có thể dùng:

```c
putchar('A');
putchar('\n');
```

`putchar` cũng trả một `int` để báo thành công hoặc lỗi. Bài đầu về I/O chưa xử lý lỗi ghi; code production cần kiểm tra khi output là dữ liệu quan trọng.

## 5. Kiến thức nền

### Input là byte/ký tự trước khi thành dữ liệu nghiệp vụ

Người dùng nghĩ họ nhập “số 4”; `getchar` đọc ký tự `'4'`. Chương trình phải:

1. đọc representation;
2. kiểm tra representation có hợp lệ;
3. chuyển thành type cần dùng;
4. kiểm tra range nghiệp vụ.

Sample mới minh họa bước 1 và 3 với giả định input hợp lệ.

### Newline vẫn là input

Khi người dùng gõ `4` rồi Enter, stream thường chứa `'4'` và `'\n'`. Sample chỉ gọi `getchar` một lần nên newline chưa được đọc. Chương trình dài hơn phải tiêu thụ phần còn lại có chủ đích; bài 08 dùng vòng lặp để làm việc đó.

### `EOF`

`EOF` là macro từ `<stdio.h>`, báo không còn ký tự để đọc hoặc lỗi đọc. Không được đổi kết quả `getchar()` sang `char` trước khi so sánh `EOF`, vì có thể mất giá trị phân biệt.

### Vì sao chưa dùng `scanf`?

`scanf` ghi dữ liệu vào storage của biến và đòi hỏi hiểu địa chỉ, format, phần input còn dư. Pointer được dạy ở module 02. Tuyến học này dùng `getchar` và sau đó mảng ký tự để validation được nhìn thấy rõ, thay vì đưa `&variable` như một công thức chưa hiểu.

## 6. Lỗi thường gặp

### Nhập chữ nhưng vẫn trừ `'0'`

Nếu input là `'x'`, phép trừ vẫn tạo một integer nhưng không phải số lượng hợp lệ. Bài 07 sẽ kiểm tra range ký tự trước conversion.

### Dùng `'4'` và `4` như nhau

`'4'` là mã ký tự; `4` là giá trị số. Conversion trong sample nối hai representation này.

### Dùng `char` để nhận `getchar`

Như vậy có thể không phân biệt được mọi byte hợp lệ với `EOF`. Luôn lưu kết quả vào `int` trước.

### Prompt không xuất hiện ngay

Khi output không nối terminal, buffering có thể giữ prompt chưa có newline. Có thể gọi `fflush(stdout)` trước thao tác đọc; API này sẽ được dùng khi cần trong project.

### Cho rằng pipeline giống terminal echo

Terminal tương tác thường echo phím; pipe không làm vậy. Hãy so sánh các dòng chương trình thực sự ghi, không nhầm echo thành output của code.

## 7. Bài tập

### Bài 1 — Đọc một chữ số khác

Chạy chương trình với các input `0`, `5`, `9` và dự đoán tổng tiền.

**Gợi ý:** dùng `printf '5\n' | ./drink_order`.

### Bài 2 — In ký tự

Đọc một ký tự rồi dùng `putchar` in lại ký tự đó trên một dòng.

**Gợi ý:** kết quả `getchar` là `int`, nhưng `putchar` nhận giá trị đó.

### Bài 3 — Quan sát newline

Gọi `getchar` hai lần, in mã của hai kết quả khi input là `4\n`.

**Gợi ý:** newline thường có mã `10`, nhưng hãy tin kết quả môi trường.

### Bài 4 — Quan sát `EOF`

Chạy `./drink_order < /dev/null` và ghi nhận kết quả bất hợp lý hiện tại.

**Gợi ý:** chưa sửa bằng `if`; mục đích là chứng minh input phải validate.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt stdin, stdout và stderr.
- [ ] Tôi đọc một ký tự bằng `getchar`.
- [ ] Tôi giải thích được vì sao `getchar` trả `int`.
- [ ] Tôi đổi được ký tự chữ số thành giá trị số.
- [ ] Tôi biết newline còn lại trong stream.
- [ ] Tôi không coi sample chưa validation là production-ready.

Điều hướng:

- Prerequisite: [Toán tử và biểu thức](./05-toan-tu-va-bieu-thuc.md)
- Bài tiếp theo: [Điều kiện if và switch](./07-dieu-kien-if-switch.md)
