# Vòng lặp for, while và do-while

## 1. Mục tiêu

Sau bài này, bạn có thể:

- lặp một số lần biết trước bằng `for`;
- lặp khi điều kiện còn đúng bằng `while`;
- chạy thân ít nhất một lần bằng `do-while`;
- dùng accumulator và counter;
- tránh vòng lặp vô hạn và lỗi lệch một đơn vị.

## 2. Bài toán mở đầu

Một cửa hàng ghi doanh thu theo quy luật demo: ngày 1 là `100`, mỗi ngày sau tăng `20`, trong 5 ngày. Ta cần in từng ngày, tính tổng, rồi đếm ngược thời gian đóng sổ:

```text
Ngay 1: 100
...
Tong: 700
Dong so sau: 3 2 1
So lan kiem tra: 2
```

Viết lặp lại năm lần `printf` khó thay đổi và dễ sai. Vòng lặp biểu diễn phần lặp cùng điều kiện dừng.

## 3. Lời giải bằng code

Tạo file `loops.c`:

```c
#include <stdio.h>

int main(void)
{
    int total = 0;

    for (int day = 1; day <= 5; day++) {
        int revenue = 100 + (day - 1) * 20;

        /* Sau mỗi vòng, total là tổng từ ngày 1 đến ngày hiện tại. */
        total += revenue;
        printf("Ngay %d: %d\n", day, revenue);
    }

    printf("Tong: %d\n", total);

    printf("Dong so sau:");
    int seconds = 3;
    while (seconds > 0) {
        printf(" %d", seconds);
        seconds--;
    }
    printf("\n");

    int checks = 0;
    do {
        checks++;
    } while (checks < 2);
    printf("So lan kiem tra: %d\n", checks);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror loops.c -o loops
./loops
```

Output:

```text
Ngay 1: 100
Ngay 2: 120
Ngay 3: 140
Ngay 4: 160
Ngay 5: 180
Tong: 700
Dong so sau: 3 2 1
So lan kiem tra: 2
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

## 4. Giải thích cơ chế

### 4.1. `for` có ba phần điều khiển

```c
for (int day = 1; day <= 5; day++) {
    ...
}
```

Execution:

```text
khởi tạo day = 1 (một lần)
        |
kiểm tra day <= 5 -- false --> thoát
        |
       true
        v
chạy thân -> day++ -> quay lại kiểm tra
```

`day` có scope trong vòng `for`; sau vòng lặp không dùng được tên này.

### 4.2. Accumulator

`total` bắt đầu bằng phần tử trung hòa của phép cộng là `0`. Mỗi vòng:

```c
total += revenue;
```

Invariant hữu ích: sau ngày `day`, `total` bằng tổng doanh thu từ ngày 1 đến ngày đó.

### 4.3. `while` kiểm tra trước

Nếu `seconds` bắt đầu bằng `0`, thân `while` không chạy. Mỗi iteration phải có tiến triển về điều kiện dừng; ở đây `seconds--`.

### 4.4. `do-while` kiểm tra sau

Thân `do` luôn chạy ít nhất một lần rồi mới xét `checks < 2`. Dấu `;` sau `while (...)` là bắt buộc.

## 5. Kiến thức nền

### Chọn loại vòng lặp

- `for`: số bước hoặc counter rõ.
- `while`: lặp dựa trên trạng thái/điều kiện, có thể không chạy lần nào.
- `do-while`: nghiệp vụ bắt buộc thực hiện một lần trước khi quyết định lặp.

Mọi dạng có thể chuyển đổi, nhưng chọn dạng làm điều kiện dừng dễ thấy nhất.

### `break` và `continue`

- `break` thoát vòng lặp gần nhất.
- `continue` bỏ phần còn lại của iteration hiện tại.

Chúng hữu ích nhưng dùng quá nhiều làm khó chứng minh tiến triển. Trong bài core, ưu tiên điều kiện loop rõ.

### Off-by-one

`day <= 5` tạo các giá trị `1,2,3,4,5`: năm lần. `day < 5` chỉ tạo bốn lần. Luôn liệt kê giá trị đầu/cuối trước khi viết điều kiện.

## 6. Lỗi thường gặp

### Quên cập nhật biến điều khiển

`while (seconds > 0)` mà không giảm `seconds` sẽ không dừng.

### Dấu `;` ngay sau `for` hoặc `while`

`while (condition);` có thân rỗng. Block sau không thuộc loop.

### Sai điểm bắt đầu của accumulator

Tổng bắt đầu `0`; tích thường bắt đầu `1`. Chọn sai làm mọi iteration sai.

### Thay đổi counter trong thân và phần update

Nếu vừa `day++` trong thân vừa ở header, vòng lặp bỏ phần tử. Chỉ có một nơi chịu trách nhiệm tiến triển.

### Dùng `do-while` khi zero iteration là hợp lệ

Nó vẫn chạy một lần. Dùng `while` nếu cần kiểm tra trước.

## 7. Bài tập

### Bài 1 — Tổng 1 đến N

Dùng `for` tính tổng từ `1` đến `10`.

**Gợi ý:** khởi tạo accumulator bằng `0`.

### Bài 2 — Bảng nhân

In bảng nhân 7 từ `7 x 1` đến `7 x 10`.

**Gợi ý:** counter biểu diễn thừa số thứ hai.

### Bài 3 — Đếm chữ số input

Dùng `getchar` và `while` đọc đến newline **hoặc `EOF`**, đếm bao nhiêu
ký tự là `'0'..'9'`.

**Gợi ý:** lưu kết quả `getchar` trong `int`; điều kiện loop phải kiểm
tra cả `character != '\n'` và `character != EOF`.

### Bài 4 — Menu lặp

Dùng `do-while` đọc lựa chọn cho đến khi người dùng gõ `q` hoặc stream
kết thúc bằng `EOF`.

**Gợi ý:** mỗi iteration đọc cả lựa chọn và phần còn lại đến newline
hoặc `EOF`; nếu gặp `EOF`, thoát loop thay vì tiếp tục gọi `getchar`.

### Bài 5 — Tìm off-by-one

Viết hai loop với `< 5` và `<= 5`, in counter rồi giải thích số iteration.

**Gợi ý:** đừng chỉ đếm output; liệt kê miền giá trị.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi chọn được giữa `for`, `while`, `do-while`.
- [ ] Tôi mô tả initialization, condition, body và update.
- [ ] Tôi dùng accumulator đúng giá trị đầu.
- [ ] Tôi chứng minh loop có tiến triển đến điểm dừng.
- [ ] Tôi nhận ra off-by-one.
- [ ] Tôi biết scope của biến khai báo trong `for`.

Điều hướng:

- Prerequisite: [Điều kiện với if và switch](./07-dieu-kien-if-switch.md)
- Bài tiếp theo: [Hàm, tham số và giá trị trả về](./09-ham-tham-so-gia-tri-tra-ve.md)
