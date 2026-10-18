# Template và generic programming

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Template mô tả code dùng cho nhiều kiểu; concept ràng buộc điều kiện compile-time.
- Dùng khi nhiều kiểu thật sự chia sẻ cùng thuật toán và semantics.
- Constraint kiểu không tự validate miền runtime; capacity template là một phần kiểu.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- viết function template dùng lại thuật toán cho nhiều kiểu;
- viết class template có type parameter và non-type parameter;
- dùng concept C++20 để biểu đạt constraint;
- đọc lỗi khi một kiểu không thỏa operation template yêu cầu;
- hiểu mỗi specialization là một kiểu hoặc function cụ thể do compiler tạo khi cần.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một khuôn hộp có tham số loại đồ và số ngăn tạo ra các hộp cụ thể khác nhau. Compiler dùng khuôn để kiểm tra code cho từng kiểu; khi chương trình chạy, đó vẫn là các object/hàm có kiểu rõ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| template | khuôn tạo code theo tham số kiểu/giá trị | FixedStack<T, Capacity> |
| specialization | phiên bản cụ thể từ khuôn | FixedStack<int,2> |
| concept | điều kiện kiểu kiểm tra khi compile | Number |
| LIFO | vào sau ra trước | push rồi pop phần tử cuối |
| static_assert | yêu cầu điều kiện compile-time phải đúng | Capacity > 0 |

### Ví dụ nhỏ — tính tay trước

Stack capacity 2: push 4 → [4], push 7 → [4,7], push 9 thất bại giữ size 2; pop trả 7 còn [4]. Hai và ba ngăn là hai specialization khác nhau.

Hệ thống cần hai công cụ:

- chặn một giá trị số trong khoảng min/max, dùng được cho `int`, `long long`, `double`;
- một stack dung lượng cố định, dùng được cho `int` hoặc `std::string`.

Copy/paste một function/class cho từng kiểu làm logic dễ lệch nhau. Ta muốn mô tả thuật toán một lần nhưng vẫn được compiler kiểm tra kiểu, không chuyển mọi dữ liệu thành `void*`.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Trong class template, `static_assert(condition, message)` yêu cầu một điều kiện compile-time phải đúng. `std::array<T, N>` từ `<array>` là wrapper C++ cho dãy cố định gồm `N` phần tử; bài này chỉ cần phép truy cập `[]`, còn cách chọn container sẽ học ở [bài 09](./09-stl-container.md). `std::array<T, 0>` vẫn là một type hợp lệ, nên nếu caller thử tạo `FixedStack<T, 0>`, chính `static_assert` đưa ra diagnostic có chủ đích.

```cpp
#include <array>
#include <concepts>
#include <cstddef>
#include <iostream>
#include <string>
#include <type_traits>

template <typename T>
concept Number = std::is_arithmetic_v<T>;

template <Number T>
T clamp_value(T value, T minimum, T maximum)
{
    if (value < minimum)
    {
        return minimum;
    }

    if (value > maximum)
    {
        return maximum;
    }

    return value;
}

template <typename T, std::size_t Capacity>
class FixedStack
{
public:
    static_assert(Capacity > 0, "Capacity must be positive");

    bool push(const T& value)
    {
        if (size_ == Capacity)
        {
            return false;
        }

        items_[size_] = value;
        ++size_;
        return true;
    }

    bool pop(T& output)
    {
        if (size_ == 0)
        {
            return false;
        }

        // Chỉ commit size mới sau khi copy output thành công.
        output = items_[size_ - 1];
        --size_;
        return true;
    }

    std::size_t size() const
    {
        return size_;
    }

private:
    std::array<T, Capacity> items_{};
    std::size_t size_ = 0;
};

int main()
{
    std::cout << "Clamped stock: "
              << clamp_value(135, 0, 100) << '\n';
    std::cout << "Clamped rate: "
              << clamp_value(0.25, 0.0, 1.0) << '\n';

    FixedStack<std::string, 3> commands;
    commands.push("first");
    commands.push("second");

    std::string popped;
    if (commands.pop(popped))
    {
        std::cout << "Popped: " << popped << '\n';
    }
    std::cout << "Remaining: " << commands.size() << '\n';

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o templates
./templates
```

