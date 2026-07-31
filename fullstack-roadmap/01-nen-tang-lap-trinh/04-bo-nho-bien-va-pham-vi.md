# Bộ nhớ, biến và phạm vi

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt tên biến, giá trị hiện tại, storage và scope;
- dự đoán kết quả khi gán một biến số sang biến khác;
- đọc block scope tạo bởi `{ ... }`;
- phân biệt lifetime của biến trong block ngoài và block lồng;
- vẽ mô hình storage logic của `main` mà không đoán địa chỉ vật lý.

## 2. Bài toán mở đầu

Một quầy thu ngân giữ số dư ban đầu `500`. Trước khi trừ giao dịch `120`, chương trình lưu một bản chụp vào `before_payment`. Sau đó một block kiểm tra tạm tính phí `30`.

Ta cần trả lời chính xác:

1. Sửa `balance` có làm `before_payment` đổi theo không?
2. Biến `temporary_fee` dùng được ngoài block không?
3. Khi block kết thúc, storage nào còn sống?

Đây là câu hỏi về copy, scope và lifetime, không chỉ là phép tính.

## 3. Lời giải bằng code

Tạo file `scope.c`:

```c
#include <stdio.h>

int main(void)
{
    int balance = 500;

    /* before_payment nhận một bản sao; nó không đổi theo balance về sau. */
    int before_payment = balance;

    balance = balance - 120;

    printf("Truoc giao dich: %d\n", before_payment);
    printf("Sau giao dich: %d\n", balance);

    {
        int temporary_fee = 30;
        int projected_balance = balance - temporary_fee;

        printf("Phi tam tinh: %d\n", temporary_fee);
        printf("So du tam tinh: %d\n", projected_balance);
    }

    printf("So du chinh thuc: %d\n", balance);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror scope.c -o scope
./scope
```

Output:

```text
Truoc giao dich: 500
Sau giao dich: 380
Phi tam tinh: 30
So du tam tinh: 350
So du chinh thuc: 380
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

## 4. Giải thích cơ chế

### 4.1. Gán số tạo một bản sao giá trị

Sau hai lệnh đầu:

```c
int balance = 500;
int before_payment = balance;
```

mô hình logic là:

```text
storage của balance        chứa 500
storage của before_payment chứa 500
```

`before_payment = balance` đọc giá trị `500`, rồi chép giá trị đó vào storage riêng của `before_payment`. Không có liên kết tự động giữa hai biến.

Sau:

```c
balance = balance - 120;
```

ta có:

```text
balance        = 380
before_payment = 500
```

Vế phải dùng giá trị cũ của `balance` để tính `380`; sau đó `380` thay giá trị trong storage của chính `balance`.

### 4.2. Block tạo scope

Tại block lồng:

```text
scope của main
├── balance
├── before_payment
└── block lồng
    ├── temporary_fee
    └── projected_balance
```

Code trong block lồng nhìn thấy biến của scope ngoài, nên dùng được `balance`. Code ngoài block không nhìn thấy `temporary_fee` hay `projected_balance`; thử đọc chúng sau `}` sẽ gây compile error.

### 4.3. Lifetime của local variable

Một cách mô hình hóa lần gọi `main`:

```text
main đang chạy

