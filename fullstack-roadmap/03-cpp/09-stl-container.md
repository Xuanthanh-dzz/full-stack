# STL container

## 1. Mục tiêu

Sau bài này, bạn có thể:

- chọn container chuẩn theo nhu cầu truy cập, thứ tự và tra cứu;
- dùng `std::vector`, `std::map` và `std::set` trong một bài toán hoàn chỉnh;
- duyệt container bằng range-based `for`;
- mô tả ownership và vùng nhớ của `std::vector`;
- nhận ra khi thay đổi container làm reference/pointer đến phần tử mất hiệu lực.

## 2. Bài toán mở đầu

Một thư viện nhỏ cần lưu:

- danh mục sách theo thứ tự nhập;
- số bản còn lại tra cứu theo mã ISBN;
- tập mã thành viên đang mượn, không trùng nhau.

Mảng C có capacity cố định và yêu cầu tự dịch phần tử khi thêm/xóa. Một cấu trúc duy nhất cũng không tối ưu cho cả ba nhu cầu. Ta sẽ chọn từng container theo operation quan trọng thay vì dùng cùng một cấu trúc cho mọi dữ liệu.

## 3. Lời giải bằng code

Mẫu dùng hai cú pháp mới:

- `for (const Book& book : books)` duyệt lần lượt từng phần tử mà không copy;
- `const auto& [isbn, copies]` tách một cặp key/value của map; `auto` yêu cầu compiler suy luận kiểu dài đó.

```cpp
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>

struct Book
{
    std::string isbn;
    std::string title;
};

int main()
{
    const std::vector<Book> books{
        {"CPP20", "C++20 in Practice"},
        {"RAII", "Resource Safety"}};

    std::map<std::string, int> stock_by_isbn{
        {"CPP20", 2},
        {"RAII", 3}};

    std::set<std::string> active_members;

    const std::string borrowed_isbn = "CPP20";
    if (stock_by_isbn.contains(borrowed_isbn)
        && stock_by_isbn[borrowed_isbn] > 0)
    {
        --stock_by_isbn[borrowed_isbn];
        active_members.insert("MEM-002");
        active_members.insert("MEM-001");
        active_members.insert("MEM-001"); // set bỏ giá trị trùng.
    }

    std::cout << "Catalog:\n";
    for (const Book& book : books)
    {
        std::cout << "- " << book.isbn << ": " << book.title << '\n';
    }

    std::cout << "Stock:\n";
    for (const auto& [isbn, copies] : stock_by_isbn)
    {
        std::cout << isbn << ": " << copies << '\n';
    }

    std::cout << "Active members:\n";
    for (const std::string& member_id : active_members)
    {
        std::cout << member_id << '\n';
    }

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o containers
./containers
```

Kết quả:

