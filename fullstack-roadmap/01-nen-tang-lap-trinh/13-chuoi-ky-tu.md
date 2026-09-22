# Chuỗi ký tự

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Chuỗi C là dãy char kết thúc bằng byte zero, không phải mọi mảng char đều là chuỗi.
- Dùng khi cần đọc, in và so sánh nội dung text theo byte.
- Capacity phải chừa terminator; số byte khác số ký tự người dùng nhìn thấy.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- biểu diễn string bằng mảng `char` kết thúc bởi `'\0'`;
- đọc một dòng có giới hạn mà không dùng input không giới hạn;
- in string bằng `%s`;
- dùng `strlen` và `strcmp`;
- phân biệt length với capacity.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một dãy chữ cần dấu kết thúc để người đọc biết dừng ở đâu. Trong C dấu đó là byte có giá trị 0. Nếu không để chỗ cho dấu kết thúc, thao tác in chuỗi có thể đọc tiếp ra ngoài dãy vì không biết đã hết tên.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| null terminator | byte zero đánh dấu hết chuỗi | '\0' |
| length | số byte nội dung trước terminator | strlen |
| capacity | toàn bộ chỗ có thể ghi | 31 byte |
| overflow input | dòng dài hơn sức chứa | báo lỗi nhưng đọc hết dòng |

### Ví dụ nhỏ — tính tay trước

Tên An cần ba slot: A, n, \0. strlen cho 2, sizeof mảng `char name[] = "An"` cho 3. Mảng capacity 2 chỉ giữ tối đa một byte nội dung nếu phải là chuỗi.

Chương trình đăng ký cần đọc cả tên có khoảng trắng, tối đa **30 byte
nội dung**, rồi kiểm tra có trùng `"Lan Anh"` không. `getchar` một lần
không đủ; ta cần mảng ký tự, byte kết thúc và validation overflow.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `name_check.c`:

```c
#include <stdio.h>
#include <string.h>

int read_line(char text[], int capacity)
{
    if (capacity <= 0) {
        return -2;
    }

    int length = 0;
    int overflow = 0;
    int character = getchar();

    while (character != '\n' && character != EOF) {
        /* Luôn giữ lại một slot cuối cho null terminator. */
        if (length < capacity - 1) {
            text[length] = (char)character;
            length++;
        } else {
            overflow = 1;
        }
        character = getchar();
    }

    text[length] = '\0';

    if (overflow) {
        return -1;
    }
    if (character == EOF && length == 0) {
        return 0;
    }
    return 1;
}

int main(void)
{
    char name[31];
    const char expected[] = "Lan Anh";

    printf("Nhap ten: ");
    int status = read_line(name, 31);

    if (status == 0) {
        fprintf(stderr, "Khong co input.\n");
        return 1;
    }
    if (status < 0) {
        fprintf(stderr, "Ten qua dai.\n");
        return 2;
    }
    if (name[0] == '\0') {
        fprintf(stderr, "Ten khong duoc rong.\n");
        return 3;
    }

    printf("Ten: %s\n", name);
    printf("Do dai: %zu\n", strlen(name));
    printf("Trung ten mau: %d\n", strcmp(name, expected) == 0);

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror name_check.c -o name_check
printf 'Lan Anh\n' | ./name_check
```

Output:

```text
Nhap ten: Ten: Lan Anh
Do dai: 7
Trung ten mau: 1
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. read_line đọc từng byte Lan Anh, length tăng tới 7 rồi đặt '\0' ở index 7.
2. Nếu dòng vượt 30 byte, hàm ngừng ghi nhưng vẫn đọc tới newline/EOF và trả -1.
3. Caller chỉ gọi strlen/strcmp sau khi đã kiểm tra status và tên rỗng.
4. name nằm trong main, local đọc dòng nằm trong invocation read_line. CPU đọc từng byte; strlen lại duyệt tới terminator, không có độ dài được lưu sẵn trong chuỗi.

### Mini-check

Dòng 31 byte bị từ chối; vì sao vẫn phải đọc hết dòng thay vì return ngay khi buffer đầy?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. String là mảng `char` có terminator

```text
name capacity 31
index: 0   1   2   3   4   5   6   7   8 ... 30
       L   a   n  ' '  A   n   h  \0  ?     ?
