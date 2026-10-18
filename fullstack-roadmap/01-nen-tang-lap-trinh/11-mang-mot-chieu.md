# Mảng một chiều

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Mảng giữ các phần tử cùng type liên tiếp, dùng index để chọn từng phần tử.
- Dùng khi cần duyệt và xử lý một dãy có giới hạn rõ.
- C không kiểm tra biên; count phải đúng và khác capacity.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- khai báo và khởi tạo mảng có kích thước cố định;
- đọc/ghi phần tử bằng index hợp lệ;
- duyệt mảng bằng loop;
- tính số phần tử bằng `sizeof` tại nơi còn biết toàn bộ mảng;
- truyền mảng cùng số phần tử vào hàm;
- vẽ các element nằm liên tiếp trong storage của mảng.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Thay vì năm hộp có năm tên, ta có một dãy hộp đánh số từ 0. Biết tên dãy và số thứ tự là chọn được một hộp. Dãy không tự biết có bao nhiêu hộp đã chứa dữ liệu nghiệp vụ; khi đưa dãy cho hàm, phải nói cả số phần tử được phép dùng.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| array / mảng | dãy các object cùng type | scores |
| index | vị trí bắt đầu từ 0 | scores[3] |
| count | số phần tử đang dùng | 5 |
| capacity | số slot thực có | kích thước mảng |
| undefined behavior | chuẩn không còn bảo đảm hành vi | truy cập ngoài biên |

### Ví dụ nhỏ — tính tay trước

[5, 2, 8] có index 0, 1, 2. Tổng đi từ 0 → 5 → 7 → 15. Đọc index 3 không phải đọc số 0 mặc định; nó đã ngoài mảng.

Ta cần xử lý 5 điểm: `8, 7, 9, 6, 10`. Năm biến rời làm loop và hàm tổng quát trở nên khó. Mảng gom các giá trị cùng type dưới một tên, còn index chọn từng phần tử.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `scores.c`:

```c
#include <limits.h>
#include <stdio.h>

int sum_scores(const int scores[], int count)
{
    if (count < 0) {
        return -1;
    }

    int total = 0;
    for (int index = 0; index < count; index++) {
        if (scores[index] < 0 || scores[index] > 10) {
            return -1;
        }
        if (total > INT_MAX - scores[index]) {
            return -1;
        }
        total += scores[index];
    }
    return total;
}

int find_max(const int scores[], int count)
{
    int maximum = scores[0];
    for (int index = 1; index < count; index++) {
        if (scores[index] > maximum) {
            maximum = scores[index];
        }
    }
    return maximum;
}

int main(void)
{
    int scores[] = {8, 7, 9, 6, 10};

    /* Công thức sizeof chỉ dùng ở scope còn thấy toàn bộ array object. */
    int count = (int)(sizeof scores / sizeof scores[0]);

    scores[3] = 7;

    printf("Cac diem:");
    for (int index = 0; index < count; index++) {
        printf(" %d", scores[index]);
    }
    printf("\n");

    int total = sum_scores(scores, count);
    if (count <= 0 || total < 0) {
        fprintf(stderr, "Mang diem khong hop le.\n");
        return 1;
    }

    printf("Tong: %d\n", total);
    printf("Trung binh: %.2f\n", (double)total / count);
    printf("Cao nhat: %d\n", find_max(scores, count));

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror scores.c -o scores
./scores
```

Output:

```text
Cac diem: 8 7 9 7 10
Tong: 41
Trung binh: 8.20
Cao nhat: 10
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. main tạo 5 phần tử; assignment scores[3]=7 thay đúng phần tử thứ tư.
2. sum_scores nhận cách truy cập cùng mảng và count=5; total lần lượt 8,15,24,31,41.
3. Caller kiểm tra count và sentinel trước chia; find_max chỉ được gọi với count>0.
4. Mảng giữ 5 int; mỗi lượt tổng/max đọc số phần tử tỷ lệ count, local tổng chỉ một int. Dữ liệu không được copy toàn mảng vào hàm.

### Mini-check

Nếu count=5, tại sao index<=count thực hiện một lần truy cập không hợp lệ?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Index bắt đầu từ 0

```text
scores
index:    0    1    2    3    4
        +----+----+----+----+----+
