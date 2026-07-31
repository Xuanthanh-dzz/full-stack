# Dự án C: quản lý kho

## 1. Mục tiêu

Sau dự án này, bạn có thể ghép toàn bộ module thành một chương trình C11 nhiều file:

- quản lý mảng động sản phẩm với `count` và `capacity`;
- xác định ownership của mảng `Product` và từng chuỗi động;
- thêm, tìm, cập nhật, xóa mà không leak/double free;
- chống overflow ở tăng capacity, cập nhật quantity và tính tổng;
- lưu text file qua temp file rồi `rename`;
- load vào state tạm, chỉ commit khi toàn bộ file hợp lệ;
- trả status code nhất quán và cleanup mọi resource;
- build bằng Makefile và kiểm tra bằng warnings-as-errors/sanitizer.

Đây là checkpoint của module 02. Bạn nên tự gõ lại, chạy, thay input và vẽ memory trước khi sang C++.

## 2. Bài toán mở đầu

Một cửa hàng cần ứng dụng quản lý kho có các use case:

1. thêm sản phẩm gồm code, name, quantity và unit price;
2. tìm sản phẩm theo code;
3. thay đổi quantity sau bán/nhập hàng;
4. xóa sản phẩm;
5. tính tổng giá trị tồn kho;
6. lưu và tải lại dữ liệu.

Các failure mode phải được thiết kế trước:

- code trùng hoặc record không hợp lệ;
- `malloc`/`realloc` thất bại;
- quantity/total overflow;
- file bị cắt, sai version, field số lỗi;
- ghi file dở dang;
- lỗi giữa chừng khi load.

Quy tắc ownership:

```text
Inventory owner
  ├─ owns allocation mảng Product
  ├─ mỗi Product owns allocation code
  └─ mỗi Product owns allocation name

inventory_find trả borrowed pointer.
Borrowed pointer hết hợp lệ sau add/remove/dispose vì realloc hoặc dịch phần tử.
```

## 3. Lời giải bằng code

Tạo thư mục project với sáu file sau.

### `inventory.h`

```c
#ifndef INVENTORY_H
#define INVENTORY_H

#include <stddef.h>

typedef enum {
    INV_OK,
    INV_INVALID_ARGUMENT,
    INV_NOT_FOUND,
    INV_DUPLICATE,
    INV_OUT_OF_MEMORY,
    INV_OUT_OF_RANGE,
    INV_IO_ERROR,
    INV_FORMAT_ERROR
} InvStatus;

typedef struct {
    char *code;
    char *name;
    int quantity;
    long price_cents;
} Product;

typedef struct {
    Product *items;
    size_t count;
    size_t capacity;
} Inventory;

void inventory_init(Inventory *inventory);
void inventory_dispose(Inventory *inventory);

InvStatus inventory_validate(const Inventory *inventory);

InvStatus inventory_add(
    Inventory *inventory,
    const char *code,
    const char *name,
    int quantity,
    long price_cents
);

/*
 * Borrowed pointer: caller must not free it. Any mutating inventory operation
 * may invalidate it because the Product array can move or its elements shift.
 */
const Product *inventory_find(
    const Inventory *inventory,
    const char *code
);

InvStatus inventory_change_quantity(
    Inventory *inventory,
    const char *code,
    int delta
);

InvStatus inventory_remove(
    Inventory *inventory,
    const char *code
);

InvStatus inventory_total_value(
    const Inventory *inventory,
    long long *result
);

const char *inv_status_name(InvStatus status);

#endif
```

### `inventory.c`