logical storage của lần gọi main
┌──────────────────────────────┐
│ balance = 380                │
│ before_payment = 500         │
│                              │
│ khi đang ở block lồng:       │
│ temporary_fee = 30           │
│ projected_balance = 350      │
└──────────────────────────────┘
```

Khi rời block lồng, lifetime của hai biến trong block kết thúc. Khi `main` trả về, lifetime của các local còn lại kết thúc.

Mô hình gọi hàm thường được triển khai bằng **call stack**, nhưng compiler có thể đặt một local trong register hoặc tối ưu bỏ storage vật lý nếu hành vi không đổi. Vì vậy sơ đồ trên mô tả state và lifetime quan sát được, không khẳng định địa chỉ byte cụ thể. Call stack được học kỹ ở bài 10; địa chỉ và pointer ở module 02.

### 4.4. Scope không đồng nghĩa lifetime trong mọi trường hợp

Với các local đơn giản ở bài này, scope và lifetime đi gần nhau:

- scope quyết định tên dùng được ở phần source nào;
- lifetime quyết định object/storage tồn tại trong thời gian nào.

Đây là hai khái niệm khác nhau. Ở module 02, storage duration và object được cấp phát động sẽ cho thấy lifetime có thể không trùng block scope.

## 5. Kiến thức nền

### Declaration, definition và assignment trong phạm vi bài

```c
int balance = 500;        /* khai báo biến và khởi tạo */
balance = balance - 120;  /* assignment vào biến đã tồn tại */
```

Khởi tạo tạo giá trị đầu tiên cho object. Assignment thay giá trị của object còn sống.

### Shadowing

C cho phép block trong khai báo một tên trùng tên ở block ngoài:

```c
int count = 1;
{
    int count = 2;
    printf("%d\n", count);
}
```

Tên trong che tên ngoài ở phạm vi đó. Đây là hợp lệ nhưng dễ làm người đọc hiểu sai storage nào đang được cập nhật. Trong code production, ưu tiên tên khác khi hai biến có vai trò khác.

### Automatic storage duration

Các local thông thường trong block như ví dụ có automatic storage duration. Storage của chúng được tạo khi execution đi vào block tương ứng và không còn tồn tại khi rời block. Chi tiết đầy đủ về storage duration sẽ học ở module 02.

### Tên không phải là “chiếc hộp vĩnh viễn”

Tên chỉ có ý nghĩa trong source scope. Compiler biến thao tác trên tên thành thao tác phù hợp trên register/memory. Đừng suy ra địa chỉ hoặc kích thước stack chỉ từ số tên biến trong source.

## 6. Lỗi thường gặp

### Nghĩ phép gán tạo liên kết

Với các số trong bài, phép gán copy giá trị. Thay đổi biến nguồn về sau không tự cập nhật biến đích.

### Dùng biến ngoài scope

`printf("%d", temporary_fee);` sau dấu `}` của block không compile. Nếu dữ liệu phải dùng tiếp, khai báo nó trong scope đủ rộng; không mở rộng scope mọi biến “cho tiện”.

### Khai báo lại cùng tên trong cùng block

Hai declaration `int balance` trong cùng một block xung đột. Assignment lần sau không viết lại type.

### Shadowing ngoài ý muốn

Khai báo `int balance` mới trong block khiến assignment tác động storage mới, không phải biến ngoài. Dùng tên riêng rõ vai trò.

### Đọc giá trị không xác định

Scope hợp lệ không đảm bảo biến đã được khởi tạo. `int fee;` rồi đọc `fee` vẫn sai.

### Đồng nhất local với stack byte cố định

Call stack là mô hình quan trọng, nhưng optimization có thể dùng register hoặc bỏ biến. Hãy nói “local có automatic lifetime trong lần gọi” trước khi khẳng định vị trí vật lý.

## 7. Bài tập

### Bài 1 — Dự đoán bản sao

Tạo `original = 40`, `copy = original`, sau đó đổi `original = 70`. Viết output dự đoán trước khi chạy.

**Gợi ý:** vẽ hai dòng storage riêng.

### Bài 2 — Block giảm giá

Tạo `price = 100`; trong block tính `discount = 20` và `final_price`; ngoài block in lại `price`.

**Gợi ý:** phép tính tạm không cần thay `price`.

### Bài 3 — Tìm compile error về scope

Thử in `projected_balance` sau block trong sample, đọc diagnostic rồi hoàn tác.

**Gợi ý:** compiler thường nói identifier undeclared.

### Bài 4 — Khảo sát shadowing

Tạo một `score` ở scope ngoài và một `score` khác trong block; in cả trong và sau block rồi vẽ storage.

**Gợi ý:** đây là demo để hiểu cơ chế, không phải cách đặt tên nên dùng trong production.

### Bài 5 — Audit lifetime

Đánh dấu trên source thời điểm bắt đầu và kết thúc lifetime của từng local trong sample.

**Gợi ý:** theo dấu `{` và `}` của block chứa declaration.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt tên, giá trị và storage của biến.
- [ ] Tôi biết assignment giữa các số tạo bản sao giá trị.
- [ ] Tôi xác định được scope theo block.
- [ ] Tôi chỉ ra được local nào còn sống tại mỗi điểm trong sample.
- [ ] Tôi vẽ được storage logic mà không khẳng định địa chỉ vật lý.
- [ ] Tôi phân biệt scope với lifetime.

Điều hướng:

- Prerequisite: [Biến, hằng số và kiểu dữ liệu](./03-bien-hang-so-kieu-du-lieu.md)
- Bài tiếp theo: [Toán tử và biểu thức](./05-toan-tu-va-bieu-thuc.md)