value:  |  8 |  7 |  9 |  7 | 10 |
        +----+----+----+----+----+
```

Mảng 5 phần tử có index hợp lệ `0..4`. `scores[3] = 7` chỉ thay element thứ tư.

Các element cùng type được lưu liên tiếp trong array object. Mỗi element là storage riêng; assignment một element không tự đổi element khác.

### 4.2. Loop và biên mảng

Điều kiện đúng là:

```c
index < count
```

Khi `index == count`, loop dừng trước lần truy cập. C không tự kiểm tra biên; đọc/ghi ngoài mảng là undefined behavior.

### 4.3. Tính số phần tử

Trong `main`, `sizeof scores` là tổng số byte của cả mảng; `sizeof scores[0]` là byte của một element. Tỷ số cho số element. Cast sang `int` phù hợp sample nhỏ; `sizeof` thực tế tạo type không dấu chuyên dụng sẽ học sâu ở module 02.

### 4.4. Mảng khi gọi hàm

Hàm nhận mảng và `count` riêng:

```c
sum_scores(scores, count)
```

Trong cách khai báo parameter `const int scores[]`, hàm truy cập **cùng các element** của mảng caller; C không copy toàn bộ mảng. `const` ngăn hàm này sửa element qua parameter. Kích thước không tự đi kèm nên phải truyền `count`.

Cơ chế địa chỉ khiến array parameter hoạt động như vậy được dạy ở module 02. Lần đọc đầu chỉ cần giữ contract: luôn truyền đúng mảng và đúng số phần tử.

`sum_scores` còn áp dụng domain `0..10`. Trước mỗi phép cộng, nó so
`total` với `INT_MAX - scores[index]`; chỉ cộng khi kết quả còn biểu diễn
được. Hàm trả `-1` khi count âm, điểm sai hoặc tổng không an toàn.
Caller kiểm tra sentinel trước phép chia và trước `find_max`.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Array object | storage của toàn dãy | sizeof ở nơi có full array biết cả size |
| Array parameter | cách truy cập các element của caller | không copy dãy; không dùng sizeof parameter để suy count |
| Count / capacity | số đang dùng / số có chỗ chứa | duyệt count; ghi mới phải kiểm tra capacity |

### Misconception check

**Đúng hay sai?** Array và pointer là một thứ nên sizeof luôn giống nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: array object có size toàn dãy; cơ chế chuyển đổi lúc gọi hàm sẽ học ở Module 02.

</details>

**Đúng hay sai?** Mảng capacity 10 thì luôn có 10 phần tử nghiệp vụ hợp lệ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: count có thể chỉ là 3.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** index, count, traversal.

- **Working Developer — dùng khi làm việc:** contract của hàm và test biên.

- **Deep Dive — có thể quay lại sau:** array-to-pointer conversion ở Module 02.

### Khởi tạo

`int scores[] = {8, 7, 9};` để compiler suy ra size 3. Với `int scores[5] = {8, 7};`, các element còn lại được zero-initialize.

### Mảng có kích thước cố định

Size của mảng sample không tăng khi chạy. Muốn chứa tối đa N phần tử, tạo capacity N và giữ biến `count` cho số phần tử đang dùng.

### Hàm và mảng rỗng

`find_max` đọc `scores[0]`, nên contract yêu cầu `count > 0`.
Trong sample, caller chỉ gọi nó sau khi đã kiểm tra `count` và kết quả
validation của `sum_scores`.

### Đào sâu (có thể quay lại sau)

Không dùng công thức `sizeof parameter / sizeof parameter[0]` bên trong `sum_scores`: array parameter không còn mang size toàn mảng. Đây là lý do API C thường nhận thêm `count`. Module 02 sẽ giải thích array-to-pointer conversion chính xác.

## 6. Lỗi thường gặp

### Dùng `<= count`

Iteration cuối truy cập `scores[count]`, vượt biên.

### Dùng index âm

Cũng vượt biên; C không ném exception bảo vệ.

### Gọi `find_max` với count 0

Hàm đọc phần tử không tồn tại. Ghi precondition và validate.

### Cộng điểm mà chưa giới hạn domain

Signed `int` overflow là undefined behavior. Validate từng điểm và kiểm
tra `total > INT_MAX - score` trước phép cộng.

### Nhầm capacity với count

Capacity là số slot đã cấp; count là số slot có dữ liệu hợp lệ.

### Mong assignment copy toàn bộ mảng

C không cho `destination = source` với hai mảng. Copy element bằng loop và bảo đảm capacity.

## 7. Khi nào KHÔNG dùng

Không dùng mảng cố định rất lớn cho số phần tử chưa biết chỉ để tránh nghĩ về capacity. Với đúng 5 điểm, mảng là đủ; khi số lượng biến động vượt giới hạn, học cấp phát động ở Module 02. Không chọn linked list chỉ vì “linh hoạt” khi chỉ cần duyệt.

## 8. Production notes & scale check

Team nhỏ có thể dùng mảng giới hạn cho cấu hình hoặc buffer nhỏ. Khi tăng count, ghi rõ memory = capacity × sizeof element và số lượt duyệt. Caller phải bảo đảm vùng thực đủ count; kiểm tra count không thể tự chứng minh vùng nhớ đó tồn tại. Dùng sanitizer và ca count=0/1/max để điều tra lỗi.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Tìm minimum

Viết hàm trả điểm thấp nhất với precondition `count > 0`.

**Gợi ý:** bắt đầu bằng element 0, duyệt từ index 1.

### Bài 2 — Đếm đạt

Đếm số điểm `>= 5`.

**Gợi ý:** counter bắt đầu 0, chỉ tăng khi điều kiện đúng.

### Bài 3 — Đảo tại chỗ

Đổi chỗ element đầu/cuối tiến dần vào giữa.

**Gợi ý:** cần biến tạm; loop đến `count / 2`.

### Bài 4 — Capacity và count

Tạo mảng capacity 10 nhưng chỉ dùng 3 element; chỉ in element hợp lệ.

**Gợi ý:** mọi loop nghiệp vụ dùng `count`, không dùng capacity.

### Bài 5 — Test biên

Test hàm tổng với 1 element, điểm âm, điểm lớn hơn 10 và nhiều số.

**Gợi ý:** các điểm ngoài `0..10` phải trả sentinel; không gọi
`find_max` với mảng rỗng nếu chưa đổi contract.

## 10. Bài tập tích hợp liên module — Judgment

Chuẩn bị Module 02 và 07: danh sách tối đa 5 điểm cần mảng cố định hay cấu trúc cấp phát từng phần tử? Bảo vệ lựa chọn theo số lượt duyệt, memory và driver khiến capacity cố định không còn đủ.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ index hợp lệ cho 3 phần tử.
2. Vì sao hàm cần count?
3. sum_scores và find_max có cùng contract cho count=0 không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi xác định đúng index đầu/cuối.
- [ ] Tôi không truy cập khi `index == count`.
- [ ] Tôi phân biệt count với capacity.
- [ ] Tôi tính được count bằng `sizeof` tại nơi có full array.
- [ ] Tôi truyền mảng kèm count vào hàm.
- [ ] Tôi vẽ được storage từng element.

Điều hướng:

- Prerequisite: [Ngăn xếp lời gọi hàm](./10-ngan-xep-loi-goi-ham.md)
- Bài tiếp theo: [Mảng hai chiều](./12-mang-hai-chieu.md)
