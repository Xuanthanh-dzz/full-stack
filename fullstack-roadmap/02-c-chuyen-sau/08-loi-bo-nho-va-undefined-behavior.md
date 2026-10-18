# Lỗi bộ nhớ và undefined behavior

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Lỗi bộ nhớ xảy ra khi truy cập sai biên, sai vòng đời hoặc giải phóng sai quyền sở hữu.
- Dùng contract và sanitizer để tìm bằng chứng lỗi trên đường chạy đã thực thi.
- Undefined behavior không đảm bảo crash; một lần chạy không lỗi không chứng minh chương trình an toàn.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- nhận diện out-of-bounds, use-after-free, double free, leak và pointer chưa khởi tạo;
- hiểu undefined behavior không phải là một loại exception có thể bắt;
- viết ownership API nhỏ để giảm khả năng dùng pointer sau giải phóng;
- dùng AddressSanitizer và UndefinedBehaviorSanitizer để tìm lỗi khi phát triển;
- audit đường đi thành công và thất bại để đảm bảo mỗi allocation được giải phóng đúng một lần.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Đọc một trang ngoài cuốn sổ hay dùng chìa khóa phòng đã trả đều không có kết quả được cam kết. Máy đôi khi vẫn in dữ liệu nhìn hợp lý, nhưng điều đó không biến thao tác sai thành hợp lệ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| undefined behavior — UB | chuẩn không đặt yêu cầu cho hành vi của chương trình ở tình huống đó | đọc ngoài vùng hợp lệ |
| use-after-free | dùng storage sau khi đã giải phóng | alias còn giữ địa chỉ cũ |
| double free | giải phóng lại cùng allocation đã hết quyền sở hữu | hai owner giả |
| sanitizer | công cụ thêm kiểm tra lúc chạy để phát hiện một số lỗi | AddressSanitizer và UndefinedBehaviorSanitizer |

### Ví dụ nhỏ — tính tay trước

Chuỗi "AB" cần 3 byte A, B, 0. Chỉ số ký tự hợp lệ để trả ở đây là 0 và 1; index 2 là terminator. Khi free owner, alias từng trỏ A không được đọc nữa dù còn giữ cùng con số địa chỉ.

Ta cần sao chép một mã sản phẩm vào vùng nhớ động, đọc một ký tự có kiểm tra giới hạn rồi giải phóng. API phải an toàn cả khi hàm giải phóng được gọi hai lần qua cùng owner pointer.

Mục tiêu không chỉ là “chương trình không crash”. Ta phải chứng minh:

- mọi lần đọc nằm trong object;
- object vẫn còn lifetime;
- owner không bị thất lạc;
- sau giải phóng, owner pointer không còn giữ địa chỉ cũ.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.c`:

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char *duplicate_text(const char *source)
{
    if (source == NULL) {
        return NULL;
    }

    size_t length = strlen(source);
    if (length == SIZE_MAX) {
        return NULL;
    }

    char *copy = malloc(length + 1);
    if (copy == NULL) {
        return NULL;
    }

    for (size_t index = 0; index <= length; ++index) {
        copy[index] = source[index];
    }

    return copy;
}

static int try_get_character(
    const char *text,
    size_t index,
    char *result
)
{
    if (text == NULL || result == NULL) {
        return 0;
    }

    size_t length = strlen(text);
    if (index >= length) {
        return 0;
    }

    *result = text[index];
    return 1;
}

static void release_text(char **owner)
{
    if (owner == NULL) {
        return;
    }

    /* Reset the same owner object so repeated release through it is safe. */
    free(*owner);
    *owner = NULL;
}

int main(void)
{
    char *code = duplicate_text("BOOK-2026");
    if (code == NULL) {
        fprintf(stderr, "Khong sao chep duoc ma\n");
        return 1;
    }

    char selected = '\0';
    if (!try_get_character(code, 4, &selected)) {
        release_text(&code);
        return 1;
    }

    printf("Ban sao: %s\n", code);
    printf("Ky tu vi tri 4: %c\n", selected);
    printf(
        "Vi tri 99: %s\n",
        try_get_character(code, 99, &selected) ? "hop le" : "bi tu choi"
    );

    release_text(&code);
    release_text(&code);

    printf("Owner sau release: %s\n", code == NULL ? "NULL" : "con dia chi");
    return 0;
}
```