```text
Catalog:
- CPP20: C++20 in Practice
- RAII: Resource Safety
Stock:
CPP20: 1
RAII: 3
Active members:
MEM-001
MEM-002
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

## 4. Giải thích cơ chế

### 4.1. `std::vector` sở hữu dãy liên tiếp

`std::vector<Book>` là class template từ `<vector>`. `books` là automatic object; implementation thường đặt phần quản lý vector trong stack frame của `main`, nhưng standard không bắt buộc vị trí vật lý đó. Vector quản lý một vùng dynamic storage liên tiếp cho các phần tử:

```text
automatic storage (thường stack)       dynamic storage
books: vector<Book> object
├── địa chỉ đầu ─────────────────────> [Book #0][Book #1]
├── size = 2
└── capacity >= 2
```

Hai `Book` là hai object phần tử riêng, đặt liên tiếp. Mỗi `Book` lại chứa hai object `std::string`; string tự quản lý buffer ký tự nếu cần.

Khi `books` ra khỏi scope:

1. destructor từng `Book` chạy;
2. member string của từng book tự dọn dữ liệu;
3. vector trả vùng lưu trữ phần tử.

Code không gọi `delete[]`: vector là owner theo Rule of Zero.

### 4.2. `size` và `capacity`

- `size()` là số phần tử đang sống.
- `capacity()` là số phần tử vector có thể chứa trong vùng hiện tại trước khi phải xin vùng lớn hơn.

Nếu thêm phần tử khi hết capacity, vector thường:

1. cấp phát vùng lớn hơn;
2. move hoặc copy các phần tử sang vùng mới;
3. hủy phần tử và giải phóng vùng cũ.

```text
trước reallocation: pointer/ref ──> [Book ở vùng A]
sau reallocation:                  [Book ở vùng B]
                       vùng A đã hết lifetime
```

Pointer, reference và iterator đến phần tử cũ có thể bị invalid. Không giữ chúng qua operation có khả năng reallocate nếu chưa kiểm tra quy tắc.

### 4.3. `std::map` lưu key/value có thứ tự

`std::map<std::string, int>` ánh xạ một ISBN duy nhất sang số bản. Các phần tử được duyệt theo thứ tự tăng của key, nên output là `CPP20` rồi `RAII`.

`contains(key)` trong C++20 kiểm tra key có tồn tại mà không sửa map. `operator[]`:

- trả reference đến value nếu key tồn tại;
- nếu key chưa có, chèn key với value mặc định (`0` với `int`).

Vì vậy code kiểm tra `contains` trước. Với nghiệp vụ không được tự chèn, đừng dùng `[]` mà không hiểu side effect.

### 4.4. `std::set` bảo đảm phần tử duy nhất

`std::set<std::string>` lưu mỗi mã thành viên tối đa một lần và duyệt theo thứ tự tăng. Gọi `insert("MEM-001")` lần hai không tạo bản trùng.

Map và set là container kiểu node. Chúng không yêu cầu mọi phần tử nằm liên tiếp như vector. Operation chèn/xóa có đặc tính invalidation khác; xóa một node làm reference đến chính phần tử đó mất hiệu lực, còn reference đến node khác thường vẫn hợp lệ.

### 4.5. Range-based `for` không copy phần tử

```cpp
for (const Book& book : books)
```

ở mỗi vòng, `book` là const reference đến phần tử hiện tại. Nếu viết `for (Book book : books)`, mỗi vòng tạo một bản copy. Chỉ dùng bản copy khi thật sự cần state độc lập.

Structured binding:

```cpp
const auto& [isbn, copies]
```

tạo hai tên chỉ đọc tham chiếu đến key và value của phần tử map hiện tại. Không có map/cặp thứ hai được copy.

## 5. Kiến thức nền

### Bảng chọn container khởi đầu

| Nhu cầu chính | Container thường xem xét |
|---|---|
| dãy động, truy cập theo index, duyệt nhanh | `std::vector<T>` |
| đúng số phần tử biết ở compile time | `std::array<T, N>` |
| thêm/xóa hiệu quả ở hai đầu | `std::deque<T>` |
| danh sách node, cần splice/iterator ổn định đặc thù | `std::list<T>` |
| key duy nhất, có thứ tự | `std::set<T>` |
| key → value, có thứ tự | `std::map<K, V>` |
| key/set, trung bình tra cứu hằng số, không cần thứ tự | `std::unordered_map`, `std::unordered_set` |
| FIFO | `std::queue<T>` |
| LIFO | `std::stack<T>` |

`queue` và `stack` là container adaptor: chúng giới hạn interface của container bên dưới theo semantics FIFO/LIFO.

Đừng chọn `std::list` vì nghĩ “chèn O(1) luôn nhanh”. Trước hết phải tìm đúng vị trí; allocation từng node và locality kém có thể làm nó chậm hơn vector trong thực tế.

### `std::array`

`std::array<T, N>` bọc một mảng có kích thước compile-time, không tự cấp phát động cho phần tử. Nó có `size()`, range-for và API đồng nhất với container khác. Dùng khi `N` thật sự cố định.

### `unordered_map` và hash

`std::unordered_map` dùng hash và không bảo đảm thứ tự duyệt. Độ phức tạp tra cứu trung bình thường gần O(1), nhưng trường hợp xấu có thể O(n). Nếu output/test cần thứ tự, hãy sort riêng hoặc dùng `std::map` khi thứ tự key đúng nhu cầu.

### Độ phức tạp khái quát

| Operation | `vector` | `map` | `unordered_map` trung bình |
|---|---:|---:|---:|
| truy cập theo index | O(1) | không có | không có |
| tìm theo key | O(n) nếu tự quét | O(log n) | O(1) trung bình |
| thêm cuối | O(1) amortized | — | — |
| chèn/xóa giữa | O(n) do dịch phần tử | O(log n) | O(1) trung bình |

Big-O sẽ được học hệ thống ở module 07. “Amortized” nghĩa là một số lần thêm có thể đắt do reallocation, nhưng chi phí trung bình trên một chuỗi lần thêm vẫn hằng số.

### Đào sâu (có thể quay lại sau)

Container nhận một allocator template parameter để kiểm soát cách xin/trả storage. Hầu hết ứng dụng nên dùng allocator mặc định; custom allocator chỉ nên xuất hiện khi profiling và constraint tài nguyên chứng minh cần.

`reserve(n)` của vector tăng capacity tối thiểu nhưng không tăng size và không tạo `n` phần tử sống. Dùng khi biết gần đúng số phần tử để giảm reallocation. Không gọi `reserve(size() + 1)` trước mọi lần thêm vì có thể phá chiến lược tăng trưởng hình học và làm hiệu năng xấu đi.

Các bảo đảm iterator/reference invalidation khác nhau theo từng operation và container. Luôn tra contract chính xác thay vì suy từ hình dung “heap” hay “node”.

## 6. Lỗi thường gặp

### Dùng `map[key]` chỉ để kiểm tra

`operator[]` có thể chèn key mới. Dùng `contains` nếu chỉ hỏi tồn tại.

### Giữ reference đến vector rồi thêm phần tử

`push_back` có thể reallocate và làm reference dangling. Lấy lại reference sau mutation hoặc bảo đảm capacity theo contract.

### Duyệt bằng value không cần thiết

`for (Book book : books)` copy mỗi `Book`. Dùng `const Book&` nếu chỉ đọc.

### Trông đợi thứ tự từ unordered container

Thứ tự duyệt không ổn định theo insertion và có thể đổi giữa môi trường. Không viết output/test dựa vào nó.

### Chọn container chỉ theo một Big-O

Memory locality, số allocation, invalidation và pattern dữ liệu đều quan trọng. Đo workload thật khi quyết định ảnh hưởng hiệu năng.

### Lưu raw owning pointer trong container

`std::vector<Book*>` không tự biết phải `delete` object. [Bài 12](./12-smart-pointer-va-quyen-so-huu.md) sẽ dùng smart pointer khi cần polymorphic/dynamic ownership; hiện tại hãy lưu object trực tiếp.

## 7. Bài tập

### Bài 1 — Thêm sách

Đổi `books` thành không `const`, dùng `push_back` thêm một `Book` và in lại catalog.

**Gợi ý:** `books.push_back(Book{"NEW", "New Book"});`.

### Bài 2 — Kiểm tra mượn thất bại

Thử ISBN không tồn tại và ISBN có stock `0`, in lý do riêng mà không vô tình chèn key.

**Gợi ý:** gọi `contains` trước khi dùng `[]`.

### Bài 3 — Hàng chờ

Dùng `std::queue<std::string>` lưu mã thành viên chờ sách theo FIFO.

**Gợi ý:** cần `<queue>`; thao tác chính là `push`, `front`, `pop`, `empty`.

### Bài 4 — So sánh map/unordered_map

Thay map bằng unordered_map, chạy nhiều lần và ghi nhận vì sao không được dựa vào thứ tự output.

**Gợi ý:** thêm `<unordered_map>`; semantics key/value vẫn giữ nhưng iteration order không được bảo đảm.

### Bài 5 — Quan sát reallocation

In `size()`, `capacity()` và địa chỉ phần tử đầu sau mỗi `push_back`.

**Gợi ý:** chỉ lấy `&books[0]` khi vector không rỗng; không dereference địa chỉ cũ sau reallocation.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] chọn vector/map/set theo operation của bài toán;
- [ ] vẽ vector object và vùng phần tử liên tiếp nó sở hữu;
- [ ] phân biệt `size` với `capacity`;
- [ ] giải thích side effect của `map::operator[]`;
- [ ] nhận ra operation có thể invalidate reference.

**Bài prerequisite:** [Template và generic programming](./08-template-va-generic-programming.md)

**Bài tiếp theo:** [Iterator, algorithm và lambda](./10-iterator-algorithm-va-lambda.md)
