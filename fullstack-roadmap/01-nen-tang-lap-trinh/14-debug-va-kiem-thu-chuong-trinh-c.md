# Debug và kiểm thử chương trình C

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Test đối chiếu behavior với kỳ vọng; debugger cho thấy state tại lúc chạy.
- Dùng khi cần tái hiện và xác định nguyên nhân output sai.
- Test xanh chỉ bao phủ ca đã kiểm tra; assert có thể bị tắt bởi NDEBUG.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tái hiện bug bằng input/test case cụ thể;
- phân biệt compile warning, assertion failure và output sai;
- viết test nhỏ bằng `assert`;
- compile debug build với symbol;
- dùng breakpoint, step, inspect và backtrace theo quy trình.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Thay vì đoán vì sao điểm 8 bị xếp sai, viết một ca nhỏ buộc lỗi xuất hiện. Test giống một câu hỏi có đáp án cố định. Debugger cho dừng chương trình để nhìn đúng giá trị đã dẫn tới đáp án sai; sửa ít nhất có thể rồi giữ ca hỏi đó.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| assertion | kiểm tra một điều phải đúng trong test | classify(8.0)==A |
| breakpoint | điểm dừng execution để quan sát | đầu classify |
| regression test | ca giữ lại để chặn lỗi tái xuất | đúng ngưỡng 8.0 |
| sanitizer | công cụ phát hiện một số lỗi khi chạy | address/undefined sanitizer |

### Ví dụ nhỏ — tính tay trước

Ngưỡng A là >=8: 7.9→B, 8.0→A, 8.1→A. Nếu đổi thành >8, chỉ ca giữa fail; hai ca ngoài không đủ bắt bug.

Một hàm xếp loại từng sai đúng tại mốc `8.0` vì dùng `>` thay vì `>=`. Test “điểm 7” và “điểm 9” đều không lộ lỗi. Ta cần test boundary, không chỉ vài ví dụ thuận tiện.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. main gọi run_tests, mỗi assertion gọi classify với một input mới.
2. classify thử các ngưỡng và trả grade; assertion so kết quả với kỳ vọng độc lập.
3. Nếu sai, process dừng bất thường trước dòng thành công; nếu đúng hết, mới in Tat ca test da qua.
4. State nằm trong lời gọi đang kiểm tra; số phép tính tăng theo số ca. Instrumentation/debug làm thêm việc nên không dùng thời gian sanitizer làm benchmark release.

### Mini-check

Nếu bỏ hết assert mà vẫn in “Tat ca test da qua”, dòng output còn chứng minh điều gì?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Test output | so behavior với contract | tự động lặp lại; không chỉ ra mọi nguyên nhân |
| Debugger | quan sát state và đường gọi | tốn công điều tra; không thay regression test |
| assert / validation | phát hiện lỗi lập trình / xử lý input ngoài | assert có thể bị tắt; validation phải hoạt động trong production |

### Misconception check

**Đúng hay sai?** Chạy không crash nghĩa là test đã kiểm tra mọi output.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần kỳ vọng và assertion cụ thể.

</details>

**Đúng hay sai?** Có thể dùng assert để từ chối input user ở mọi build.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: NDEBUG có thể loại bỏ kiểm tra.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** test biên và diagnostic.

- **Working Developer — dùng khi làm việc:** quy trình tái hiện → sửa → regression.

- **Deep Dive — có thể quay lại sau:** sanitizer và optimized debug.

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

## 7. Khi nào KHÔNG dùng

Không bật breakpoint để kiểm tra hàng nghìn ca có thể tự động so output. Không dùng assert cho lỗi input bình thường. Không thêm test lặp đúng công thức implementation mà thiếu kỳ vọng độc lập; chọn ca từ contract và bug đã tái hiện.

## 8. Production notes & scale check

Team 2–3 người nên giữ vài test biên chạy trong CI (kiểm tra tự động sau thay đổi) trước khi thêm framework lớn. Ghi input, compiler, output, status và backtrace trong bug report. Sanitizer bắt nhiều lỗi tại đường thực sự chạy, không chứng minh không còn lỗi ở đường chưa chạy.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Module 02 có lỗi memory không thể phát hiện chỉ bằng output. Chọn kết hợp expected output, sanitizer hay chỉ một công cụ? Nêu loại bằng chứng từng công cụ cung cấp, không coi pass một ca là bảo đảm toàn bộ chương trình.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vì sao cần đúng ngưỡng, không chỉ hai phía?
2. Một bug report tái hiện được cần gì?
3. NDEBUG ảnh hưởng assert thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi viết test theo boundary.
- [ ] Tôi dùng `assert` cho test/invariant, không thay validation.
- [ ] Tôi compile được debug build `-O0 -g`.
- [ ] Tôi dùng breakpoint, inspect và backtrace.
- [ ] Tôi sửa nguyên nhân rồi chạy lại toàn bộ test.
- [ ] Tôi giữ regression test cho bug đã tìm.

Điều hướng:

- Prerequisite: [Chuỗi ký tự](./13-chuoi-ky-tu.md)
- Bài tiếp theo: [Dự án console quản lý điểm](./15-du-an-console-quan-ly-diem.md)
