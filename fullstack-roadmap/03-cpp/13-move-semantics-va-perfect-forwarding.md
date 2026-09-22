# Move semantics và perfect forwarding

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- std::move cho phép chọn move; std::forward giữ category của đối số được suy luận.
- Dùng forwarding ở wrapper generic có trách nhiệm thực, không cho mọi API.
- Tên parameter là lvalue expression dù kiểu khai báo có &&; forward sai có thể lấy state caller còn cần.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt lvalue, prvalue và xvalue ở mức dùng API;
- giải thích chính xác `std::move` là một cast cho phép move;
- viết overload nhận `const T&` và `T&&`;
- dùng forwarding reference cùng `std::forward`;
- tránh move từ `const`, move quá sớm và wrapper forwarding vô ích.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một quầy trung gian nhận đồ gửi tới nơi khác: nếu khách chỉ cho mượn, quầy phải giữ cách mượn; nếu khách bàn giao, quầy mới chuyển quyền. Luôn move giống tự ý nhận quyền sở hữu, còn không forward có thể copy dù được phép chuyển.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| lvalue | biểu thức chỉ object có identity theo cách không đánh dấu chuyển tài nguyên | draft |
| prvalue | biểu thức tạo giá trị dùng để khởi tạo object | string temporary |
| xvalue | biểu thức chỉ object có thể dùng làm nguồn move | std::move(draft) |
| forwarding reference | tham số T&& với T được suy luận phù hợp | Args&&... |
| parameter pack | nhóm không hoặc nhiều tham số template | Args... |

### Ví dụ nhỏ — tính tay trước

create_message(draft) suy luận reference lvalue → copy text, draft giữ nguyên. create_message(string{"B"}) chuyển tiếp rvalue → constructor nhận &&. Trong constructor, tên text vẫn cần std::move để member có thể move.

Một factory tạo `Message` từ text:

- nếu caller truyền một `std::string` có tên và còn cần dùng, factory phải copy;
- nếu caller truyền temporary, factory nên move buffer;
- wrapper phải giữ nguyên “lvalue hay rvalue” của argument khi chuyển tiếp vào constructor.

Nếu wrapper luôn truyền parameter bằng tên, mọi parameter trở thành lvalue expression và overload rvalue không được chọn. Nếu wrapper luôn `std::move`, nó có thể lấy mất dữ liệu mà caller còn cần.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

`typename... Args` khai báo một *type parameter pack*: zero hoặc nhiều type được suy luận từ lời gọi. `Args&&... args` là nhóm parameter tương ứng; `std::forward<Args>(args)...` áp dụng forwarding cho từng phần tử của nhóm. Mẫu dùng pack vì constructor đích có thể có nhiều argument, nhưng kịch bản hiện tại truyền đúng một chuỗi mỗi lần.

```cpp
#include <iostream>
#include <memory>
#include <string>
#include <utility>

class Message
{
public:
    explicit Message(const std::string& text)
        : text_{text}
    {
        std::cout << "Constructed from lvalue: copied text\n";
    }

    explicit Message(std::string&& text)
        : text_{std::move(text)}
    {
        std::cout << "Constructed from rvalue: moved text\n";
    }

    const std::string& text() const
    {
        return text_;
    }

private:
    std::string text_;
};

template <typename... Args>
std::unique_ptr<Message> create_message(Args&&... args)
{
    // Giữ nguyên value category của từng argument khi chuyển đến constructor.
    return std::make_unique<Message>(std::forward<Args>(args)...);
}

int main()
{
    std::string draft = "Review pull request";

    const std::unique_ptr<Message> first = create_message(draft);
    const std::unique_ptr<Message> second =
        create_message(std::string{"Deploy release"});

    std::cout << "Draft remains: " << draft << '\n';
    std::cout << "First: " << first->text() << '\n';
    std::cout << "Second: " << second->text() << '\n';

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o forwarding
./forwarding
```

Kết quả:

```text
Constructed from lvalue: copied text
Constructed from rvalue: moved text
Draft remains: Review pull request
First: Review pull request
Second: Deploy release
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

Factory mỏng này được viết để nhìn thấy perfect forwarding. Production không cần bọc `make_unique` nếu wrapper không thêm validation, policy hoặc abstraction có giá trị.

### Walkthrough — execution / state / cost

1. draft sống trong main; wrapper nhận reference với category suy luận từ caller.
2. forward của lời gọi đầu giữ lvalue nên Message copy text.
3. Lời gọi thứ hai giữ rvalue, Message move vào string member; temporary nguồn kết thúc đúng vòng đời.
4. Hai unique_ptr sở hữu hai Message. Copy string có cost theo độ dài; move không phải cam kết mọi implementation zero-copy, đặc biệt chuỗi ngắn. Wrapper template thêm công compile, không tự thêm runtime thread.

### Mini-check

Thay std::forward<Args>(args)... bằng args... chọn overload nào khi caller truyền temporary? Vì sao?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Value category trả lời expression có thể dùng như nguồn move không

Ở mức thực hành:

- **lvalue:** expression có identity ổn định, thường có tên; `draft` là lvalue;
- **prvalue:** giá trị tạm được tạo bởi expression như `std::string{"Deploy release"}`;
- **xvalue:** object có identity nhưng được đánh dấu có thể lấy tài nguyên, thường từ `std::move(draft)`.

Rvalue gồm prvalue và xvalue. Overload `std::string&&` nhận rvalue; overload `const std::string&` nhận lvalue và cũng có thể nhận rvalue nếu không có overload tốt hơn.

### 4.2. Tên của parameter luôn là lvalue expression

Trong:

```cpp
template <typename... Args>
std::unique_ptr<Message> create_message(Args&&... args)
```

dù type của `args` có thể chứa `&&`, mỗi tên `args` xuất hiện trong thân function là lvalue expression. Nếu viết:

```cpp
// std::make_unique<Message>(args...);
```

constructor `const std::string&` sẽ được chọn cả khi caller truyền temporary.

### 4.3. Forwarding reference và reference collapsing

`Args&&` là forwarding reference vì `Args` được compiler suy luận ở chính lời gọi.

Với `draft`:

```text
argument là lvalue std::string
Args suy luận thành std::string&
Args&& = std::string& && -> collapse thành std::string&
```

Với temporary:

```text
argument là rvalue std::string
Args suy luận thành std::string
Args&& = std::string&&
```

Quy tắc rút gọn cần nhớ:

```text
&  + &  -> &
&  + && -> &
&& + &  -> &
&& + && -> &&
```

Chỉ khi cả hai phía là `&&`, kết quả mới là rvalue reference.

### 4.4. `std::forward` phục hồi category ban đầu

```cpp
std::forward<Args>(args)
```

trả:

- lvalue nếu `Args` đã suy luận là lvalue reference;
- rvalue nếu `Args` là non-reference type.

Vì vậy lời gọi đầu chọn constructor copy, lời gọi thứ hai chọn constructor move. Đây là *perfect forwarding*: wrapper giữ category và cv-qualification phù hợp của argument thay vì ép mọi thứ về một phía.

Mỗi parameter chỉ nên forward một lần đến nơi nhận ownership. Dùng lại sau khi forward rvalue có thể quan sát moved-from state.

### 4.5. `std::move` không tự move

Trong constructor:

```cpp
text_{std::move(text)}
```

`text` là tên parameter nên là lvalue expression. `std::move(text)` cast nó thành xvalue; constructor move của member `std::string` mới thực hiện chuyển resource nếu implementation chọn.

Nếu type không có move operation phù hợp, expression sau `std::move` vẫn có thể dẫn đến copy. Tên “move” mô tả ý định/cast, không phải lệnh runtime bảo đảm zero-copy.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| const T& | mượn đọc | rõ, đủ khi không nhận ownership |
| T theo value rồi move | nhận một bản riêng để sở hữu | API đơn giản, có thể thêm move; hợp kiểu cụ thể |
| T&& suy luận + forward | giữ category qua wrapper generic | phức tạp deduction/overload; chỉ dùng khi wrapper cần tổng quát |

### Misconception check

**Đúng hay sai?** Mọi T&& đều là forwarding reference.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phụ thuộc T có được suy luận ở lời gọi và không gắn const sẵn hay không.

</details>

**Đúng hay sai?** std::move trên const string chắc chắn chọn move constructor.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: thường không phù hợp move cần sửa nguồn, nên có thể chọn copy.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** phân biệt move cast và operation.

- **Working Developer — dùng khi làm việc:** trace deduction/collapsing/forward.

- **Deep Dive — có thể quay lại sau:** overload constraints và codegen khi có driver.

### Khi nào nhận by value?

Nếu function chắc chắn cần sở hữu một bản `T`, một API đơn giản thường là:

```cpp
void set_text(std::string text)
{
    text_ = std::move(text);
}
```

- caller lvalue: copy vào parameter, rồi move vào member;
- caller rvalue: move/elide vào parameter, rồi move vào member.

Cách này dễ đọc nhưng có thể thêm một move và không phù hợp mọi type/workload. Chỉ tạo overload `const T&`/`T&&` khi đo đạc hoặc API semantics biện minh độ phức tạp.

### Move từ `const`

Move constructor thường cần sửa source để đặt nó vào state hợp lệ. `const T&&` không cho sửa source, nên thường không bind vào `T(T&&)` và cuối cùng copy qua `const T&`.

Đừng viết `const` cho object mà bạn thật sự định chuyển ownership, và đừng dùng `std::move` để “tối ưu” một object `const`.

### Moved-from state

Sau move, object chuẩn thường hợp lệ nhưng giá trị không được chỉ rõ, trừ contract cụ thể. Có thể:

- hủy;
- gán giá trị mới;
- gọi operation được contract nói rõ.

Không kiểm tra `source.empty()` rồi biến hành vi quan sát được đó thành giả định chung cho mọi type.

### Return by value

Trả object theo value là cách viết chuẩn. Compiler có copy elision và move để tránh bản sao không cần thiết. Không trả reference đến local và không mặc định bọc mọi kết quả bằng smart pointer.

### Đào sâu (có thể quay lại sau)

`std::forward<T>` về bản chất là conditional cast dựa trên `T`. Dùng sai `T` có thể ép lvalue thành rvalue, nên chỉ dùng đúng type parameter được suy luận cho forwarding reference tương ứng.

Không phải mọi `T&&` là forwarding reference:

- `Widget&&` là rvalue reference cụ thể;
- `const T&&` không phải forwarding reference;
- `T&&` trong class template mà `T` đã được xác định ở cấp class không tự forwarding;
- `auto&&` thường có quy tắc suy luận tương tự forwarding reference, trừ một số trường hợp đặc biệt.

Braced initializer như `{1, 2, 3}` không có type theo cách argument thông thường, nên generic forwarding wrapper có thể không suy luận được `Args`. API có `std::initializer_list` cần overload rõ.

Forwarding constructor quá tổng quát có thể “nuốt” copy constructor hoặc overload khác. Dùng constraint và ưu tiên API cụ thể trước khi thêm `template <typename T> Class(T&&)`.

## 6. Lỗi thường gặp

### Luôn `std::move` argument trong wrapper

Nó biến cả lvalue caller còn cần thành nguồn move. Dùng `std::forward<Args>(args)` cho forwarding reference.

### Quên forward vì parameter có `&&`

Tên parameter vẫn là lvalue. `&&` trong declaration không tự giữ rvalue category trong thân function.

### Dùng source sau move như còn nguyên

Chỉ dựa vào contract moved-from; tốt nhất gán lại hoặc không dùng giá trị cũ.

### `return std::move(local)`

Move tường minh ở return có thể cản named return value optimization. Thường viết `return local;` và để compiler elide/move.

### Perfect-forward mọi API

Template làm diagnostic, overload resolution và compile time phức tạp. Nếu function chỉ nhận một type rõ, by-value hoặc overload thường dễ duy trì hơn.

### Forward cùng argument nhiều lần

Lần đầu có thể move resource; lần sau nhận state đã bị move. Chỉ forward một lần đến consumer cuối.

## 7. Khi nào KHÔNG dùng

Không bọc make_unique bằng một factory generic nếu không có validation/policy có ích ngoài demo. Không return std::move(local) máy móc vì có thể cản NRVO. Không forward cùng đối số hai lần tới consumer nhận ownership.

## 8. Production notes & scale check

Test bằng log overload và giá trị đích, không assert mọi string nguồn sau move rỗng. Lvalue phải giữ draft theo contract. Nếu cần tối ưu, đo copy/allocation với workload thực trước khi tăng số overload.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Quan sát overload

Thêm lời gọi `create_message(std::move(draft))`, sau đó chỉ in `draft.size()` và giải thích contract.

**Gợi ý:** đừng yêu cầu nội dung draft cụ thể sau move.

### Bài 2 — Setter by value

Thêm `set_text(std::string text)` cho `Message` và thử với lvalue/rvalue.

**Gợi ý:** move parameter vào member ở dòng cuối.

### Bài 3 — Wrapper sai

Tạo phiên bản wrapper truyền `args...` không forward, chạy để thấy cả hai lời gọi chọn copy.

**Gợi ý:** đây là demo đối chiếu; phiên bản cuối phải dùng `std::forward`.

### Bài 4 — Factory có policy

Viết `create_non_empty_message` kiểm tra chuỗi rỗng trước khi tạo.

**Gợi ý:** tránh forward argument rồi lại đọc nó; validate trước, forward đúng một lần.

### Bài 5 — Phân loại reference

Với `T&&`, `const T&&`, `std::string&&` và `auto&&`, xác định trường hợp nào có thể là forwarding reference.

**Gợi ý:** type phải được suy luận tại lời gọi và không có `const` gắn sẵn.

## 10. Bài tập tích hợp liên module — Judgment

So với callback Module 02 nhận bản sao pointer, giải thích vì sao forwarding chỉ là quy tắc biểu thức/kiểu, không tự giải quyết ownership. Thiết kế factory một Message cụ thể: by-value đủ hay cần variadic template?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Tên tham số && có category gì trong thân?
2. T suy luận thế nào khi argument là string&?
3. Vì sao copy elision làm đếm constructor khó dùng như cam kết chung?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] phân biệt lvalue, prvalue và xvalue trong ví dụ;
- [ ] giải thích tên parameter là lvalue expression;
- [ ] tính reference collapsing cho lvalue/rvalue;
- [ ] dùng `std::forward` đúng type parameter;
- [ ] tránh `std::move` máy móc và forwarding quá mức.

**Bài prerequisite:** [Smart pointer và quyền sở hữu](./12-smart-pointer-va-quyen-so-huu.md)

**Bài tiếp theo:** [Dự án C++ quản lý thư viện](./14-du-an-cpp-quan-ly-thu-vien.md)
