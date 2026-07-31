# Constructor, destructor và bộ nhớ

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng constructor để khởi tạo đầy đủ các member ngay khi lifetime object bắt đầu;
- dùng member initializer list để khởi tạo data member;
- xác định thời điểm constructor và destructor chạy;
- phân biệt automatic storage duration với dynamic storage do `new` tạo;
- ghép đúng mỗi `new` minh họa với một `delete` và giải thích vì sao production ưu tiên RAII.

## 2. Bài toán mở đầu

Ở bài trước, `LoyaltyAccount` được tạo với ID rỗng rồi mới gọi setter. Giữa hai thao tác, object tồn tại ở trạng thái chưa sẵn sàng.

Với một cuốn sách, ta muốn:

- tên và giá phải có ngay khi object được tạo;
- in thông báo để quan sát chính xác lifetime;
- so sánh một object tự động với một object cấp phát động;
- không để rò rỉ object được cấp phát động.

Đoạn `new`/`delete` trong bài là thí nghiệm ownership có chủ đích. Đây chưa phải mẫu nên dùng cho code production; [RAII](./11-exception-va-raii.md) và [smart pointer](./12-smart-pointer-va-quyen-so-huu.md) sẽ thay thế nó ở bài 11–12.

Constructor mẫu chỉ yêu cầu caller truyền đủ `title` và `price`; nó **chưa** kiểm tra title rỗng hay price âm. Contract của bài là caller phải kiểm tra `title` không rỗng và `price >= 0` trước khi tạo `Book`. Cách báo lỗi ngay từ constructor sẽ được hoàn thiện sau khi học [exception ở bài 11](./11-exception-va-raii.md); không coi object từ input chưa kiểm tra là hợp lệ chỉ vì constructor đã chạy.

Tên biến/output `stack_book` và `heap_book` được giữ như nhãn học tập quen thuộc. Thuật ngữ chuẩn xác dùng trong phần cơ chế là *automatic storage duration* và *dynamic storage duration*; stack/heap chỉ là vị trí triển khai phổ biến.

## 3. Lời giải bằng code

```cpp
#include <iostream>
#include <string>

class Book
{
public:
    Book(const std::string& title, long long price)
        : title_{title}, price_{price}
    {
        std::cout << "Constructed: " << title_ << '\n';
    }

    ~Book()
    {
        std::cout << "Destroyed: " << title_ << '\n';
    }

    const std::string& title() const
    {
        return title_;
    }

    long long price() const
    {
        return price_;
    }

private:
    std::string title_;
    long long price_;
};

int main()
{
    Book stack_book{"Clean Code", 320000};

    // Demo ownership thủ công để quan sát heap.
    // Production nên dùng object tự động hoặc smart pointer.
    Book* heap_book = new Book{"C++ Core Guidelines", 450000};

    std::cout << "Stack book: " << stack_book.title()
              << ", " << stack_book.price() << " VND\n";
    std::cout << "Heap book: " << heap_book->title()
              << ", " << heap_book->price() << " VND\n";

    delete heap_book;
    heap_book = nullptr;

    std::cout << "Leaving main\n";
    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o lifetime
./lifetime
```

Kết quả:

```text
Constructed: Clean Code
Constructed: C++ Core Guidelines
Stack book: Clean Code, 320000 VND
Heap book: C++ Core Guidelines, 450000 VND
Destroyed: C++ Core Guidelines
Leaving main
Destroyed: Clean Code
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

## 4. Giải thích cơ chế

### 4.1. Constructor khởi tạo các member ban đầu

Constructor có cùng tên với class và không khai báo kiểu trả về:

```cpp
Book(const std::string& title, long long price)
    : title_{title}, price_{price}
{
}
```

Phần sau dấu `:` là *member initializer list*. `title_` được copy từ parameter `title`; `price_` được khởi tạo từ `price`. Member được khởi tạo trước khi thân constructor chạy. Việc này bảo đảm hai member đã được khởi tạo đầy đủ, nhưng không tự chứng minh giá trị đáp ứng quy tắc nghiệp vụ; precondition nêu ở phần bài toán vẫn thuộc trách nhiệm caller trong phiên bản hiện tại.

Viết initializer list khác với tạo member trước rồi gán trong thân. Với reference member, `const` member và nhiều object member, khởi tạo trực tiếp còn là bắt buộc. Vì vậy đây là cách viết mặc định nên dùng.

### 4.2. Automatic storage và mô hình stack thường gặp

```cpp
Book stack_book{"Clean Code", 320000};
```

`stack_book` có automatic storage duration. Triển khai thông thường dành chỗ cho nó trong stack frame của `main`, rồi gọi constructor trên vùng đó; chuẩn C++ chỉ quy định lifetime/scope, không bắt buộc vị trí vật lý và compiler có thể tối ưu representation.

```text
stack frame main (mô hình triển khai phổ biến)
└── stack_book: Book object
    ├── title_: std::string object
    └── price_: 320000
