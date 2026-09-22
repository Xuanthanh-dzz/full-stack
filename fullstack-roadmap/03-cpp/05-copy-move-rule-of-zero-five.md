# Copy, move và Rule of Zero/Five

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Copy tạo state độc lập; move có thể chuyển tài nguyên; Rule of Zero giao cleanup cho member đã an toàn.
- Dùng member string/vector trước khi tự quản lý raw resource.
- std::move chỉ cho phép chọn move; copy pointer sở hữu mặc định dễ double delete.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt copy object với move tài nguyên;
- nhận ra shallow copy nguy hiểm ở class sở hữu raw pointer;
- triển khai nền tảng năm special member function khi thật sự phải quản lý tài nguyên thủ công;
- hiểu Rule of Zero và ưu tiên kiểu thành phần tự quản lý tài nguyên;
- biết trạng thái tối thiểu được bảo đảm của object sau move.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Copy một kho hàng có thể nghĩa là tạo kho mới với hàng riêng; move giống bàn giao chìa khóa kho cũ. Sao chép mỗi địa chỉ rồi để cả hai cùng tự phá kho là sai ownership, dù hai object trông độc lập.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| deep copy | tạo dữ liệu sở hữu riêng | IntBuffer copy cấp mảng mới |
| move | chuyển state/tài nguyên theo contract kiểu | IntBuffer chuyển pointer |
| special member | operation tạo/copy/move/gán/hủy đặc biệt | năm operation cần xem xét |
| Rule of Zero | dùng member tự quản lý để không tự viết special member | Report chứa string |
| noexcept | cam kết operation không để exception thoát | move số/pointer |

### Ví dụ nhỏ — tính tay trước

A sở hữu [10,20]. Copy B → mảng khác; B[0]=99 không đổi A. Move B sang C → C giữ mảng B cũ, B có size 0 theo contract IntBuffer này.

Một buffer số nguyên cấp phát động được dùng để xử lý dữ liệu. Nếu để compiler copy từng data member:

```text
buffer_a.data_ ──┐
                 ├──> cùng một mảng cấp phát động
buffer_b.data_ ──┘
```

hai object sẽ tưởng mình cùng sở hữu một mảng. Khi cả hai destructor gọi `delete[]`, chương trình double free.

Ta cần:

- copy tạo một mảng dynamic storage độc lập;
- move chuyển ownership mà không copy từng phần tử;
- assignment không rò rỉ tài nguyên đang sở hữu;
- object nguồn sau move vẫn có thể bị hủy an toàn;
- đồng thời biết vì sao code production nên tránh tự viết toàn bộ cơ chế này.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

`IntBuffer` dưới đây cố ý dùng `new[]`/`delete[]` để học copy/move. Khi học [STL ở bài 09](./09-stl-container.md), `std::vector<int>` sẽ là lựa chọn production thông thường.

```cpp
#include <cstddef>
#include <iostream>
#include <string>
#include <utility>

struct Report
{
    std::string title;
    std::string body;
};

class IntBuffer
{
public:
    explicit IntBuffer(std::size_t size)
        : size_{size},
          data_{size == 0 ? nullptr : new int[size]{}}
    {
    }

    ~IntBuffer()
    {
        delete[] data_;
    }

    IntBuffer(const IntBuffer& other)
        : size_{other.size_},
          data_{other.size_ == 0 ? nullptr : new int[other.size_]}
    {
        for (std::size_t index = 0; index < size_; ++index)
        {
            data_[index] = other.data_[index];
        }
    }

    IntBuffer& operator=(const IntBuffer& other)
    {
        if (this == &other)
        {
            return *this;
        }

        int* new_data = other.size_ == 0 ? nullptr : new int[other.size_];
        for (std::size_t index = 0; index < other.size_; ++index)
        {
            new_data[index] = other.data_[index];
        }

        delete[] data_;
        data_ = new_data;
        size_ = other.size_;
        return *this;
    }

    IntBuffer(IntBuffer&& other) noexcept
        : size_{other.size_}, data_{other.data_}
    {
        other.size_ = 0;
        other.data_ = nullptr;
    }

    IntBuffer& operator=(IntBuffer&& other) noexcept
    {
        if (this == &other)
        {
            return *this;
        }

        delete[] data_;
        size_ = other.size_;
        data_ = other.data_;
        other.size_ = 0;
        other.data_ = nullptr;
        return *this;
    }

    std::size_t size() const
    {
        return size_;
    }

    int& at(std::size_t index)
    {
        return data_[index];
    }

    const int& at(std::size_t index) const
    {
        return data_[index];
    }

private:
    std::size_t size_ = 0;
    int* data_ = nullptr;
};

int main()
{
    Report first_report{"Daily sales", "Stable"};
    Report second_report = first_report; // Rule of Zero: member tự copy đúng.
    second_report.body = "Updated";

    std::cout << "First report: " << first_report.body << '\n';
    std::cout << "Second report: " << second_report.body << '\n';

    IntBuffer original{2};
    original.at(0) = 10;
    original.at(1) = 20;

    IntBuffer copied = original;
    copied.at(0) = 99;

    std::cout << "Original[0]: " << original.at(0) << '\n';
    std::cout << "Copied[0]: " << copied.at(0) << '\n';

    IntBuffer moved = std::move(copied);
    std::cout << "Moved[1]: " << moved.at(1) << '\n';
    std::cout << "Copied size after move: " << copied.size() << '\n';

    IntBuffer assigned{1};
    assigned = original;
    std::cout << "Assigned[0]: " << assigned.at(0) << '\n';

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o copy_move
./copy_move
```

