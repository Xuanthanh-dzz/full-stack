# Xử lý lỗi và lập trình phòng thủ

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- phân loại lỗi expected thành status code rõ nghĩa;
- parse số bằng `strtol` và kiểm tra toàn bộ input;
- validate pointer, range và invariant trước khi thao tác;
- dùng một cleanup path để đóng tài nguyên đúng một lần;
- tách thông báo cho người dùng khỏi chi tiết chẩn đoán;
- quy định output parameter chỉ hợp lệ khi status thành công.

## 2. Bài toán mở đầu

Số lượng sản phẩm đến từ text. Các input `"25"`, `"-2"` và `"12x"` không thể đều được xử lý như nhau:

- `"25"` hợp lệ;
- `"-2"` là số nhưng ngoài miền nghiệp vụ;
- `"12x"` không phải một số nguyên hoàn chỉnh.

Sau khi parse, chương trình lưu số hợp lệ vào file. Mọi lỗi phải được báo bằng status, không crash, không để stream mở và không dùng kết quả output khi parse thất bại.

## 3. Lời giải bằng code

Tạo `main.c`:

```c
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

typedef enum {
    APP_OK,
    APP_INVALID_ARGUMENT,
    APP_OUT_OF_RANGE,
    APP_IO_ERROR
} AppStatus;

static const char *status_name(AppStatus status)
{
    switch (status) {
        case APP_OK:
            return "OK";
        case APP_INVALID_ARGUMENT:
            return "INVALID_ARGUMENT";
        case APP_OUT_OF_RANGE:
            return "OUT_OF_RANGE";
        case APP_IO_ERROR:
            return "IO_ERROR";
    }

    return "UNKNOWN";
}

static AppStatus parse_quantity(const char *text, int *result)
{
    if (text == NULL || result == NULL || *text == '\0') {
        return APP_INVALID_ARGUMENT;
    }

    errno = 0;
    char *end = NULL;
    long parsed = strtol(text, &end, 10);

    if (text == end || *end != '\0') {
        return APP_INVALID_ARGUMENT;
    }

    if (errno == ERANGE || parsed < 0 || parsed > INT_MAX) {
        return APP_OUT_OF_RANGE;
    }

    *result = (int)parsed;
    return APP_OK;
}

static AppStatus save_quantity(const char *path, int quantity)
{
    if (path == NULL || *path == '\0' || quantity < 0) {
        return APP_INVALID_ARGUMENT;
    }

    AppStatus status = APP_IO_ERROR;
    FILE *file = fopen(path, "w");

    if (file == NULL) {
        goto cleanup;
    }

    if (fprintf(file, "%d\n", quantity) < 0) {
        goto cleanup;
    }

    status = APP_OK;

cleanup:
    /* One cleanup path closes an acquired stream exactly once. */
    if (file != NULL && fclose(file) != 0) {
        status = APP_IO_ERROR;
    }

    return status;
}

int main(void)
{
    const char *samples[] = {"25", "-2", "12x"};
    int valid_quantity = 0;

    for (size_t index = 0;
         index < sizeof samples / sizeof samples[0];
         ++index) {
        int parsed = 0;
        AppStatus status = parse_quantity(samples[index], &parsed);

        if (status == APP_OK) {
            printf("%s -> %s (%d)\n", samples[index], status_name(status), parsed);
            valid_quantity = parsed;
        } else {
            printf("%s -> %s\n", samples[index], status_name(status));
        }
    }

    const char *path = "quantity.txt";
    AppStatus save_status = save_quantity(path, valid_quantity);
    printf("Luu file -> %s\n", status_name(save_status));

    if (save_status != APP_OK) {
        return 1;
    }

    if (remove(path) != 0) {
        fprintf(stderr, "Khong xoa duoc file demo\n");
        return 1;
    }

    return 0;
}
```