```c
#include "inventory.h"

#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define INITIAL_CAPACITY 4U
#define MAX_FIELD_LENGTH 100U

static int header_is_valid(const Inventory *inventory)
{
    return inventory != NULL
        && inventory->count <= inventory->capacity
        && ((inventory->capacity == 0 && inventory->items == NULL)
            || (inventory->capacity > 0 && inventory->items != NULL));
}

static int text_is_valid(const char *text)
{
    if (text == NULL || *text == '\0') {
        return 0;
    }

    size_t length = 0;
    while (text[length] != '\0') {
        if (length >= MAX_FIELD_LENGTH
            || text[length] == '|'
            || text[length] == '\n'
            || text[length] == '\r') {
            return 0;
        }
        ++length;
    }

    return 1;
}

static char *duplicate_text(const char *source)
{
    size_t length = strlen(source);
    char *copy = malloc(length + 1);
    if (copy == NULL) {
        return NULL;
    }

    for (size_t index = 0; index <= length; ++index) {
        copy[index] = source[index];
    }

    return copy;
}

static void product_dispose(Product *product)
{
    if (product == NULL) {
        return;
    }

    free(product->code);
    free(product->name);
    product->code = NULL;
    product->name = NULL;
    product->quantity = 0;
    product->price_cents = 0;
}

static int find_index(
    const Inventory *inventory,
    const char *code,
    size_t *result
)
{
    if (!header_is_valid(inventory) || code == NULL || result == NULL) {
        return 0;
    }

    for (size_t index = 0; index < inventory->count; ++index) {
        if (strcmp(inventory->items[index].code, code) == 0) {
            *result = index;
            return 1;
        }
    }

    return 0;
}

static InvStatus ensure_capacity(Inventory *inventory)
{
    if (!header_is_valid(inventory)) {
        return INV_INVALID_ARGUMENT;
    }

    if (inventory->count < inventory->capacity) {
        return INV_OK;
    }

    size_t new_capacity = INITIAL_CAPACITY;
    if (inventory->capacity > 0) {
        if (inventory->capacity > SIZE_MAX / 2) {
            return INV_OUT_OF_RANGE;
        }
        new_capacity = inventory->capacity * 2;
    }

    if (new_capacity > SIZE_MAX / sizeof *inventory->items) {
        return INV_OUT_OF_RANGE;
    }

    Product *resized = realloc(
        inventory->items,
        new_capacity * sizeof *inventory->items
    );
    if (resized == NULL) {
        return INV_OUT_OF_MEMORY;
    }

    /*
     * realloc may move the Product allocation. Only commit the owner pointer
     * after success; individual code/name allocations do not move here.
     */
    for (size_t index = inventory->capacity;
         index < new_capacity;
         ++index) {
        resized[index] = (Product){0};
    }

    inventory->items = resized;
    inventory->capacity = new_capacity;
    return INV_OK;
}

void inventory_init(Inventory *inventory)
{
    if (inventory == NULL) {
        return;
    }

    inventory->items = NULL;
    inventory->count = 0;
    inventory->capacity = 0;
}

void inventory_dispose(Inventory *inventory)
{
    if (!header_is_valid(inventory)) {
        return;
    }

    for (size_t index = 0; index < inventory->count; ++index) {
        product_dispose(&inventory->items[index]);
    }

    free(inventory->items);
    inventory_init(inventory);
}

InvStatus inventory_validate(const Inventory *inventory)
{
    if (!header_is_valid(inventory)) {
        return INV_INVALID_ARGUMENT;
    }

    for (size_t index = 0; index < inventory->count; ++index) {
        const Product *product = &inventory->items[index];
        if (!text_is_valid(product->code)
            || !text_is_valid(product->name)
            || product->quantity < 0
            || product->price_cents < 0) {
            return INV_INVALID_ARGUMENT;
        }

        for (size_t other = index + 1;
             other < inventory->count;
             ++other) {
            if (strcmp(product->code, inventory->items[other].code) == 0) {
                return INV_DUPLICATE;
            }
        }
    }

    return INV_OK;
}

InvStatus inventory_add(
    Inventory *inventory,
    const char *code,
    const char *name,
    int quantity,
    long price_cents
)
{
    if (!header_is_valid(inventory)
        || !text_is_valid(code)
        || !text_is_valid(name)) {
        return INV_INVALID_ARGUMENT;
    }

    if (quantity < 0 || price_cents < 0) {
        return INV_OUT_OF_RANGE;
    }

    size_t existing_index = 0;
    if (find_index(inventory, code, &existing_index)) {
        return INV_DUPLICATE;
    }

    char *code_copy = duplicate_text(code);
    if (code_copy == NULL) {
        return INV_OUT_OF_MEMORY;
    }

    char *name_copy = duplicate_text(name);
    if (name_copy == NULL) {
        free(code_copy);
        return INV_OUT_OF_MEMORY;
    }

    InvStatus capacity_status = ensure_capacity(inventory);
    if (capacity_status != INV_OK) {
        free(name_copy);
        free(code_copy);
        return capacity_status;
    }

    inventory->items[inventory->count] = (Product){
        .code = code_copy,
        .name = name_copy,
        .quantity = quantity,
        .price_cents = price_cents
    };
    ++inventory->count;
    return INV_OK;
}

const Product *inventory_find(
    const Inventory *inventory,
    const char *code
)
{
    size_t index = 0;
    if (!find_index(inventory, code, &index)) {
        return NULL;
    }

    return &inventory->items[index];
}

InvStatus inventory_change_quantity(
    Inventory *inventory,
    const char *code,
    int delta
)
{
    size_t index = 0;
    if (!find_index(inventory, code, &index)) {
        return header_is_valid(inventory) && text_is_valid(code)
            ? INV_NOT_FOUND
            : INV_INVALID_ARGUMENT;
    }

    int current = inventory->items[index].quantity;
    if (current < 0) {
        return INV_INVALID_ARGUMENT;
    }

    if (delta > 0 && current > INT_MAX - delta) {
        return INV_OUT_OF_RANGE;
    }

    int updated = current + delta;
    if (updated < 0) {
        return INV_OUT_OF_RANGE;
    }

    inventory->items[index].quantity = updated;
    return INV_OK;
}

InvStatus inventory_remove(
    Inventory *inventory,
    const char *code
)
{
    size_t index = 0;
    if (!find_index(inventory, code, &index)) {
        return header_is_valid(inventory) && text_is_valid(code)
            ? INV_NOT_FOUND
            : INV_INVALID_ARGUMENT;
    }

    product_dispose(&inventory->items[index]);

    /*
     * Struct assignment transfers the owned string pointers leftward.
     * Clear the old last slot so the same pointers are not owned twice.
     */
    for (size_t current = index;
         current + 1 < inventory->count;
         ++current) {
        inventory->items[current] = inventory->items[current + 1];
    }

    --inventory->count;
    inventory->items[inventory->count] = (Product){0};
    return INV_OK;
}

InvStatus inventory_total_value(
    const Inventory *inventory,
    long long *result
)
{
    if (result == NULL) {
        return INV_INVALID_ARGUMENT;
    }

    InvStatus validation = inventory_validate(inventory);
    if (validation != INV_OK) {
        return validation;
    }

    long long total = 0;
    for (size_t index = 0; index < inventory->count; ++index) {
        const Product *product = &inventory->items[index];
        long long price = product->price_cents;

        if (product->quantity > 0
            && price > LLONG_MAX / product->quantity) {
            return INV_OUT_OF_RANGE;
        }

        long long line_total = price * product->quantity;
        if (total > LLONG_MAX - line_total) {
            return INV_OUT_OF_RANGE;
        }

        total += line_total;
    }

    *result = total;
    return INV_OK;
}

const char *inv_status_name(InvStatus status)
{
    switch (status) {
        case INV_OK:
            return "OK";
        case INV_INVALID_ARGUMENT:
            return "INVALID_ARGUMENT";
        case INV_NOT_FOUND:
            return "NOT_FOUND";
        case INV_DUPLICATE:
            return "DUPLICATE";
        case INV_OUT_OF_MEMORY:
            return "OUT_OF_MEMORY";
        case INV_OUT_OF_RANGE:
            return "OUT_OF_RANGE";
        case INV_IO_ERROR:
            return "IO_ERROR";
        case INV_FORMAT_ERROR:
            return "FORMAT_ERROR";
    }

    return "UNKNOWN";
}
```

