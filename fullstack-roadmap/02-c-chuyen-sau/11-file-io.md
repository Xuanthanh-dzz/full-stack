# File I/O

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- File I/O đưa dữ liệu ra khỏi vòng đời process; đọc lại phải kiểm tra format và lỗi từng bước.
- Dùng file text cho dữ liệu nhỏ, một người ghi, cần mở lại ở lần chạy sau.
- Mở chế độ w có thể xóa nội dung cũ; parse thành công một phần chưa phải file hợp lệ.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- mở và đóng text file bằng `fopen`/`fclose`;
- ghi dữ liệu có kiểm tra lỗi bằng `fprintf`;
- đọc theo từng dòng bằng `fgets`, rồi tách field và parse số có kiểm tra overflow;
- kiểm tra EOF và I/O error đúng cách;
- thiết kế format file có version thay vì ghi raw byte của `struct`;
- bảo đảm stream được đóng trên mọi đường đi.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Biến giống ghi chú trên bảng sẽ mất khi đóng chương trình; file giống sổ để lần sau đọc lại. Nhưng sổ có thể thiếu dòng, sai chữ hoặc không ghi hết. Chương trình phải kiểm tra cả lúc ghi lẫn lúc đọc thay vì tin file do mình từng tạo.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| stream | đối tượng thư viện quản lý đọc/ghi tuần tự | FILE * |
| format | quy tắc biểu diễn dữ liệu thành byte | header và trường ngăn bằng dấu `&#124;` |
| parse | chuyển văn bản theo quy tắc thành giá trị | chuỗi chữ số thành quantity |
| EOF | đã tới cuối dữ liệu đọc được | khác lỗi đọc ferror |
| close | kết thúc dùng stream, có thể phát hiện lỗi ghi còn đệm | fclose |

### Ví dụ nhỏ — tính tay trước

File hai dòng: header INV1 rồi BOOK|2|100. Đọc header đúng → tách ba trường → kiểm tra mã → đổi 2 và 100 → mới tạo record. Nếu quantity là 2x, không lấy tiền tố 2 rồi bỏ x.

Danh sách sản phẩm đang mất khi chương trình kết thúc. Ta cần ghi hai sản phẩm vào `inventory.txt`, mở lại, kiểm tra version, parse từng dòng và xóa file demo.

Ta chọn text format:

```text
INVENTORY_V1
BOOK-01|5|1200
PEN-02|20|150
```

Mỗi dòng sản phẩm có `code|quantity|price_cents`. Code không được chứa dấu `|`; độ dài tối đa là 15 ký tự. Format có header version để loader từ chối dữ liệu không tương thích.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.c`:

```c
#include <limits.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    char code[16];
    int quantity;
    long price_cents;
} Product;

static int product_is_valid(const Product *product)
{
    if (product == NULL
        || product->quantity < 0
        || product->price_cents < 0) {
        return 0;
    }

    size_t length = 0;
    while (length < sizeof product->code
           && product->code[length] != '\0') {
        char current = product->code[length];
        if (current == '|' || current == '\n' || current == '\r') {
            return 0;
        }
        ++length;
    }

    return length > 0 && length < sizeof product->code;
}

static int parse_nonnegative_int(const char *text, int *result)
{
    if (text == NULL || result == NULL || *text == '\0') {
        return 0;
    }

    int value = 0;
    for (size_t index = 0; text[index] != '\0'; ++index) {
        if (text[index] < '0' || text[index] > '9') {
            return 0;
        }

        int digit = text[index] - '0';
        if (value > (INT_MAX - digit) / 10) {
            return 0;
        }
        value = value * 10 + digit;
    }

    *result = value;
    return 1;
}

static int parse_nonnegative_long(const char *text, long *result)
{
    if (text == NULL || result == NULL || *text == '\0') {
        return 0;
    }

    long value = 0;
    for (size_t index = 0; text[index] != '\0'; ++index) {
        if (text[index] < '0' || text[index] > '9') {
            return 0;
        }

        int digit = text[index] - '0';
        if (value > (LONG_MAX - digit) / 10) {
            return 0;
        }
        value = value * 10 + digit;
    }

    *result = value;
    return 1;
}

