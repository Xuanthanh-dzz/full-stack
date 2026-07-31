# Hàm, tham số và giá trị trả về

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tách một bài toán thành các hàm nhỏ;
- khai báo parameter và return type;
- gọi hàm bằng argument phù hợp;
- giải thích parameter số nhận bản sao giá trị;
- phân biệt hàm trả dữ liệu với hàm chỉ tạo side effect.

## 2. Bài toán mở đầu

Chương trình học tập cần tính trung bình ba điểm, xếp loại, rồi in báo cáo. Nếu mọi việc nằm trong `main`, công thức và format trộn lẫn, khó test riêng.

Ta chia trách nhiệm:

```text
calculate_average -> trả average
grade_from_average -> trả grade
print_report       -> in output
main               -> điều phối
```

## 3. Lời giải bằng code

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

## 4. Giải thích cơ chế

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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi đọc được signature của hàm.
- [ ] Tôi phân biệt parameter với argument.
- [ ] Tôi giải thích được pass-by-value cho số.
- [ ] Tôi chọn đúng return type.
- [ ] Tôi tách tính toán khỏi output.
- [ ] Tôi bảo đảm mọi đường của hàm non-void đều return.

Điều hướng:

- Prerequisite: [Vòng lặp for, while và do-while](./08-vong-lap-for-while-do-while.md)
- Bài tiếp theo: [Ngăn xếp lời gọi hàm](./10-ngan-xep-loi-goi-ham.md)
