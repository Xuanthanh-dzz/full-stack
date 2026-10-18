# Stack, heap và vòng đời bộ nhớ

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Vòng đời quyết định khi nào object được phép truy cập; scope chỉ quyết định nơi dùng được tên.
- Dùng mô hình automatic, static và allocated để quyết định trả giá trị hay mượn địa chỉ.
- Chuẩn C không bắt buộc biến cục bộ nằm vật lý trên stack; địa chỉ local không sống qua return.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- theo dõi lifetime của biến cục bộ qua từng lời gọi hàm;
- phân biệt stack frame, vùng cấp phát động thường gọi là heap và vùng lưu trữ tĩnh;
- giải thích vì sao không được trả địa chỉ của biến cục bộ;
- chọn output parameter do bên gọi sở hữu khi cần trả kết quả an toàn;
- tách ba khái niệm thường bị trộn lẫn: vị trí lưu trữ, lifetime và ownership.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một chiếc chìa khóa còn trong tay không làm căn phòng đã tháo dỡ tồn tại lại. Tương tự, giữ con trỏ không kéo dài vòng đời object. Trước khi đọc dữ liệu, cần biết ai tạo nó và lúc nào nó kết thúc.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| scope | vùng source code nơi tên được nhìn thấy | biến trong block |
| storage duration | quy tắc thời gian storage tồn tại | automatic, static, allocated |
| stack frame | mô hình phổ biến lưu thông tin một lời gọi | không phải vị trí vật lý bắt buộc |
| static local | object tồn tại suốt chương trình, tên chỉ dùng trong scope | completed_calculations |

### Ví dụ nhỏ — tính tay trước

Gọi tính 2 × 5 rồi 3 × 4: mỗi lần có biến tạm riêng; bộ đếm static đổi 0 → 1 → 2. Kết quả output nằm trong caller, nên không biến mất cùng biến tạm callee.

Hàm tính tổng đơn hàng cần đưa kết quả về `main`. Một cách nguy hiểm là tạo biến cục bộ rồi trả địa chỉ của nó: pointer object ở bên gọi có thể còn trong scope, nhưng khi object đích hết lifetime, giá trị pointer trỏ tới nó trở thành indeterminate.

Ta sẽ dùng một contract an toàn: `main` sở hữu biến kết quả và truyền địa chỉ vào hàm. Đồng thời, chương trình có một bộ đếm cần tồn tại xuyên suốt nhiều lời gọi.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.c`:

```c
#include <limits.h>
#include <stdio.h>

static int completed_calculations = 0;

static int calculate_total(
    int unit_price,
    int quantity,
    int *result
)
{
    if (unit_price < 0 || quantity < 0 || result == NULL) {
        return 0;
    }

    /* Check before multiplication: signed overflow would already be UB. */
    if (quantity > 0 && unit_price > INT_MAX / quantity) {
        return 0;
    }

    if (completed_calculations == INT_MAX) {
        return 0;
    }

    int subtotal = unit_price * quantity;
    *result = subtotal;
    ++completed_calculations;
    return 1;
}