Build và chạy bình thường:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o memory-safety
./memory-safety
```

Output:

```text
Ban sao: BOOK-2026
Ky tu vi tri 4: -
Vi tri 99: bi tu choi
Owner sau release: NULL
```

Trong lúc phát triển với GCC hoặc Clang, build thêm sanitizer:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror \
  -fsanitize=address,undefined -fno-omit-frame-pointer -g \
  main.c -o memory-safety-sanitized
./memory-safety-sanitized
```

Chương trình đúng không tạo báo cáo sanitizer.

### Walkthrough — execution / state / cost

1. duplicate_text tạo bản sao BOOK-2026 trong storage riêng và trả owner.
2. try_get kiểm tra vị trí trước khi ghi output; index 4 cho dấu -, index 99 bị từ chối.
3. release_text nhận địa chỉ owner, free rồi đặt owner về NULL; gọi lại với owner NULL không giải phóng allocation cũ lần nữa.
4. Copy/đo độ dài tốn thời gian theo số byte; storage bản sao cũng theo chiều dài. Sanitizer quan sát các đường chạy này, không tự kiểm tra mọi input hoặc mọi alias.

### Mini-check

Output của try_get nên đổi không khi index = 99? Thiết kế assertion để phát hiện ghi output trước validation.

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Một allocation, một owner

`duplicate_text` cấp đúng `length + 1` byte:

```text
Stack main                  Heap

code = H1 ────────────────► H1: B O O K - 2 0 2 6 \0
                             allocation do code sở hữu
```

Vòng lặp dùng `index <= length` để sao chép cả terminator `'\0'`. Đây không phải lỗi vượt biên vì block có `length + 1` phần tử, chỉ số hợp lệ cuối là `length`.

### Bounds check trước access

`try_get_character` tính chiều dài rồi từ chối `index >= length`. Hàm không cho đọc terminator như một ký tự dữ liệu và không đọc ngoài block.

Output parameter chỉ được ghi sau khi mọi kiểm tra thành công. Nếu hàm thất bại, bên gọi không dùng một kết quả mới.

### Kết thúc ownership qua pointer cấp hai

`release_text` nhận địa chỉ owner pointer:

```text
owner ──► code ──► H1
```

Sau:

```c
free(*owner);
*owner = NULL;
```

trạng thái là:

```text
owner ──► code = NULL       H1 đã hết lifetime
```

Lần gọi thứ hai truyền `free(NULL)`, thao tác hợp lệ và không làm gì. Mẫu này chỉ bảo vệ việc gọi lại qua **cùng object owner**. Nếu trước đó có alias khác trỏ H1, alias đó không tự trở thành `NULL`; sau khi lifetime của H1 kết thúc, không được đọc, so sánh, in hay dereference giá trị alias đó.

### Undefined behavior là gì

Khi chương trình thực hiện thao tác mà chuẩn C không quy định hành vi—như đọc ngoài mảng hoặc dereference pointer đã `free`—toàn bộ execution không còn được chuẩn đảm bảo.

Hệ quả có thể là:

- crash ngay;
- in dữ liệu cũ và có vẻ đúng;
- hỏng dữ liệu ở chỗ khác;
- chỉ lỗi khi tối ưu;
- tạo lỗ hổng bảo mật.

Không có yêu cầu “compiler phải báo” hoặc “runtime phải ném lỗi”. Vì vậy test chạy qua một lần không chứng minh code không có undefined behavior.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| NULL check | loại con trỏ rỗng | rẻ; không phát hiện mọi dangling pointer |
| Kiểm tra biên/vòng đời | chứng minh điều kiện trước truy cập | cần contract caller; nền tảng correctness |
| Sanitizer | phát hiện một số vi phạm khi chạy | thêm thời gian/bộ nhớ; dùng test, không coi PASS là chứng minh tuyệt đối |

### Misconception check

**Đúng hay sai?** Không crash nghĩa là không có UB.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: UB có thể biểu hiện khác giữa compiler, tối ưu và lần chạy.