static int parse_product_line(char *line, Product *product)
{
    if (line == NULL || product == NULL) {
        return 0;
    }

    size_t line_length = strlen(line);
    if (line_length > 0 && line[line_length - 1] == '\n') {
        line[--line_length] = '\0';
    }
    if (line_length > 0 && line[line_length - 1] == '\r') {
        line[--line_length] = '\0';
    }

    char *first_separator = strchr(line, '|');
    if (first_separator == NULL) {
        return 0;
    }
    *first_separator = '\0';

    char *quantity_text = first_separator + 1;
    char *second_separator = strchr(quantity_text, '|');
    if (second_separator == NULL) {
        return 0;
    }
    *second_separator = '\0';

    char *price_text = second_separator + 1;
    if (strchr(price_text, '|') != NULL) {
        return 0;
    }

    size_t code_length = strlen(line);
    if (code_length == 0 || code_length >= sizeof product->code) {
        return 0;
    }

    for (size_t index = 0; index <= code_length; ++index) {
        product->code[index] = line[index];
    }

    return parse_nonnegative_int(quantity_text, &product->quantity)
        && parse_nonnegative_long(price_text, &product->price_cents);
}

static int save_products(
    const char *path,
    const Product *products,
    size_t count
)
{
    if (path == NULL || (products == NULL && count > 0)) {
        return 0;
    }

    /*
     * Validate the complete snapshot before "w" can truncate an old file.
     * A malformed record therefore cannot leave a partially replaced file.
     */
    for (size_t index = 0; index < count; ++index) {
        if (!product_is_valid(&products[index])) {
            return 0;
        }
    }

    FILE *file = fopen(path, "w");
    if (file == NULL) {
        return 0;
    }

    int succeeded = fprintf(file, "INVENTORY_V1\n") >= 0;

    for (size_t index = 0; succeeded && index < count; ++index) {
        if (fprintf(
                file,
                "%s|%d|%ld\n",
                products[index].code,
                products[index].quantity,
                products[index].price_cents
            ) < 0) {
            succeeded = 0;
        }
    }

    if (fclose(file) != 0) {
        succeeded = 0;
    }

    return succeeded;
}

static int load_and_print_products(
    const char *path,
    size_t *loaded_count
)
{
    if (path == NULL || loaded_count == NULL) {
        return 0;
    }

    *loaded_count = 0;

    FILE *file = fopen(path, "r");
    if (file == NULL) {
        return 0;
    }

    char line[128];
    int succeeded = 1;

    if (fgets(line, sizeof line, file) == NULL
        || strcmp(line, "INVENTORY_V1\n") != 0) {
        succeeded = 0;
    }

    while (succeeded && fgets(line, sizeof line, file) != NULL) {
        /* The canonical format requires every record to end with '\n'. */
        if (strchr(line, '\n') == NULL) {
            succeeded = 0;
            break;
        }

        Product product = {0};
        if (!parse_product_line(line, &product)
            || !product_is_valid(&product)) {
            succeeded = 0;
            break;
        }

        printf(
            "%s | quantity=%d | price=%ld\n",
            product.code,
            product.quantity,
            product.price_cents
        );
        ++*loaded_count;
    }

    if (ferror(file)) {
        succeeded = 0;
    }

    if (fclose(file) != 0) {
        succeeded = 0;
    }

    return succeeded;
}

