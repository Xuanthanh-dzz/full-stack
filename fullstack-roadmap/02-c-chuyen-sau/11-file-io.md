# File I/O

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- mở và đóng text file bằng `fopen`/`fclose`;
- ghi dữ liệu có kiểm tra lỗi bằng `fprintf`;
- đọc theo từng dòng bằng `fgets`, rồi tách field và parse số có kiểm tra overflow;
- kiểm tra EOF và I/O error đúng cách;
- thiết kế format file có version thay vì ghi raw byte của `struct`;
- bảo đảm stream được đóng trên mọi đường đi.

## 2. Bài toán mở đầu

Danh sách sản phẩm đang mất khi chương trình kết thúc. Ta cần ghi hai sản phẩm vào `inventory.txt`, mở lại, kiểm tra version, parse từng dòng và xóa file demo.

Ta chọn text format:

```text
INVENTORY_V1
BOOK-01|5|1200
PEN-02|20|150
```

Mỗi dòng sản phẩm có `code|quantity|price_cents`. Code không được chứa dấu `|`; độ dài tối đa là 15 ký tự. Format có header version để loader từ chối dữ liệu không tương thích.

## 3. Lời giải bằng code

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

## 4. Giải thích cơ chế

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

Trong mỗi vòng lặp, `Product product` là object automatic trong stack frame. Parser chỉ ghi member sau khi kiểm tra từng field. Code chỉ in rồi bỏ object; không trả pointer tới nó.

File chứa text độc lập với layout/padding của `Product`. Không có pointer hoặc địa chỉ process nào được ghi vào file.

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi ghép mỗi `fopen` thành công với đúng một `fclose`.
- [ ] Tôi kiểm tra cả kết quả ghi lẫn `fclose`.
- [ ] Tôi đọc theo dòng và giới hạn mọi field chuỗi.
- [ ] Tôi phân biệt EOF bình thường với `ferror`.
- [ ] Tôi không serialize raw memory layout của `struct`.

**Bài prerequisite:** [Union, bit-field và bộ nhớ](./10-union-bit-field-va-bo-nho.md)

**Bài tiếp theo:** [Preprocessor, header và macro](./12-preprocessor-header-va-macro.md)
