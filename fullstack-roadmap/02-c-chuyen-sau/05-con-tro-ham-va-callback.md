# Con trỏ hàm và callback

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Con trỏ hàm chọn một hàm có chữ ký phù hợp để gọi trong quá trình xử lý.
- Dùng khi thuật toán chung cần nhận một chính sách nhỏ thay đổi được.
- Callback không tự tạo thread; chữ ký, NULL và contract kết quả vẫn phải kiểm tra.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- lưu địa chỉ của một hàm trong function pointer;
- truyền function pointer làm callback cho một hàm khác;
- đọc khai báo `int (*rule)(int)`;
- kiểm tra callback `NULL` trước khi gọi;
- nhận ra khi callback giúp tách phần ổn định khỏi chính sách có thể thay đổi.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Cùng một nhân viên tính tiền, nhưng cửa hàng đưa quy tắc “giá thường” hoặc “giảm 10%”. Người tính gọi quy tắc được đưa vào, không phải biết trước mọi lựa chọn. Con trỏ hàm giữ cách chọn quy tắc đó.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| chữ ký hàm | kiểu trả về và các kiểu tham số | cùng contract tính tổng |
| function pointer | giá trị dùng để gọi một hàm phù hợp kiểu | chính sách tính giá |
| callback | hàm được truyền vào để bên nhận gọi | regular hoặc discount |
| synchronous | lời gọi hoàn tất trước khi chạy lệnh tiếp theo | callback chạy ngay trong phép tính |

### Ví dụ nhỏ — tính tay trước

Giá 1000, số lượng 2: chọn regular → 2000; chọn ten-percent → 1800. Input giống nhau; hàm được chọn khác nhau. Caller vẫn đợi callback trả về mới in kết quả.

Quy trình tính tiền luôn giống nhau:

1. nhận đơn giá;
2. áp dụng chính sách giá;
3. nhân với số lượng.

Nhưng chính sách giá có thể là giữ nguyên hoặc giảm 10%. Ta không muốn chép lại toàn bộ hàm tính tổng cho mỗi chính sách. Thay vào đó, hàm tính tổng nhận một callback: địa chỉ của hàm thực hiện chính sách.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. main chọn function pointer và truyền dữ liệu 1000 × 3 cho hàm tính.
2. calculate_line_total kiểm tra price_rule và miền dữ liệu trước lời gọi gián tiếp; không có output parameter.
3. Regular cho 3000; ten-percent cho 2700; price_rule NULL trả -1 báo lỗi thay vì gọi địa chỉ rỗng.
4. Callback chạy trên cùng luồng gọi của chương trình này. print_total nhận giá trị trả về vào total, biến tạm ở từng lời gọi; số phép toán cố định, không có hàng đợi hay chạy nền.

### Mini-check

Tại dòng in tổng, callback trong sample còn đang chạy không? Dòng code nào chứng minh thứ tự?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Gọi trực tiếp | hàm được viết rõ tại nơi gọi | đơn giản nhất cho một chính sách |
| if/switch | chọn giữa vài nhánh đã biết | dễ theo dõi với ít lựa chọn; tránh kéo dài vô hạn |
| Callback | caller đưa hành vi cùng chữ ký | thêm gián tiếp và contract; dùng khi cần thay chính sách, không để tạo abstraction vô cớ |

### Misconception check

**Đúng hay sai?** Callback nghĩa là hàm chạy sau trên một thread khác.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample gọi đồng bộ; lịch chạy do bên nhận quyết định.

</details>

**Đúng hay sai?** Ép kiểu function pointer làm mọi chữ ký gọi được an toàn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: gọi qua kiểu không tương thích có thể gây undefined behavior.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** gọi được hàm qua pointer.

- **Working Developer — dùng khi làm việc:** kiểm tra policy và miền số.

- **Deep Dive — có thể quay lại sau:** cân nhắc indirection sau khi có nhu cầu mở rộng.

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

## 7. Khi nào KHÔNG dùng

Không thêm callback cho một phép nhân cố định chỉ có một người dùng. Không thiết kế cơ chế plugin khi hai nhánh if đã đủ và không có yêu cầu thay chính sách độc lập.

## 8. Production notes & scale check

Team nhỏ với hai chính sách cần kiểm tra output, tràn số, NULL và quy tắc làm tròn. Phần giảm giá dùng số nguyên, không ngầm hứa độ chính xác thập phân tùy ý. Cost chính hiện là I/O, không phải một lời gọi gián tiếp; chỉ tối ưu sau khi đo.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Module 01 dùng switch để chọn thao tác. So sánh switch với callback cho hai chính sách giá ít thay đổi: chọn cách dễ bảo trì nhất, nêu driver nào khiến bạn đổi lựa chọn sau này.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vì sao chữ ký callback phải khớp?
2. Trace thứ tự main → tính → callback → in.
3. Một callback được phép báo lỗi bằng cách nào trong contract mẫu?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi đọc đúng khai báo `int (*rule)(int)`.
- [ ] Tôi hiểu function pointer chứa địa chỉ hàm, không chứa kết quả hàm.
- [ ] Tôi kiểm tra `NULL` trước khi gọi callback.
- [ ] Tôi không cast để ghép các chữ ký không tương thích.
- [ ] Tôi biết callback trong ví dụ chạy đồng bộ.

**Bài prerequisite:** [Con trỏ cấp hai](./04-con-tro-cap-hai.md)

**Bài tiếp theo:** [Stack, heap và vòng đời bộ nhớ](./06-stack-heap-va-vong-doi-bo-nho.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/01-doi-pointer-khong-doi-caller.md) · [Spaced Review](./reviews/review-01-pointer-va-contract.md).
