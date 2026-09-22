# Ngăn xếp lời gọi hàm

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Call stack mô tả các lời gọi đang chờ nhau; mỗi lần gọi có state riêng.
- Dùng khi trace hàm lồng nhau, đọc backtrace hoặc suy luận recursion.
- Đệ quy có điểm dừng vẫn có thể quá sâu; C không bảo đảm tối ưu hết frame.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- vẽ call stack tại một điểm trong lời gọi lồng nhau;
- giải thích mỗi invocation có parameter/local riêng;
- theo dõi return value quay về caller;
- mô tả recursion tạo nhiều frame;
- nhận ra recursion thiếu điểm dừng và stack overflow.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bạn đang làm một việc thì giao một việc con và chờ kết quả. Việc con lại giao việc nhỏ hơn. Ghi lại ai đang chờ ai giúp quay về đúng chỗ. Mỗi tờ ghi riêng tương ứng một lần gọi, không phải một hàm duy nhất cho mọi lần gọi.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| frame | state của một lần gọi trong mô hình stack | calculate_total đang chờ subtotal |
| caller / callee | hàm gọi / hàm được gọi | main / calculate_total |
| recursion | hàm gọi lại chính nó | print_countdown |
| base case | trường hợp dừng gọi tiếp | number == 0 |
| backtrace | danh sách lời gọi đang hoạt động | dùng khi debug |

### Ví dụ nhỏ — tính tay trước

countdown(2) in 2 rồi gọi (1), in 1 rồi gọi (0), in Bat dau. Các lần gọi (0), (1), (2) lần lượt kết thúc theo chiều ngược.

Một đơn hàng gọi `calculate_total`, hàm này lại gọi `calculate_subtotal`. Khi debugger dừng trong hàm sâu nhất, người mới thường thấy nhiều dòng cùng tên biến và không biết giá trị thuộc lần gọi nào.

Ta sẽ đặt tên từng frame, theo dõi lúc push/pop và thêm một countdown recursive nhỏ để thấy mỗi lời gọi là độc lập.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `call_stack.c`:

```c
#include <limits.h>
#include <stdio.h>

int calculate_subtotal(int quantity, int unit_price)
{
    if (quantity < 0 || unit_price < 0) {
        return -1;
    }
    if (quantity != 0 && unit_price > INT_MAX / quantity) {
        return -1;
    }
    return quantity * unit_price;
}

int calculate_total(int quantity, int unit_price, int discount)
{
    int subtotal = calculate_subtotal(quantity, unit_price);
    if (subtotal < 0 || discount < 0 || discount > subtotal) {
        return -1;
    }
    return subtotal - discount;
}

void print_countdown(int number)
{
    /* Guard bảo đảm recursive step luôn bắt đầu trong miền hội tụ về 0. */
    if (number < 0) {
        fprintf(stderr, "So dem nguoc phai khong am.\n");
        return;
    }

    if (number == 0) {
        printf("Bat dau\n");
        return;
    }

    printf("%d\n", number);
    print_countdown(number - 1);
}

int main(void)
{
    int total = calculate_total(3, 120, 20);
    if (total < 0) {
        fprintf(stderr, "Don hang hoac phep tinh khong hop le.\n");
        return 1;
    }

    printf("Tong: %d\n", total);
    print_countdown(3);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror call_stack.c -o call_stack
./call_stack
```

Output:

```text
Tong: 340
3
2
1
Bat dau
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. main chờ calculate_total; calculate_total chờ calculate_subtotal.
2. Callee kiểm tra miền và overflow trước khi nhân 3*120, trả 360.
3. Caller trừ 20 rồi trả 340 về main; return value không kéo dài vòng đời local của callee.
4. countdown(3) có bốn invocation từ 3 tới 0. CPU và độ sâu lời gọi tăng theo number; frame vật lý có thể được compiler tối ưu khác mô hình.

### Mini-check

Trong calculate_subtotal, subtotal của calculate_total đã nhận giá trị chưa?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Frame được thêm khi gọi hàm

Khi đang ở `calculate_subtotal`, mô hình logical call stack là:

```text
đỉnh stack
┌──────────────────────────────────────┐
│ calculate_subtotal frame             │
│ quantity=3, unit_price=120           │
│ return expression tạo giá trị 360    │
├──────────────────────────────────────┤
│ calculate_total frame                │
│ quantity=3, unit_price=120           │
│ discount=20, subtotal chưa nhận      │
├──────────────────────────────────────┤
│ main frame                           │
│ total chưa nhận                      │
└──────────────────────────────────────┘
đáy stack
```

Trước phép nhân, `calculate_subtotal` loại số âm và kiểm tra
`unit_price > INT_MAX / quantity`. Chỉ khi phép nhân chắc chắn biểu diễn
được bằng `int`, nó mới tạo `360` rồi return. Frame trên cùng kết thúc.

Caller nhận kết quả vào local `subtotal`. `calculate_total` từ chối
sentinel `-1`, discount âm hoặc discount lớn hơn subtotal; nhờ đó phép
trừ còn lại luôn cho kết quả từ `0` đến `INT_MAX`. Với input mẫu, nó
return `340`, rồi `main` kiểm tra sentinel trước khi in.

### 4.2. Cùng tên không phải cùng storage

`quantity` trong hai hàm là hai parameter storage logic khác nhau. Value `3` được copy qua lời gọi:

```text
calculate_total.quantity = 3
             |
             | copy
             v