</details>

**Đúng hay sai?** Đặt owner = NULL làm mọi alias khác an toàn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ object pointer đó đổi; alias khác vẫn cần bị bỏ hoặc cập nhật.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** nhận ra biên và vòng đời sai.

- **Working Developer — dùng khi làm việc:** tái hiện bằng sanitizer và regression.

- **Deep Dive — có thể quay lại sau:** giới hạn công cụ và tối ưu dưới giả định không có UB.

### Năm nhóm lỗi cần audit

1. **Out-of-bounds:** truy cập trước đầu hoặc sau cuối object.
2. **Use-after-free / dangling:** dùng pointer sau khi lifetime object đã kết thúc.
3. **Double free / invalid free:** giải phóng hai lần hoặc giải phóng địa chỉ không phải đầu allocation sống.
4. **Memory leak:** allocation còn sống nhưng chương trình mất mọi owner pointer cần để `free`.
5. **Uninitialized/indeterminate read:** đọc object chưa được gán giá trị phù hợp.

### Phản ví dụ: không chạy, không dùng trong production

Các đoạn sau chỉ để nhận diện lỗi.

Out-of-bounds:

```c
int values[3] = {1, 2, 3};
int invalid = values[3]; /* UB: chỉ số hợp lệ là 0..2 */
```

Use-after-free:

```c
int *value = malloc(sizeof *value);
if (value != NULL) {
    *value = 10;
    free(value);
    printf("%d\n", *value); /* UB */
}
```

Double free:

```c
int *value = malloc(sizeof *value);
free(value);
free(value); /* UB nếu allocation đầu đã được tạo */
```

Leak do ghi đè owner:

```c
int *values = malloc(10 * sizeof *values);
values = NULL; /* mất địa chỉ nếu malloc thành công */
```

Pointer chưa khởi tạo:

```c
int *pointer;
*pointer = 5; /* UB */
```

### Sanitizer hỗ trợ nhưng không thay thế reasoning

AddressSanitizer thường phát hiện out-of-bounds, use-after-free và double free trong đường code đã chạy. UndefinedBehaviorSanitizer phát hiện một số UB như signed integer overflow hoặc alignment sai.

Giới hạn:

- chỉ kiểm tra execution và input đã chạy;
- không chứng minh mọi đường đi đều an toàn;
- không thay thế compiler warning, review và test;
- tùy compiler/nền tảng, flags có thể khác hoặc không có.

### Cleanup theo mọi đường đi

Sau mỗi allocation thành công, liệt kê mọi `return` tiếp theo. Mỗi đường phải:

- chuyển ownership rõ ràng; hoặc
- giải phóng allocation đúng một lần.

Quy tắc này sẽ được áp dụng trong file I/O và dự án cuối module.

### Đào sâu (có thể quay lại sau)

Compiler tối ưu dựa trên giả định chương trình không thực hiện undefined behavior. Vì vậy một check viết sau thao tác UB có thể không cứu được chương trình; quyền suy luận của optimizer có thể làm kết quả khác giữa `-O0` và `-O2`.

Theo C11, khi lifetime của object đích kết thúc, giá trị pointer trỏ tới object đó trở thành **indeterminate**. Vì vậy không được giả định pointer còn một bit pattern cụ thể, cũng không đọc, so sánh hoặc in giá trị cũ sau `free`. Nếu cần log địa chỉ để debug, hãy in nó **trước** `free`; ngay sau `free`, gán owner pointer thành `NULL` mà không đọc lại giá trị cũ. Allocator có thể tái sử dụng cùng địa chỉ số cho allocation khác, nhưng điều đó cũng không làm object cũ sống lại.

Sanitizer cũng thay đổi layout và timing, nên một bug biến mất dưới sanitizer vẫn cần được xử lý bằng contract/lifetime reasoning.

## 6. Lỗi thường gặp

### Gán `NULL` một alias rồi nghĩ mọi alias an toàn

```text
owner ──► H1
alias ──► H1
```

Sau `free(owner); owner = NULL;`, object pointer `alias` không tự được gán `NULL`, nhưng giá trị của nó đã indeterminate vì H1 hết lifetime. Dừng dùng mọi alias trước khi giải phóng; không đọc, so sánh, in hoặc dereference chúng sau đó.

