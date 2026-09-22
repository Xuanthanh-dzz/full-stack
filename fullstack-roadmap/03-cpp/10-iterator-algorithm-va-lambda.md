# Iterator, algorithm và lambda

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Iterator mô tả range; algorithm duyệt; lambda cung cấp quy tắc nhỏ tại chỗ.
- Dùng sort/find/count/accumulate khi contract khớp thay vì viết lại cơ chế duyệt.
- Không dereference end; comparator/capture/kiểu accumulator sai có thể phá kết quả hoặc vòng đời.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- hiểu range nửa mở `[first, last)` do iterator biểu diễn;
- dùng `std::sort`, `std::find_if`, `std::count_if` và `std::accumulate`;
- viết lambda không capture và lambda capture theo giá trị;
- dùng `auto` cho kiểu iterator dài nhưng vẫn hiểu giá trị được suy luận;
- giữ comparator đúng contract và tránh iterator invalidation.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bạn giao một đoạn danh sách và câu hỏi “đơn nào chưa trả?”. Algorithm lo đi từng vị trí, lambda chỉ trả lời câu hỏi cho một phần tử. Biên cuối là dấu dừng, không phải phần tử để đọc.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| iterator | giá trị mô tả vị trí trong range | begin/end |
| range nửa mở | gồm đầu, không gồm cuối | [begin,end) |
| predicate | hàm trả đúng/sai cho điều kiện | order chưa paid |
| lambda/closure | hàm viết tại chỗ kèm state được giữ | capture minimum_total |
| accumulator | giá trị tổng hợp mang qua từng bước | sum bắt đầu 0LL |

### Ví dụ nhỏ — tính tay trước

[5,2,8] sort giảm → [8,5,2]; count >=5 → 2. Accumulate bắt đầu 0LL: 0→8→13→15. Với dãy rỗng, begin==end và không đọc phần tử nào.

Một danh sách đơn hàng cần:

- sắp xếp giảm dần theo tổng tiền;
- tìm đơn chưa thanh toán đầu tiên;
- đếm đơn đạt ngưỡng báo cáo;
- tính tổng tiền của các đơn đã thanh toán.

Viết bốn vòng lặp tay sẽ lặp lại logic duyệt và dễ sai biên. Thư viện chuẩn đã có algorithm; ta chỉ truyền phần nghiệp vụ thay đổi dưới dạng lambda.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Trong mẫu:

- `begin()` và `end()` tạo biên cho range;
- lambda có dạng `[capture](parameters) { body }`;
- `auto` yêu cầu compiler suy luận kiểu iterator trả về từ `find_if`; đây vẫn là static type, không phải kiểu động.

```cpp
#include <algorithm>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

struct Order
{
    std::string id;
    long long total;
    bool paid;
};

int main()
{
    std::vector<Order> orders{
        {"ORD-A", 250000, true},
        {"ORD-B", 120000, false},
        {"ORD-C", 400000, true}};

    std::sort(
        orders.begin(),
        orders.end(),
        [](const Order& left, const Order& right)
        {
            return left.total > right.total;
        });

    std::cout << "Sorted orders:\n";
    for (const Order& order : orders)
    {
        std::cout << order.id << ": " << order.total << '\n';
    }

    const auto first_unpaid = std::find_if(
        orders.begin(),
        orders.end(),
        [](const Order& order)
        {
            return !order.paid;
        });

    if (first_unpaid != orders.end())
    {
        std::cout << "First unpaid: " << first_unpaid->id << '\n';
    }

    const long long minimum_total = 200000;
    const auto eligible_count = std::count_if(
        orders.begin(),
        orders.end(),
        [minimum_total](const Order& order)
        {
            return order.total >= minimum_total;
        });

    const long long paid_total = std::accumulate(
        orders.begin(),
        orders.end(),
        // Literal long long giữ accumulator trong đúng miền tiền.
        0LL,
        [](long long sum, const Order& order)
        {
            return order.paid ? sum + order.total : sum;
        });

    std::cout << "Eligible count: " << eligible_count << '\n';
    std::cout << "Paid total: " << paid_total << " VND\n";

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o algorithms
./algorithms
```

Kết quả:

```text
Sorted orders:
ORD-C: 400000
ORD-A: 250000
ORD-B: 120000
First unpaid: ORD-B
Eligible count: 2
Paid total: 650000 VND
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

### Walkthrough — execution / state / cost

1. Vector chứa A250000 paid, B120000 unpaid, C400000 paid; sort thay thứ tự thành C,A,B.
2. find_if trả vị trí B; code so end trước đọc id.
3. Lambda capture threshold 200000 theo value, count cho 2; accumulate 0LL cộng C+A thành 650000.
4. Algorithms làm việc đồng bộ trên dữ liệu vector sở hữu. Sort O(n log n) so sánh; các lượt find/count/sum tuyến tính; capture một số dùng state cố định.

### Mini-check

Comparator >= trả gì với hai đơn cùng total? Điều đó vi phạm điều kiện compare(x,x) nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Iterator biểu diễn vị trí

`orders.begin()` trả iterator đến phần tử đầu. `orders.end()` trả iterator *past-the-end*: một vị trí ngay sau phần tử cuối, không được dereference.

```text
[begin, end)
   |                    |
   v                    v
[ORD-A][ORD-B][ORD-C]  (past-the-end)
```

Range nửa mở `[first, last)` chứa `first` nhưng không chứa `last`. Range rỗng có `first == last`, nên algorithm xử lý dãy rỗng mà không cần biên đặc biệt.

Iterator có cú pháp gần pointer:

- `*iterator` truy cập phần tử;
- `iterator->member` truy cập member phần tử;
- `++iterator` sang vị trí tiếp theo;
- so sánh với end để biết đã hết.

Không phải mọi iterator là raw pointer; container quyết định type và operation được hỗ trợ.

### 4.2. Algorithm nhận range và operation

`std::sort(first, last, comparator)` thay đổi thứ tự phần tử trong range. Comparator trả `true` khi `left` phải đứng trước `right`; `left.total > right.total` tạo thứ tự giảm dần.

`std::find_if` trả iterator đến phần tử đầu tiên làm predicate đúng, hoặc trả `end()` nếu không tìm thấy. Vì vậy phải kiểm tra trước `first_unpaid->id`.

`std::count_if` đếm phần tử thỏa predicate. `std::accumulate` gấp dãy thành một giá trị, bắt đầu từ `0LL`.

### 4.3. Lambda là function object viết tại chỗ

Lambda:

```cpp
[](const Order& order)
{
    return !order.paid;
}
```

không capture biến ngoài vì `[]` rỗng. Nó nhận một `Order` chỉ đọc và trả `bool`.

Lambda đếm đơn dùng:

```cpp
[minimum_total](const Order& order)
```

Capture theo giá trị tạo một bản `minimum_total` bên trong lambda object. Việc thay biến ngoài sau khi tạo lambda không đổi bản capture.

Nếu capture bằng reference `[&minimum_total]`, lambda tham chiếu biến gốc; khi đó lifetime của biến phải dài hơn mọi lần gọi lambda. Ưu tiên capture tường minh, tránh `[&]`/`[=]` rộng khi lambda không nhỏ.

### 4.4. `auto` vẫn là static typing

Kiểu iterator có thể dài:

```cpp
std::vector<Order>::iterator
```

`const auto first_unpaid = ...` bảo compiler suy luận đúng type từ biểu thức bên phải. Sau suy luận, type cố định tại compile time và mọi operation vẫn được kiểm tra.

`const` làm biến iterator không được gán sang vị trí khác; nó không làm `Order` tự thành const. Trong ví dụ, chỉ đọc là đủ.

### 4.5. Giá trị khởi tạo của `accumulate` quyết định kiểu

`0LL` làm type nội bộ `T` của `std::accumulate` là `long long`, nên accumulator và kết quả đều giữ đúng miền tiền.

Nếu thay bằng literal `0`, `T` nội bộ trở thành `int`. Với **lambda hiện tại**, giá trị accumulator `int` được chuyển thành `long long` khi truyền vào parameter `sum`, nên biểu thức `sum + order.total` vẫn cộng trong miền `long long`. Lỗi xảy ra sau đó: kết quả `long long` do lambda trả về bị chuyển hẹp về accumulator `int` trước vòng kế tiếp, và kết quả cuối kiểu `int` chỉ được đổi lại thành `long long` khi gán vào `paid_total`. Giá trị có thể đã mất; không được mô tả nhầm rằng chính phép cộng trong lambda này diễn ra bằng `int`.

Đây là lỗi phổ biến: chọn initial value cùng kiểu kết quả mong muốn.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Loop tường minh | tự giữ iterator/biên | hợp logic tùy biến đơn giản; dễ sai biên khi lặp lại |
| Algorithm + lambda | cơ chế duyệt chuẩn và policy riêng | rõ ý định; phải giữ contract range/comparator |
| Capture value/reference | giữ bản sao/mượn biến ngoài | value độc lập hơn; reference phải giữ nguồn sống |

### Misconception check

**Đúng hay sai?** const auto iterator làm phần tử nó chỉ tới thành const.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: const hạn chế biến iterator; kiểu iterator/container quyết định quyền sửa phần tử.

</details>

**Đúng hay sai?** Gán accumulate(...,0,...) vào long long đủ tránh hẹp số.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: accumulator nội bộ đã là int; phải chọn initial value đúng kiểu.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace range và thuật toán.

- **Working Developer — dùng khi làm việc:** comparator/capture/accumulator contracts.

- **Deep Dive — có thể quay lại sau:** iterator category, cost và tối ưu closure.

### Comparator phải tạo strict weak ordering

Comparator đúng phải nhất quán, đáng chú ý:

- `compare(x, x)` phải `false`;
- nếu `x` trước `y` thì `y` không trước `x`;
- quan hệ phải bắc cầu.

Không dùng `left.total >= right.total`; với hai phần tử bằng nhau, cả hai chiều đều `true`, vi phạm contract và có thể dẫn đến hành vi không xác định của sort.

`std::sort` không bảo đảm giữ thứ tự tương đối của phần tử bằng nhau. Dùng `std::stable_sort` khi đó là requirement.

### Algorithm không sở hữu dữ liệu

Algorithm nhận iterator và làm việc trên object container đang sở hữu. Lambda nhận reference đến từng phần tử trong lúc gọi; nó không mặc định giữ reference sau khi algorithm kết thúc.

### Iterator invalidation

Nếu lambda hoặc code xung quanh thay đổi cấu trúc vector trong lúc algorithm duyệt, reallocation hoặc xóa phần tử có thể invalidate iterator mà algorithm đang dùng. Không `push_back` vào chính vector đang `sort`/`find_if`.

### Một số algorithm thường dùng

| Algorithm | Mục đích |
|---|---|
| `std::find`, `std::find_if` | tìm phần tử |
| `std::count`, `std::count_if` | đếm |
| `std::sort`, `std::stable_sort` | sắp xếp |
| `std::transform` | biến đổi input thành output |
| `std::remove_if` | dồn phần tử cần giữ; không tự giảm size container |
| `std::all_of`, `any_of`, `none_of` | kiểm tra predicate |
| `std::accumulate` | tổng hợp tuần tự |

Đọc contract từng algorithm: nó có thay đổi input không, yêu cầu loại iterator nào, và output iterator phải trỏ đến storage hợp lệ.

### Đào sâu (có thể quay lại sau)

Mỗi biểu thức lambda tạo một closure type ẩn danh riêng. Capture trở thành state trong closure object. Với capture theo reference, state thường chứa một dạng reference/address; dangling vẫn có thể xảy ra nếu closure sống lâu hơn biến.

Algorithm là function template. Compiler biết type iterator và closure cụ thể, nên thường có thể inline predicate/comparator. Abstraction này không mặc định tạo virtual call.

C++20 còn có ranges algorithm và view, giúp composition và giảm lỗi cặp iterator. Chúng có thêm khái niệm borrowed range, projection và lazy view; học sau khi đã chắc iterator/lifetime cơ bản, không cần để hoàn thành bài này.

## 6. Lỗi thường gặp

### Dereference `end()`

Khi `find_if` không thấy, kết quả bằng `end()`. Dùng `->` trước khi kiểm tra gây undefined behavior.

### Comparator dùng `>=`

Nó vi phạm strict weak ordering khi hai giá trị bằng nhau. Dùng `>` hoặc `<` theo thứ tự mong muốn.

### Capture reference sống quá ngắn

Trả một lambda capture biến cục bộ bằng reference có thể tạo dangling reference. Capture theo giá trị nếu closure cần sống độc lập.

### Khởi tạo `accumulate` bằng sai kiểu

`0` làm accumulator nội bộ có type `int`. Với lambda của bài, mỗi kết quả `long long` bị chuyển hẹp về `int`, nên tổng lớn có thể mất giá trị giữa các vòng. Dùng `0LL` cho `long long`, hoặc một giá trị khởi tạo đúng type miền nghiệp vụ.

### Sửa vector làm iterator mất hiệu lực

Không thêm/xóa phần tử trong khi algorithm đang duyệt cùng range, trừ khi contract cụ thể cho phép và bạn hiểu invalidation.

### Dùng `remove_if` rồi tưởng size đã giảm

`remove_if` chỉ sắp lại phần tử và trả logical end. Với vector C++20 có thể dùng `std::erase_if`; nếu dùng erase-remove idiom, phải gọi `erase`.

## 7. Khi nào KHÔNG dùng

Không dùng algorithm nếu lambda dài che mất luồng nghiệp vụ hơn vòng lặp rõ ràng. Không capture mọi biến bằng [&] để tiện rồi lưu closure vượt scope. Không cần ranges mới để giải bốn phép duyệt này.

## 8. Production notes & scale check

Demo ba đơn có tổng nằm trong long long; 0LL chọn đúng kiểu nhưng không tự chống overflow tổng tùy ý. Test rỗng, không tìm thấy, tổng lớn hơn int và khóa bằng nhau. Capture reference trong lời gọi đồng bộ khác callback được lưu để chạy sau.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Tìm theo ID

Dùng `find_if` tìm `ORD-A`, kiểm tra `end()` rồi in tổng tiền.

**Gợi ý:** capture ID cần tìm theo value.

### Bài 2 — Sắp xếp hai khóa

Sắp tăng theo `total`; nếu bằng nhau thì tăng theo `id`.

**Gợi ý:** comparator phải trả `false` khi hai object tương đương ở cả hai khóa.

### Bài 3 — Kiểm tra toàn bộ

Dùng `std::all_of` kiểm tra mọi đơn có total dương.

**Gợi ý:** algorithm nằm trong `<algorithm>` và predicate trả `bool`.

### Bài 4 — Xóa đơn chưa trả

Dùng `std::erase_if(orders, predicate)` của C++20 để xóa đơn chưa thanh toán.

**Gợi ý:** in size trước và sau; operation này invalidate iterator/reference theo quy tắc vector.

### Bài 5 — Lỗi initial value

Tạo các order sao cho tổng vượt miền `int`, so sánh `accumulate` bắt đầu bằng `0` và `0LL`, rồi chỉ ra chính xác điểm chuyển hẹp.

**Gợi ý:** với lambda hiện tại, phép cộng được promote lên `long long`; lỗi nằm ở lúc kết quả lambda được ghi trở lại accumulator `int`. `std::numeric_limits<int>::max()` từ `<limits>` cho biết cận trên của `int` trên môi trường đang build.

## 10. Bài tập tích hợp liên module — Judgment

Liên hệ callback C Module 02: lambda giữ threshold theo value còn function pointer C không tự chứa state. Thiết kế báo cáo sau khi threshold gốc đổi và chọn snapshot hay giá trị mới có chủ đích.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. end biểu diễn gì khi range rỗng?
2. Capture value giữ dữ liệu lúc nào?
3. Với lambda hiện tại, chuyển hẹp xảy ra ở đâu nếu initial là 0?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] vẽ range `[begin, end)` và không dereference `end`;
- [ ] dùng sort/find/count/accumulate với lambda;
- [ ] giải thích capture theo value và reference;
- [ ] viết comparator strict;
- [ ] chọn initial value đúng kiểu cho `accumulate`.

**Bài prerequisite:** [STL container](./09-stl-container.md)

**Bài tiếp theo:** [Exception và RAII](./11-exception-va-raii.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/02-vector-invalidation.md) · [Review](./reviews/review-02.md).
