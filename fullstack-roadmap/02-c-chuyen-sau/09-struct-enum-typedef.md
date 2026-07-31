# `struct`, `enum` và `typedef`

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- gom các trường liên quan thành một object `struct`;
- biểu diễn tập trạng thái hữu hạn bằng `enum`;
- tạo tên kiểu dễ đọc bằng `typedef`;
- truy cập member bằng `.` và `->`;
- truyền pointer tới `struct` với contract đọc/ghi rõ ràng;
- hiểu việc gán một `struct` sao chép từng member và các giới hạn khi member là pointer.

## 2. Bài toán mở đầu

Một sản phẩm có mã số, tên, số lượng và ngưỡng nhập thêm. Nếu lưu bốn mảng hoặc bốn biến rời, rất dễ truyền nhầm dữ liệu của sản phẩm này với sản phẩm khác.

Ta cần một kiểu `Product` gom các trường thành một object và một kiểu `StockState` chỉ cho phép ba trạng thái nghiệp vụ: hết hàng, sắp hết và đủ hàng.

## 3. Lời giải bằng code

Tạo `main.c`:

```c
#include <limits.h>
#include <stdio.h>

typedef enum {
    STOCK_EMPTY,
    STOCK_LOW,
    STOCK_OK
} StockState;

typedef struct {
    int id;
    char name[32];
    int quantity;
    int reorder_level;
} Product;

static StockState get_stock_state(const Product *product)
{
    if (product->quantity == 0) {
        return STOCK_EMPTY;
    }

    if (product->quantity <= product->reorder_level) {
        return STOCK_LOW;
    }

    return STOCK_OK;
}

static const char *stock_state_name(StockState state)
{
    switch (state) {
        case STOCK_EMPTY:
            return "EMPTY";
        case STOCK_LOW:
            return "LOW";
        case STOCK_OK:
            return "OK";
    }

    return "UNKNOWN";
}

static int restock(Product *product, int amount)
{
    if (product == NULL || product->quantity < 0 || amount < 0) {
        return 0;
    }

    /* Validate before addition so signed overflow never occurs. */
    if (amount > INT_MAX - product->quantity) {
        return 0;
    }

    product->quantity += amount;
    return 1;
}

static void print_product(const Product *product)
{
    if (product == NULL) {
        return;
    }

    printf(
        "%d | %s | quantity=%d | state=%s\n",
        product->id,
        product->name,
        product->quantity,
        stock_state_name(get_stock_state(product))
    );
}

int main(void)
{
    Product product = {
        .id = 101,
        .name = "Ban phim",
        .quantity = 4,
        .reorder_level = 5
    };

    print_product(&product);

    if (!restock(&product, 6)) {
        fprintf(stderr, "Khong the nhap them hang\n");
        return 1;
    }

    print_product(&product);
    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o struct-enum
./struct-enum
```

Output:

```text
101 | Ban phim | quantity=4 | state=LOW
101 | Ban phim | quantity=10 | state=OK
```

## 4. Giải thích cơ chế

### `struct` tạo một kiểu gồm nhiều member

Khai báo:

```c
typedef struct {
    int id;
    char name[32];
    int quantity;
    int reorder_level;
} Product;
```

định nghĩa một kiểu `struct` và đặt bí danh `Product` cho kiểu đó. Mỗi object `Product` chứa đủ bốn member:

```text
product
┌───────────────┬──────────────────────────┬──────────────┬─────────────────┐
│ id = 101      │ name = "Ban phim\0..."   │ quantity = 4 │ reorder_level=5 │
└───────────────┴──────────────────────────┴──────────────┴─────────────────┘
```

Đây là một object tổng hợp, không phải bốn allocation heap. Mảng `name` nằm **bên trong** object `product`.

### Designated initializer

```c
Product product = {
    .id = 101,
    .name = "Ban phim",
    .quantity = 4,
    .reorder_level = 5
};
```

Cú pháp `.member = value` ghi rõ member nào nhận giá trị nào. Thứ tự có thể khác thứ tự khai báo, và member không được nêu sẽ được zero-initialize.

### `.` và `->`

Khi có object trực tiếp:

```c
product.quantity
```

Khi có pointer:

```c
product_pointer->quantity
```

`product_pointer->quantity` tương đương:

```c
(*product_pointer).quantity
```

Dấu ngoặc cần thiết vì `.` có độ ưu tiên cao hơn unary `*`.

### Contract đọc và ghi

```c
static void print_product(const Product *product);
```

mượn pointer chỉ đọc. Hàm không được sửa member qua pointer.

```c
static int restock(Product *product, int amount);
```

mượn pointer có quyền ghi. Hàm kiểm tra `NULL`, số âm và integer overflow trước khi cập nhật.

Object vẫn do `main` sở hữu; không có allocation động trong ví dụ.

### `enum` đặt tên cho trạng thái

`StockState` gom ba hằng số nguyên có tên. `get_stock_state` trả đúng một trạng thái, giúp `switch` rõ nghĩa hơn việc rải các con số `0`, `1`, `2` trong code.

