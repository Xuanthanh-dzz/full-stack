# Hàm, tham số và giá trị trả về

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Hàm đóng gói một việc có input, kết quả và contract rõ.
- Dùng để tách tính điểm khỏi in báo cáo và kiểm thử từng phần.
- C truyền giá trị; caller phải xử lý giá trị báo lỗi trước khi dùng tiếp.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tách một bài toán thành các hàm nhỏ;
- khai báo parameter và return type;
- gọi hàm bằng argument phù hợp;
- giải thích parameter số nhận bản sao giá trị;
- phân biệt hàm trả dữ liệu với hàm chỉ tạo side effect.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Gửi ba điểm cho một người tính trung bình rồi nhận lại một số giống lời gọi hàm. Người đó giữ bản chép các điểm trong lần làm việc của họ; sửa bản chép không sửa sổ gốc của bạn. Việc tính và việc in báo cáo là hai trách nhiệm khác nhau.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| parameter | tên input trong định nghĩa hàm | first |
| argument | giá trị đưa vào tại lời gọi | math |
| return value | giá trị gửi về caller | 8.0 |
| sentinel | giá trị riêng dùng báo tình huống đặc biệt | -1.0 báo điểm sai |
| contract | điều kiện vào và cam kết ra | điểm 0..10 hoặc báo lỗi |

### Ví dụ nhỏ — tính tay trước

Gọi với 2, 4, 6 → cộng 12, chia 3.0 → trả 4.0. Gọi với -1, 4, 6 → trả -1.0 trước phép cộng, caller không được xếp loại số đó.

Chương trình học tập cần tính trung bình ba điểm, xếp loại, rồi in báo cáo. Nếu mọi việc nằm trong `main`, công thức và format trộn lẫn, khó test riêng.

Ta chia trách nhiệm:

```text
calculate_average -> trả average
grade_from_average -> trả grade
print_report       -> in output
main               -> điều phối
```

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `functions.c`:

```c
#include <stdio.h>

double calculate_average(int first, int second, int third)
{
    /* -1.0 báo một điểm nằm ngoài domain 0..10. */
    if (first < 0 || first > 10 ||
        second < 0 || second > 10 ||
        third < 0 || third > 10) {
        return -1.0;
    }

    /*
     * Sau validation, tổng lớn nhất chỉ là 30 nên phép cộng int an toàn.
     * Chia cho 3.0 thực hiện phép chia số thực.
     */
    return (first + second + third) / 3.0;
}

char grade_from_average(double average)
{
    if (average >= 8.0) {
        return 'A';
    }
    if (average >= 6.5) {
        return 'B';
    }
    if (average >= 5.0) {
        return 'C';
    }
    return 'D';
}

void print_report(double average, char grade)
{
    printf("Diem trung binh: %.2f\n", average);
    printf("Xep loai: %c\n", grade);
}

int main(void)
{
    const int math = 8;
    const int physics = 7;
    const int chemistry = 9;

    /* Giữ tính toán tách khỏi hàm tạo side effect output. */
    double average = calculate_average(math, physics, chemistry);
    if (average < 0.0) {
        fprintf(stderr, "Diem phai nam trong doan 0..10.\n");
        return 1;
    }

    char grade = grade_from_average(average);
    print_report(average, grade);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror functions.c -o functions
./functions
```

Output:

```text
Diem trung binh: 8.00
Xep loai: A
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. main giữ math=8, physics=7, chemistry=9; lời gọi copy vào first/second/third.
2. Hàm validate rồi trả 24/3.0=8.0; các parameter của lời gọi hết vòng đời.
3. main giữ average=8.0, kiểm tra lỗi rồi gọi xếp loại và nhận A.
4. print_report ghi output. CPU thực hiện lời gọi và số phép tính cố định; state thuộc main hoặc lần gọi đang hoạt động, không có state dùng chung lâu dài.

### Mini-check

Nếu bỏ kiểm tra average < 0, input sai có thể bị xếp thành grade nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Signature tạo contract

```c
double calculate_average(int first, int second, int third)
```

- tên hàm: `calculate_average`;
- ba parameter kiểu `int`;
- return type: `double`.

Tại lời gọi, `math`, `physics`, `chemistry` là argument. Giá trị của chúng được copy lần lượt vào parameter.

Contract của sample quy định mỗi điểm nằm trong `0..10`.
`calculate_average` trả average không âm khi thành công và sentinel
`-1.0` khi input vi phạm contract. Vì average hợp lệ không thể âm,
caller phân biệt hai kết quả mà không cần kiến thức mới.

### 4.2. Parameter là local của lần gọi

```text
main: math=8, physics=7, chemistry=9
                 |
                 | copy values
                 v