### Dựa vào crash để phát hiện UB

UB có thể im lặng. Bật warning, sanitizer, test biên và review ownership.

### Quên byte cho `'\0'`

Chuỗi dài `length` cần ít nhất `length + 1` byte. Đồng thời phải kiểm tra overflow trước phép cộng nếu kích thước đến từ nguồn không tin cậy.

### Cleanup chỉ ở đường thành công

Nếu một bước sau allocation thất bại, phải giải phóng tài nguyên đã tạo trước đó. Liệt kê tài nguyên theo thứ tự acquire và release theo thứ tự ngược.

### Tin rằng `realloc` thất bại đã giải phóng block cũ

Khi `realloc` trả `NULL` với kích thước khác `0`, allocation cũ vẫn sống. Owner phải giữ địa chỉ cũ và `free` sau.

## 7. Khi nào KHÔNG dùng

Không cố phục hồi bằng cách tiếp tục đọc pointer đã free để xem còn dữ liệu không. Không dùng sanitizer thay quy tắc ownership; công cụ chỉ quan sát những đường chạy đã được test.

## 8. Production notes & scale check

Team nhỏ nên bật warning và sanitizer ở CI, lưu lệnh/input/stack trace của lỗi đầu tiên. Demo copy một chuỗi nhỏ chưa cần allocator riêng. Ca rỗng, index sát biên, release hai lần và allocation failure có giá trị hơn chỉ chạy happy path dài.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Sao chép mảng `int`

Viết hàm tạo bản sao động của mảng và trả qua output pointer.

**Gợi ý:** kiểm tra overflow `count * sizeof **result`; chỉ cập nhật `*result` sau khi allocation và copy thành công.

### Bài 2 — API release

Viết `release_int_array(int **owner)` và chứng minh gọi hai lần qua cùng owner là an toàn.

**Gợi ý:** `free(NULL)` hợp lệ; sau `free`, đặt `*owner = NULL`.

### Bài 3 — Audit `realloc`

Viết hai phiên bản mở rộng mảng: một phiên bản sai làm mất owner và một phiên bản đúng. Không chạy phiên bản sai; giải thích đường lỗi.

**Gợi ý:** đánh dấu trạng thái khi `realloc` trả `NULL`.

### Bài 4 — Chạy sanitizer

Cố tình tạo một project học tập riêng có out-of-bounds, chạy AddressSanitizer, đọc stack trace rồi sửa. Không đưa phiên bản lỗi vào production.

**Gợi ý:** build với `-g -fsanitize=address,undefined -fno-omit-frame-pointer`.

### Bài 5 — Bảng ownership

Với một chương trình có ba allocation, lập bảng: tên owner, thời điểm acquire, các borrower, đường cleanup và thời điểm release.

**Gợi ý:** mỗi dòng phải có đúng một owner chịu trách nhiệm cuối.

## 10. Bài tập tích hợp liên module — Judgment

Kết hợp debug Module 01 và vòng đời bài 06: người review thấy test PASS nhưng code trả pointer local. Bạn có chấp nhận không? Nêu bằng chứng source, cách tái hiện phù hợp và giới hạn của một test không crash.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Phân biệt leak và use-after-free.
2. Vì sao strlen cũng đòi chuỗi hợp lệ trước khi gọi?
3. Nêu dữ liệu cần giữ trong báo cáo sanitizer.

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi nhận diện được năm nhóm lỗi bộ nhớ chính.
- [ ] Tôi biết UB không đảm bảo crash hay thông báo lỗi.
- [ ] Tôi audit mọi đường `return` sau allocation.
- [ ] Tôi hiểu gán một owner về `NULL` không sửa các alias.
- [ ] Tôi biết sanitizer hỗ trợ phát hiện, không chứng minh toàn bộ code đúng.

**Bài prerequisite:** [Cấp phát động: malloc, calloc, realloc và free](./07-cap-phat-dong-malloc-calloc-realloc-free.md)

**Bài tiếp theo:** [Struct, enum và typedef](./09-struct-enum-typedef.md)