### `storage.h`

Ranh giới contract của lời giải cần được nói rõ: `storage_save_atomic` bên dưới là bản **teaching/demo C11** cho thư mục lab riêng, đáng tin cậy và không có process khác cùng thao tác. Caller phải dành riêng cả `path` lẫn `path + ".tmp"`; temp path không được là symlink/hardlink và không được có actor đồng thời thay thế nó. Không dùng nguyên implementation này trong thư mục shared, writable bởi user khác hoặc có input path từ nguồn không tin cậy. Mục “Đào sâu” chỉ ra primitive cần dùng trong production.

```c
#ifndef STORAGE_H
#define STORAGE_H

#include "inventory.h"

/*
 * Teaching implementation precondition: path and path + ".tmp" are reserved
 * inside a trusted, single-writer directory; the temp path does not pre-exist
 * as a symlink or as a hard-link alias to another file.
 */
InvStatus storage_save_atomic(
    const char *path,
    const Inventory *inventory
);

/*
 * Destination must have been initialized. On failure it is unchanged;
 * on success it owns the fully loaded replacement state.
 */
InvStatus storage_load(
    const char *path,
    Inventory *destination
);

#endif
```

### `storage.c`

File này dùng hai API phụ trợ mới. `snprintf(buffer, capacity, ...)` format có bound; nó trả số ký tự cần ghi (không tính `'\0'`) hoặc số âm khi lỗi, nên code chỉ dùng path sau khi kiểm tra kết quả không âm và nhỏ hơn capacity. `fgetc(file)` đọc một ký tự dưới dạng `int` hoặc trả `EOF`; `read_line` dùng nó chỉ để drain phần còn lại của một record quá dài trước khi báo lỗi.