```

Khi rời block của `main`, destructor `~Book()` chạy tự động. Sau destructor, lifetime object kết thúc và storage tự động của nó được thu hồi; trong mô hình phổ biến, việc này đi cùng lúc stack frame được tháo.

### 4.3. Mỗi `new` tạo một object động riêng

```cpp
Book* heap_book = new Book{"C++ Core Guidelines", 450000};
```

Biểu thức này thực hiện hai việc:

1. gọi allocation function để xin dynamic storage đủ cho một `Book`; triển khai thường lấy vùng này từ free store/heap;
2. gọi constructor để bắt đầu lifetime của một `Book` tại vùng đó.

Kết quả của `new` là địa chỉ object:

```text
automatic storage (thường stack)        dynamic storage (thường heap/free store)
┌────────────────────────────┐           ┌────────────────────────────┐
│ heap_book: Book* ──────────┼──────────>│ Book object #1             │
│                            │           │ title_ = "C++ Core..."     │
│ stack_book: Book object    │           │ price_ = 450000            │
└────────────────────────────┘           └────────────────────────────┘
```

Nếu gọi `new Book{...}` lần nữa, lần gọi đó tạo một object khác trong một vùng lưu trữ khác và trả một địa chỉ khác. Pointer chỉ chứa địa chỉ; pointer không phải object `Book`.

`heap_book->title()` là cú pháp truy cập member qua pointer, tương đương `(*heap_book).title()`.

### 4.4. `delete` kết thúc lifetime object động

```cpp
delete heap_book;
```

`delete` gọi destructor của object rồi trả vùng lưu trữ tương ứng. Sau đó, giá trị địa chỉ cũ không còn trỏ đến object sống:

```text
heap_book --X--> vùng nhớ đã được giải phóng
```

Gán `heap_book = nullptr` không giải phóng thêm gì; nó chỉ xóa địa chỉ dangling khỏi biến pointer. Thứ tự đúng là `delete` trước, gán `nullptr` sau. Nếu chỉ gán `nullptr` mà quên `delete`, chương trình mất địa chỉ và rò rỉ vùng nhớ.

### 4.5. Thứ tự hủy

Object tự động trong cùng scope bị hủy theo thứ tự ngược với lúc xây dựng. Object được cấp phát động không tự bị hủy chỉ vì pointer cục bộ ra khỏi scope; code sở hữu phải `delete`.

Trong class, data member được khởi tạo theo thứ tự khai báo trong class, không theo thứ tự viết ở initializer list; khi object bị hủy, các member bị hủy theo thứ tự ngược lại. Thân `~Book()` chạy trước khi destructor của `title_` chạy.

## 5. Kiến thức nền

### Default constructor và constructor có parameter

Khi class tự khai báo `Book(const std::string&, long long)`, compiler không tự sinh default constructor `Book()`. Vì vậy:

```cpp
// Book book; // không build: thiếu title và price
```

Điều này buộc caller truyền hai argument, nhưng vẫn không thay thế validation nội dung của chúng.

### Destructor

Destructor:

- có tên `~ClassName`;
- không có parameter và không có kiểu trả về;
- được gọi đúng một lần khi lifetime object kết thúc đúng cách;
- dùng để giải phóng tài nguyên do object sở hữu.

`Book` không thật sự cần destructor tự viết vì `std::string` tự quản lý tài nguyên. Destructor ở đây chỉ in log để quan sát. Trong production, nếu không có cleanup riêng, hãy để compiler sinh destructor.

### Storage duration không đồng nhất với “mọi byte nằm ở đâu”

`stack_book` có automatic storage duration; implementation thường biểu diễn object trong stack frame, nhưng standard không yêu cầu điều đó. Member `title_` là một `std::string` subobject; thư viện có thể quản lý thêm buffer ký tự trong dynamic storage. Đây là các lifetime liên quan nhưng không phải một vùng nhớ duy nhất.

### Ownership trong bài này

`heap_book` là *owning raw pointer* theo quy ước tạm thời: `main` có trách nhiệm `delete`. Compiler không ghi lại ownership đó trong kiểu `Book*`, nên rất dễ quên hoặc xóa hai lần.

Mẫu production sẽ ưu tiên:

- object tự động nếu lifetime bám theo scope;
- container để sở hữu nhiều object;
- `std::unique_ptr` cho ownership động duy nhất;
- `std::shared_ptr` chỉ khi thật sự cần sở hữu chung.

Những công cụ này được dạy sau khi nền copy/move và RAII đã rõ.

## 6. Lỗi thường gặp

### Quên `delete`

Pointer ra khỏi scope nhưng object cấp phát động vẫn chiếm tài nguyên. Đây là memory leak. Gán pointer thành `nullptr` không giải phóng object.

### `delete` hai lần

Sau `delete heap_book`, gọi `delete` lại trên cùng địa chỉ cũ gây undefined behavior. Gán `nullptr` giúp `delete nullptr` trở thành no-op, nhưng không biến quản lý thủ công thành thiết kế an toàn.

### Dùng sai cặp cấp phát/giải phóng

- `new T` phải ghép với `delete`;
- `new T[n]` phải ghép với `delete[]`;
- `malloc` phải ghép với `free`.

Không trộn các họ API.

### Dùng object sau khi destructor chạy

Sau `delete`, `heap_book->title()` là use-after-free. Pointer còn giữ địa chỉ không có nghĩa object còn sống.

### Khởi tạo member sai thứ tự

Compiler luôn theo thứ tự khai báo member. Hãy viết initializer list cùng thứ tự đó để code dễ đọc và tránh member sau phụ thuộc nhầm vào member chưa khởi tạo.

### Tự viết destructor chỉ để “cho đủ”

Destructor rỗng có thể cản một số operation được compiler sinh tự động và làm class phức tạp vô ích. Chỉ tự viết khi có hành vi cleanup hoặc mục tiêu quan sát rõ như demo này.

## 7. Bài tập

### Bài 1 — Scope lồng nhau

Tạo hai `Book` tự động trong một block con và dự đoán thứ tự destructor trước khi chạy.

**Gợi ý:** object được hủy ngược thứ tự xây dựng trong cùng scope.

### Bài 2 — Hai lần `new`

Tạo hai `Book` động, vẽ hai vùng dynamic storage và hai pointer, sau đó `delete` đúng từng object.

**Gợi ý:** không ghi đè pointer đầu bằng kết quả `new` thứ hai.

### Bài 3 — Constructor có precondition

Thiết kế class `Temperature` chỉ nhận giá trị không thấp hơn `-273`. Chưa dùng exception; dùng một hàm tạo object theo quy trình kiểm tra bên ngoài.

**Gợi ý:** ở giai đoạn này có thể kiểm tra input trước khi gọi constructor và giữ constructor ở phạm vi phù hợp.

### Bài 4 — Member object

Tạo class `Shelf` có member `Book` và in log để quan sát constructor/destructor của object chứa và object thành phần.

**Gợi ý:** member `Book` phải được khởi tạo trong initializer list của `Shelf`.

### Bài 5 — Tìm lỗi ownership

Viết ba đoạn ngắn minh họa leak, double delete, use-after-free nhưng chỉ phân tích, không chạy chúng. Sau đó viết phiên bản đúng bằng object tự động.

**Gợi ý:** đánh dấu rõ lifetime bắt đầu ở `new` và kết thúc ở `delete`.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] dùng member initializer list;
- [ ] dự đoán đúng thứ tự constructor/destructor;
- [ ] vẽ automatic pointer theo mô hình stack phổ biến trỏ đến dynamic object;
- [ ] nói rõ mỗi `new` tạo một object riêng;
- [ ] giải thích vì sao owning raw pointer chỉ là minh họa ở bài này.

**Bài prerequisite:** [Class, object và encapsulation](./03-class-object-encapsulation.md)

**Bài tiếp theo:** [Copy, move và Rule of Zero/Five](./05-copy-move-rule-of-zero-five.md)