## 5. Kiến thức nền

### `typedef` không tạo object

`typedef` tạo một tên kiểu khác, không cấp bộ nhớ và không tạo một kiểu runtime bao bọc:

```c
typedef unsigned long ProductId;
```

Sau đó `ProductId id;` vẫn có representation của `unsigned long`. Dùng `typedef` để làm API dễ đọc, không để che bản chất pointer hoặc ownership.

### Named struct và anonymous struct

Phiên bản có tag:

```c
typedef struct Product {
    int id;
} Product;
```

cho phép dùng cả `struct Product` và `Product`. Tag hữu ích khi kiểu cần tự tham chiếu qua pointer hoặc khi khai báo trước. Dự án cuối module sẽ dùng named struct phù hợp với API nhiều file.

### Mảng `struct`

```c
Product products[10];
```

tạo một mảng mười object `Product` liên tiếp. Tên mảng chuyển thành `Product *` trong hầu hết biểu thức; `products[index].quantity` truy cập member của phần tử.

### Gán và truyền `struct`

C cho phép:

```c
Product copy = product;
```

Mỗi member được sao chép theo giá trị. Với `name` là mảng nằm trong struct, toàn bộ mảng được chép.

Truyền `Product` trực tiếp vào hàm cũng tạo bản sao. Với object lớn hoặc cần sửa object gốc, pointer thường phù hợp hơn.

### Đào sâu (có thể quay lại sau)

Compiler có thể chèn **padding** giữa hoặc sau các member để đáp ứng alignment. Vì vậy không giả định `sizeof(Product)` bằng tổng `sizeof` từng member, không tự serialize struct bằng cách ghi raw byte ra file và mong đọc được trên mọi compiler/hệ thống.

Nếu struct có member pointer, phép gán chỉ sao chép địa chỉ—gọi là shallow copy. Hai struct sau đó có thể cùng trỏ một allocation; code phải xác định owner, không `free` hai lần. Muốn hai bản độc lập phải tự thiết kế deep copy.

Kiểu số nguyên cụ thể dùng để biểu diễn `enum` là quyết định implementation trong các giới hạn chuẩn. Không dùng raw enum layout làm protocol/file format.

## 6. Lỗi thường gặp

### Dereference trước kiểm tra `NULL`

`get_stock_state` không kiểm tra `NULL`, nên contract nội bộ của nó yêu cầu pointer hợp lệ. `print_product` kiểm tra trước khi gọi. Nếu hàm là API public, cân nhắc trả trạng thái lỗi rõ ràng.

### Nhầm `.` với `->`

- object: `product.quantity`;
- pointer: `product_pointer->quantity`.

Không cast để che lỗi cú pháp/kiểu.

### Không kiểm tra overflow khi cập nhật member

`quantity += amount` có thể signed overflow, là undefined behavior. Kiểm tra `amount > INT_MAX - quantity` khi cả hai không âm.

### Cho rằng `enum` chặn mọi giá trị lạ

C vẫn có thể nhận giá trị không khớp enumerator từ input hoặc cast. `stock_state_name` có fallback `"UNKNOWN"` thay vì giả định mọi bit pattern đều hợp lệ.

### Ghi chuỗi quá dài vào mảng member

`name[32]` chỉ chứa tối đa 31 ký tự dữ liệu và `'\0'`. Khi lấy input, phải kiểm soát kích thước; không dùng hàm copy không biết capacity.

## 7. Bài tập

### Bài 1 — Kiểu `Student`

Tạo `struct` có mã, tên và điểm; viết hàm chỉ đọc để in.

**Gợi ý:** dùng designated initializer và `const Student *`.

### Bài 2 — Trạng thái đơn hàng

Tạo `enum OrderState` gồm `PENDING`, `PAID`, `SHIPPED`, `CANCELLED` và hàm đổi trạng thái thành chuỗi.

**Gợi ý:** thêm fallback cho giá trị không nhận diện.

### Bài 3 — Mảng sản phẩm

Tạo mảng `Product`, tìm sản phẩm có quantity thấp nhất và trả borrowed pointer.

**Gợi ý:** áp dụng pointer cấp hai từ bài 04 nếu muốn trả trạng thái riêng.

### Bài 4 — Shallow copy audit

Thêm member `char *description` vào một struct minh họa và vẽ hai object sau phép gán.

**Gợi ý:** không cần chạy code; chỉ rõ cả hai pointer cùng trỏ allocation nào và nguy cơ double free.

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi gom dữ liệu liên quan vào một `struct`.
- [ ] Tôi dùng `enum` cho tập trạng thái hữu hạn.
- [ ] Tôi phân biệt `.` và `->`.
- [ ] Tôi biết `typedef` không cấp phát bộ nhớ.
- [ ] Tôi hiểu padding và shallow copy của pointer member.

**Bài prerequisite:** [Lỗi bộ nhớ và undefined behavior](./08-loi-bo-nho-va-undefined-behavior.md)

**Bài tiếp theo:** [Union, bit-field và bộ nhớ](./10-union-bit-field-va-bo-nho.md)
