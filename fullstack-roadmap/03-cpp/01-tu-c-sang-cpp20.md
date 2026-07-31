# Từ C sang C++20

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tạo, biên dịch và chạy một chương trình C++20 từ terminal;
- dùng `std::cin`, `std::cout` và `std::string` cho nhập/xuất cơ bản;
- giải thích vai trò của header, namespace `std` và toán tử `<<`, `>>`;
- nhận ra phần C++ kế thừa từ C và một số khác biệt quan trọng;
- bật nhóm cảnh báo nghiêm ngặt để phát hiện lỗi sớm.

## 2. Bài toán mở đầu

Chương trình C quản lý kho ở module trước đã dùng mảng `char`, `printf` và `scanf`. Bây giờ cửa hàng cần một chương trình nhỏ lập hóa đơn:

- nhập tên sản phẩm có khoảng trắng;
- nhập số lượng và đơn giá nguyên theo VND;
- tính VAT `8%`;
- từ chối số lượng không dương hoặc đơn giá âm.

Ta có thể tiếp tục viết C, nhưng đây là cơ hội chuyển sang công cụ nhập/xuất và kiểu chuỗi của C++ mà chưa cần biết OOP.

## 3. Lời giải bằng code

Tạo file `main.cpp`:

```cpp
#include <iostream>
#include <string>

int main()
{
    constexpr int vat_percent = 8;
    constexpr int max_quantity = 1'000'000;
    constexpr long long max_unit_price = 1'000'000'000'000LL;

    std::string product_name;
    int quantity = 0;
    long long unit_price = 0;

    std::cout << "Product name: ";
    std::getline(std::cin, product_name);

    std::cout << "Quantity: ";
    std::cin >> quantity;

    std::cout << "Unit price (VND): ";
    std::cin >> unit_price;

    // Giới hạn nghiệp vụ giữ các phép tính bên dưới trong miền long long.
    if (!std::cin
        || product_name.empty()
        || quantity <= 0
        || quantity > max_quantity
        || unit_price < 0
        || unit_price > max_unit_price)
    {
        std::cerr << "Invalid invoice data\n";
        return 1;
    }

    const long long subtotal = static_cast<long long>(quantity) * unit_price;
    const long long vat = subtotal * vat_percent / 100;
    const long long total = subtotal + vat;

    std::cout << "\nInvoice\n";
    std::cout << "Product: " << product_name << '\n';
    std::cout << "Subtotal: " << subtotal << " VND\n";
    std::cout << "VAT: " << vat << " VND\n";
    std::cout << "Total: " << total << " VND\n";

    return 0;
}
```

Biên dịch bằng compiler hỗ trợ C++20:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o invoice
```

Chạy và nhập lần lượt `Mechanical Keyboard`, `3`, `250000`:

```text
Product name: Mechanical Keyboard
Quantity: 3
Unit price (VND): 250000

