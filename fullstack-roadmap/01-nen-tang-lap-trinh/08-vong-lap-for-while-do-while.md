# Vòng lặp for, while và do-while

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Vòng lặp thực hiện lại một thân lệnh đến điều kiện dừng.
- Dùng khi cùng thao tác áp dụng cho nhiều ngày hoặc nhiều dữ liệu.
- Phải chứng minh tiến triển và số lần chạy; điều kiện sai có thể không dừng.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- lặp một số lần biết trước bằng `for`;
- lặp khi điều kiện còn đúng bằng `while`;
- chạy thân ít nhất một lần bằng `do-while`;
- dùng accumulator và counter;
- tránh vòng lặp vô hạn và lỗi lệch một đơn vị.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Thay vì chép năm phép cộng, ta giữ “đang ở ngày mấy” và “đã cộng được bao nhiêu”. Mỗi vòng xử lý một ngày rồi chuyển sang ngày kế. Nếu không đổi ngày, máy tiếp tục làm cùng việc mãi.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| iteration | một lượt chạy thân loop | một ngày |
| counter | biến đếm lượt hoặc vị trí | day |
| accumulator | biến giữ kết quả tích lũy | total |
| invariant | điều luôn đúng tại điểm đã chọn | sau ngày d, total là tổng tới d |
| off-by-one | sai biên đúng một lượt | < thay cho <= |

### Ví dụ nhỏ — tính tay trước

Ba ngày thu 100, 120, 140: total bắt đầu 0 → 100 → 220 → 360. Kiểm tra điều kiện sau cập nhật ngày thành 4 sẽ dừng nếu giới hạn là 3.

Một cửa hàng ghi doanh thu theo quy luật demo: ngày 1 là `100`, mỗi ngày sau tăng `20`, trong 5 ngày. Ta cần in từng ngày, tính tổng, rồi đếm ngược thời gian đóng sổ:

```text
Ngay 1: 100
...
Tong: 700
Dong so sau: 3 2 1
So lan kiem tra: 2
```

Viết lặp lại năm lần `printf` khó thay đổi và dễ sai. Vòng lặp biểu diễn phần lặp cùng điều kiện dừng.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. total=0; day=1; điều kiện đúng thì revenue=100 và total=100.
2. Mỗi lượt cập nhật day; sau ngày 5 total=700, day thành 6 và thoát.
3. while giảm seconds từ 3 xuống 0; do-while tăng checks rồi mới kiểm tra.
4. CPU làm số lượt tỷ lệ với số ngày; chỉ giữ vài local, bộ nhớ không tăng theo lượt. In từng lượt thêm chi phí I/O.

### Mini-check

Nếu seconds bắt đầu 0, while chạy mấy lần? do-while làm việc tương tự có chạy không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| for | khởi tạo/điều kiện/cập nhật tập trung | hợp đếm lượt; có thể chạy 0 lần |
| while | kiểm tra trước thân | hợp đọc tới EOF; phải cập nhật state |
| do-while | kiểm tra sau thân | luôn ít nhất 1 lần; không dùng khi 0 lượt là hợp lệ |

### Misconception check

**Đúng hay sai?** Có điều kiện trong while là chắc chắn dừng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: state có thể không bao giờ làm điều kiện sai.

</details>

**Đúng hay sai?** Loop nhiều lần luôn cần nhiều local mới còn sống cùng lúc.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample chỉ giữ state của lượt hiện tại và tổng.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** loop và trace bằng tay.

- **Working Developer — dùng khi làm việc:** invariant, EOF, test biên.

- **Deep Dive — có thể quay lại sau:** đếm thao tác để chuẩn bị Big-O.

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

## 7. Khi nào KHÔNG dùng

Không dùng do-while khi input có thể không có phần tử mà thân vẫn đọc dữ liệu. Với một công thức tổng đã rõ và cần ít thao tác, có thể tính trực tiếp; chỉ thay loop sau khi kiểm tra giới hạn type và chứng minh tương đương.

## 8. Production notes & scale check

5 ngày là demo; một triệu lần printf có thể chậm vì I/O. Team nhỏ nên đo số lượt và lượng output trước khi tối ưu công thức. Với đọc input, EOF phải là đường dừng; dùng timeout trong test để bắt loop vô hạn. Kiểm tra tổng có vượt type khi tăng số ngày.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Module 07 sẽ phân tích chi phí theo kích thước input. Không cần ký hiệu mới: hãy đếm phép cộng khi ngày tăng từ 5 lên 5000. Chọn giảm output hay sửa phép cộng nếu đo thấy thời gian chủ yếu ở terminal.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Trace total sau ba lượt.
2. Nêu đại lượng tiến gần điểm dừng.
3. So số local cần giữ cho 5 và 5000 lượt.

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi chọn được giữa `for`, `while`, `do-while`.
- [ ] Tôi mô tả initialization, condition, body và update.
- [ ] Tôi dùng accumulator đúng giá trị đầu.
- [ ] Tôi chứng minh loop có tiến triển đến điểm dừng.
- [ ] Tôi nhận ra off-by-one.
- [ ] Tôi biết scope của biến khai báo trong `for`.

Điều hướng:

- Prerequisite: [Điều kiện với if và switch](./07-dieu-kien-if-switch.md)
- Bài tiếp theo: [Hàm, tham số và giá trị trả về](./09-ham-tham-so-gia-tri-tra-ve.md)