Kết quả:

```text
First report: Stable
Second report: Updated
Original[0]: 10
Copied[0]: 99
Moved[1]: 20
Copied size after move: 0
Assigned[0]: 10
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

### Walkthrough — execution / state / cost

1. Report copy hai string theo value; sửa second_report không đổi first_report.
2. IntBuffer original cấp hai int; copied cấp mảng riêng rồi chép từng int.
3. Move constructor chuyển địa chỉ sang moved và đặt copied về {0,nullptr}; không copy từng phần tử.
4. Copy assignment tạo dữ liệu mới trước rồi thay owner cũ. Deep copy O(n)/O(n) memory, move constructor của IntBuffer O(1); destructor giải phóng allocation đúng một lần.

### Mini-check

Copy assignment new thất bại trước delete[] cũ: destination có bị mất dữ liệu không? Vì sao thứ tự là quan trọng?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Rule of Zero

`Report` chỉ chứa `std::string`. Mỗi string đã biết cách copy, move và tự hủy đúng. Vì vậy `Report` không khai báo destructor, copy constructor, copy assignment, move constructor hay move assignment.

```text
first_report.body  ──> dữ liệu "Stable"
second_report.body ──> bản sao riêng, sau đó đổi thành "Updated"
```

Đây là **Rule of Zero**: thiết kế class từ những member tự quản lý tài nguyên để không phải tự viết special member function. Đây là lựa chọn production ưu tiên.

### 4.2. Vì sao `IntBuffer` cần deep copy?

Mỗi constructor `IntBuffer{2}` thực hiện đúng một `new int[2]` và tạo một mảng dynamic riêng. Sơ đồ đặt automatic object ở stack và allocation ở heap theo triển khai phổ biến; chuẩn C++ quy định storage duration/lifetime, không bắt buộc hai vị trí vật lý đó:

```text
automatic storage (thường stack)   dynamic storage (thường heap)
original
├── size_ = 2
└── data_ ────────────────────────> [10][20]  mảng A
```

Copy constructor cấp phát mảng B rồi copy từng phần tử:

```text
automatic storage (thường stack)   dynamic storage (thường heap)
original.data_ ───────────────────> [10][20]  mảng A
copied.data_   ───────────────────> [10][20]  mảng B
```

Vì hai pointer trỏ đến hai allocation, sửa `copied.at(0)` không đổi `original`.

### 4.3. Copy constructor và copy assignment

Copy constructor chạy khi tạo object mới từ lvalue cùng kiểu:

```cpp
IntBuffer copied = original;
```

Copy assignment chạy khi object đích đã tồn tại:

```cpp
assigned = original;
```

Assignment phải xử lý hai tài nguyên: tài nguyên cũ của `assigned` và bản sao mới. Code cấp phát/copy vào `new_data` trước. Nếu `new` thất bại, object cũ chưa bị thay đổi. Chỉ sau khi bản sao sẵn sàng, code `delete[]` dữ liệu cũ và nhận pointer mới.

Kiểm tra `this == &other` xử lý self-assignment như `buffer = buffer`.

### 4.4. Move chuyển ownership

```cpp
IntBuffer moved = std::move(copied);
```

`std::move` không tự chuyển byte hay tài nguyên. Nó chuyển biểu thức sang dạng cho phép chọn move constructor. Move constructor của `IntBuffer` mới là code:

1. copy `size_` và địa chỉ `data_` sang object đích;
2. đặt nguồn về `{0, nullptr}`.

```text
trước move
copied.data_ ───────────────> mảng B

