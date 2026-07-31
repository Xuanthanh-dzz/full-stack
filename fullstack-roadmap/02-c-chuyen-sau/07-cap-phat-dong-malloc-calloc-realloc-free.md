# Cấp phát động: malloc, calloc, realloc và free

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- cấp phát mảng lúc runtime bằng `malloc` hoặc `calloc`;
- kiểm tra lỗi và chống tràn kích thước trước khi cấp phát;
- mở rộng block bằng `realloc` mà không làm mất pointer cũ khi thất bại;
- giải phóng mỗi allocation đúng một lần bằng `free`;
- vẽ chính xác pointer nào sở hữu block nào trước và sau từng thao tác.

## 2. Bài toán mở đầu

Số mặt hàng cần lưu chỉ biết khi chương trình chạy. Mảng cố định có thể quá nhỏ hoặc lãng phí. Ta cần:

1. tạo mảng giá có ba phần tử;
2. tạo mảng trạng thái bán với các phần tử ban đầu bằng `0`;
3. mở rộng mảng giá lên năm phần tử;
4. giải phóng mọi block trên tất cả đường đi.

## 3. Lời giải bằng code

Tạo `main.c`:

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int resize_prices(
    int **prices,
    size_t old_count,
    size_t new_count
)
{
    if (prices == NULL || *prices == NULL
        || new_count == 0 || new_count < old_count) {
        return 0;
    }

    if (new_count > SIZE_MAX / sizeof **prices) {
        return 0;
    }

    /* Keep the owner unchanged if realloc fails. */
    int *resized = realloc(*prices, new_count * sizeof **prices);
    if (resized == NULL) {
        return 0;
    }

    for (size_t index = old_count; index < new_count; ++index) {
        resized[index] = 0;
    }

    *prices = resized;
    return 1;
}