calculate_subtotal.quantity = 3
```

Sửa parameter ở frame trên không tự sửa frame dưới.

### 4.3. Recursion tạo một frame cho mỗi invocation

Ngay trước base case in `Bat dau`:

```text
top -> print_countdown(number=0)
       print_countdown(number=1)
       print_countdown(number=2)
       print_countdown(number=3)
       main
```

Nhánh `number == 0` là **base case**. Nó return, rồi các frame lần lượt kết thúc theo thứ tự ngược với lúc gọi: last in, first out.

Guard `number < 0` chạy trước base case và recursive step. Nhờ đó input
ngoài contract bị từ chối ngay, thay vì tiếp tục giảm từ số âm và ngày
càng xa `0`. Với input không âm, mỗi lời gọi dùng `number - 1`, nên tiến
gần base case đúng một đơn vị.

### 4.4. Stack là hữu hạn

Nếu recursion không tiến về base case, số frame tăng đến khi môi trường không thể cấp thêm call stack; chương trình có thể kết thúc vì stack overflow. Không có cách portable để “bắt rồi tiếp tục an toàn” sau khi stack đã cạn. Thiết kế điểm dừng và giới hạn input từ trước.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Loop | giữ state trong một lời gọi | đếm ngược rõ, memory không tăng theo số bước |
| Recursion | giữ chuỗi lời gọi đang chờ | tự nhiên cho bài toán chia nhỏ; tránh độ sâu không giới hạn |
| Stack logic | mô hình ai chờ ai | dùng giải thích; không cam kết layout byte |

### Misconception check

**Đúng hay sai?** Hàm gọi hai lần chỉ có một bộ parameter chung.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: mỗi invocation có state riêng.

</details>

**Đúng hay sai?** Có base case thì input lớn tùy ý luôn an toàn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể cạn stack trước khi chạm base case.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** frame và đường return.

- **Working Developer — dùng khi làm việc:** backtrace, guard, giới hạn độ sâu.

- **Deep Dive — có thể quay lại sau:** inline và tail-call như chi tiết implementation.

### Call stack lưu điều gì?

Về mặt khái niệm, một invocation cần:

- nơi quay về trong caller;
- parameter và local có automatic lifetime;
- state cần khôi phục.

ABI, compiler và optimization quyết định layout vật lý. Local có thể nằm trong register; frame có thể được tối ưu. Sơ đồ dùng để theo dõi semantics, không phải bản đồ địa chỉ byte.

### Lifetime theo invocation

`subtotal` là local của `calculate_total`, không phải của
`calculate_subtotal`. Trong lúc initializer gọi callee, `subtotal` chưa nhận
giá trị; sau khi callee trả `360`, initialization mới hoàn tất. Frame callee
chỉ có các parameter trong source này. Return value được chuyển về caller theo
quy ước thực thi; nó không làm frame cũ tiếp tục sống.

### Sentinel và miền giá trị

Tổng hợp lệ trong sample luôn không âm, nên `-1` dành riêng để báo
failure. Mỗi caller kiểm tra sentinel trước arithmetic hoặc output tiếp
theo. `<limits.h>` cung cấp `INT_MAX`, giới hạn trên của `int` ở đúng
môi trường đang compile; code không giả định `int` có bao nhiêu bit.

### Iteration hay recursion?

Countdown dùng recursion để minh họa. Với bài toán lặp tuyến tính đơn giản, loop thường:

- dễ đọc hơn;
- không tăng call depth theo input;
- tránh rủi ro stack overflow.

Recursion tự nhiên hơn khi cấu trúc bài toán tự chia thành bài toán con, ví dụ cây; ta sẽ gặp sau khi học cấu trúc dữ liệu.

### Đào sâu (có thể quay lại sau)

Compiler có thể inline một lời gọi hoặc tail-call trong vài trường hợp, làm call stack vật lý khác sơ đồ. C không bảo đảm tail-call optimization. Khi suy luận tính đúng, hãy dùng semantics của các invocation; khi debug build tối ưu, chấp nhận frame/variable có thể bị tối ưu.

## 6. Lỗi thường gặp

### Cho rằng cùng tên là cùng biến

Tên chỉ được resolve trong scope/frame tương ứng. Ghi cả `function.variable` khi vẽ.

### Quên base case

Recursion tiếp tục đến stack overflow. Viết base case trước recursive call.

### Có base case nhưng không tiến gần nó

Gọi lại với `number` thay vì `number - 1` vẫn không dừng.

### Trả địa chỉ local

Đây là lỗi pointer sẽ học ở module 02: lifetime local kết thúc khi frame return. Không lưu cách truy cập tới storage đã chết.

### Tin frame luôn có layout như source

Optimization có thể thay đổi layout/khả năng quan sát. Debug lần đầu nên compile thêm `-O0 -g`.

### Dùng recursion cho input không giới hạn

Ngay cả recursion đúng logic vẫn có thể quá sâu. Xác định maximum depth hoặc chuyển sang iteration/data structure phù hợp.

### Nhân trước rồi mới kiểm tra overflow

Kiểm tra kết quả sau `quantity * unit_price` là quá muộn vì signed
integer overflow đã tạo undefined behavior. So với `INT_MAX / quantity`
trước, và chỉ chia sau khi đã chứng minh `quantity != 0`.

## 7. Khi nào KHÔNG dùng

Không dùng recursion cho đếm ngược không giới hạn khi while rõ hơn. Không dựa vào tail-call optimization để bảo đảm an toàn trong C. Dùng recursion khi cấu trúc bài toán có lợi và đã xác định giới hạn độ sâu.

## 8. Production notes & scale check

Sample sâu 4 lời gọi đếm ngược. Với input do người dùng điều khiển, giới hạn độ sâu trước hoặc dùng loop. Team nhỏ cần backtrace và input tái hiện trước khi tăng stack size. Debug build dễ quan sát; release có thể inline, nên không coi frame biến mất là chứng cứ code không chạy.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Vẽ stack

Vẽ stack tại thời điểm `calculate_subtotal` sắp return.

**Gợi ý:** ghi đầy đủ tên hàm trước mỗi parameter/local.

### Bài 2 — Theo dõi hai lần gọi

Gọi `calculate_total` lần lượt với hai đơn hàng và chứng minh local của lần đầu không được tái sử dụng như state nghiệp vụ.

**Gợi ý:** mỗi invocation có lifetime riêng dù implementation có thể tái dùng vùng stack sau return.

### Bài 3 — Tổng recursive

Viết hàm tính `1 + ... + n` với base case `n == 0`.

**Gợi ý:** recursive call phải nhận `n - 1`.

### Bài 4 — Chuyển recursion thành loop

Viết lại countdown bằng `while`, so sánh output và call depth.

**Gợi ý:** loop chỉ giữ một frame của hàm chứa nó.

### Bài 5 — Debug call stack

Compile `-O0 -g`, đặt breakpoint trong `calculate_subtotal` và xem backtrace.

**Gợi ý:** với GDB, dùng `break calculate_subtotal`, `run`, `backtrace`.

## 10. Bài tập tích hợp liên module — Judgment

Trước Module 07 về đệ quy, chọn loop hay recursion cho countdown 1 triệu bước. Tách số thao tác CPU khỏi state các lời gọi; nêu bằng chứng cần đo nếu bài toán là cây thay vì đếm tuyến tính.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ stack tại number=0 cho input 2.
2. Return value có giữ callee sống không?
3. Vì sao base case chưa đủ bảo đảm an toàn?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi vẽ được stack của lời gọi lồng nhau.
- [ ] Tôi phân biệt biến cùng tên ở hai frame.
- [ ] Tôi theo dõi được return value về caller.
- [ ] Tôi giải thích recursion tạo frame mới.
- [ ] Tôi xác định base case và bước tiến.
- [ ] Tôi không đồng nhất sơ đồ logic với layout vật lý cố định.

Điều hướng:

- Prerequisite: [Hàm, tham số và giá trị trả về](./09-ham-tham-so-gia-tri-tra-ve.md)
- Bài tiếp theo: [Mảng một chiều](./11-mang-mot-chieu.md)

- Spaced review: [Review 10](./reviews/review-02-control-flow-va-ham.md)
- Failure Lab: [Điều tra lỗi](./failure-labs/02-sentinel-thanh-diem.md)
