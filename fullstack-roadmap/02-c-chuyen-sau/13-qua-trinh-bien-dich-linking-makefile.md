# Quá trình biên dịch, linking và Makefile

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Build nhiều file gồm tiền xử lý, biên dịch từng đơn vị, rồi liên kết thành executable.
- Dùng header cho contract, source cho implementation và Makefile để theo dõi phụ thuộc.
- Compile từng file thành công chưa chứng minh linker tìm đủ định nghĩa hoặc executable là bản mới.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- mô tả các bước preprocessing, compilation, assembly và linking;
- tách declaration trong header khỏi definition trong source;
- build nhiều translation unit thành một executable;
- đọc lỗi compiler khác lỗi linker;
- viết Makefile có dependency cơ bản và build tăng dần;
- dùng internal linkage cho helper chỉ thuộc một file.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mỗi người chuẩn bị một bộ phận theo cùng bản vẽ; cuối cùng phải ráp được chúng. Header giống bản vẽ chung, object file là bộ phận đã dịch, linker nối các chỗ gọi với định nghĩa. Make chỉ làm lại bộ phận nó biết đã cũ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| translation unit | source sau khi đã xử lý các include/chỉ thị | main.c hoặc inventory.c sau tiền xử lý |
| object file | kết quả biên dịch trung gian | main.o, inventory.o |
| linking | nối tham chiếu với định nghĩa thành chương trình | inventory-app |
| dependency | file mà kết quả build phụ thuộc vào | main.o phụ thuộc inventory.h |
| incremental build | chỉ dựng lại phần đã cũ theo quan hệ phụ thuộc | make |

### Ví dụ nhỏ — tính tay trước

main.c gọi total được khai báo ở inventory.h; inventory.c định nghĩa total. Thiếu inventory.o: compiler có thể đã chấp nhận main.c, nhưng linker không tìm được thân hàm. Sửa header cần dịch lại cả hai source dùng nó.

Chương trình kho đã dài. Nếu mọi hàm nằm trong `main.c`, thay đổi một phần buộc ta đọc và build lại một khối lớn.

Ta tách:

```text
inventory.h  — public contract
inventory.c  — implementation
main.c       — caller
Makefile     — quy tắc build
```

Mỗi file `.c` được compile riêng thành object file. Linker ghép các definition thành executable.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `inventory.h`:

```c
#ifndef INVENTORY_H
#define INVENTORY_H

#include <stddef.h>

typedef struct {
    const char *code;
    int quantity;
    long long price_cents;
} InventoryItem;

int inventory_total(
    const InventoryItem *items,
    size_t count,
    long long *result
);

#endif
```

Tạo `inventory.c`:

```c
#include "inventory.h"

#include <limits.h>

static int item_is_valid(const InventoryItem *item)
{
    return item->code != NULL
        && item->quantity >= 0
        && item->price_cents >= 0;
}

int inventory_total(
    const InventoryItem *items,
    size_t count,
    long long *result
)
{
    if (result == NULL || (items == NULL && count > 0)) {
        return 0;
    }

    long long total = 0;

    for (size_t index = 0; index < count; ++index) {
        if (!item_is_valid(&items[index])) {
            return 0;
        }

        /* Guard each line multiplication before evaluating it. */
        if (items[index].quantity > 0
            && items[index].price_cents
                > LLONG_MAX / items[index].quantity) {
            return 0;
        }

        long long line_total =
            items[index].price_cents * items[index].quantity;

        if (total > LLONG_MAX - line_total) {
            return 0;
        }

        total += line_total;
    }

    *result = total;
    return 1;
}
```

Tạo `main.c`:

```c
#include "inventory.h"

#include <stdio.h>

int main(void)
{
    const InventoryItem items[] = {
        {.code = "BOOK-01", .quantity = 5, .price_cents = 1200},
        {.code = "PEN-02", .quantity = 20, .price_cents = 150}
    };
    long long total = 0;

    if (!inventory_total(
            items,
            sizeof items / sizeof items[0],
            &total
        )) {
        fprintf(stderr, "Du lieu kho khong hop le\n");
        return 1;
    }

    printf("Tong gia tri kho: %lld xu\n", total);
    return 0;
}
```

Tạo `Makefile` (các dòng command bắt đầu bằng một ký tự tab):

```makefile
CC := cc
CFLAGS := -std=c11 -Wall -Wextra -Wpedantic -Werror

.PHONY: all run clean

all: inventory-app

inventory-app: main.o inventory.o
	$(CC) main.o inventory.o -o inventory-app

main.o: main.c inventory.h
	$(CC) $(CFLAGS) -c main.c -o main.o

inventory.o: inventory.c inventory.h
	$(CC) $(CFLAGS) -c inventory.c -o inventory.o

run: inventory-app
	./inventory-app

clean:
	rm -f inventory-app main.o inventory.o
```

Build và chạy:

```bash
make
make run
```

Output:

```text
Tong gia tri kho: 9000 xu
```

Có thể build thủ công tương đương:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror -c main.c -o main.o
cc -std=c11 -Wall -Wextra -Wpedantic -Werror -c inventory.c -o inventory.o
cc main.o inventory.o -o inventory-app
./inventory-app
```

### Walkthrough — execution / state / cost

1. make đọc target và dependency; header mới hơn khiến các object phụ thuộc cần build lại.
2. Compiler dịch main.c và inventory.c riêng, cùng đọc contract trong inventory.h.
3. Linker nối hai object với thư viện cần dùng thành inventory-app; chạy executable mới tính tổng 9000.
4. Source tách file không tách thành hai process hay hai kho dữ liệu. Cost build theo phần phải dịch; runtime tổng vẫn duyệt các sản phẩm như code gốc.

### Mini-check

Nếu sửa inventory.h mà make nói không cần làm gì, nên kiểm tra công thức tính trước hay đồ thị dependency trước?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Hai translation unit

Preprocessor tạo:

```text
main.c + nội dung inventory.h      => translation unit main
inventory.c + nội dung inventory.h => translation unit inventory
```

Mỗi translation unit được compiler kiểm tra độc lập. Header bảo đảm caller và implementation nhìn cùng một function declaration và cùng definition kiểu.

### Declaration và definition

Trong header:

```c
int inventory_total(...);
```

là declaration: cho compiler biết tên và chữ ký.

Trong `inventory.c`:

```c
int inventory_total(...) { ... }
```

là definition: cung cấp thân hàm và symbol để linker tìm.

`main.c` compile được nhờ declaration dù chưa thấy thân hàm. Ở bước link, linker nối lời gọi từ `main.o` tới definition trong `inventory.o`.

### Bốn bước build

```text
source .c
  │ preprocessing (#include/#define)
  ▼
translation unit
  │ compilation (parse, type-check, tối ưu, sinh assembly)
  ▼
assembly
  │ assembler
  ▼
object file .o
  │ linker + object/library khác
  ▼
executable
```

Toolchain có thể gộp các bước trong một lệnh `cc`, nhưng mô hình này giúp chẩn đoán lỗi.

### Internal và external linkage

`inventory_total` cần caller ở file khác nên có external linkage.

`item_is_valid` chỉ là helper implementation:

```c
static int item_is_valid(...);
```

`static` ở file scope cho internal linkage: symbol này không xuất ra để translation unit khác gọi trực tiếp. Nó giữ bề mặt API nhỏ và tránh xung đột tên.

### Make dependency

Target:

```makefile
main.o: main.c inventory.h
```

nói `main.o` phụ thuộc cả source và header. Nếu header mới hơn object file, `make` compile lại. Nếu chỉ `inventory.c` đổi, `main.o` có thể được giữ và chỉ `inventory.o` cùng executable được tạo lại.

`inventory-app` phụ thuộc hai object; linker chỉ chạy khi một dependency thay đổi hoặc executable chưa có.

### Memory và ownership

Mảng `items` thuộc `main`; các pointer `code` mượn string literal có static storage duration. `inventory_total` chỉ đọc trong lời gọi và không giữ pointer.

Không có allocation động trong module nhỏ này. Việc tách file không đổi lifetime hoặc tự tạo bản sao runtime của mảng.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Một source | mọi định nghĩa cùng file | dễ bắt đầu; khó phân công khi file quá dài |
| Header + source | contract và implementation tách | cần dependency đúng; hợp hai phần đã có trách nhiệm riêng |
| Makefile | mô tả target/phụ thuộc/lệnh | giảm build lặp; thiếu dependency có thể chạy binary cũ |

### Misconception check

**Đúng hay sai?** Include header là đủ để linker có implementation.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: khai báo không thay thân hàm; cần liên kết object có định nghĩa.

</details>

**Đúng hay sai?** Tách hai file tạo hai bản state runtime độc lập tự động.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: file source là tổ chức build; state theo các định nghĩa/linkage của chương trình.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** dịch từng file rồi link.

- **Working Developer — dùng khi làm việc:** kiểm tra dependency và incremental build.

- **Deep Dive — có thể quay lại sau:** inspect symbol/object khi lỗi liên kết khó thấy.

### Phân biệt loại lỗi

- **Preprocessor:** thiếu header, directive sai.
- **Compiler:** cú pháp sai, kiểu không tương thích, warning thành error.
- **Linker:** undefined reference vì thiếu definition/object; multiple definition vì có quá nhiều definition external.
- **Runtime:** executable đã tạo nhưng input/resource/logic gây lỗi khi chạy.

Đọc đúng giai đoạn trước khi sửa.

### Lệnh quan sát từng bước

```bash
cc -E main.c -o main.i
cc -S -std=c11 main.c -o main.s
cc -c -std=c11 main.c -o main.o
```

- `-E`: dừng sau preprocessing;
- `-S`: dừng sau sinh assembly;
- `-c`: tạo object, chưa link.

Các file `.i`, `.s`, `.o` là build artifact, không sửa bằng tay.

### Header là public contract

Caller chỉ nên include header, không `#include "inventory.c"`. Include source làm definition bị chép vào translation unit và dễ gây multiple definition.

### `.PHONY`

`all`, `run`, `clean` là tên hành động, không phải file artifact. `.PHONY` ngăn một file tình cờ có tên `clean` làm target bị coi là đã cập nhật.

`clean` là thao tác xóa build artifact đã liệt kê rõ; không dùng glob hoặc đường dẫn rộng không kiểm soát.

### Đào sâu (có thể quay lại sau)

Thứ tự object/library trên command link có thể quan trọng với static library. Build lớn còn cần automatic dependency generation (`-MMD -MP`), build directory riêng và cấu hình debug/release.

Link-time optimization, symbol visibility, ABI compatibility và shared library là chủ đề nâng cao. Cốt lõi vẫn là: declaration phải khớp definition, mỗi external symbol có đúng definition cần thiết, và mọi object/library phải tham gia lệnh link.

## 6. Lỗi thường gặp

### Đặt function definition external trong header

Mỗi `.c` include header có thể tạo một definition, dẫn đến linker báo multiple definition. Header thường chỉ có declaration; ngoại lệ nhỏ là function `static inline` có contract phù hợp.

### Quên object ở lệnh link

Link chỉ `main.o` sẽ báo undefined reference tới `inventory_total`. Thêm `inventory.o`.

### Declaration lệch definition

Nếu header và source tự khai báo khác nhau, caller có thể truyền/đọc sai. `inventory.c` phải include chính header public của nó để compiler đối chiếu.

### Makefile thiếu dependency header

Nếu `main.o` chỉ phụ thuộc `main.c`, đổi struct trong header có thể không compile lại caller và tạo artifact không nhất quán.

### Dùng tab sai trong recipe

Make truyền thống yêu cầu tab đầu dòng recipe. Space thường tạo lỗi “missing separator”.

## 7. Khi nào KHÔNG dùng

Không tách mỗi hàm một file chỉ để trông chuyên nghiệp. Với chương trình vài dòng, một source dễ đọc hơn. Không dùng clean build mỗi lần để che dependency thiếu; incremental build phải đúng trước.

## 8. Production notes & scale check

Nhóm nhỏ cần clean build tái tạo được và test sửa header có rebuild đúng. Ghi compiler/flags và exit status, không chỉ ảnh IDE xanh. Demo hai source dùng dependency tường minh đủ; project lớn hơn có thể dùng dependency compiler tạo khi có driver.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Thêm hàm đếm hàng sắp hết

Thêm declaration vào header, definition vào source và lời gọi trong `main`.

**Gợi ý:** build lại và quan sát target nào chạy.

### Bài 2 — Tái hiện linker error

Trong bản sao project học tập, bỏ `inventory.o` khỏi lệnh link, đọc lỗi rồi khôi phục.

**Gợi ý:** compiler từng file vẫn thành công; linker mới thất bại.

### Bài 3 — Helper internal

Thêm helper validate code với `static`; xác nhận không đặt nó vào public header.

**Gợi ý:** chỉ public contract mới thuộc `inventory.h`.

### Bài 4 — Xem các phase

Sinh `.i`, `.s`, `.o` cho `inventory.c` và ghi vai trò từng file.

**Gợi ý:** dùng `-E`, `-S`, `-c`.

### Bài 5 — Make incremental

Chạy `make` hai lần, rồi sửa lần lượt `main.c`, `inventory.c`, `inventory.h`; ghi target được build lại.

**Gợi ý:** timestamp dependency quyết định target out-of-date.

## 10. Bài tập tích hợp liên module — Judgment

Liên hệ bài build Module 01: test chạy executable cũ vẫn PASS sau khi source lỗi có chứng minh bản sửa đúng không? Viết chuỗi compile/link/run dừng khi lỗi và kiểm tra khi header đổi.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Compile error khác link error ở giai đoạn nào?
2. Vì sao main.o phụ thuộc inventory.h?
3. Make có tự hiểu mọi include nếu chưa khai báo dependency không?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt declaration với definition.
- [ ] Tôi biết mỗi `.c` tạo một translation unit.
- [ ] Tôi phân biệt compiler error và linker error.
- [ ] Tôi dùng `static` cho helper chỉ thuộc một source file.
- [ ] Makefile của tôi ghi dependency header.

**Bài prerequisite:** [Preprocessor, header và macro](./12-preprocessor-header-va-macro.md)

**Bài tiếp theo:** [Xử lý lỗi và lập trình phòng thủ](./14-xu-ly-loi-va-lap-trinh-phong-thu.md)