```c
#include "storage.h"

#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LINE_CAPACITY 512U

typedef enum {
    LINE_OK,
    LINE_END,
    LINE_IO_ERROR,
    LINE_TOO_LONG
} LineStatus;

static LineStatus read_line(
    FILE *file,
    char *buffer,
    size_t capacity
)
{
    if (file == NULL || buffer == NULL
        || capacity < 2 || capacity > INT_MAX) {
        return LINE_IO_ERROR;
    }

    if (fgets(buffer, (int)capacity, file) == NULL) {
        return ferror(file) ? LINE_IO_ERROR : LINE_END;
    }

    char *newline = strchr(buffer, '\n');
    if (newline != NULL) {
        *newline = '\0';
        if (newline > buffer && newline[-1] == '\r') {
            newline[-1] = '\0';
        }
        return LINE_OK;
    }

    int current = 0;
    do {
        current = fgetc(file);
    } while (current != '\n' && current != EOF);

    /*
     * The canonical writer always emits '\n'. Missing newline also rejects
     * a final record containing an embedded NUL hidden from string functions.
     */
    return ferror(file) ? LINE_IO_ERROR : LINE_TOO_LONG;
}

static int split_record(
    char *line,
    char **code,
    char **name,
    char **quantity,
    char **price
)
{
    char *first = strchr(line, '|');
    if (first == NULL) {
        return 0;
    }
    *first = '\0';

    char *second = strchr(first + 1, '|');
    if (second == NULL) {
        return 0;
    }
    *second = '\0';

    char *third = strchr(second + 1, '|');
    if (third == NULL || strchr(third + 1, '|') != NULL) {
        return 0;
    }
    *third = '\0';

    *code = line;
    *name = first + 1;
    *quantity = second + 1;
    *price = third + 1;
    return 1;
}

static int parse_long_between(
    const char *text,
    long minimum,
    long maximum,
    long *result
)
{
    if (text == NULL || result == NULL || *text == '\0') {
        return 0;
    }

    for (size_t index = 0; text[index] != '\0'; ++index) {
        if (text[index] < '0' || text[index] > '9') {
            return 0;
        }
    }

    errno = 0;
    char *end = NULL;
    long value = strtol(text, &end, 10);

    if (text == end
        || *end != '\0'
        || errno == ERANGE
        || value < minimum
        || value > maximum) {
        return 0;
    }

    *result = value;
    return 1;
}

InvStatus storage_save_atomic(
    const char *path,
    const Inventory *inventory
)
{
    if (path == NULL || *path == '\0') {
        return INV_INVALID_ARGUMENT;
    }

    InvStatus validation = inventory_validate(inventory);
    if (validation != INV_OK) {
        return validation;
    }

    size_t path_length = strlen(path);
    if (path_length > SIZE_MAX - 5
        || path_length > (size_t)INT_MAX - 4U) {
        return INV_OUT_OF_RANGE;
    }

    char *temporary_path = malloc(path_length + 5);
    if (temporary_path == NULL) {
        return INV_OUT_OF_MEMORY;
    }

    int path_characters = snprintf(
        temporary_path,
        path_length + 5,
        "%s.tmp",
        path
    );
    if (path_characters < 0
        || (size_t)path_characters >= path_length + 5) {
        free(temporary_path);
        return INV_OUT_OF_RANGE;
    }

    InvStatus status = INV_IO_ERROR;
    int temporary_exists = 0;
    FILE *file = fopen(temporary_path, "w");
    if (file == NULL) {
        goto cleanup;
    }
    temporary_exists = 1;

    int write_succeeded = fprintf(file, "INVENTORY_V1\n") >= 0;
    for (size_t index = 0;
         write_succeeded && index < inventory->count;
         ++index) {
        const Product *product = &inventory->items[index];
        if (fprintf(
                file,
                "%s|%s|%d|%ld\n",
                product->code,
                product->name,
                product->quantity,
                product->price_cents
            ) < 0) {
            write_succeeded = 0;
        }
    }

    if (write_succeeded && fflush(file) != 0) {
        write_succeeded = 0;
    }

    if (fclose(file) != 0) {
        write_succeeded = 0;
    }
    file = NULL;

    if (!write_succeeded) {
        goto cleanup;
    }

    /*
     * Commit only a fully written, closed temp file. On POSIX, rename within
     * one filesystem atomically replaces the destination directory entry.
     */
    if (rename(temporary_path, path) != 0) {
        goto cleanup;
    }

    temporary_exists = 0;
    status = INV_OK;

cleanup:
    if (file != NULL && fclose(file) != 0) {
        status = INV_IO_ERROR;
    }

    if (temporary_exists) {
        (void)remove(temporary_path);
    }

    free(temporary_path);
    return status;
}

InvStatus storage_load(
    const char *path,
    Inventory *destination
)
{
    if (path == NULL || *path == '\0'
        || inventory_validate(destination) != INV_OK) {
        return INV_INVALID_ARGUMENT;
    }

    FILE *file = fopen(path, "r");
    if (file == NULL) {
        return INV_IO_ERROR;
    }

    Inventory temporary;
    inventory_init(&temporary);
    InvStatus status = INV_OK;
    char line[LINE_CAPACITY];

    LineStatus line_status = read_line(file, line, sizeof line);
    if (line_status == LINE_IO_ERROR) {
        status = INV_IO_ERROR;
    } else if (line_status != LINE_OK
               || strcmp(line, "INVENTORY_V1") != 0) {
        status = INV_FORMAT_ERROR;
    }

    while (status == INV_OK) {
        line_status = read_line(file, line, sizeof line);
        if (line_status == LINE_END) {
            break;
        }
        if (line_status == LINE_IO_ERROR) {
            status = INV_IO_ERROR;
            break;
        }
        if (line_status == LINE_TOO_LONG) {
            status = INV_FORMAT_ERROR;
            break;
        }

        char *code = NULL;
        char *name = NULL;
        char *quantity_text = NULL;
        char *price_text = NULL;

        if (!split_record(
                line,
                &code,
                &name,
                &quantity_text,
                &price_text
            )) {
            status = INV_FORMAT_ERROR;
            break;
        }

        long quantity = 0;
        long price = 0;
        if (!parse_long_between(
                quantity_text,
                0,
                INT_MAX,
                &quantity
            )
            || !parse_long_between(
                price_text,
                0,
                LONG_MAX,
                &price
            )) {
            status = INV_FORMAT_ERROR;
            break;
        }

        status = inventory_add(
            &temporary,
            code,
            name,
            (int)quantity,
            price
        );
        if (status == INV_INVALID_ARGUMENT
            || status == INV_DUPLICATE
            || status == INV_OUT_OF_RANGE) {
            status = INV_FORMAT_ERROR;
        }
    }

    if (fclose(file) != 0 && status == INV_OK) {
        status = INV_IO_ERROR;
    }

    if (status == INV_OK) {
        /*
         * Commit is a move: destination takes all owner pointers, then the
         * temporary is reset so cleanup cannot free the transferred state.
         */
        inventory_dispose(destination);
        *destination = temporary;
        inventory_init(&temporary);
    }

    inventory_dispose(&temporary);
    return status;
}
```

