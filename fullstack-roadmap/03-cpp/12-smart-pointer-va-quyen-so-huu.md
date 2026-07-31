# Smart pointer và quyền sở hữu

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng `std::unique_ptr` cho ownership duy nhất;
- chuyển ownership bằng move và tạo object bằng `std::make_unique`;
- dùng `std::shared_ptr` chỉ khi lifetime thật sự có nhiều owner;
- dùng `std::weak_ptr` làm observer và phá ownership cycle;
- vẽ object, smart pointer và control block đúng vùng/lifetime.

## 2. Bài toán mở đầu

Một kệ sách cần sở hữu nhiều object `Book` được tạo động. Khi kệ bị hủy, toàn bộ sách phải tự bị hủy. Một màn hình khác chỉ quan sát chương trình khuyến mãi dùng chung:

- kệ là owner duy nhất của từng sách;
- không có raw `new`/`delete` trong code nghiệp vụ;
- chương trình khuyến mãi có thể được nhiều component sở hữu;
- observer không được kéo dài lifetime khuyến mãi và phải phát hiện khi nó hết hạn.

## 3. Lời giải bằng code

Điều kiện `if (const std::shared_ptr<...> promotion = promotion_.lock())` vừa tạo một smart pointer cục bộ, vừa kiểm tra pointer đó có object hay không. Biến `promotion` chỉ sống trong nhánh `if`/`else`.

```cpp
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

class Book
{
public:
    explicit Book(const std::string& title)
        : title_{title}
    {
    }

    const std::string& title() const
    {
        return title_;
    }

private:
    std::string title_;
};

class Shelf
{
public:
    void add(std::unique_ptr<Book> book)
    {
        if (!book)
        {
            throw std::invalid_argument{"Book must not be null"};
        }

        // Chuyển owner duy nhất vào vector; parameter trở thành empty.
        books_.push_back(std::move(book));
    }

    void print() const
    {
        std::cout << "Shelf:\n";
        for (const std::unique_ptr<Book>& book : books_)
        {
            std::cout << "- " << book->title() << '\n';
        }
    }

private:
    std::vector<std::unique_ptr<Book>> books_;
};

class Promotion
{
public:
    explicit Promotion(const std::string& code)
        : code_{code}
    {
    }

    const std::string& code() const
    {
        return code_;
    }

private:
    std::string code_;
};

class PromotionObserver
{
public:
    explicit PromotionObserver(
        const std::shared_ptr<const Promotion>& promotion)
        : promotion_{promotion}
    {
    }

    void print_status() const
    {
        if (const std::shared_ptr<const Promotion> promotion = promotion_.lock())
        {
            std::cout << "Promotion active: " << promotion->code() << '\n';
        }
        else
        {
            std::cout << "Promotion expired\n";
        }
    }

private:
    std::weak_ptr<const Promotion> promotion_;
};

int main()
{
    Shelf shelf;
    shelf.add(std::make_unique<Book>("Effective C++"));
    shelf.add(std::make_unique<Book>("C++ Templates"));
    shelf.print();

    std::shared_ptr<const Promotion> promotion =
        std::make_shared<const Promotion>("SUMMER");
    PromotionObserver observer{promotion};

    observer.print_status();
    promotion.reset();
    observer.print_status();

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o smart_pointers
./smart_pointers
```

Kết quả:

```text
Shelf:
- Effective C++
- C++ Templates
Promotion active: SUMMER
Promotion expired
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

## 4. Giải thích cơ chế

### 4.1. `unique_ptr` biểu đạt một owner

Mỗi lời gọi:

```cpp
std::make_unique<Book>("Effective C++")
```

tạo một `Book` động riêng và trả `std::unique_ptr<Book>` sở hữu object đó:

```text
temporary unique_ptr ─────> dynamic Book #1 (thường ở heap)
```

Lời gọi thứ hai tạo `Book #2` trong vùng lưu trữ khác. Hai title không dùng chung một `Book`.

`unique_ptr` không copy được vì copy sẽ tạo hai owner. `Shelf::add` nhận ownership theo value, rồi:

```cpp
books_.push_back(std::move(book));
```

move ownership vào phần tử vector:

```text
trước move
parameter book ───────────> Book #1

sau move
vector[0] unique_ptr ─────> Book #1
parameter book = empty
```

Khi `Shelf` bị hủy, vector hủy từng `unique_ptr`; mỗi pointer hủy đúng `Book` nó sở hữu.

`add` từ chối empty pointer trước khi commit, nên `print` có invariant rằng mọi phần tử trong `books_` đều sở hữu một `Book`.

### 4.2. Vì sao dùng `make_unique`

`make_unique<T>(arguments...)`:

- tạo object và smart pointer trong một expression;
- tránh raw owning pointer xuất hiện ở caller;
- an toàn trước exception trong composition phức tạp;
- thể hiện ownership ngay trong type.

Nếu object không cần dynamic lifetime hoặc polymorphism, vẫn ưu tiên object theo value; smart pointer không phải mặc định cho mọi object.

### 4.3. `shared_ptr` có nhiều owner

`std::shared_ptr<const Promotion>` quản lý shared ownership. Về logic có:

```text
shared_ptr owner(s) ───────> const Promotion object
                    \
                     └────> control block
                            ├── strong owner count
                            └── weak observer count
```

`std::make_shared` tạo object và control block; triển khai thường đồng cấp phát chúng trong một allocation để giảm overhead. Về semantics, control block vẫn theo dõi hai loại count riêng.

Khi strong owner cuối cùng release/reset:

1. `Promotion` bị hủy;
2. control block còn có thể sống nếu vẫn còn `weak_ptr`;
3. control block bị giải phóng khi cả weak observer cuối cùng biến mất.

### 4.4. `weak_ptr` quan sát nhưng không sở hữu

`PromotionObserver` giữ `weak_ptr`, nên không tăng strong owner count. `lock()` thực hiện kiểm tra an toàn:

- nếu object còn sống, trả một `shared_ptr` tạm giữ object sống trong suốt block;
- nếu object đã bị hủy, trả empty `shared_ptr`.

Không kiểm tra `expired()` rồi mới dùng riêng rẽ trong code concurrent; lifetime có thể đổi giữa hai bước. `lock()` gộp kiểm tra và lấy temporary owner.

### 4.5. Raw pointer vẫn có vai trò non-owning

`unique_ptr::get()` trả raw pointer nhưng không chuyển ownership. Raw pointer/reference có thể dùng làm view ngắn hạn nếu contract lifetime rõ:

```text
unique_ptr owner ─────> Book
raw Book* view ───────> cùng Book, không được delete
```

View trở thành dangling khi object đích bị hủy, chẳng hạn owner hiện tại bị
`reset`, bị hủy hoặc được gán để sở hữu object khác. Move một `unique_ptr` chỉ
chuyển ownership; nó không tự di chuyển hay hủy `Book`, nên raw view vẫn hợp lệ
trong lúc owner đích còn giữ chính object đó. Không gọi `delete` trên kết quả
`get()`.

## 5. Kiến thức nền

### Bảng quyết định ownership

| Nhu cầu | Biểu diễn ưu tiên |
|---|---|
| object sống theo scope, không cần indirection | `T` theo value |
| đúng một owner động | `std::unique_ptr<T>` |
| chuyển owner | move `std::unique_ptr<T>` |
| nhiều owner lifetime thật sự | `std::shared_ptr<T>` |
| observer không sở hữu shared object | `std::weak_ptr<T>` |
| view bắt buộc có object | `T&` / `const T&` |
| view có thể không có object | `T*` / `const T*` |

Hãy bắt đầu với value/`unique_ptr`. Shared ownership làm lifetime khó suy luận hơn và có overhead control block.

### Cycle của `shared_ptr`

Nếu A giữ `shared_ptr` đến B và B giữ `shared_ptr` đến A, strong count không bao giờ về `0` dù code bên ngoài bỏ cả hai:

```text
A --shared--> B
^             |
└---shared----┘
```

Một cạnh không mang ownership phải đổi thành `weak_ptr`. Xác định owner theo domain, không chọn cạnh yếu tùy tiện chỉ để “hết leak”.

### `reset`, empty và boolean check