Build và chạy trong thư mục lab riêng; demo tạo/truncate rồi xóa `quantity.txt`, vì vậy không đặt dữ liệu thật cùng tên:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o defensive-programming
./defensive-programming
```

Output:

```text
25 -> OK (25)
-2 -> OUT_OF_RANGE
12x -> INVALID_ARGUMENT
Luu file -> OK
```

## 4. Giải thích cơ chế

### Status code là một phần contract

`AppStatus` phân biệt:

- input/hợp đồng hàm sai;
- giá trị số ngoài range;
- lỗi tài nguyên file;
- thành công.

Caller kiểm tra status trước khi dùng output. `parse_quantity` chỉ ghi `*result` ở đường `APP_OK`; khi lỗi, giá trị output cũ không được coi là kết quả mới.

### Parse bằng `strtol`

```c
errno = 0;
char *end = NULL;
long parsed = strtol(text, &end, 10);
```

`strtol`:

- đọc số theo cơ số `10`;
- trả giá trị `long`;
- đặt `end` trỏ tới ký tự đầu tiên chưa parse;
- có thể đặt `errno = ERANGE` khi vượt range của `long`.

Kiểm tra đầy đủ:

```text
text == end      => không đọc được chữ số nào
*end != '\0'     => còn rác phía sau
errno == ERANGE  => vượt range long
parsed < 0       => ngoài miền quantity
parsed > INT_MAX => không chuyển an toàn sang int
```

Chỉ cast sau mọi kiểm tra.

Contract hiện tại kế thừa cú pháp của `strtol`: bỏ leading whitespace và chấp nhận dấu `+`; dấu `-` được parse rồi bị range nghiệp vụ từ chối. Nếu format chỉ cho phép digit `0..9`, hãy duyệt precheck từng ký tự như loader ở [bài File I/O](./11-file-io.md) trước khi gọi `strtol`.

### `errno` phải được dùng đúng

`errno` có thể giữ giá trị từ thao tác trước, nên đặt `0` ngay trước `strtol`. Chỉ đọc nó theo contract của hàm sau khi gọi. Không xem `errno` như status global tự động cho mọi hàm.

### Một cleanup path

`save_quantity` có một nơi đóng file:

```c
cleanup:
    if (file != NULL && fclose(file) != 0) {
        status = APP_IO_ERROR;
    }