### `main.c`

```c
#include "inventory.h"
#include "storage.h"

#include <stdio.h>

static void report_failure(const char *operation, InvStatus status)
{
    fprintf(stderr, "%s: %s\n", operation, inv_status_name(status));
}

int main(void)
{
    const char *path = "inventory-demo-v1.txt";
    Inventory inventory;
    Inventory loaded;
    inventory_init(&inventory);
    inventory_init(&loaded);

    int exit_code = 1;
    int saved_file_exists = 0;
    InvStatus status = inventory_add(
        &inventory,
        "BOOK-01",
        "Keyboard",
        10,
        350000
    );
    if (status != INV_OK) {
        report_failure("add BOOK-01", status);
        goto cleanup;
    }

    status = inventory_add(
        &inventory,
        "MOUSE-02",
        "Mouse",
        20,
        180000
    );
    if (status != INV_OK) {
        report_failure("add MOUSE-02", status);
        goto cleanup;
    }

    status = inventory_add(
        &inventory,
        "CABLE-03",
        "Cable",
        30,
        90000
    );
    if (status != INV_OK) {
        report_failure("add CABLE-03", status);
        goto cleanup;
    }

    status = inventory_change_quantity(&inventory, "MOUSE-02", -3);
    if (status != INV_OK) {
        report_failure("sell MOUSE-02", status);
        goto cleanup;
    }

    const Product *mouse = inventory_find(&inventory, "MOUSE-02");
    if (mouse == NULL) {
        report_failure("find MOUSE-02", INV_NOT_FOUND);
        goto cleanup;
    }
    printf("Sau ban: MOUSE-02 con %d\n", mouse->quantity);

    status = inventory_remove(&inventory, "CABLE-03");
    if (status != INV_OK) {
        report_failure("remove CABLE-03", status);
        goto cleanup;
    }
    printf("Da xoa CABLE-03\n");

    status = storage_save_atomic(path, &inventory);
    if (status != INV_OK) {
        report_failure("save", status);
        goto cleanup;
    }
    saved_file_exists = 1;

    status = storage_load(path, &loaded);
    if (status != INV_OK) {
        report_failure("load", status);
        goto cleanup;
    }

    printf("Da tai %zu san pham\n", loaded.count);
    for (size_t index = 0; index < loaded.count; ++index) {
        const Product *product = &loaded.items[index];
        printf(
            "%s | %s | %d | %ld\n",
            product->code,
            product->name,
            product->quantity,
            product->price_cents
        );
    }

    long long total = 0;
    status = inventory_total_value(&loaded, &total);
    if (status != INV_OK) {
        report_failure("total", status);
        goto cleanup;
    }

    printf("Tong gia tri: %lld xu\n", total);
    exit_code = 0;

cleanup:
    /*
     * Release in reverse ownership order. dispose is idempotent for an
     * initialized Inventory because it resets the owner to the empty state.
     */
    inventory_dispose(&loaded);
    inventory_dispose(&inventory);

    if (saved_file_exists && remove(path) != 0) {
        fprintf(stderr, "cleanup file: IO_ERROR\n");
        exit_code = 1;
    }

    return exit_code;
}
```

### `Makefile`

Các recipe bên dưới bắt đầu bằng tab:

```makefile
CC := cc
CFLAGS := -std=c11 -Wall -Wextra -Wpedantic -Werror
LDFLAGS :=
LDLIBS :=

OBJECTS := main.o inventory.o storage.o
DEPENDENCIES := $(OBJECTS:.o=.d)

.PHONY: all run clean

all: inventory-app

inventory-app: $(OBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) $(LDLIBS) -o inventory-app

%.o: %.c
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

run: inventory-app
	./inventory-app

clean:
	rm -f inventory-app $(OBJECTS) $(DEPENDENCIES)

-include $(DEPENDENCIES)
```