length = 7
```

`'\0'` có giá trị zero và đánh dấu kết thúc string. Nó không phải ký tự
`'0'`. Capacity 31 dành đúng tối đa 30 byte nội dung cộng một
terminator.

### 4.2. `read_line` luôn chừa chỗ kết thúc

Caller phải truyền một mảng `char` thực có ít nhất `capacity` element.
Hàm từ chối `capacity <= 0` trước khi đọc hoặc ghi. Khi contract đó
đúng, nó chỉ ghi nội dung nếu `length < capacity - 1`, luôn chừa một
slot cho `'\0'`.

Dù input hợp lệ hay quá dài, hàm tiêu thụ đến newline/EOF và đặt
terminator trong biên. Nó kiểm tra `overflow` trước trường hợp EOF rỗng,
nên capacity 1 nhận dữ liệu rồi gặp EOF vẫn được báo là quá dài. Trạng
thái trả về:

- `1`: có một dòng hợp lệ nằm trong capacity;
- `0`: EOF trước khi có ký tự;
- `-1`: dòng quá dài.
- `-2`: caller truyền `capacity <= 0`; hàm từ chối trước lần ghi đầu.

### 4.3. `strlen` và `strcmp`

- `strlen(name)` đếm byte trước `'\0'`, không tính terminator; kết quả dùng format `%zu`.
- `strcmp(left, right)` trả `0` khi hai string bằng nhau; nhỏ/lớn hơn 0 cho thứ tự từ điển theo character code.

Không viết `name == expected` để so nội dung mảng.

### 4.4. Mảng string trong call stack

```text
main frame
┌────────────────────────────────┐
│ name[31]: L a n ... \0         │
│ expected[8]: L a n ... h \0    │
│ status                         │
└────────────────────────────────┘
        ^
        | read_line thao tác trên các element của name