int main(void)
{
    const char *path = "inventory.txt";
    const Product products[] = {
        {.code = "BOOK-01", .quantity = 5, .price_cents = 1200},
        {.code = "PEN-02", .quantity = 20, .price_cents = 150}
    };
    size_t product_count = sizeof products / sizeof products[0];

    if (!save_products(path, products, product_count)) {
        fprintf(stderr, "Khong ghi duoc file\n");
        return 1;
    }
    printf("Da ghi %zu san pham\n", product_count);

    size_t loaded_count = 0;
    if (!load_and_print_products(path, &loaded_count)) {
        fprintf(stderr, "Khong doc duoc file\n");
        remove(path);
        return 1;
    }
    printf("Da doc %zu san pham\n", loaded_count);

    if (remove(path) != 0) {
        fprintf(stderr, "Khong xoa duoc file demo\n");
        return 1;
    }
    printf("Da xoa file demo\n");
    return 0;
}
```

Build và chạy trong thư mục lab riêng. Chương trình cố ý tạo/truncate rồi xóa `inventory.txt`; không chạy tại nơi đang có dữ liệu thật cùng tên:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o file-io
./file-io
```

Output:

```text
Da ghi 2 san pham
BOOK-01 | quantity=5 | price=1200
PEN-02 | quantity=20 | price=150
Da doc 2 san pham
Da xoa file demo
```

### Walkthrough — execution / state / cost

1. main chuẩn bị BOOK-01 và PEN-02 trong memory rồi gọi lưu inventory.txt ở thư mục thử riêng.
2. Hàm kiểm tra dữ liệu trước fopen(w), ghi header/record và kiểm tra cả fclose.
3. Hàm đọc dùng buffer dòng hữu hạn, đòi newline và các trường hợp lệ trước đổi số; giá trị quá lớn bị chặn trước tràn.
4. Đọc xong đóng file và sample xóa file thử. Memory dùng theo buffer/record; cost chủ yếu là số byte I/O và parse, không chỉ số lời gọi fopen.

### Mini-check

File kết thúc giữa một dòng không có newline: sample coi hợp lệ hay lỗi? Vì sao quyết định đó phải nằm trong format contract?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### `FILE *` là handle tới stream

```c
FILE *file = fopen(path, "w");
```

Nếu thành công, thư viện C tạo trạng thái stream và trả một pointer `FILE *`. `FILE` là kiểu do thư viện quản lý; code không dereference hoặc tự `free(file)`.

```text
Stack                          Trạng thái do thư viện quản lý

file ────────────────────────► stream ghi inventory.txt
```

`file` là owner handle theo contract của hàm hiện tại. Nó phải được ghép với đúng một `fclose(file)`.

Mode:

- `"w"`: mở để ghi, tạo mới hoặc truncate file cũ;
- `"r"`: mở file đã tồn tại để đọc.

Nếu `fopen` thất bại, nó trả `NULL`; không có stream cần đóng.

### Ghi và xác nhận lỗi

Trước `%s`, `product_is_valid` duyệt tối đa đúng capacity `code[16]` để chứng minh có `'\0'`, code không rỗng/không chứa delimiter hoặc newline, và các số không âm. Hàm không gọi `strlen` hay `%s` trước khi chứng minh terminator, nên một record malformed không làm code đọc vượt mảng.

`fprintf` trả số ký tự đã ghi hoặc giá trị âm khi lỗi. Dữ liệu có thể còn nằm trong buffer thư viện, nên thành công của các lời gọi `fprintf` chưa đủ: `fclose` flush buffer và cũng có thể báo lỗi.

Hàm `save_products` giữ biến `succeeded`, nhưng vẫn luôn tới `fclose` sau khi stream đã mở.

### Đọc dòng trước, parse sau

`fgets(line, sizeof line, file)` đọc tối đa `sizeof line - 1` ký tự và luôn thêm `'\0'` khi đọc được dữ liệu.

Ta kiểm tra:

- header đúng version;
- mỗi record có newline kết thúc, nên dòng bị cắt hoặc chứa NUL ẩn đều bị từ chối;
- đúng hai delimiter tách thành ba field;
- không có delimiter hoặc ký tự thừa trong field số;
- code dài `1..15` và không chứa newline;
- từng field số chỉ có digit, không âm và không vượt `INT_MAX`/`LONG_MAX`.

Parser số tích lũy từng digit và kiểm tra `value > (MAX - digit) / 10` **trước** phép nhân/cộng. Vì vậy một token cực dài bị từ chối sạch, không đưa giá trị vượt miền vào `%d`, `%ld` hay phép tính signed.