Build và chạy trong thư mục lab riêng. `inventory-demo-v1.txt` và file `.tmp` tương ứng là tên dành riêng cho demo; chương trình có thể replace rồi xóa chúng, nên không đặt dữ liệu thật cùng tên:

```bash
make
make run
```

Output:

```text
Sau ban: MOUSE-02 con 17
Da xoa CABLE-03
Da tai 2 san pham
BOOK-01 | Keyboard | 10 | 350000
MOUSE-02 | Mouse | 17 | 180000
Tong gia tri: 6560000 xu
```

Build kiểm tra memory trong môi trường GCC/Clang hỗ trợ sanitizer:

```bash
make clean
make CFLAGS="-std=c11 -Wall -Wextra -Wpedantic -Werror \
  -fsanitize=address,undefined -fno-omit-frame-pointer -g" \
  LDFLAGS="-fsanitize=address,undefined"
./inventory-app
```

## 4. Giải thích cơ chế

### Mô hình bộ nhớ sau ba lần `inventory_add`

`Inventory` là object automatic trong `main`. Lần add đầu gọi `ensure_capacity`; `realloc(NULL, bytes)` hoạt động như allocation mới và tạo block mảng `Product`.

Mỗi lần `duplicate_text` thành công tạo **một allocation riêng**:

```text
Stack main
┌───────────────────────────────────────────┐
│ inventory                                │
│   items = H1 ───────────────────────────┐ │
│   count = 3                            │ │
│   capacity = 4                         │ │
└────────────────────────────────────────│─┘
                                         ▼
Heap H1: mảng Product
┌──────────────────────────────────────────────────────────────┐
│ [0] code=C1 name=N1 qty=10 price=350000                     │
│ [1] code=C2 name=N2 qty=20 price=180000                     │
│ [2] code=C3 name=N3 qty=30 price= 90000                     │
│ [3] zero-initialized, chưa nằm trong count                  │
└──────────────────────────────────────────────────────────────┘
      │       │
      │       └────► N1: "Keyboard\0"   (allocation malloc)
      └────────────► C1: "BOOK-01\0"     (allocation malloc)

C2 ─► "MOUSE-02\0"  N2 ─► "Mouse\0"
C3 ─► "CABLE-03\0"  N3 ─► "Cable\0"
```

Tổng cộng ở thời điểm này có bảy allocation sống: H1 và sáu chuỗi. Không chuỗi nào nằm “bên trong pointer”; member pointer chỉ chứa địa chỉ.

### Tăng capacity

Khi `count == capacity`, `ensure_capacity`:

1. kiểm tra `capacity * 2`;
2. kiểm tra `new_capacity * sizeof(Product)`;
3. gọi `realloc` vào pointer tạm;
4. zero-initialize slot mới;
5. commit `inventory->items = resized`.

Nếu `realloc` trả địa chỉ mới và thay H1 bằng H2:

```text
Trước: inventory.items ─► H1 [Product...]
Sau:   inventory.items ─► H2 [Product...][slot mới...]
       H1 đã hết lifetime
```

Giá trị pointer `C1`, `N1`... được sao chép như member sang H2, nhưng các allocation chuỗi không di chuyển. Một `realloc` thành công kết thúc lifetime array allocation cũ kể cả khi địa chỉ số được tái sử dụng, nên mọi borrowed pointer tới `Product` phải được tìm lại. Contract vì thế nói mutation có thể invalidate kết quả `inventory_find` mà không cho caller dựa vào việc “địa chỉ trông vẫn giống”.

### Thêm sản phẩm là một transaction nhỏ

`inventory_add` tạo `code_copy`, rồi `name_copy`, rồi bảo đảm capacity. Nếu bước sau thất bại:

```text
name allocation thất bại  => free(code_copy)
capacity thất bại         => free(name_copy), free(code_copy)
thành công                => Product nhận ownership hai pointer
```

`count` chỉ tăng ở cuối. Caller không thấy một record nửa hoàn thành.

### Xóa và chuyển ownership

Đầu tiên `product_dispose` giải phóng hai chuỗi của record bị xóa. Sau đó struct assignment dịch các record sau sang trái.

Phép gán chỉ copy các pointer, nên ownership được **chuyển vị trí**, không nhân đôi allocation. Slot cũ cuối mảng được zero hóa để không còn hai slot cùng thể hiện ownership:

```text
Trước xóa index 1: [A owns CA/NA][B owns CB/NB][C owns CC/NC]
free B:            [A            ][empty       ][C owns CC/NC]
dịch C:            [A            ][C owns CC/NC][stale copy   ]
clear cuối:        [A            ][C owns CC/NC][zero          ]
```

### Save bằng temp file

```text
inventory
   │ serialize
   ▼
inventory-demo-v1.txt.tmp
   │ write + fflush + fclose đều thành công
   ▼
rename thành inventory-demo-v1.txt
```

