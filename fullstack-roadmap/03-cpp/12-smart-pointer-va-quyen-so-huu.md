# Smart pointer và quyền sở hữu

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Smart pointer biểu đạt ownership; raw pointer/reference vẫn có thể là view không sở hữu.
- Ưu tiên value, rồi unique_ptr; chỉ dùng shared_ptr khi thật sự có nhiều owner.
- Reference counting không tự làm dữ liệu thread-safe; shared cycle có thể giữ object mãi.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng `std::unique_ptr` cho ownership duy nhất;
- chuyển ownership bằng move và tạo object bằng `std::make_unique`;
- dùng `std::shared_ptr` chỉ khi lifetime thật sự có nhiều owner;
- dùng `std::weak_ptr` làm observer và phá ownership cycle;
- vẽ object, smart pointer và control block đúng vùng/lifetime.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một người giữ chìa khóa là unique owner; chuyển chìa đổi người chịu trách nhiệm. Nhiều người cùng có quyền giữ căn phòng tồn tại là shared ownership. Người chỉ xem lịch phòng là observer, không kéo dài thời gian thuê.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| unique_ptr | owner động duy nhất, không copy | sách trong Shelf |
| shared_ptr | owner cùng chia sẻ vòng đời | Promotion |
| weak_ptr | observer không giữ object sống | PromotionObserver |
| control block | state quản lý shared/weak ownership | số owner và thông tin cleanup |
| lock | thử lấy shared owner từ weak observer | giữ object sống trong nhánh if |

### Ví dụ nhỏ — tính tay trước

Owner A giữ Book, raw view V nhìn Book. Move A sang B → A rỗng, B sở hữu cùng Book, V vẫn dùng được khi Book còn sống. B.reset() → Book hủy, V không được dùng nữa.

Một kệ sách cần sở hữu nhiều object `Book` được tạo động. Khi kệ bị hủy, toàn bộ sách phải tự bị hủy. Một màn hình khác chỉ quan sát chương trình khuyến mãi dùng chung:

- kệ là owner duy nhất của từng sách;
- không có raw `new`/`delete` trong code nghiệp vụ;
- chương trình khuyến mãi có thể được nhiều component sở hữu;
- observer không được kéo dài lifetime khuyến mãi và phải phát hiện khi nó hết hạn.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. make_unique tạo hai Book; Shelf::add nhận ownership và move vào vector.
2. Vector reallocation có thể dời unique_ptr, nhưng không tự dời Book mà chúng sở hữu.
3. Promotion có shared owner ở main; observer giữ weak. lock lần đầu tạo owner tạm rồi trả sau block.
4. main reset owner cuối, Promotion hủy; lock sau trả rỗng. Control block có thể sống tới khi weak cuối hết; shared có overhead quản lý count, unique không cần shared count.

### Mini-check

weak_ptr còn sống sau khi owner cuối reset: object Promotion hay control block còn tồn tại?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Value / reference | sở hữu theo object hoặc mượn | đơn giản khi vòng đời đủ; reference không gia hạn |
| unique_ptr | một owner động | chuyển bằng move, ít overhead; không dùng dynamic khi value đủ |
| shared_ptr / weak_ptr | nhiều owner / quan sát | cần control block và tránh cycle; không dùng để che owner chưa rõ |

### Misconception check

**Đúng hay sai?** Move unique_ptr luôn làm raw view tới Book mất hiệu lực.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chuyển owner không dời Book; view còn hợp lệ trong vòng đời Book.

</details>

**Đúng hay sai?** shared_ptr làm mọi thao tác trên T tự đồng bộ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: quản lý count không đồng bộ việc sửa object T.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** vẽ owner và borrow.

- **Working Developer — dùng khi làm việc:** unique move, weak lock và cleanup.

- **Deep Dive — có thể quay lại sau:** control block, cycle và giới hạn thread safety.

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

## 7. Khi nào KHÔNG dùng

Không dùng shared_ptr mặc định cho toàn bộ graph. Không delete kết quả get(); đó là view. Nếu kệ chỉ chứa Book đồng nhất theo value và không cần địa chỉ/lifetime động riêng, vector<Book> thường đơn giản hơn.

## 8. Production notes & scale check

Demo hai sách không có driver performance; dùng để quan sát ownership. Test move giữ địa chỉ object, source rỗng, reject empty pointer và weak hết hạn. Shared cycle cần thiết kế cạnh sở hữu theo domain, không đổi ngẫu nhiên một cạnh chỉ để hết leak.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Thay Product* owner và chuỗi cấp phát tay của Module 02 bằng lựa chọn C++: phần nào nên là value/string, phần nào thực sự cần unique_ptr? Nêu lý do không dùng shared_ptr cho dữ liệu một kho sở hữu.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Ai hủy Book khi Shelf hết scope?
2. get khác release về ownership thế nào? Tra contract release trước khi dùng.
3. Vẽ vòng shared cycle và cạnh observer hợp lý.

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] chọn smart pointer theo ownership thay vì thói quen;
- [ ] vẽ move của `unique_ptr`;
- [ ] phân biệt object với control block của `shared_ptr`;
- [ ] dùng `weak_ptr::lock`;
- [ ] giải thích raw pointer từ `get()` không phải owner.

**Bài prerequisite:** [Exception và RAII](./11-exception-va-raii.md)

**Bài tiếp theo:** [Move semantics và perfect forwarding](./13-move-semantics-va-perfect-forwarding.md)
