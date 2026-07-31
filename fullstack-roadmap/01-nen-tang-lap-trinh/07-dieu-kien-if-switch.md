# Điều kiện với if và switch

## 1. Mục tiêu

Sau bài này, bạn có thể:

- rẽ nhánh bằng `if`, `else if`, `else`;
- chọn một trường hợp rời rạc bằng `switch`;
- dùng `break` để kết thúc một `case`;
- validate input trước khi chuyển đổi;
- chọn cấu trúc điều kiện phù hợp với bài toán.

## 2. Bài toán mở đầu

Máy bán vé nhận một ký tự:

- `1`: vé thường, `50000` VND;
- `2`: vé sinh viên, `30000` VND;
- `3`: vé trẻ em, `20000` VND.

Input khác phải bị từ chối, không được âm thầm tạo giá. Với input `2`, chương trình phải in đúng loại vé và giá.

## 3. Lời giải bằng code

Tạo file `ticket.c`:

```c
#include <stdio.h>

int main(void)
{
    printf("Chon ve (1-3): ");
    int choice = getchar();

    /* Từ chối input ngoài contract trước khi tính bất kỳ mức giá nào. */
    if (choice < '1' || choice > '3') {
        fprintf(stderr, "Lua chon khong hop le.\n");
        return 1;
    }

    int price = 0;

    switch (choice) {
    case '1':
        printf("Loai ve: Thuong\n");
        price = 50000;
        break;
    case '2':
        printf("Loai ve: Sinh vien\n");
        price = 30000;
        break;
    case '3':
        printf("Loai ve: Tre em\n");
        price = 20000;
        break;
    default:
        fprintf(stderr, "Loi logic khong mong doi.\n");
        return 2;
    }

    if (price >= 50000) {
        printf("Nhom gia: Cao\n");
    } else if (price >= 30000) {
        printf("Nhom gia: Trung binh\n");
    } else {
        printf("Nhom gia: Thap\n");
    }

    printf("Gia: %d VND\n", price);
    return 0;
}
```

Compile và kiểm tra input `2`:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror ticket.c -o ticket
printf '2\n' | ./ticket
```

Output:

```text
Chon ve (1-3): Loai ve: Sinh vien
Nhom gia: Trung binh
Gia: 30000 VND
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`; input `x` trả exit status `1` và ghi lỗi vào `stderr`.

## 4. Giải thích cơ chế

### 4.1. `if` chỉ chạy block khi điều kiện đúng

```c
if (choice < '1' || choice > '3') {
    ...
}
```

Điều kiện đúng khi ký tự nằm ngoài range. `return 1` kết thúc `main` ngay, nên phần tính giá không chạy với input sai. Đây là **guard clause**: từ chối trạng thái không hợp lệ sớm.

### 4.2. Chuỗi `if` / `else if` / `else`

Các điều kiện được thử từ trên xuống. Chỉ block đầu tiên có điều kiện đúng được chạy; `else` nhận mọi trường hợp còn lại.

Thứ tự quan trọng: kiểm tra `>= 50000` trước `>= 30000`. Đảo lại sẽ phân loại `50000` vào nhóm trung bình rồi dừng.

### 4.3. `switch` chọn theo một giá trị

`switch (choice)` so giá trị với từng nhãn `case`. `break` thoát khỏi `switch`. Nếu bỏ `break`, execution tiếp tục sang case sau; đó gọi là fallthrough và thường gây bug nếu không có chủ ý.

`default` là hàng rào phòng thủ. Guard phía trên đã giới hạn `choice`, nên nhánh này không dự kiến xảy ra; giữ nó giúp code rõ invariant và an toàn khi được sửa về sau.

## 5. Kiến thức nền

### Truth trong C

Trong vị trí điều kiện:

- `0` là false;
- giá trị khác `0` là true.

Các operator so sánh và logic tạo `0` hoặc `1`. Dùng biểu thức thể hiện ý định, thay vì so sánh thừa như `if (valid == true)`.

### Khi dùng `if`, khi dùng `switch`?

- Dùng `if` cho range, nhiều điều kiện kết hợp, hoặc nhánh dựa trên biểu thức khác nhau.
- Dùng `switch` khi so cùng một giá trị integer/character với các lựa chọn rời rạc.

`switch` không biểu diễn trực tiếp `price >= 30000`.

### Block luôn có dấu ngoặc

C cho phép bỏ `{}` khi chỉ có một statement. Bộ tài liệu vẫn dùng block đầy đủ để việc thêm dòng sau này không vô tình nằm ngoài điều kiện.

### Error output và exit status

`fprintf(stderr, ...)` có format giống `printf` nhưng ghi vào standard error. Exit status khác `0` cho script gọi biết chương trình thất bại, ngay cả khi text lỗi bị chuyển hướng.

## 6. Lỗi thường gặp

### Dùng `=` trong điều kiện

`if (choice = '1')` gán rồi xét giá trị, không so sánh. Dùng `==`.

### Quên `break`

Case tiếp theo chạy ngoài ý muốn. Chỉ dùng fallthrough khi thật cần và comment rõ.

### Xếp range sai thứ tự

Kiểm tra điều kiện rộng trước làm nhánh hẹp không bao giờ tới. Đi từ điều kiện cụ thể/cao hơn phù hợp logic.

### Không xử lý `EOF`

`EOF` cũng nằm ngoài `'1'..'3'`, nên sample từ chối đúng. Với thông báo production, nên phân biệt hết input với ký tự sai.

### Không có đường thất bại

In lỗi nhưng vẫn `return 0` khiến automation hiểu nhầm thành công. Trả status khác `0`.

### Lồng `if` quá sâu

Validate và return sớm; tách hàm sau khi học bài 09.

## 7. Bài tập

### Bài 1 — Chẵn/lẻ

Dùng `if/else` in một số cố định là chẵn hay lẻ.

**Gợi ý:** dùng `% 2`.

### Bài 2 — Xếp loại điểm

Phân loại điểm `0–100` thành A/B/C/D/F và từ chối ngoài range.

**Gợi ý:** validate trước, rồi kiểm tra từ ngưỡng cao xuống thấp.

### Bài 3 — Menu bốn phép tính

Dùng `switch` với ký tự `+`, `-`, `*`, `/` trên hai số cố định.

**Gợi ý:** ở case `/`, bảo vệ mẫu số khác `0`.

### Bài 4 — Test lỗi

Chạy sample với `1`, `3`, `x` và input rỗng; ghi output cùng exit status.

**Gợi ý:** dùng `echo $?` ngay sau mỗi lần chạy.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được guard clause bằng `if`.
- [ ] Tôi sắp xếp đúng chuỗi `else if`.
- [ ] Tôi dùng `switch`, `case`, `break`, `default`.
- [ ] Tôi giải thích truth trong C.
- [ ] Tôi ghi lỗi ra `stderr` và trả status thất bại.
- [ ] Tôi biết khi nào `if` rõ hơn `switch`.

Điều hướng:

- Prerequisite: [Nhập xuất với stdio](./06-nhap-xuat-voi-stdio.md)
- Bài tiếp theo: [Vòng lặp for, while và do-while](./08-vong-lap-for-while-do-while.md)