File đích chỉ được commit sau khi temp file ghi và đóng thành công. Khi lỗi, cleanup cố xóa temp. Trên POSIX, `rename` trong cùng filesystem thay directory entry atomically; portability/durability tuyệt đối vẫn phụ thuộc nền tảng.

Sơ đồ này chỉ đúng dưới precondition của demo: thư mục do ứng dụng kiểm soát, một writer, temp name dành riêng và không phải link. `fopen(..., "w")` của ISO C11 không có lựa chọn create-exclusive/no-follow; nếu một symlink hoặc hardlink đã chiếm temp path, nó có thể làm hỏng file ngoài dự kiến trước bước `rename`.

### Load không phá state cũ

`storage_load` không thêm trực tiếp vào `destination`:

```text
destination (state cũ, vẫn nguyên)
temporary   (load từng record)
```

Nếu bất kỳ dòng nào sai, `inventory_dispose(&temporary)` giải phóng toàn bộ partial state và `destination` không đổi.

Chỉ sau EOF + parse + `fclose` thành công:

```c
inventory_dispose(destination);
*destination = temporary;
inventory_init(&temporary);
```

Đây là move ownership thủ công:

```text
trước commit: temporary ─► Hnew
sau commit:   destination ─► Hnew
              temporary = empty
```

Reset `temporary` là bắt buộc; nếu không, cleanup sẽ `free` Hnew lần nữa.

### Cleanup cuối chương trình

`inventory_dispose` đi qua đúng `count` product, free code/name, rồi free mảng và reset owner. Thứ tự:

```text
free từng C/N allocation → free H array → items=NULL,count=0,capacity=0
```

Không đọc member product sau khi H array bị giải phóng.

## 5. Kiến thức nền

### Invariant của `Inventory`

State hợp lệ thỏa:

```text
count <= capacity
capacity == 0  <=> items == NULL
mỗi index < count có code/name hợp lệ và số không âm
code là duy nhất
slot index >= count không phải dữ liệu nghiệp vụ
```

Mọi public operation phải giữ invariant nếu trả `INV_OK`.

### API ownership

| API | Input ownership | Output/lifetime |
|---|---|---|
| `inventory_add` | mượn `code`, `name` trong lời gọi | tạo bản copy do inventory sở hữu |
| `inventory_find` | mượn inventory/code | trả borrowed `Product *`; mutation có thể invalidate |
| `inventory_remove` | mượn code | giải phóng resource record bị xóa |
| `inventory_dispose` | nhận owner object | giải phóng toàn bộ và reset empty |
| `storage_load` | mượn path; destination đã init | success: destination sở hữu state mới |

Contract này quan trọng hơn tên biến. C không có type system tự thực thi ownership.

### Strong failure guarantee ở mức ứng dụng

`inventory_add` không đổi `count` khi lỗi. `storage_load` không đổi destination khi lỗi. Đây là thuộc tính dễ reasoning: operation hoặc commit đầy đủ, hoặc state quan sát được giữ nguyên.

`storage_save_atomic` giảm nguy cơ file nửa record, nhưng không hứa durability tuyệt đối qua mất điện và không giải quyết concurrent writer.

### Complexity

- find/change/remove: `O(n)` do linear search;
- append trung bình: `O(1)` amortized nhờ capacity nhân đôi;
- remove: `O(n)` do dịch phần tử;
- validate duplicate toàn bộ: `O(n²)`;
- save: `O(n²)` vì gọi `inventory_validate` trước khi ghi; phần ghi từng record là `O(n)` chưa tính tổng độ dài text;
- load: `O(n²)` vì mỗi record đi qua `inventory_add`, trong đó kiểm tra code trùng bằng linear search; phần đọc/parse là `O(n)` chưa tính tổng độ dài text.

Module cấu trúc dữ liệu sau này sẽ giới thiệu hash table để lookup nhanh hơn. Ở checkpoint này, tính đúng và ownership rõ quan trọng hơn tối ưu sớm.

### Test cần có

Ngoài happy path:

- add code trùng;
- add field rỗng, chứa `|`, newline, dài hơn 100;
- bán nhiều hơn tồn kho;
- tăng quantity vượt `INT_MAX`;
- total vượt `LLONG_MAX`;
- load sai header, thiếu/thừa field, số có rác/overflow, dòng quá dài, thiếu newline hoặc có NUL ẩn;
- file không tồn tại/không có quyền;
- load lỗi phải giữ destination cũ;
- sanitizer không báo leak/use-after-free.

### Flags trong Makefile

`CFLAGS` đi vào bước compile; `LDFLAGS` đi vào bước link; `LDLIBS` dành cho library. Sanitizer cần runtime ở bước link, vì vậy lệnh kiểm tra truyền `-fsanitize=...` cho cả `CFLAGS` và `LDFLAGS`.

`-MMD -MP` yêu cầu compiler sinh file dependency `.d` cho project header. Dòng `-include $(DEPENDENCIES)` nạp chúng ở lần `make` sau, để thay đổi `inventory.h` hoặc `storage.h` compile lại đúng object liên quan.