read_line frame giữ length, overflow, character
```

Như bài 11, array parameter cho hàm truy cập cùng các element. Cơ chế pointer đầy đủ thuộc module 02.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| strlen | đếm byte tới terminator | tốn một lượt duyệt; không dùng để đếm ký tự Unicode hiển thị |
| sizeof array | size storage tại nơi còn full array | không duyệt text; không thay cho length |
| strcmp / == | so nội dung / không so nội dung mảng | dùng strcmp==0; không suy bằng nhau từ tên biến |

### Misconception check

**Đúng hay sai?** strlen gồm cả terminator.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: nó đếm byte trước terminator.

</details>

**Đúng hay sai?** Capacity 31 chứa được 31 byte nội dung như một chuỗi C.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ 30 nếu còn cần terminator.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** terminator, length, capacity.

- **Working Developer — dùng khi làm việc:** biên input và status.

- **Deep Dive — có thể quay lại sau:** UTF-8, embedded zero, lỗi I/O.

### String literal và mảng sửa được

```c
char name[] = "Lan";
```

tạo mảng có bốn element `L,a,n,\0`, và element của mảng này sửa được. Không cố sửa string literal thông qua cách truy cập khác; hành vi là undefined.

### Các ký tự escape

- `'\n'`: newline;
- `'\t'`: tab;
- `'\0'`: null terminator;
- `'\\'`: backslash;
- `'\''`: single quote.

### Sao chép string

Copy string phải copy cả terminator và bảo đảm destination capacity. Có thể dùng loop có biên. Một số API như `strcpy` không biết destination capacity nên chỉ an toàn khi caller đã chứng minh đủ chỗ; không dùng nó với input có độ dài chưa kiểm soát.

### Đào sâu (có thể quay lại sau)

`strlen` và `strcmp` đọc đến `'\0'`. Nếu mảng không có terminator trong
vùng hợp lệ, chúng đọc vượt biên và gây undefined behavior. In `%s` cũng
có precondition tương tự. Contract 30 của bài là **30 byte**, không phải
30 ký tự người dùng nhìn thấy: UTF-8 có thể dùng nhiều byte cho một ký
tự; `strlen` đếm byte, không đếm grapheme.

## 6. Lỗi thường gặp

### Không chừa slot cho `'\0'`

Mảng capacity N chỉ chứa string tối đa N-1 byte nội dung.

### So string bằng `==`

Đó không phải so nội dung. Dùng `strcmp(...) == 0`.

### Bỏ qua dòng quá dài

Nếu chỉ giữ phần đầu và để phần sau trong stdin, lần đọc kế nhận dữ liệu thừa. Sample tiêu thụ hết rồi báo lỗi.

### Dùng `%d` cho `strlen`

Kết quả `strlen` có type phù hợp `%zu`, không bảo đảm là `int`.

### Nhầm `'\0'`, `'0'` và `0`

`'\0'` là character value zero; `'0'` là chữ số có mã khác zero.

## 7. Khi nào KHÔNG dùng

Không dùng char đơn cho một tên hoặc so == để so text. Không dùng parser ASCII này để khẳng định đã xử lý tên Unicode theo ký tự. Với text người dùng, xác định contract byte hoặc dùng thư viện phù hợp khi yêu cầu vượt byte-level.

## 8. Production notes & scale check

Team nhỏ vẫn cần biên 0,30,31 byte và EOF. Tên có dấu có thể chiếm nhiều byte; đừng đổi nhãn giới hạn thành “30 ký tự”. Input có byte zero bên trong hoặc lỗi stream chưa được sample phân loại riêng: với nguồn binary cần contract khác. Muốn lưu tên lâu dài phải copy đủ buffer và xác định vòng đời.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Đếm ký tự cụ thể

Đếm số lần ký tự `'a'` xuất hiện trước `'\0'`.

**Gợi ý:** loop theo index và dừng khi element bằng `'\0'`.

### Bài 2 — Copy có capacity

Viết hàm copy string bằng loop, trả lỗi nếu destination quá nhỏ.

**Gợi ý:** cần chỗ cho cả terminator.

### Bài 3 — So sánh không phân biệt hoa cho ASCII

So hai tên chỉ gồm chữ ASCII bằng cách quy đổi từng chữ hoa.

**Gợi ý:** `<ctype.h>` có `tolower`; đọc contract type trước khi gọi.

### Bài 4 — Test biên input

Test dòng rỗng, đúng 30 byte, 31 byte và EOF.

**Gợi ý:** 30 byte phải vừa buffer; 31 byte phải báo quá dài. Kiểm tra cả
exit status, không chỉ output.

## 10. Bài tập tích hợp liên module — Judgment

Khi chuyển sang C# Module 04, string không có cùng API/representation C. Quy tắc “tối đa 30 ký tự hiển thị” nên đo byte hay ký tự? Nêu yêu cầu còn thiếu trước khi chọn cách validate.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ memory của An cùng terminator.
2. Vì sao strlen không biết capacity?
3. Tên quá dài có ảnh hưởng lần đọc tiếp theo thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi vẽ string gồm nội dung và `'\0'`.
- [ ] Tôi phân biệt length với capacity.
- [ ] Tôi không ghi quá `capacity - 1`.
- [ ] Tôi dùng `%s`, `%zu`, `strlen`, `strcmp` đúng contract.
- [ ] Tôi xử lý dòng quá dài và EOF.
- [ ] Tôi biết `strlen` đếm byte trước terminator.

Điều hướng:

- Prerequisite: [Mảng hai chiều](./12-mang-hai-chieu.md)
- Bài tiếp theo: [Debug và kiểm thử chương trình C](./14-debug-va-kiem-thu-chuong-trinh-c.md)
