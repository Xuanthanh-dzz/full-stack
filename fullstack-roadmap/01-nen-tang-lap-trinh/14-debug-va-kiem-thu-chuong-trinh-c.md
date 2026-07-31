# Debug và kiểm thử chương trình C

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tái hiện bug bằng input/test case cụ thể;
- phân biệt compile warning, assertion failure và output sai;
- viết test nhỏ bằng `assert`;
- compile debug build với symbol;
- dùng breakpoint, step, inspect và backtrace theo quy trình.

## 2. Bài toán mở đầu

Một hàm xếp loại từng sai đúng tại mốc `8.0` vì dùng `>` thay vì `>=`. Test “điểm 7” và “điểm 9” đều không lộ lỗi. Ta cần test boundary, không chỉ vài ví dụ thuận tiện.

## 3. Lời giải bằng code

Tạo file `grade_tests.c`:

```c
#include <assert.h>
#include <stdio.h>

char classify(double average)
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

void run_tests(void)
{
    /* Ba case quanh 8.0 bắt cả lỗi sai operator lẫn sai boundary. */
    assert(classify(8.1) == 'A');
    assert(classify(8.0) == 'A');
    assert(classify(7.9) == 'B');

    assert(classify(6.5) == 'B');
    assert(classify(6.4) == 'C');
    assert(classify(5.0) == 'C');
    assert(classify(4.9) == 'D');
}

int main(void)
{
    run_tests();
    printf("Tat ca test da qua.\n");
    return 0;
}
```

Compile debug build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror -O0 -g \
  grade_tests.c -o grade_tests
./grade_tests
```

Output:

```text
Tat ca test da qua.
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

## 4. Giải thích cơ chế

### 4.1. Test có arrange, act, assert

Trong expression:

```c
assert(classify(8.0) == 'A');
```

- arrange: input `8.0`;
- act: gọi `classify`;
- assert: so kết quả với `'A'`.

Nếu điều kiện false, `assert` ghi diagnostic và kết thúc bất thường. Dòng “tất cả test” chỉ xuất hiện nếu mọi assertion trước đã qua.

### 4.2. Boundary test

Mỗi ngưỡng cần ít nhất:

```text
ngay dưới | đúng ngưỡng | ngay trên
```

Test đúng `8.0` bắt lỗi dùng `>` thay vì `>=`. Chọn test từ nhánh và biên của logic, không chọn ngẫu nhiên.

### 4.3. Quy trình debug

```text
1. Tái hiện bằng test nhỏ ổn định
2. Đọc diagnostic đầu tiên
3. Đặt breakpoint trước state sai
4. Step từng statement
5. Inspect parameter/local và call stack
6. Sửa nguyên nhân nhỏ nhất
7. Chạy lại toàn bộ test
```

Với GDB:

```bash
gdb ./grade_tests
break classify
run
print average
backtrace
next
continue
```

### 4.4. Debug build

`-g` thêm thông tin để debugger ánh xạ machine code về source. `-O0` giảm optimization để bước chạy gần source hơn. Đây là cấu hình debug, không phải mặc định tối ưu cho production.

## 5. Kiến thức nền

### Test không chứng minh không còn bug

Test chỉ kiểm chứng các case và property đã viết. Coverage cao mà assertion yếu vẫn bỏ lọt lỗi. Ưu tiên behavior quan trọng, boundary và failure path.

### `assert` không thay validation

`assert` dành cho invariant/lỗi lập trình trong debug. Nếu build định nghĩa `NDEBUG`, assertion có thể bị loại bỏ. Không dùng `assert` để kiểm tra input người dùng hoặc điều kiện bắt buộc trong production.

### Regression test

Khi tìm thấy bug:

1. viết test đang fail vì bug;
2. sửa code;
3. giữ test để bug không quay lại.

### Sanitizer

Compiler thường hỗ trợ `-fsanitize=address,undefined` để bắt nhiều lỗi memory/undefined behavior khi test. Đây không thuộc chuẩn C11 nhưng rất hữu ích:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror -O1 -g \
  -fsanitize=address,undefined grade_tests.c -o grade_tests
```

Module 02 sẽ dùng sanitizer khi học pointer và cấp phát.

## 6. Lỗi thường gặp

### Debug bằng cách sửa nhiều nơi cùng lúc

Bạn mất khả năng biết thay đổi nào sửa lỗi. Tạo reproduction nhỏ, thay một giả thuyết mỗi lần.

### Chỉ test happy path

Thiếu boundary, input sai, empty và maximum.

### In rồi nhìn bằng mắt thay cho assertion

Output thủ công khó chạy lặp. Tách hàm tính và assert kết quả.

### Dựa vào `assert` trong production

Assertion có thể bị tắt và kết thúc process. Validate dữ liệu bên ngoài bằng flow lỗi bình thường.

### Debug optimized build rồi tin mọi local

Variable có thể bị optimized out hoặc statement đổi thứ tự. Dùng `-O0 -g` cho lần điều tra đầu.

### Không giữ test tái hiện

Bug dễ quay lại khi refactor. Giữ regression test.

## 7. Bài tập

### Bài 1 — Cố tình làm test fail

Đổi `>= 8.0` thành `> 8.0`, chạy và đọc assertion diagnostic rồi hoàn tác.

**Gợi ý:** case đúng ngưỡng phải fail.

### Bài 2 — Test hàm maximum

Test hai số bằng nhau, số âm và thứ tự đảo.

**Gợi ý:** mỗi case bảo vệ một giả định.

### Bài 3 — Debug bằng breakpoint

Đặt breakpoint ở `classify`, inspect `average` qua từng test.

**Gợi ý:** dùng `continue` sang invocation kế.

### Bài 4 — Test hàm tổng mảng

Test 1 element, nhiều element và số âm.

**Gợi ý:** array rỗng cần contract riêng.

### Bài 5 — Chạy sanitizer

Tạo bản sao lab, cố tình truy cập quá biên rồi quan sát sanitizer; sau đó xóa lỗi.

**Gợi ý:** không giữ undefined behavior trong source hoàn tất.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết test theo boundary.
- [ ] Tôi dùng `assert` cho test/invariant, không thay validation.
- [ ] Tôi compile được debug build `-O0 -g`.
- [ ] Tôi dùng breakpoint, inspect và backtrace.
- [ ] Tôi sửa nguyên nhân rồi chạy lại toàn bộ test.
- [ ] Tôi giữ regression test cho bug đã tìm.

Điều hướng:

- Prerequisite: [Chuỗi ký tự](./13-chuoi-ky-tu.md)
- Bài tiếp theo: [Dự án console quản lý điểm](./15-du-an-console-quan-ly-diem.md)