int main(void)
{
    size_t price_count = 3;

    if (price_count > SIZE_MAX / sizeof(int)) {
        return 1;
    }

    int *prices = malloc(price_count * sizeof *prices);
    if (prices == NULL) {
        fprintf(stderr, "Khong cap phat duoc prices\n");
        return 1;
    }

    int *sold = calloc(price_count, sizeof *sold);
    if (sold == NULL) {
        fprintf(stderr, "Khong cap phat duoc sold\n");
        free(prices);
        return 1;
    }

    prices[0] = 120;
    prices[1] = 250;
    prices[2] = 180;

    printf(
        "Gia ban dau: %d %d %d\n",
        prices[0],
        prices[1],
        prices[2]
    );
    printf(
        "calloc khoi tao sold: %d %d %d\n",
        sold[0],
        sold[1],
        sold[2]
    );

    size_t new_count = 5;
    if (!resize_prices(&prices, price_count, new_count)) {
        fprintf(stderr, "Khong mo rong duoc prices\n");
        free(sold);
        free(prices);
        return 1;
    }

    price_count = new_count;
    prices[3] = 300;
    prices[4] = 400;

    int total = 0;
    for (size_t index = 0; index < price_count; ++index) {
        total += prices[index];
    }

    printf(
        "Sau realloc: %d %d %d %d %d\n",
        prices[0],
        prices[1],
        prices[2],
        prices[3],
        prices[4]
    );
    printf("Tong gia: %d xu\n", total);

    free(sold);
    sold = NULL;
    free(prices);
    prices = NULL;
    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o dynamic-allocation
./dynamic-allocation
```

Output thành công:

```text
Gia ban dau: 120 250 180
calloc khoi tao sold: 0 0 0
Sau realloc: 120 250 180 300 400
Tong gia: 1250 xu
```

Các nhánh lỗi ghi thông báo vào standard error và trả exit code khác `0`.

## 4. Giải thích cơ chế

### `malloc`: tạo một block chưa khởi tạo

```c
int *prices = malloc(price_count * sizeof *prices);
```

Nếu thành công:

1. allocator tạo một allocation đủ byte cho ba `int`;
2. `malloc` trả địa chỉ byte đầu của block;
3. địa chỉ được lưu trong object pointer `prices` trên stack;
4. byte trong block có giá trị chưa xác định—phải gán trước khi đọc.

```text
Stack                         Heap / allocated storage

prices = H1 ─────────────────► H1: [ ? ][ ? ][ ? ]
                                  một allocation do malloc tạo
```

Nếu thất bại, `malloc` trả `NULL` và không tạo block. C không ném exception.

Không cast giá trị trả về của `malloc` trong C. `void *` được chuyển ngầm sang pointer object phù hợp; cast có thể che lỗi thiếu khai báo hàm nếu header sai.

### `calloc`: tạo một block và zero-initialize byte

```c
int *sold = calloc(price_count, sizeof *sold);
```

Nếu thành công, đây là allocation **khác**:

```text
prices ──► H1: [120][250][180]
sold   ──► H2: [  0][  0][  0]
```

`calloc(count, size)` kiểm tra phép nhân theo contract của allocator và đặt toàn bộ byte trong block về zero. Với kiểu số nguyên `int` trên implementation C thông thường mà bài đang chạy, các phần tử đọc ra là `0`.

Mỗi lời gọi `malloc`/`calloc` thành công tạo một allocation độc lập, dù hai block có cùng kích thước.

### `realloc`: block có thể giữ nguyên hoặc di chuyển

Hàm nhận địa chỉ của owner pointer:

```c
resize_prices(&prices, 3, 5);
```

Trong hàm:

```c
int *resized = realloc(*prices, new_size);
```

Có ba kết quả quan trọng:

1. **Thành công, cùng giá trị địa chỉ:** lifetime allocation cũ H1 kết thúc; allocation thay thế bắt đầu tại cùng địa chỉ số, bảo toàn nội dung phần chung, và `resized` là pointer phải dùng từ đây.
2. **Thành công, địa chỉ mới:** allocator tạo allocation H3, bảo toàn nội dung cũ trong phần chung, kết thúc H1 và trả địa chỉ H3.
3. **Thất bại:** trả `NULL`; H1 vẫn sống, không đổi và vẫn do `*prices` sở hữu.

```text
Trước:
prices ──► H1 [120][250][180]

Thành công có di chuyển:
resized ─► H3 [120][250][180][ ? ][ ? ]
H1 đã hết lifetime

Sau *prices = resized:
prices ──► H3 [120][250][180][ 0 ][ 0 ]
```

Vì vậy phải giữ kết quả trong pointer tạm. Viết thẳng `prices = realloc(prices, ...)` sẽ làm mất địa chỉ H1 nếu `realloc` thất bại.

Các byte mới thêm không tự được khởi tạo; vòng lặp đặt chúng bằng `0`.

### `free`: kết thúc lifetime của allocation

```c
free(prices);
```

kết thúc allocation mà `prices` trỏ tới. Sau đó:

- giá trị pointer cũ không còn được dereference;
- không được truyền lại cùng địa chỉ cho `free`;
- gán pointer owner về `NULL` giúp tránh vô tình dùng lại qua tên đó.

`free(NULL)` được phép và không làm gì, nhưng gán một alias về `NULL` không tự cập nhật các pointer khác cùng trỏ block.

### Ownership trong chương trình

`main` là owner của hai allocation. `resize_prices` được mượn địa chỉ owner pointer để có thể cập nhật nó khi `realloc` di chuyển block. Hàm không giữ lại pointer và không giải phóng block khi thành công.

Mọi nhánh sau khi cả hai allocation được tạo đều phải `free(sold)` và `free(prices)` đúng một lần.

## 5. Kiến thức nền

### Tính kích thước không ghi lặp kiểu

Ưu tiên:

```c
malloc(count * sizeof *pointer)
```

thay vì:

```c
malloc(count * sizeof(int))
```

Nếu kiểu pointer thay đổi, biểu thức đầu tự đi theo. `sizeof` không đánh giá dereference trong trường hợp này; `pointer` có thể đang `NULL` mà `sizeof *pointer` vẫn xác định từ kiểu.

### Chống integer overflow

Trước khi nhân:

```c
if (count > SIZE_MAX / sizeof *pointer) {
    /* kích thước không biểu diễn được */
}
```

Nếu phép nhân tràn `size_t`, allocator có thể nhận một số byte nhỏ hơn cần thiết, rồi code ghi vượt block.

### Kích thước logic và capacity

Trong cấu trúc mảng động thường có:

- `count`: số phần tử đã khởi tạo và được phép đọc;
- `capacity`: số phần tử block có thể chứa.

Ví dụ đơn giản dùng `price_count` đúng bằng capacity. Dự án cuối module sẽ tách hai con số để tránh `realloc` sau mỗi lần thêm.

### Quy ước owner/borrower

Một API production nên ghi:

- pointer trả về là owned hay borrowed;
- caller hay callee gọi `free`;
- allocator và deallocator phải là cặp nào;
- pointer có được giữ sau lời gọi không.

### Đào sâu (có thể quay lại sau)

`malloc(0)`, `calloc(0, size)` và `realloc(pointer, 0)` có các chi tiết dễ gây code không portable. Trong lộ trình này, contract từ chối hoặc xử lý riêng kích thước `0`; không dùng `realloc(..., 0)` thay cho `free`.

Allocator có thể cấp block lớn hơn yêu cầu và giữ metadata riêng. Code chỉ được truy cập đúng số byte đã yêu cầu, không dựa vào kích thước nội bộ.

Một `realloc` thành công kết thúc lifetime allocation cũ kể cả khi giá trị địa chỉ trả về trùng địa chỉ cũ. Hãy coi mọi alias/pointer vào phần tử cũ là không còn hợp lệ và tính lại chúng từ pointer được trả về. Vì vậy phải thiết kế điểm resize rõ ràng, không giữ borrowed pointer qua thao tác có thể `realloc`.

## 6. Lỗi thường gặp

### Đọc vùng `malloc` trước khi khởi tạo

Byte từ `malloc` chưa mang giá trị phần tử hợp lệ để đọc. Gán từng phần tử hoặc dùng `calloc` khi zero-initialization đúng với nhu cầu.

### Gán trực tiếp kết quả `realloc`

Sai:

```c
prices = realloc(prices, new_size);
```

Nếu thất bại, `prices` thành `NULL` và địa chỉ allocation cũ bị thất lạc: memory leak. Dùng pointer tạm.

### Quên kiểm tra overflow

`count * sizeof *prices` có thể tràn trước khi được truyền vào allocator. Kiểm tra bằng phép chia trước.

### Dùng pointer sau `free`

Gán owner về `NULL` sau `free`, nhưng quan trọng hơn là dừng mọi alias trước khi giải phóng.

### `free` hai lần hoặc `free` pointer không phải đầu allocation

Chỉ truyền cho `free` đúng pointer được allocator trả về gần nhất. Không `free(&local)`, không `free(prices + 1)`, không `free` cùng allocation hai lần.

## 7. Bài tập

### Bài 1 — Mảng nhiệt độ động

Cấp phát `count` phần tử `double`, gán dữ liệu, tính trung bình và giải phóng.

**Gợi ý:** kiểm tra `count > SIZE_MAX / sizeof *temperatures`.

### Bài 2 — Mảng đếm bằng `calloc`

Tạo mảng tần suất 10 phần tử, xác nhận giá trị ban đầu rồi tăng các ô.

**Gợi ý:** vẫn phải kiểm tra kết quả `calloc`.

### Bài 3 — Thu nhỏ an toàn

Viết hàm thu mảng từ năm xuống ba phần tử bằng `realloc`.

**Gợi ý:** nội dung ba phần tử đầu được bảo toàn khi thành công; pointer cũ vẫn hợp lệ khi thất bại.

### Bài 4 — Mảng động có capacity

Viết hàm append, tăng capacity gấp đôi khi `count == capacity`.

**Gợi ý:** kiểm tra cả phép nhân đôi capacity và phép nhân với `sizeof`.

### Bài 5 — Sơ đồ ownership

Vẽ tất cả trạng thái có thể của `prices` trước/sau `realloc`, gồm thất bại, tại chỗ và di chuyển.

**Gợi ý:** ở nhánh thành công có di chuyển, đánh dấu block cũ đã hết lifetime.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi kiểm tra `NULL` sau mọi allocation.
- [ ] Tôi không đọc byte từ `malloc` trước khi khởi tạo.
- [ ] Tôi dùng pointer tạm cho `realloc`.
- [ ] Tôi chống overflow trước phép nhân kích thước.
- [ ] Tôi chỉ `free` đầu allocation, đúng một lần.
- [ ] Tôi vẽ được owner pointer trước/sau `realloc`.

**Bài prerequisite:** [Stack, heap và vòng đời bộ nhớ](./06-stack-heap-va-vong-doi-bo-nho.md)

**Bài tiếp theo:** [Lỗi bộ nhớ và undefined behavior](./08-loi-bo-nho-va-undefined-behavior.md)