### EOF khác I/O error

Khi `fgets` trả `NULL`, có thể vì:

- đã tới end-of-file;
- xảy ra lỗi đọc.

Sau vòng lặp, `ferror(file)` phân biệt lỗi. EOF bình thường không làm loader thất bại.

### Dữ liệu `Product` nằm ở đâu

Trong mỗi vòng lặp, `Product product` là object có automatic storage duration (thường minh họa bằng stack frame, không phải yêu cầu vị trí vật lý). Parser chỉ ghi member sau khi kiểm tra từng field. Code chỉ in rồi bỏ object; không trả pointer tới nó.

File chứa text độc lập với layout/padding của `Product`. Không có pointer hoặc địa chỉ process nào được ghi vào file.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Memory | state trong process | nhanh, mất khi thoát; đủ dữ liệu tạm |
| File text | state thành byte ngoài process | dễ xem nhưng phải parse/validate; hợp kho nhỏ một writer |
| Database | hệ quản trị lưu và truy vấn dữ liệu | thêm vận hành; chỉ cân nhắc khi truy vấn/đồng thời và durability có yêu cầu cụ thể |

### Misconception check

**Đúng hay sai?** fgets trả NULL luôn nghĩa là EOF bình thường.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần phân biệt EOF và lỗi qua trạng thái stream.

</details>

**Đúng hay sai?** Validate trước fopen(w) bảo đảm file cũ không bao giờ mất.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ ngăn truncate do input biết trước là sai; lỗi ghi sau khi mở vẫn có thể xảy ra.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** mở/đọc/ghi/đóng và kiểm tra kết quả.

- **Working Developer — dùng khi làm việc:** validate format và giới hạn dòng/số.

- **Deep Dive — có thể quay lại sau:** phân tích truncate, partial write và thay file an toàn.

### Các mode thường gặp

- `"r"`: đọc, file phải tồn tại;
- `"w"`: ghi và truncate;
- `"a"`: ghi nối cuối;
- thêm `"+"`: cho phép cả đọc và ghi;
- thêm `"b"`: binary mode, quan trọng trên hệ thống phân biệt text/binary.

Chọn mode nhỏ nhất đúng nhu cầu. Đừng mở `"w"` nếu chưa chấp nhận mất nội dung cũ.

### Text format và binary format

Text dễ debug và có thể version/validate rõ. Binary có thể nhỏ và nhanh hơn, nhưng phải tự quy định:

- byte order;
- kích thước integer;
- encoding;
- version;
- validation.

Không gọi `fwrite(&product, sizeof product, 1, file)` rồi coi đó là format portable: padding, enum layout, endianness và pointer member có thể khác.

### Parse trực tiếp và formatted input

Parse trực tiếp bằng `fscanf` dễ để lại phần input lỗi trong stream và khó giới hạn một record. Pattern production-minded hơn cho format dòng nhỏ:

1. `fgets` vào buffer có capacity rõ;
2. xác nhận có cả dòng;
3. tách delimiter và parse từng field với overflow check;
4. validate semantics.

Với format phức tạp, viết parser rõ ràng thay vì cố kéo dài format string.

### Vị trí và buffering

Stream có vị trí đọc/ghi và buffer. `fflush` yêu cầu đẩy dữ liệu ghi đang buffer; `fclose` vừa flush vừa giải phóng trạng thái stream. Không dùng `FILE *` sau `fclose`.

### Đào sâu (có thể quay lại sau)

Một lần ghi file thành công không mặc nhiên bảo đảm dữ liệu đã nằm bền vững trên thiết bị lưu trữ khi mất điện; C standard I/O không cung cấp mọi primitive durability của hệ điều hành. Dự án cuối dùng temp file + `rename` để tránh để lại nửa file ở mức ứng dụng, nhưng durability tuyệt đối còn phụ thuộc filesystem/OS.

`rename` thay thế file có khác biệt nền tảng. Khi cần production đa nền tảng, phải kiểm tra contract cụ thể của hệ điều hành và thiết kế recovery.