sau move
moved.data_  ───────────────> mảng B
copied.data_ = nullptr
```

Không có allocation mới và không copy từng `int`. Destructor của `copied` gọi `delete[] nullptr`, việc này hợp lệ.

Object sau move phải còn **hợp lệ nhưng trạng thái có thể không được chỉ rõ** đối với nhiều kiểu thư viện. Chỉ hủy hoặc gán giá trị mới, trừ khi contract của kiểu nói rõ operation nào khác dùng được. Riêng `IntBuffer` do ta viết quy định nguồn có `size() == 0`.

### 4.5. Rule of Five

Nếu class trực tiếp sở hữu tài nguyên và phải tự viết destructor, thường cần xem xét cả năm operation:

1. destructor;
2. copy constructor;
3. copy assignment;
4. move constructor;
5. move assignment.

Không có nghĩa luôn phải bật cả copy lẫn move. Một resource có thể chỉ cho move và chủ động `delete` copy operation. Điều quan trọng là quyết định ownership rõ ràng, không để compiler shallow-copy raw owning pointer.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Copy member RAII | member quyết định copy hợp lệ | ít code, ưu tiên Rule of Zero |
| Copy raw owner mặc định | copy cùng địa chỉ | rẻ nhưng sai khi cả hai delete; cấm hoặc viết deep copy |
| Move owner | chuyển quyền theo contract | có thể rẻ; không giả định mọi kiểu luôn zero-copy |

### Misconception check

**Đúng hay sai?** std::move tự gọi free và chép byte.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: nó là cast; move operation được chọn mới làm việc.

</details>

**Đúng hay sai?** Mọi kiểu sau move đều rỗng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: IntBuffer quy định rỗng; nhiều kiểu thư viện chỉ hứa trạng thái hợp lệ nhưng không chỉ rõ giá trị.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** phân biệt copy/move với sơ đồ owner.

- **Working Developer — dùng khi làm việc:** test assignment và trạng thái nguồn.

- **Deep Dive — có thể quay lại sau:** exception guarantee và noexcept của container.

### Lvalue và rvalue ở mức cần thiết

- `original` là lvalue: một object có identity và tên ổn định.
- temporary như `IntBuffer{2}` là rvalue.
- `std::move(original)` cho phép coi expression là nguồn có thể chuyển tài nguyên.

[Bài 13](./13-move-semantics-va-perfect-forwarding.md) sẽ đào sâu value category, forwarding reference và `std::forward`. Ở đây chỉ dùng `std::move` khi caller chấp nhận không dựa vào giá trị cũ của source.

### `explicit`

Constructor một parameter:

```cpp
explicit IntBuffer(std::size_t size)
```

được đánh dấu `explicit` để ngăn chuyển đổi ngầm từ số sang `IntBuffer`. Caller phải viết rõ `IntBuffer{2}`.

### `noexcept` ở move operation

Move constructor/assignment chỉ chuyển số và pointer nên không ném exception; code khai báo `noexcept`. Đây vừa là contract vừa giúp container thư viện có thể chọn move an toàn khi tái bố trí phần tử.

### Overload `at` theo constness

Object thường nhận `int&` để có thể sửa phần tử. Object `const` nhận `const int&` để chỉ đọc. Hai member function có cùng tên nhưng khác `const` phía sau.

Ví dụ này giả định `index < size_`. API production phải kiểm tra biên hoặc dùng container chuẩn có operation phù hợp.

### Đào sâu (có thể quay lại sau)

Compiler có thể bỏ hẳn một số copy/move qua *copy elision*, đặc biệt khi trả object theo giá trị. Vì constructor không xuất hiện trong log không đồng nghĩa semantics trả-by-value sai.

`noexcept` quan trọng với strong exception guarantee của container: khi tái cấp phát, một container như `std::vector` có thể ưu tiên copy thay vì một move có khả năng ném nếu copy vẫn khả dụng. Đây là lý do move operation chỉ nên đánh dấu `noexcept` khi nó thực sự không ném.

Các special member function còn tương tác với quy tắc compiler tự sinh hoặc xóa operation. Thay vì ghi nhớ ma trận chi tiết ngay lần đầu, hãy giữ quyết định thiết kế:

- Rule of Zero nếu có thể;
- nếu sở hữu resource cấp thấp, khai báo rõ toàn bộ semantics;
- dùng `= delete` cho operation phải cấm;
- viết test copy, move, self-assignment và cleanup.

## 6. Lỗi thường gặp

### Shallow-copy owning pointer

Copy mặc định chỉ copy địa chỉ `data_`, dẫn đến hai owner và double delete. Phải deep-copy, cấm copy, hoặc tốt nhất dùng member RAII.

### Quên giải phóng tài nguyên cũ trong move assignment

Object đích đã có thể sở hữu một mảng. Nếu ghi đè `data_` ngay, mảng cũ bị leak.

### Dùng source như chưa từng move

Sau `std::move`, đừng giả định dữ liệu cũ còn nguyên. Chỉ dùng operation được contract bảo đảm, gán lại hoặc hủy.

### Viết `std::move` trên object `const`

Move thường cần sửa source để chuyển ownership. `const T` không cho sửa, nên nhiều trường hợp `std::move(const_object)` vẫn chọn copy. Đừng thêm `std::move` máy móc.

### Tự quản lý mảng khi container đã giải quyết

`IntBuffer` là bài học cơ chế. Production nên ưu tiên `std::vector<int>` sau khi học [bài 09](./09-stl-container.md): Rule of Zero, kiểm soát kích thước và exception safety tốt hơn.

### Đọc ngoài biên

`at` tự viết chưa kiểm tra `index`. Gọi với index sai gây undefined behavior. Đừng sao chép API tối giản này vào production.

## 7. Khi nào KHÔNG dùng

Không viết Rule of Five cho class chỉ chứa string/int. Không dùng IntBuffer::at mẫu như API production có kiểm tra biên: nó có precondition index < size dù tên giống at của thư viện.

## 8. Production notes & scale check

Buffer hai int chỉ để nhìn ownership. Test copy độc lập, copy/move assignment, self-assignment, size 0, dùng lại source sau gán mới và sanitizer cleanup. Khi cần dãy thực tế, vector giảm bề mặt lỗi; chỉ giữ raw resource wrapper khi API cấp thấp bắt buộc.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Theo dõi allocation

Thêm log vào năm special member function và dự đoán operation nào chạy ở từng dòng `main`.

**Gợi ý:** phân biệt “tạo object mới” với “gán vào object đã tồn tại”.

### Bài 2 — Move assignment

Thêm một object rồi thực hiện `destination = std::move(moved)`. In `size()` hai bên.

**Gợi ý:** object đích phải giải phóng mảng cũ trước khi nhận mảng mới.

### Bài 3 — Cấm copy

Thiết kế `UniqueBuffer` chỉ cho move bằng cách dùng `= delete` cho copy constructor và copy assignment.

**Gợi ý:** declaration có dạng `UniqueBuffer(const UniqueBuffer&) = delete;`.

### Bài 4 — Thực hành Rule of Zero

Tạo class `CustomerProfile` gồm hai `std::string` và một `int`, không khai báo special member function. Copy một object, sửa bản copy rồi chứng minh object gốc không đổi.

**Gợi ý:** các member đã tự quản lý copy, move và destructor; class của bạn không cần raw owning pointer.

### Bài 5 — Kiểm tra self-assignment

Chạy `original = original` và `original = std::move(original)`, xác nhận object vẫn hợp lệ.

**Gợi ý:** hai nhánh `this == &other` đang bảo vệ trường hợp này.

## 10. Bài tập tích hợp liên module — Judgment

Đối chiếu struct Product chứa char* Module 02: copy mặc định thiếu trách nhiệm nào? Chọn cấm copy, deep copy hay member tự sở hữu theo nhu cầu kho; giải thích cost của lựa chọn.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ allocation trước/sau copy và move.
2. Constructor khác assignment về tài nguyên cũ thế nào?
3. Khi nào Rule of Zero tốt hơn tự viết đủ năm hàm?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] vẽ deep copy với hai allocation riêng;
- [ ] phân biệt copy/move constructor với assignment;
- [ ] giải thích `std::move` không tự di chuyển tài nguyên;
- [ ] nêu năm special member function cần xem xét;
- [ ] ưu tiên Rule of Zero cho code production.

**Bài prerequisite:** [Constructor, destructor và bộ nhớ](./04-constructor-destructor-va-bo-nho.md)

**Bài tiếp theo:** [Kế thừa và đa hình](./06-ke-thua-va-da-hinh.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/01-copy-raw-owner.md) · [Review](./reviews/review-01.md).