calculate_average: first=8, second=7, third=9
```

Nếu hàm gán `first = 0`, `math` trong `main` không đổi. Mỗi lần gọi có bộ parameter/local riêng. Bài 10 sẽ vẽ các call frame đầy đủ.

### 4.3. `return` kết thúc lời gọi

`return expression;` tính expression, chuyển phù hợp sang return type và đưa kết quả về caller. Code sau `return` trong cùng đường đi không chạy.

Caller phải kiểm tra sentinel trước khi gọi `grade_from_average`. Nếu bỏ
kiểm tra, một giá trị báo lỗi sẽ bị hiểu nhầm thành điểm thật.

Hàm `void` không trả một value:

```c
void print_report(...)
```

Nó vẫn có side effect: ghi output. Tách hàm tính toán thuần khỏi I/O giúp test dễ hơn.

### 4.4. Vì sao định nghĩa hàm nằm trước `main`?

Compiler đọc source theo declaration. Khi gặp lời gọi trong `main`, nó phải biết signature. Đặt full definition trước là cách đơn giản ở bài này. Module 02 sẽ dùng function prototype/header để tổ chức nhiều file.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Hàm tính | nhận input, trả dữ liệu | dễ test nhiều ca; không cần I/O bên trong |
| Hàm in | tạo side effect ra stdout | hợp trình bày; khó dùng như kết quả tính |
| Parameter số | bản sao giá trị | local riêng; không dùng để sửa trực tiếp biến caller |

### Misconception check

**Đúng hay sai?** Gán first=0 sẽ đổi math trong main.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: parameter số là bản sao.

</details>

**Đúng hay sai?** void nghĩa là hàm không làm gì.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: hàm vẫn có thể in hoặc thay đổi state qua cách truy cập phù hợp.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** signature và pass-by-value.

- **Working Developer — dùng khi làm việc:** contract, test biên, tách I/O.

- **Deep Dive — có thể quay lại sau:** quy ước gọi và giới hạn của sentinel.

### Một hàm nên có một trách nhiệm rõ

Tên và contract phải cho biết:

- cần input gì;
- trả output gì;
- có side effect nào.

`calculate_average` không tự đọc input hay in output, nên có thể gọi với
nhiều test case. Validation xảy ra **trước phép cộng**: ba điểm hợp lệ
có tổng tối đa `30`, vì vậy không thể làm `int` overflow trong expression
của sample.

### Pass-by-value

C truyền argument theo giá trị. Với type số, parameter chứa bản copy độc lập. Khi học mảng ở bài 11, quy tắc gọi hàm với mảng có semantics khác cần mô tả riêng; cơ chế địa chỉ đầy đủ thuộc module 02.

### Local variable

`average` trong hàm xếp loại là parameter khác với biến `average` của
`main`; chúng thuộc các lần gọi/scope riêng.

### Đường return đầy đủ

Hàm không phải `void` phải trả giá trị trên mọi đường có thể đi đến cuối. Cấu trúc `grade_from_average` có return cho từng ngưỡng và fallback cuối.

## 6. Lỗi thường gặp

### Dùng hàm trước khi compiler biết declaration

Trong C11 nghiêm ngặt, implicit function declaration không hợp lệ. Đặt definition trước hoặc cung cấp prototype đúng.

### Return type không khớp ý định

Trả average bằng `int` làm mất phần lẻ. Chọn `double`.

### Chia nguyên hoặc cộng trước khi validate

`return (first + second + third) / 3;` vừa chia integer, vừa cộng input
chưa được giới hạn. Validate domain trước, rồi chia cho literal `3.0`.

### Không kiểm tra sentinel

Đưa `-1.0` vào hàm xếp loại sẽ tạo một grade nhìn có vẻ hợp lệ. Caller
phải xử lý failure trước bước tiếp theo.

### Hàm làm quá nhiều việc

Một hàm vừa đọc, validate, tính, in khó tái sử dụng và test. Tách theo trách nhiệm.

### Mong parameter sửa argument số

Assignment parameter chỉ sửa bản copy. Module 02 sẽ dạy pointer khi thật sự cần cho hàm cập nhật storage của caller.

### Bỏ qua argument order

Argument ghép theo vị trí. Với nhiều parameter cùng type, tên rõ và hàm nhỏ giảm nguy cơ đảo thứ tự.

## 7. Khi nào KHÔNG dùng

Không tách mỗi phép cộng thành một hàm nếu tên và contract không giúp đọc/test. Không dùng sentinel trùng miền kết quả hợp lệ: khi miền thay đổi phải chọn cách báo lỗi khác. Với ba điểm, hàm nhỏ đủ, chưa cần framework tính điểm.

## 8. Production notes & scale check

Team nhỏ nên giữ hàm tính độc lập I/O để test biên 0, 10 và input sai. Khi số môn thay đổi, chuyển input thành mảng kèm count sau bài 11. Chi phí một lời gọi thường không là vấn đề cần ưu tiên; đo trước khi gộp code và mất khả năng test.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Hàm bình phương

Viết `int square(int value)` và gọi từ `main`.

**Gợi ý:** hàm chỉ return, không cần `printf`.

### Bài 2 — Hàm tìm lớn nhất

Viết hàm trả số lớn hơn trong hai `int`.

**Gợi ý:** dùng `if` và hai đường return.

### Bài 3 — Kiểm tra range

Viết `bool is_valid_score(int score)` với range `0..10`.

**Gợi ý:** include `<stdbool.h>` và ghép hai so sánh.

### Bài 4 — Refactor bảng nhân

Đưa phần in bảng nhân của bài trước vào `void print_table(int number)`.

**Gợi ý:** vòng lặp là local implementation của hàm.

### Bài 5 — Test hàm xếp loại

Gọi `grade_from_average` với các giá trị ngay dưới, đúng và ngay trên mỗi ngưỡng.

**Gợi ý:** boundary quan trọng hơn một giá trị ở giữa.

## 10. Bài tập tích hợp liên module — Judgment

Hàm tính trung bình sẽ tái sử dụng trong Module 04. Chọn để caller hay hàm tính kiểm tra miền 0..10? Bảo vệ lựa chọn với hai caller khác nhau và nêu phần test giữ nguyên khi đổi ngôn ngữ.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Argument khác parameter thế nào?
2. Vì sao sentinel -1 hợp lệ cho contract này?
3. Vẽ đường return value về main.

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi đọc được signature của hàm.
- [ ] Tôi phân biệt parameter với argument.
- [ ] Tôi giải thích được pass-by-value cho số.
- [ ] Tôi chọn đúng return type.
- [ ] Tôi tách tính toán khỏi output.
- [ ] Tôi bảo đảm mọi đường của hàm non-void đều return.

Điều hướng:

- Prerequisite: [Vòng lặp for, while và do-while](./08-vong-lap-for-while-do-while.md)
- Bài tiếp theo: [Ngăn xếp lời gọi hàm](./10-ngan-xep-loi-goi-ham.md)