- `pointer.reset()` release ownership hiện tại.
- smart pointer empty không sở hữu object.
- `if (pointer)` kiểm tra có object trước khi dereference.
- dereference empty smart pointer là lỗi giống null raw pointer.

### `unique_ptr<T[]>`

`std::unique_ptr<T[]>` quản lý mảng động và dùng `delete[]`, nhưng với dãy động thông thường, `std::vector<T>` có size/capacity/API tốt hơn. Dùng array specialization khi contract API cấp thấp thật sự yêu cầu mảng.

### Đào sâu (có thể quay lại sau)

`shared_ptr` control block thường cập nhật count theo cách thread-safe, nhưng object `T` không tự trở thành thread-safe. Hai thread sửa cùng `T` vẫn cần synchronization.

`shared_ptr` tạo từ cùng raw pointer bằng hai constructor độc lập sẽ có hai control block và cuối cùng double delete. Không “bọc lại” raw pointer đã có owner; truyền/copy shared pointer gốc.

Smart pointer hỗ trợ custom deleter cho resource không được giải phóng bằng `delete`, ví dụ handle từ C API. Type của deleter là một phần type `unique_ptr`, còn `shared_ptr` type-erase deleter trong control block. Chỉ dùng khi contract resource yêu cầu.

## 6. Lỗi thường gặp

### Dùng `shared_ptr` cho mọi thứ

Nó che mờ owner, tăng allocation/counting và cho phép object sống lâu bất ngờ. Dùng value hoặc `unique_ptr` nếu ownership duy nhất.

### Copy `unique_ptr`

Copy bị compiler cấm. Nếu muốn chuyển ownership, dùng `std::move` và không dùng source như còn owner.

### Gọi `delete pointer.get()`

Smart pointer vẫn nghĩ nó sở hữu object và sẽ delete lần nữa. Kết quả là double delete.

### Tạo hai `shared_ptr` từ một raw pointer

Hai control block độc lập cùng sở hữu một địa chỉ. Dùng `make_shared` hoặc copy `shared_ptr` hiện có.

### Dùng `use_count()` làm logic nghiệp vụ

Count có thể đổi và không nói owner nào tồn tại. Nó phù hợp để chẩn đoán hạn chế, không phải điều kiện đồng bộ hay business rule.

### Giữ reference từ object sau khi owner hủy

Smart pointer bảo vệ lifetime chỉ trong khi có owner. Reference/raw view lấy ra không tự kéo dài lifetime.

## 7. Bài tập

### Bài 1 — Chuyển ownership

Tạo một `unique_ptr<Book>`, chuyển vào `Shelf` và kiểm tra pointer nguồn trở thành empty.

**Gợi ý:** `if (!book)` sau `std::move(book)`.

### Bài 2 — Xóa một sách

Thêm operation xóa sách theo title khỏi vector.

**Gợi ý:** dùng `std::erase_if`; khi phần tử `unique_ptr` bị xóa, `Book` tương ứng tự bị hủy.

### Bài 3 — Observer thứ hai

Tạo hai `PromotionObserver`, reset strong owner và xác nhận cả hai báo expired.

**Gợi ý:** weak observer không kéo dài lifetime.

### Bài 4 — Phá cycle

Thiết kế `Parent` sở hữu `Child` bằng `shared_ptr`, còn `Child` quan sát `Parent` bằng `weak_ptr`; vẽ control block.

**Gợi ý:** cạnh từ child lên parent không mang ownership.

### Bài 5 — Chọn representation

Với năm tình huống: local config, optional view, factory polymorphic, shared cache entry, callback observer, chọn value/reference/raw pointer/unique/shared/weak và giải thích.

**Gợi ý:** bắt đầu bằng câu hỏi “ai quyết định lifetime?”.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] chọn smart pointer theo ownership thay vì thói quen;
- [ ] vẽ move của `unique_ptr`;
- [ ] phân biệt object với control block của `shared_ptr`;
- [ ] dùng `weak_ptr::lock`;
- [ ] giải thích raw pointer từ `get()` không phải owner.

**Bài prerequisite:** [Exception và RAII](./11-exception-va-raii.md)

**Bài tiếp theo:** [Move semantics và perfect forwarding](./13-move-semantics-va-perfect-forwarding.md)
