# Toán tử và biểu thức

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Biểu thức kết hợp giá trị qua toán tử để tạo kết quả hoặc cập nhật state.
- Dùng để tính tiền, so điều kiện và bảo vệ phép tính cần tiền điều kiện.
- Chia nguyên, overflow và thứ tự đánh giá có thể làm biểu thức nhìn đúng vẫn sai.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng operator số học, so sánh, logic và assignment;
- phân biệt chia nguyên với chia số thực;
- dự đoán thứ tự đánh giá theo precedence cơ bản;
- dùng ngoặc để biểu diễn ý định rõ ràng;
- tránh overflow và side effect khó đọc trong biểu thức.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Tính hóa đơn bằng các dòng trên giấy dễ kiểm tra hơn một chuỗi ký hiệu dài. Mỗi biến trung gian giữ kết quả một bước. Ngoặc cho biết cách nhóm phép toán, nhưng không tự làm kiểu số rộng hơn hoặc bảo đảm mọi hàm con chạy từ trái sang phải.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| toán tử | ký hiệu thực hiện phép tính | *, >=, && |
| biểu thức | các giá trị và toán tử tạo kết quả | quantity * unit_price |
| short-circuit | dừng xét logic khi đã biết kết quả | && bỏ vế phải nếu trái sai |
| overflow | kết quả vượt miền type | nhân int quá lớn |
| side effect | tác động ngoài giá trị kết quả | assignment hoặc tăng biến |

### Ví dụ nhỏ — tính tay trước

3 × 120 = 360; trừ 20 còn 340; 340 >= 300 đúng nên phí 15 không cộng. Nếu lượng bằng 0, quy tắc hợp lệ phải báo sai, dù tổng số học vẫn tính được.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. subtotal nhận 360000 từ phép nhân int.
2. discounted_total nhận 340000; phép so sánh tạo điều kiện đúng.
3. !has_free_shipping cho 0 nên phần phí bằng 0; payable nhận 340000.
4. valid_order kiểm tra các ràng buộc; stdout nhận các kết quả. CPU và local trong process chịu chi phí, chưa có truy cập mạng hay lưu file.

### Mini-check

Vì sao điều kiện count != 0 phải đứng trước total / count trong một chuỗi &&?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| = | gán giá trị | thay state; không dùng để so bằng |
| == | so sánh bằng | không tự sửa state; dùng trong điều kiện |
| && | logic và có short-circuit | bảo vệ vế phải; không thay bằng & để viết ngắn |
| Ngoặc | nhóm phép tính | cải thiện đọc; không chữa overflow |

### Misconception check

**Đúng hay sai?** Cast kết quả phép nhân sang double luôn ngăn int overflow.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phép nhân int có thể đã overflow trước cast.

</details>

**Đúng hay sai?** Ngoặc buộc mọi toán hạng chạy trái sang phải.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cách nhóm không đồng nghĩa thứ tự đánh giá mọi toán hạng.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** operator, type và ngoặc.

- **Working Developer — dùng khi làm việc:** tách bước tính và test biên.

- **Deep Dive — có thể quay lại sau:** sequencing và overflow.

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

## 7. Khi nào KHÔNG dùng

Không dùng phép nhân boolean cho luật tính tiền nhiều nhánh: if ở bài 07 rõ hơn. Không dồn nhiều cập nhật vào một expression. Với vài điều kiện cố định, tên biến trung gian đủ; chưa cần bộ máy quy tắc.

## 8. Production notes & scale check

Sample giới hạn con số nên phép nhân an toàn. Input thật cần kiểm tra giới hạn trước phép nhân, không đợi kết quả tràn. Team 2–3 người nên ưu tiên test tại ngưỡng miễn phí và kiểm tra tiền theo đơn vị nguyên. Chỉ tối ưu phép toán khi đo được đây là phần tốn thời gian.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Một công thức sẽ dùng lại trong C# và SQL sau này: nên bàn giao một biểu thức khó đọc hay các bước kèm ví dụ tại 299999/300000? Chỉ ra quy tắc miễn phí và rủi ro type cần kiểm tra lại khi đổi ngôn ngữ.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Phân biệt = với ==.
2. Giải thích short-circuit bằng ca mẫu số 0.
3. Vì sao cast sau phép tính có thể quá muộn?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi dùng được operator số học, so sánh và logic.
- [ ] Tôi phân biệt `=` với `==`.
- [ ] Tôi dự đoán đúng `17 / 5`, `17 % 5` và `17.0 / 5.0`.
- [ ] Tôi giải thích được short-circuit.
- [ ] Tôi dùng ngoặc và biến trung gian để code rõ hơn.
- [ ] Tôi biết signed integer overflow không chỉ là “quay vòng”.

Điều hướng:

- Prerequisite: [Bộ nhớ, biến và phạm vi](./04-bo-nho-bien-va-pham-vi.md)
- Bài tiếp theo: [Nhập xuất với stdio](./06-nhap-xuat-voi-stdio.md)

- Spaced review: [Review 05](./reviews/review-01-du-lieu-va-bieu-thuc.md)
- Failure Lab: [Điều tra lỗi](./failure-labs/01-tien-va-chia-nguyen.md)