Kết quả:

```text
Clamped stock: 100
Clamped rate: 0.25
Popped: second
Remaining: 1
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

### Walkthrough — execution / state / cost

1. Compiler suy luận clamp<int> và clamp<double>; runtime lần lượt trả 100 và 0.25.
2. FixedStack<string,3> giữ ba string member đã được dựng, size ban đầu 0.
3. Push first/second đổi size 0→1→2; pop copy second ra output rồi giảm size còn 1.
4. Buffer phần tử là member, không cấp phát riêng bởi FixedStack; từng string vẫn có thể cấp storage. Push/pop không duyệt stack nhưng cost phụ thuộc phép gán T; storage theo Capacity.

### Mini-check

Khi gán output trong pop ném lỗi, size_ đã giảm chưa? Điều đó có bảo đảm output của caller cũng giữ nguyên với mọi T không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Function template

```cpp
template <Number T>
T clamp_value(T value, T minimum, T maximum)
```

`T` là type parameter. Khi gọi:

```cpp
clamp_value(135, 0, 100)
```

compiler suy luận `T` là `int`. Với `0.25, 0.0, 1.0`, `T` là `double`. Về mặt mô hình:

```text
template clamp_value<T>
├── dùng với T = int    -> clamp_value<int>
└── dùng với T = double -> clamp_value<double>
```

Compiler kiểm tra phép `<` và `>` trên kiểu cụ thể khi tạo specialization cần dùng.

### 4.2. Concept biểu đạt tập kiểu hợp lệ

```cpp
template <typename T>
concept Number = std::is_arithmetic_v<T>;
```

`concept` là một điều kiện compile-time. `std::is_arithmetic_v<T>` từ `<type_traits>` đúng với các kiểu số học built-in như integer và floating-point.

`template <Number T>` yêu cầu `T` thỏa `Number`. Vì vậy lời gọi với `std::string` bị từ chối tại compile time với diagnostic về constraint, thay vì đi sâu vào lỗi toán tử khó đọc.

Concept không tự kiểm tra quy tắc nghiệp vụ như `minimum <= maximum`; đó vẫn là trách nhiệm contract/function.

### 4.3. Class template và capacity compile-time

```cpp
template <typename T, std::size_t Capacity>
class FixedStack
```

có hai parameter:

- `T`: kiểu phần tử;
- `Capacity`: một giá trị `std::size_t` biết ở compile time.

`FixedStack<std::string, 3>` là một kiểu cụ thể, khác với `FixedStack<std::string, 5>` và `FixedStack<int, 3>`.

Member lưu phần tử:

```cpp
std::array<T, Capacity> items_{};
```

`items_` là một subobject nằm trực tiếp bên trong `FixedStack`; `FixedStack` không gọi `new` để tạo vùng chứa phần tử. Object `commands` có automatic storage duration; triển khai thông thường đặt nó trong stack frame, nhưng chuẩn C++ không bắt buộc vị trí vật lý đó.

```text
commands: FixedStack<string, 3> (automatic object; mô hình thường gặp là stack)
├── items_[0] = "first"
├── items_[1] = "second"
├── items_[2] = ""
└── size_ = 2
```

Mỗi `std::string` member tự quản lý dữ liệu ký tự của nó theo RAII.

### 4.4. LIFO và operation tổng quát

`push` ghi tại `items_[size_]` rồi tăng size. `pop` copy phần tử tại `items_[size_ - 1]` sang output, sau đó mới giảm size, nên đây là Last In, First Out. Nếu phép gán vào output thất bại, `size_` chưa đổi.

Class yêu cầu ngầm rằng `T` có thể default-construct và copy-assign vì `items_{}` và các phép gán. Có thể viết concept chi tiết hơn, nhưng contract hiện tại được giải thích tại chỗ và đủ cho kiểu dùng trong bài. `std::array` không làm thay đổi requirement đó.

### 4.5. Template vẫn type-safe

Không có cast về `void*`. `FixedStack<std::string, 3>::push` chỉ nhận `const std::string&`; compiler từ chối object không chuyển được sang string. Type được giữ đến machine code.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Hàm thường | một kiểu cụ thể | diagnostic đơn giản; đủ nếu không có nhiều kiểu |
| Template | tạo code cho kiểu biết lúc compile | type-safe nhưng tăng compile/code size; hợp thuật toán chung |
| Virtual interface | chọn implementation runtime | hợp tập object đa hình; không thay mọi nhu cầu generic |

### Misconception check

**Đúng hay sai?** Number tự bảo đảm minimum <= maximum.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: đó là precondition giá trị runtime, concept chỉ ràng buộc kiểu.

</details>

**Đúng hay sai?** FixedStack không new nên mọi byte string chắc chắn nằm trong object stack.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: string member có thể sở hữu storage ký tự riêng.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** suy luận specialization và LIFO.

- **Working Developer — dùng khi làm việc:** constraint kiểu, biên và contract T.

- **Deep Dive — có thể quay lại sau:** code bloat và exception behavior của phần tử.

### Type deduction phải thống nhất

Ba argument của `clamp_value` đều dùng cùng `T`. Lời gọi sau có type lẫn lộn:

```cpp
// clamp_value(5, 0.0, 10.0); // int và double, không suy luận được một T
```

Caller có thể truyền cùng kiểu hoặc chỉ rõ:

```cpp
clamp_value<double>(5.0, 0.0, 10.0);
```

Không thêm cast ngẫu nhiên; chọn miền kiểu đúng cho bài toán.

### `typename`

Trong `template <typename T>`, `typename` nói parameter là một kiểu. Ở vị trí này có thể dùng `class T`; hai cách có cùng ý nghĩa.

### Template declaration và definition

Compiler phải thấy definition template tại nơi instantiate. Vì vậy template thường được định nghĩa hoàn chỉnh trong header, khác với function/class thường có thể tách declaration ở `.h` và definition ở `.cpp`.

### Specialization

C++ cho phép tùy biến template cho một tập type cụ thể qua specialization hoặc overload có constraint. Chưa cần dùng ở bài đầu; ưu tiên một contract chung rõ ràng. Khi hành vi khác hẳn, có thể đó là dấu hiệu cần type/abstraction khác.

### Đào sâu (có thể quay lại sau)

Mỗi specialization được dùng có thể sinh machine code riêng, tạo cơ hội tối ưu mạnh nhưng cũng có thể làm tăng kích thước binary (*code bloat*). Linker có thể gộp một số definition trùng; kết quả phụ thuộc toolchain.

Template error từng nổi tiếng dài vì compiler báo chuỗi instantiation. Concepts cải thiện điểm báo lỗi bằng cách kiểm tra yêu cầu sớm hơn. Với generic library lớn, có thể viết constraint từ các concept chuẩn như `std::integral`, `std::copyable`, `std::totally_ordered` hoặc bằng `requires` expression.

Đây là compile-time polymorphism, khác virtual dispatch ở bài 06:

```text
template: chọn/instantiate tại compile time
virtual:  chọn override theo dynamic type tại runtime
```

Không có loại nào luôn tốt hơn; chọn theo nhu cầu extension, binary boundary, hiệu năng và độ phức tạp.

## 6. Lỗi thường gặp

### Template quá tổng quát nhưng không nói requirement

Nếu code dùng `<`, type phải hỗ trợ so sánh phù hợp. Dùng concept hoặc ghi contract rõ, đừng chờ lỗi sâu trong implementation.

### Trộn type khiến deduction thất bại

`clamp_value(5, 0.0, 10.0)` không có một `T` duy nhất. Chuẩn hóa input về kiểu đúng.

### Đặt definition template chỉ trong `.cpp`

Translation unit khác nhìn thấy declaration nhưng không thấy definition khi instantiate, thường dẫn đến lỗi link. Template thường đặt trong header.

### Capacity bằng `0`

`std::array<T, 0>` hợp lệ, nhưng một stack nghiệp vụ có capacity `0` không hữu ích trong contract hiện tại. `static_assert` của `FixedStack` chủ động từ chối specialization đó với message rõ ràng.

### Cho rằng template tự làm code đúng

Template loại bỏ copy/paste theo type, không tự sửa invariant, kiểm tra biên hay thuật toán sai.

### Dùng template khi một function thường đã đủ

Generic code làm interface và diagnostic phức tạp hơn. Chỉ tổng quát hóa khi thật sự có nhiều type hợp lệ với cùng semantics.

## 7. Khi nào KHÔNG dùng

Không tổng quát hóa một hàm duy nhất cho loại dữ liệu không có semantics chung. Không thêm perfect forwarding/concept dài vào stack đầu tiên khi requirement default construction và copy assignment đã đủ và được ghi rõ.

## 8. Production notes & scale check

Test capacity 0 phải bị compiler từ chối, đầy/rỗng không đổi state, và kiểu không số không gọi clamp được. Number gồm cả float/bool; production phải quy định NaN và miền min/max nếu dùng. pop chỉ giữ size khi assignment lỗi, không tự hứa strong guarantee cho output T tùy ý.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — `minimum_of`

Viết function template trả giá trị nhỏ hơn trong hai giá trị cùng kiểu số.

**Gợi ý:** tái sử dụng concept `Number`.

### Bài 2 — Chặn capacity 0

Đổi message của `static_assert` hiện có, thử instantiate `FixedStack<int, 0>` và đọc diagnostic đầu tiên.

**Gợi ý:** assertion được kiểm tra khi compiler instantiate class.

### Bài 3 — Stack số nguyên

Tạo `FixedStack<int, 2>`, thử push ba lần và xử lý kết quả `false`.

**Gợi ý:** không đọc phần tử nếu `pop` thất bại.

### Bài 4 — Query `top`

Thiết kế operation đọc phần tử trên cùng mà không xóa, nhưng phải biểu đạt được stack rỗng.

**Gợi ý:** ở mức hiện tại có thể dùng `bool top(T& output) const`.

### Bài 5 — Constraint rõ hơn

Tìm các concept chuẩn cần thiết cho `FixedStack` hiện tại và thử thêm constraint.

**Gợi ý:** xem `std::default_initializable` và `std::assignable_from`; đây là bài đào sâu.

## 10. Bài tập tích hợp liên module — Judgment

So với pointer + count C Module 02, FixedStack<int,2> chuyển điều kiện nào sang compile-time, điều kiện nào vẫn runtime? Chọn mảng cố định/template khi biết trần nhỏ và giải thích chi phí tổng quát hóa.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Capacity 2 và 3 có cùng kiểu không?
2. T cần operation gì trong implementation hiện tại?
3. Pop có hủy ngay string ở slot vừa bỏ không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] viết function template có type parameter;
- [ ] giải thích concept kiểm tra constraint ở compile time;
- [ ] phân biệt type parameter và non-type parameter;
- [ ] chỉ ra các specialization là kiểu/function cụ thể;
- [ ] nói rõ requirement mà `FixedStack` đặt lên `T`.

**Bài prerequisite:** [Abstract class và interface trong C++](./07-abstract-class-va-interface-trong-cpp.md)

**Bài tiếp theo:** [STL container](./09-stl-container.md)
