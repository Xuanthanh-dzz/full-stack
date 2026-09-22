# Bộ nhớ, biến và phạm vi

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Scope quyết định nơi dùng được tên; vòng đời quyết định khoảng thời gian object tồn tại.
- Dùng để xác định biến nào đang được đọc/sửa và khi nào state hết hiệu lực.
- Copy giá trị không tạo liên kết; sơ đồ local không bảo đảm layout vật lý trên stack.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt tên biến, giá trị hiện tại, storage và scope;
- dự đoán kết quả khi gán một biến số sang biến khác;
- đọc block scope tạo bởi `{ ... }`;
- phân biệt lifetime của biến trong block ngoài và block lồng;
- vẽ mô hình storage logic của `main` mà không đoán địa chỉ vật lý.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Chụp một con số vào giấy khác rồi sửa bản gốc thì bản chụp không đổi. Block giống một khu vực chỉ cho dùng một số tên bên trong; rời khu vực, tên tạm không dùng tiếp được. Điều này giúp việc tính thử không làm thay đổi số dư chính thức.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| scope | phần source được phép dùng một tên | block chứa temporary_fee |
| vòng đời | thời gian object còn tồn tại | từ lúc vào đến lúc ra block của local thường |
| storage | chỗ giữ giá trị của object | balance và before_payment riêng |
| shadowing | tên bên trong che tên ngoài | hai biến cùng tên trong hai block |

### Ví dụ nhỏ — tính tay trước

a = 10; b nhận giá trị a; a đổi thành 20 → a là 20, b vẫn 10. Đó là hai object chứa hai số, không phải hai tên của cùng một số.

Một quầy thu ngân giữ số dư ban đầu `500`. Trước khi trừ giao dịch `120`, chương trình lưu một bản chụp vào `before_payment`. Sau đó một block kiểm tra tạm tính phí `30`.

Ta cần trả lời chính xác:

1. Sửa `balance` có làm `before_payment` đổi theo không?
2. Biến `temporary_fee` dùng được ngoài block không?
3. Khi block kết thúc, storage nào còn sống?

Đây là câu hỏi về copy, scope và lifetime, không chỉ là phép tính.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. balance nhận 500; before_payment sao chép 500.
2. Trừ 120 chỉ thay balance thành 380.
3. Block trong giữ temporary_fee=30 và projected_balance=350; nó chỉ đọc balance.
4. Ra block, các local tạm hết vòng đời; main vẫn giữ balance=380. Chi phí là vài phép tính và số local cố định; compiler có thể dùng thanh ghi thay chỗ nhớ vật lý.

### Mini-check

Nếu gán balance = projected_balance bên trong block, giá trị nào còn sau dấu }?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Scope | quy tắc dùng tên trong source | compiler kiểm tra; không mô tả toàn bộ thời gian tồn tại |
| Vòng đời | quy tắc object còn tồn tại lúc chạy | cần biết khi giữ cách truy cập; sâu hơn ở Module 02 |
| Bản sao số | object khác nhận cùng giá trị | tốn storage riêng; không dùng nếu yêu cầu cập nhật cùng state |

### Misconception check

**Đúng hay sai?** Sửa balance sẽ cập nhật before_payment.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phép gán số sao chép giá trị.

</details>

**Đúng hay sai?** Mỗi tên local chắc chắn chiếm một ô stack vật lý.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: compiler có thể dùng thanh ghi hoặc tối ưu bỏ storage.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** copy số và block scope.

- **Working Developer — dùng khi làm việc:** thu hẹp state và tránh shadowing.

- **Deep Dive — có thể quay lại sau:** phân biệt mô hình logic với bố trí của compiler.

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

## 7. Khi nào KHÔNG dùng

Không mở scope mọi biến lên toàn chương trình để dùng cho tiện. Giữ biến gần đoạn cần nó; với phép tính tạm, block nhỏ giảm nhầm state. Tránh shadowing khi hai biến có vai trò khác, dù C cho phép.

## 8. Production notes & scale check

Một quầy nhỏ chỉ cần state local cho phép tính một hóa đơn. Khi state phải sống qua nhiều thao tác, xác định chủ sở hữu trước khi mở rộng vòng đời. Debug bằng breakpoint trước/sau assignment và quan sát đúng scope; nhiều người dùng đồng thời cần bài toán state khác, không chữa bằng biến toàn cục.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Module 02 sẽ cho hàm giữ cách truy cập dữ liệu. Trước khi học cú pháp đó, hãy quyết định: phí tạm cần tồn tại sau phép tính hay chỉ trả kết quả số? Nêu lợi ích của trả bản sao thay vì giữ state tạm lâu hơn.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ hai object sau phép gán số.
2. Scope khác vòng đời ở câu hỏi nào?
3. Tại sao số dư chính thức vẫn là 380?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi phân biệt tên, giá trị và storage của biến.
- [ ] Tôi biết assignment giữa các số tạo bản sao giá trị.
- [ ] Tôi xác định được scope theo block.
- [ ] Tôi chỉ ra được local nào còn sống tại mỗi điểm trong sample.
- [ ] Tôi vẽ được storage logic mà không khẳng định địa chỉ vật lý.
- [ ] Tôi phân biệt scope với lifetime.

Điều hướng:

- Prerequisite: [Biến, hằng số và kiểu dữ liệu](./03-bien-hang-so-kieu-du-lieu.md)
- Bài tiếp theo: [Toán tử và biểu thức](./05-toan-tu-va-bieu-thuc.md)