int main(void)
{
    int first_total = 0;
    int second_total = 0;

    if (!calculate_total(250, 4, &first_total)) {
        return 1;
    }

    if (!calculate_total(120, 3, &second_total)) {
        return 1;
    }

    printf("Don thu nhat: %d xu\n", first_total);
    printf("Don thu hai: %d xu\n", second_total);
    printf("So lan tinh thanh cong: %d\n", completed_calculations);
    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o lifetime
./lifetime
```

Output:

```text
Don thu nhat: 1000 xu
Don thu hai: 360 xu
So lan tinh thanh cong: 2
```

### Walkthrough — execution / state / cost

1. main giữ output và gọi calculate; mỗi lời gọi có tham số/biến tạm riêng.
2. Lần một ghi 1000 từ 250 × 4, lần hai ghi 360 từ 120 × 3.
3. completed_calculations có static storage duration nên giữ trạng thái qua cả hai lời gọi, cuối cùng bằng 2.
4. Không có malloc. Chi phí mỗi lần cố định; state tích lũy là một bộ đếm dùng chung, còn output thuộc caller.

### Mini-check

Sau calculate return, output của caller và biến tạm của callee khác nhau về vòng đời thế nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Trước lời gọi

`first_total` là object cục bộ của `main`, thường nằm trong stack frame của `main`. Trước phép nhân, hàm còn kiểm tra `unit_price > INT_MAX / quantity` khi `quantity > 0`; nhờ vậy phép nhân `int` không signed overflow. Bộ đếm cũng từ chối lời gọi tiếp theo khi đã bằng `INT_MAX`, nên phép tăng luôn hợp lệ:

```text
Stack

frame main
┌─────────────────────────┐
│ first_total  = 0         │
│ second_total = 0         │
└─────────────────────────┘
```

Object sống từ lúc execution đi qua khai báo đến khi khối của `main` kết thúc.

### Trong `calculate_total`

Mỗi lời gọi tạo một frame mới chứa tham số và biến cục bộ:

```text
frame calculate_total
┌─────────────────────────┐
│ unit_price = 250        │
│ quantity   = 4          │
│ result ─────────────────┼──┐
│ subtotal   = 1000       │  │
└─────────────────────────┘  │
                             ▼
frame main                  first_total = 0
```

Dòng:

```c
*result = subtotal;
```

chép giá trị `1000` vào object `first_total` của `main`.

Khi `calculate_total` trả về:

- các object tham số và `subtotal` hết lifetime;
- frame của lời gọi được thu hồi;
- `first_total` vẫn sống vì frame `main` chưa kết thúc;
- giá trị đã chép vào `first_total` vẫn là `1000`.

### Vì sao không trả địa chỉ biến cục bộ

Đoạn dưới có lỗi lifetime, chỉ để nhận diện và **không được chạy**:

```c
static int *calculate_wrong(int price, int quantity)
{
    int subtotal = price * quantity;
    return &subtotal;
}
```

Ngay sau khi hàm trả về, `subtotal` hết lifetime:

```text
Trong hàm: pointer ──► subtotal = 1000  (còn sống)
Sau hàm:   pointer = indeterminate       (subtotal đã hết lifetime)
```

Pointer như vậy thường được gọi là dangling pointer. Theo C11, không được đọc, so sánh, in hoặc dereference giá trị indeterminate đó. Sự tồn tại của pointer object không kéo dài lifetime của object đích.

### Biến `static`

`completed_calculations` có static storage duration. Object được tạo cho cả thời gian chạy chương trình, không được tạo lại theo mỗi lời gọi:

```text
Static storage
┌──────────────────────────────┐
│ completed_calculations = 2   │
└──────────────────────────────┘

Stack
┌──────────────────────────────┐
│ các frame xuất hiện/rời đi   │
└──────────────────────────────┘
```

Từ khóa `static` ở phạm vi file còn làm tên này chỉ được dùng trực tiếp trong translation unit hiện tại. Khái niệm translation unit sẽ được dạy ở bài 13.

### Heap sẽ giải quyết bài toán nào

Đôi khi kích thước chỉ biết lúc chạy hoặc object cần sống lâu hơn một lời gọi. Khi đó, chương trình yêu cầu một block từ dynamic storage allocator—thường gọi là heap—và giữ địa chỉ bằng pointer.

Khác stack frame, block này không tự mất đi khi hàm trả về. Code phải giải phóng đúng một lần khi không còn cần. Bài tiếp theo mới giới thiệu các API `malloc`, `calloc`, `realloc` và `free`.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Automatic | vòng đời gắn với block/lời gọi | dễ quản lý; không trả địa chỉ để dùng sau vòng đời |
| Static | storage suốt chương trình | giữ trạng thái giữa lời gọi; cần cân nhắc test và đồng thời |
| Allocated | từ cấp phát tới giải phóng | chủ động thời gian sống nhưng phải quản lý lỗi/cleanup; chưa cần cho hai phép tính |

### Misconception check

**Đúng hay sai?** Tên hết scope luôn đồng nghĩa object hết vòng đời.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: static local hết khả năng gọi tên từ ngoài nhưng object vẫn tồn tại.

</details>

**Đúng hay sai?** Đổi local sang static luôn sửa API trả con trỏ một cách tốt.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tạo state dùng chung, các lần gọi có thể ghi đè và khó dùng đồng thời.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace lúc object bắt đầu/kết thúc.

- **Working Developer — dùng khi làm việc:** tránh trả borrow vượt vòng đời.

- **Deep Dive — có thể quay lại sau:** phân biệt storage chuẩn với tối ưu register/stack của compiler.

### Storage duration

C mô tả lifetime qua storage duration:

- **automatic:** tham số và biến cục bộ thông thường; lifetime gắn với lần đi vào khối;
- **static:** object tồn tại suốt lần chạy chương trình;
- **allocated:** vùng được allocator cấp theo yêu cầu và tồn tại tới lúc giải phóng;
- **thread:** mỗi thread có một instance; chưa cần dùng trong module này.

“Stack” và “heap” là mô hình triển khai rất phổ biến, hữu ích khi debug. Chuẩn C quy định hành vi và storage duration, không bắt buộc mọi hệ thống phải dùng đúng một cấu trúc máy có hai vùng mang tên này.

### Lifetime khác scope

- **Scope** quyết định đoạn source code nào nhìn thấy một tên.
- **Lifetime** quyết định thời gian object tồn tại.

`completed_calculations` có tên chỉ dùng trong file này do `static`, nhưng object sống suốt chương trình. Một object cấp phát động có thể vẫn sống dù pointer cục bộ đã hết scope—và có thể bị leak nếu không còn pointer nào giữ địa chỉ.

### Ownership

Ownership là quy ước thiết kế trả lời “ai chịu trách nhiệm kết thúc tài nguyên?” C không tự ghi ownership vào kiểu pointer.

Trong chương trình chính:

- `main` sở hữu `first_total` và `second_total`;
- `calculate_total` chỉ mượn pointer trong thời gian lời gọi;
- không bên nào cần `free` vì các object có automatic storage duration.

### Pointer không giữ object sống

C không có garbage collector theo dõi pointer. Pointer không ngăn object automatic hết lifetime, cũng không tự giải phóng object allocated. Nếu object đích hết lifetime trong khi pointer object vẫn còn trong scope, giá trị pointer đó trở thành indeterminate; không được đọc, so sánh, in hoặc dereference nó.

### Đào sâu (có thể quay lại sau)

Compiler có thể giữ một biến trong register hoặc tối ưu bỏ stack slot nếu hành vi quan sát được không đổi. Sơ đồ stack là mô hình để lý luận về frame và lifetime, không phải cam kết rằng mọi biến luôn có một ô RAM cố định.

Địa chỉ các frame cũng có thể thay đổi do cơ chế bảo vệ của hệ điều hành. Đừng dùng thứ tự địa chỉ để suy ra logic chương trình.

## 6. Lỗi thường gặp

### Trả địa chỉ biến cục bộ

Pointer trở thành dangling ngay khi hàm kết thúc. Dùng output parameter trỏ tới object của bên gọi, hoặc cấp phát động khi lifetime thực sự phải vượt qua lời gọi.

### Cho rằng biến cùng tên là cùng object

Mỗi lần gọi hàm tạo instance mới của biến automatic. Hai lời gọi lồng nhau không dùng chung một `subtotal`.

### Dùng `static` để né mọi vấn đề lifetime

Một buffer `static` dùng chung có thể bị ghi đè ở lần gọi sau, làm hàm không reentrant và khó dùng đồng thời. Chỉ chọn static storage khi dữ liệu thật sự mang lifetime toàn chương trình.

### Nhầm pointer với ownership

Nhiều pointer có thể trỏ cùng object nhưng không có nghĩa tất cả đều được quyền giải phóng. Contract phải chỉ một owner rõ ràng.

### Dùng object sau lifetime

Undefined behavior không nhất thiết crash ngay. Chương trình “có vẻ chạy” không làm pointer dangling trở nên hợp lệ.

### Kiểm tra overflow sau phép tính

Signed overflow đã là undefined behavior trước khi code có cơ hội kiểm tra kết quả. Với các toán hạng không âm, kiểm tra bằng phép chia **trước** `unit_price * quantity`, như chương trình chính.

## 7. Khi nào KHÔNG dùng

Không dùng static làm giải pháp chung để giữ mọi kết quả. Nếu một giá trị nhỏ chỉ cần trả về, trả bản sao đơn giản hơn state dùng chung. Không malloc khi storage caller đã đủ vòng đời.

## 8. Production notes & scale check

Demo một thread nên bộ đếm tăng tuần tự. Khi nhiều thread dùng chung, thao tác tăng cần thiết kế đồng bộ; bài không tuyên bố thread-safe. Debug scope bằng source, lifetime bằng trace lời gọi; không suy vòng đời từ địa chỉ còn đọc được tình cờ.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Output parameter an toàn

Viết hàm tính diện tích hình chữ nhật, trả trạng thái bằng `int` và ghi kết quả qua pointer của bên gọi.

**Gợi ý:** từ chối chiều dài âm, chiều rộng âm và output pointer `NULL`.

### Bài 2 — Vẽ hai lời gọi

Vẽ stack frame của `main` và `calculate_total` ở từng lời gọi trong chương trình chính.

**Gợi ý:** `subtotal` ở hai lần gọi là hai object có lifetime khác nhau.

### Bài 3 — Bộ đếm static

Viết hàm trả số thứ tự lần gọi, dùng một biến `static` cục bộ.

**Gợi ý:** giải thích vì sao giá trị không trở về `0` sau mỗi lần hàm kết thúc.

### Bài 4 — Audit lifetime

Tìm ba pointer trong code bạn đã viết ở bài 01–05 và ghi object đích, owner, thời điểm bắt đầu/kết thúc lifetime.

**Gợi ý:** pointer vào mảng là borrowed pointer; pointer đó không sở hữu phần tử.

## 10. Bài tập tích hợp liên module — Judgment

Liên hệ module trước: hàm trung bình trả int/float và hàm trả pointer local, phương án nào còn hợp lệ sau return? Nếu cần đếm số lần tính cho từng lớp riêng, vì sao một static global counter chưa đúng nghiệp vụ?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Scope khác lifetime qua ví dụ static local thế nào?
2. Ai giữ output sống trong sample?
3. Vì sao địa chỉ nhìn có vẻ còn dữ liệu chưa chứng minh được đọc hợp lệ?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi biết khi nào biến automatic hết lifetime.
- [ ] Tôi giải thích được vì sao trả `&local_variable` là sai.
- [ ] Tôi phân biệt stack, allocated storage và static storage.
- [ ] Tôi không cho rằng pointer làm object sống lâu hơn.
- [ ] Tôi ghi được owner và borrower cho một pointer.

**Bài prerequisite:** [Con trỏ hàm và callback](./05-con-tro-ham-va-callback.md)

**Bài tiếp theo:** [Cấp phát động: malloc, calloc, realloc và free](./07-cap-phat-dong-malloc-calloc-realloc-free.md)