## 6. Lỗi thường gặp

### Quên kiểm tra `fopen`

Không gọi `fprintf`, `fgets` hay `fclose` với `file == NULL`.

### Quên kiểm tra `fclose` khi ghi

Lỗi flush có thể chỉ xuất hiện lúc đóng stream. Đừng báo “save thành công” trước khi `fclose` thành công.

### Đưa input không tin cậy thẳng vào numeric conversion của `scanf`

Ngoài việc phải giới hạn field chuỗi, formatted conversion còn khó kiểm soát token số vượt miền kiểu đích. Loader dùng parser digit có bound check trước mỗi phép tính; bài 14 sẽ giới thiệu `strtol` như API tổng quát hơn.

### Dùng `while (!feof(file))`

EOF chỉ được đặt sau một lần đọc không lấy được dữ liệu. Hãy dùng kết quả của `fgets` làm điều kiện vòng lặp, rồi kiểm tra `ferror`.

### Ghi raw `struct`

Raw memory layout không phải file contract portable. Serialize field theo format đã định nghĩa.

## 7. Khi nào KHÔNG dùng

Không dùng raw struct dump khi file phải đọc được qua compiler/phiên bản khác. Không dùng file text một writer làm kho dùng chung nhiều process nếu chưa có cơ chế phối hợp. Với demo, không cần database chỉ để lưu hai dòng.

## 8. Production notes & scale check

Team nhỏ cần test file thiếu, dòng dài, thiếu trường, số tràn và lỗi đóng/ghi. Sample chạy trong thư mục riêng, đường dẫn tin cậy; không tự nhận an toàn với path do người lạ cung cấp. Giữ bản sao file thật trước thử chế độ w; đây chưa phải giao thức lưu chống crash.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Nhật ký text

Ghi ba dòng log vào file bằng mode `"w"`, đóng, mở lại và in.

**Gợi ý:** kiểm tra mọi `fprintf`, `fgets` và `fclose`.

### Bài 2 — Append record

Thêm một record bằng mode `"a"` mà không truncate dữ liệu cũ.

**Gợi ý:** header không nên được ghi lại mỗi lần append.

### Bài 3 — Loader chặt hơn

Từ chối code rỗng, code có khoảng trắng và dòng dài hơn buffer.

**Gợi ý:** validate sau parse; nếu dòng bị cắt, drain phần còn lại hoặc fail toàn bộ.

### Bài 4 — Format version 2

Thêm member tên sản phẩm và tạo `INVENTORY_V2`; loader phải từ chối version không hỗ trợ.

**Gợi ý:** đừng âm thầm đọc V1 như V2.

### Bài 5 — Inject lỗi

Thử đọc đường dẫn không tồn tại và ghi vào vị trí không có quyền; xác nhận exit code và không dereference `NULL`.

**Gợi ý:** thông báo lỗi đi vào `stderr`.

## 10. Bài tập tích hợp liên module — Judgment

Capstone điểm Module 01 cần giữ dữ liệu qua lần chạy. Đề xuất header/version và cách từ chối file thiếu điểm cuối; giải thích khác biệt giữa validation trước ghi và bảo vệ dữ liệu cũ khi disk lỗi.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. EOF khác ferror thế nào?
2. Vì sao phải kiểm tra fclose sau ghi?
3. Một parser chấp nhận 12x thành 12 gây lỗi contract gì?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi ghép mỗi `fopen` thành công với đúng một `fclose`.
- [ ] Tôi kiểm tra cả kết quả ghi lẫn `fclose`.
- [ ] Tôi đọc theo dòng và giới hạn mọi field chuỗi.
- [ ] Tôi phân biệt EOF bình thường với `ferror`.
- [ ] Tôi không serialize raw memory layout của `struct`.

**Bài prerequisite:** [Union, bit-field và bộ nhớ](./10-union-bit-field-va-bo-nho.md)

**Bài tiếp theo:** [Preprocessor, header và macro](./12-preprocessor-header-va-macro.md)