### Đào sâu (có thể quay lại sau)

`inventory_dispose` chỉ an toàn với object đã `inventory_init` và chưa bị caller làm hỏng representation. C không có constructor tự chạy. Production API có thể dùng opaque type để caller không sửa trực tiếp `items/count/capacity`.

Production không nên ghép một temp name cố định rồi mở bằng `fopen(..., "w")`. Trên POSIX, một flow dùng standard I/O là: tạo temp file **duy nhất trong cùng directory** bằng `mkstemp`, chuyển file descriptor thành `FILE *` bằng `fdopen`, ghi dữ liệu, kiểm tra `fflush(stream)`, gọi `fsync(fileno(stream))`, kiểm tra `fclose`, rồi `rename` và `fsync` parent directory khi cần durability. Mọi bước đều phải kiểm tra lỗi và cleanup đúng ownership. Trên Windows, dùng API tương đương với create-new độc quyền rồi replace/move theo semantics của nền tảng. Việc chống symlink/reparse-point còn cần quyền directory và no-follow/path-handling phù hợp threat model. Đây là lý do code production phải có adapter filesystem theo platform thay vì giả vờ ISO C11 cung cấp đủ primitive.

`rename` có semantics khác trên Windows khi đích đã tồn tại. Durability mạnh không nằm trong ISO C11. Nếu nhiều process cùng ghi, cần locking/version/concurrency strategy riêng.

Failure injection cho allocator/file I/O cần wrapper hoặc dependency injection bằng function pointer để test mọi nhánh hiếm. Không cố tạo out-of-memory bằng cách cấp phát vô hạn trên máy thật.

## 6. Lỗi thường gặp

### Giữ `Product *` qua `inventory_add`

Add có thể `realloc` mảng, làm pointer phần tử cũ dangling. Chỉ dùng borrowed pointer trong khoảng contract; tìm lại sau mutation.

### Shallow copy cả `Inventory`

```c
Inventory second = first;
```

làm hai object cùng chứa owner pointer. Dispose cả hai gây double free. Chỉ move có reset source như `storage_load`, hoặc viết deep-copy riêng.

### Tăng `count` trước khi mọi allocation thành công

State sẽ chứa record nửa khởi tạo. Acquire tài nguyên trước, commit record và `count` ở cuối.

### Dùng `realloc` trực tiếp lên owner

Nếu thất bại, mất block cũ. Luôn dùng pointer tạm, kiểm tra rồi commit.

### Parse thẳng vào destination

File lỗi ở record cuối sẽ để destination chứa một phần dữ liệu mới. Load vào temporary state và commit một lần.

### Ghi raw `Product`

Member là địa chỉ process, không phải nội dung chuỗi; padding/layout không portable. Serialize field.

### Bỏ qua lỗi `fclose` hoặc `rename`

Không báo save thành công trước khi write, flush, close và commit đều thành công.

## 7. Bài tập

### Bài 1 — Update tên và giá

Thêm API đổi tên/giá với strong failure guarantee.

**Gợi ý:** duplicate tên mới trước; chỉ free tên cũ và swap pointer sau khi allocation thành công.

### Bài 2 — Reserve capacity

Thêm `inventory_reserve`, không làm giảm capacity và không đổi state khi lỗi.

**Gợi ý:** chống overflow trước `realloc`; document borrowed pointer invalidation.

### Bài 3 — Test loader lỗi

Tạo bảng file malformed và xác nhận destination cũ giữ nguyên.

**Gợi ý:** dùng inventory có một record sentinel trước mỗi lần load.

### Bài 4 — Failure injection

Bọc allocator qua callback để yêu cầu allocation thứ `N` thất bại; chạy mọi `N`.

**Gợi ý:** sau mỗi test, invariant phải đúng và sanitizer không báo leak.

### Bài 5 — CLI thật

Thêm command `add`, `sell`, `remove`, `list`, `total`; parse toàn bộ số bằng `strtol`.

**Gợi ý:** tách lớp parse command khỏi inventory API; không cho input trực tiếp sửa struct.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi vẽ được H1 mảng `Product` và từng allocation chuỗi.
- [ ] Tôi chỉ rõ owner/borrower và thời điểm pointer bị invalidate.
- [ ] Tôi giữ invariant sau cả success lẫn failure.
- [ ] Tôi không overflow khi resize, update hoặc tính total.
- [ ] Tôi load vào state tạm và commit ownership đúng một lần.
- [ ] Tôi kiểm tra write, flush, close và rename.
- [ ] Tôi build sạch với C11 warnings-as-errors và sanitizer.
- [ ] Tôi tự giải thích được vì sao không có leak/double free.

**Bài prerequisite:** [Xử lý lỗi và lập trình phòng thủ](./14-xu-ly-loi-va-lap-trinh-phong-thu.md)

**Bài tiếp theo:** [Từ C sang C++20](../03-cpp/01-tu-c-sang-cpp20.md)