Invoice
Product: Mechanical Keyboard
Subtotal: 750000 VND
VAT: 60000 VND
Total: 810000 VND
```

Mẫu này đã được kiểm tra bằng `g++ 15.2.0`, chế độ C++20 và toàn bộ cờ cảnh báo trong lệnh trên.

## 4. Giải thích cơ chế

### 4.1. Chương trình vẫn bắt đầu tại `main`

Giống C, hệ điều hành chuyển quyền điều khiển cho hàm `main`. `return 0` báo thành công; `return 1` báo dữ liệu không hợp lệ.

Các cấu trúc đã học trong C vẫn giữ ý nghĩa quen thuộc:

- khai báo biến, phép toán và `if`;
- block `{ ... }` và phạm vi biến;
- kiểu số nguyên `int`, `long long`;
- biểu thức điều kiện và thứ tự chạy từ trên xuống.

C++ không phải “C có thêm vài keyword”. Hai ngôn ngữ có lịch sử chung nhưng là hai ngôn ngữ riêng. Từ đây, file dùng đuôi `.cpp` và được biên dịch ở chế độ C++20.

### 4.2. Header và namespace

```cpp
#include <iostream>
#include <string>
```

- `<iostream>` khai báo các stream chuẩn như `std::cin`, `std::cout`, `std::cerr`.
- `<string>` khai báo kiểu `std::string`.
- `std::` cho biết tên nằm trong namespace chuẩn `std`, nhờ đó tên thư viện không xung đột với tên do chương trình tự đặt.

Không viết `using namespace std;` ở phạm vi toàn cục. Cách đó đưa rất nhiều tên vào cùng phạm vi và dễ gây xung đột khi chương trình lớn lên. Viết rõ `std::` giúp người đọc biết tên đến từ thư viện chuẩn.

### 4.3. Stream nhập và xuất

Trong biểu thức:

```cpp
std::cout << "Total: " << total << " VND\n";
```

toán tử `<<` lần lượt đưa chuỗi, giá trị `total` và chuỗi cuối vào output stream. Cùng một ký hiệu làm việc với nhiều kiểu vì C++ cho phép *operator overloading*. [Bài 03](./03-class-object-encapsulation.md) sẽ đặt cơ chế này trong bối cảnh class; hiện tại chỉ cần biết stream chọn cách in phù hợp với kiểu dữ liệu.

Ngược lại:

```cpp
std::cin >> quantity;
```

đọc và chuyển token tiếp theo thành `int`. Nếu người dùng nhập chữ, phép đọc thất bại và stream chuyển sang trạng thái lỗi. Điều kiện `!std::cin` phát hiện trạng thái đó.

`std::getline(std::cin, product_name)` đọc cả dòng, nên giữ được khoảng trắng trong tên sản phẩm. Do `getline` được gọi trước mọi toán tử `>>`, bài này chưa gặp ký tự xuống dòng còn sót lại trong input.

### 4.4. Bộ nhớ của các biến

Các biến cục bộ dưới đây có automatic storage duration. Chuẩn C++ quy định scope/lifetime chứ không bắt buộc vị trí vật lý; compiler có thể dùng register hoặc tối ưu bỏ storage. Mô hình triển khai phổ biến để học lần đầu là stack frame:

```text
stack frame của main (mô hình triển khai phổ biến)
├── vat_percent       = 8
├── max_quantity      = 1000000
├── max_unit_price    = 1000000000000
├── product_name      = object std::string
├── quantity          = 3
├── unit_price        = 250000
├── subtotal          = 750000
├── vat               = 60000
└── total             = 810000
```

`std::string` là một kiểu thư viện quản lý chuỗi. `product_name` là automatic object, thường được biểu diễn trong stack frame của `main`; phần ký tự dài có thể được object quản lý trong dynamic storage tùy triển khai. Khi ra khỏi `main`, destructor của `std::string` tự thu hồi tài nguyên nó sở hữu. Constructor, destructor và mô hình storage sẽ được phân tích ở [bài 04](./04-constructor-destructor-va-bo-nho.md).

Chương trình không gọi `malloc` hoặc `free` cho chuỗi. Chính object `std::string` chịu trách nhiệm quản lý phần lưu trữ của nó.

## 5. Kiến thức nền

### `constexpr`, `const` và khởi tạo

`constexpr int vat_percent = 8;` nói giá trị có thể được xác định khi biên dịch và không đổi. Các biến kết quả dùng `const` vì sau khi tính xong không nên bị gán lại.

C++ khuyến khích khởi tạo ngay khi khai báo:

```cpp
int quantity = 0;
```

Biến cục bộ kiểu số không tự động có giá trị `0` nếu bạn chỉ viết `int quantity;`. Đọc nó trước khi gán gây undefined behavior.

### Chuyển kiểu có chủ đích

```cpp
static_cast<long long>(quantity)
```

chuyển `quantity` sang `long long` trước phép nhân. Cú pháp `static_cast<T>(value)` thể hiện rõ kiểu đích hơn cast kiểu C. Trong bài này, `unit_price` vốn đã là `long long`, nhưng viết chuyển kiểu tường minh cũng làm ý định “tính bằng miền số rộng” rõ ràng.

### Tiền và phép chia nguyên

Chương trình lưu VND bằng số nguyên, tránh sai số biểu diễn của `float`/`double`. Hai giới hạn nghiệp vụ bảo đảm các phép nhân và phép cộng trong công thức không vượt miền `long long`; input ngoài giới hạn bị từ chối trước khi tính. Công thức `subtotal * 8 / 100` bỏ phần lẻ nhỏ hơn một VND vì là phép chia nguyên. Hệ thống thật phải quy định cả miền dữ liệu và chính sách làm tròn; không tự giả định.

### Các cờ compiler

| Cờ | Ý nghĩa |
|---|---|
| `-std=c++20` | biên dịch theo chuẩn C++20 |
| `-Wall -Wextra` | bật nhiều cảnh báo hữu ích |
| `-Wpedantic` | cảnh báo extension ngoài chuẩn |
| `-Werror` | coi cảnh báo là lỗi build |

Compiler khác có thể dùng tên cờ khác, nhưng mục tiêu vẫn là chọn C++20 và không bỏ qua warning.

## 6. Lỗi thường gặp

### Biên dịch `.cpp` như C

`cc main.cpp` có thể chọn driver hoặc linker không phù hợp. Dùng compiler driver C++ như `c++`, `g++` hoặc `clang++`.

### Viết `using namespace std;` ở đầu mọi file

Ví dụ nhỏ vẫn có thể build, nhưng thói quen này gây va chạm tên trong code lớn, đặc biệt ở header. Dùng tiền tố `std::`.

### Dùng `std::endl` cho mọi dòng

`std::endl` vừa xuống dòng vừa buộc flush buffer. Việc flush liên tục có thể không cần thiết. Dùng `'\n'` khi chỉ cần xuống dòng.

### Không kiểm tra trạng thái input

Nếu `std::cin >> quantity` thất bại, `quantity` không chứa dữ liệu người dùng mong muốn. Kiểm tra stream trước khi tính.

### Trộn `>>` rồi `getline` mà không xử lý newline

Sau `std::cin >> number`, ký tự xuống dòng thường vẫn còn trong stream; `getline` kế tiếp có thể đọc một dòng rỗng. Bài này gọi `getline` trước. Khi phải gọi sau, có thể dùng:

```cpp
std::getline(std::cin >> std::ws, product_name);
```

`std::ws` bỏ whitespace đứng trước. Đây là API được giới thiệu ngay tại đây; chỉ dùng khi việc bỏ toàn bộ whitespace đầu dòng là đúng yêu cầu.

### Cho rằng code C hợp lệ luôn là C++ hợp lệ

Không phải mọi chương trình C đều biên dịch hoặc có cùng ý nghĩa trong C++. Hãy biên dịch file C bằng chế độ C và file C++ bằng đúng chuẩn C++20.

## 7. Bài tập

### Bài 1 — Đổi hóa đơn

Nhập số lượng và đơn giá cho một sản phẩm khác, sau đó thêm dòng in số lượng.

**Gợi ý:** nối thêm `<< quantity` vào output stream.

### Bài 2 — Giảm giá

Thêm hằng số giảm giá `5%`, tính giảm giá trước VAT và in đủ `subtotal`, `discount`, `vat`, `total`.

**Gợi ý:** giữ toàn bộ số tiền ở `long long`; viết rõ thứ tự nghiệp vụ.

### Bài 3 — Kiểm tra lỗi từng trường

Thay thông báo chung bằng ba thông báo riêng cho tên rỗng, số lượng không dương và đơn giá âm.

**Gợi ý:** kiểm tra trạng thái stream trước, rồi kiểm tra từng giá trị bằng các `if` riêng.

### Bài 4 — Quan sát warning

Tạo một biến cục bộ không dùng, build với và không có `-Werror`, ghi lại khác biệt.

**Gợi ý:** không giữ biến thừa trong phiên bản cuối.

### Bài 5 — Chính sách làm tròn

Thử `subtotal = 101` và VAT `8%`. Mô tả chính xác vì sao kết quả VAT là `8`, rồi đề xuất quy tắc làm tròn khác bằng số nguyên.

**Gợi ý:** muốn làm tròn gần nhất cho số không âm, nghiên cứu việc cộng nửa mẫu số trước phép chia.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] build chương trình bằng C++20 với warning nghiêm ngặt;
- [ ] phân biệt `std::getline` với toán tử `>>`;
- [ ] giải thích `std::`, `<iostream>` và `<string>`;
- [ ] mô tả automatic object và stack-frame model thường gặp mà không coi đó là yêu cầu vật lý của chuẩn;
- [ ] giải thích vì sao bài này không tự `free` dữ liệu của `std::string`.

**Bài prerequisite:** [Dự án C quản lý kho](../02-c-chuyen-sau/15-du-an-c-quan-ly-kho.md)

**Bài tiếp theo:** [Reference, const và vòng đời object](./02-reference-const-va-vong-doi-doi-tuong.md)