```

Mọi đường sau khi khai báo `file` đi qua đoạn này. Nếu `fopen` thất bại, `file == NULL` và không đóng. Nếu mở thành công, `fclose` chạy đúng một lần kể cả `fprintf` thất bại.

`goto cleanup` trong C là công cụ có phạm vi rõ để gom release tài nguyên; nó không nhảy tùy tiện giữa logic nghiệp vụ.

### Fail trước khi thay đổi state

`parse_quantity` validate đầy đủ trước `*result = ...`. `save_quantity` validate đường dẫn và quantity trước `fopen`. Pattern này giảm trạng thái dở dang.

## 5. Kiến thức nền

### Expected error và programming error

- Expected: file không tồn tại, input sai, hết bộ nhớ—trả status và xử lý.
- Programming error: vi phạm invariant nội bộ do bug—sửa code, test và có thể dùng assertion trong build phát triển.

Không biến mọi lỗi expected thành crash. Cũng không im lặng “sửa” input sai nếu nghiệp vụ không cho phép.

### Error code hay sentinel

Trả `-1` đôi khi đủ, nhưng mơ hồ nếu `-1` cũng là dữ liệu hợp lệ hoặc có nhiều nguyên nhân. Enum status + output parameter làm contract rõ:

```c
AppStatus operation(Input input, Output *result);
```

### Logging và thông báo người dùng

`status_name` là mã ổn định cho demo. Production thường:

- log chi tiết kỹ thuật ở ranh giới phù hợp;
- trả thông báo không tiết lộ đường dẫn nội bộ hoặc dữ liệu nhạy cảm;
- giữ nguyên nguyên nhân đủ để chẩn đoán.

Không in một lỗi ở mọi tầng vì sẽ tạo log trùng. Tầng xử lý cuối quyết định cách báo.

### Cleanup theo thứ tự ngược

Nếu acquire:

```text
allocation A → stream B → allocation C
```

thì cleanup thường:

```text
free C → close B → free A
```

Khởi tạo handle/pointer về trạng thái rỗng giúp cleanup kiểm tra an toàn.

### Đào sâu (có thể quay lại sau)

`goto cleanup` cần tránh nhảy vào scope nơi object chưa được khởi tạo hoặc bỏ qua invariant. Một pattern ổn định là khai báo resource handle ở đầu hàm, khởi tạo `NULL`, acquire tuần tự và chỉ nhảy tiến về nhãn cleanup cuối hàm.

Trong hệ thống nhiều tầng, status enum có thể cần mapping thay vì dùng chung một “enum khổng lồ”. Mỗi boundary chuyển lỗi hạ tầng thành lỗi domain/application có ngữ cảnh, đồng thời giữ chi tiết kỹ thuật trong log.

## 6. Lỗi thường gặp

### Dùng `atoi`

`atoi` không cung cấp cách đáng tin cậy để phân biệt input sai và số `0`, cũng không báo overflow phù hợp. Dùng `strtol` với `end` và `errno`.

### Chỉ kiểm tra ký tự đầu

`strtol("12x", ...)` trả `12`; nếu không kiểm tra `*end == '\0'`, input rác bị chấp nhận.

### Cast trước khi kiểm tra range

Chuyển `long` ngoài range sang `int` không tạo validation. Kiểm tra `INT_MAX`/miền nghiệp vụ trước.

### Return sớm làm leak resource

Sau khi acquire resource, mọi `return` phải release hoặc chuyển ownership. Cleanup path duy nhất giúp audit dễ hơn.

### Ghi output rồi mới phát hiện lỗi

Caller có thể quan sát state nửa cập nhật. Validate trước và commit output cuối cùng khi thành công.

## 7. Bài tập

### Bài 1 — Parse giá tiền

Viết `parse_price_cents` nhận `long *result`, từ chối âm, rác cuối và overflow.

**Gợi ý:** dùng `strtol`; giới hạn nghiệp vụ có thể nhỏ hơn `LONG_MAX`.

### Bài 2 — Đọc quantity từ file

Đọc một dòng bằng `fgets`, bỏ newline có kiểm soát rồi gọi `parse_quantity`.

**Gợi ý:** phân biệt file rỗng, dòng quá dài và I/O error.

### Bài 3 — Hai resource

Viết hàm mở file input và output, sao chép từng dòng, dùng một cleanup path.

**Gợi ý:** khởi tạo cả hai `FILE *` bằng `NULL`, đóng theo thứ tự ngược.

### Bài 4 — Error mapping

Tạo `StorageStatus` riêng rồi map sang `AppStatus`.

**Gợi ý:** caller không cần biết mọi chi tiết lỗi filesystem.

### Bài 5 — Test bảng input

Kiểm tra `""`, `"0"`, `"25"`, `"-1"`, `"12x"` và số lớn hơn `INT_MAX`.

**Gợi ý:** ghi expected status trước khi chạy.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi parse toàn bộ input, không chỉ tiền tố số.
- [ ] Tôi đặt và kiểm tra `errno` đúng quanh `strtol`.
- [ ] Tôi chỉ ghi output parameter khi thành công.
- [ ] Tôi release mọi resource trên mọi đường đi.
- [ ] Tôi dùng status đủ rõ để caller quyết định.

**Bài prerequisite:** [Quá trình biên dịch, linking và Makefile](./13-qua-trinh-bien-dich-linking-makefile.md)

**Bài tiếp theo:** [Dự án C: quản lý kho](./15-du-an-c-quan-ly-kho.md)
