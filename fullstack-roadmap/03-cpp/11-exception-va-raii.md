# Exception và RAII

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Exception chuyển xử lý lỗi tới handler; RAII gắn việc trả tài nguyên với vòng đời object.
- Dùng RAII cho memory/file/lock và bắt lỗi ở nơi có thể xử lý hoặc báo thất bại.
- Cleanup không đồng nghĩa rollback hay dữ liệu đã bền trên đĩa.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- ném exception khi function không thể hoàn thành contract;
- bắt exception theo `const` reference tại boundary phù hợp;
- giải thích stack unwinding gọi destructor của object tự động;
- dùng RAII để file luôn được đóng cả ở đường thành công lẫn thất bại;
- phân biệt lỗi có thể phục hồi với bug/vi phạm precondition nội bộ.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bạn mượn chìa khóa khi vào phòng; dù ra cửa thường hay phải rời sớm vì lỗi, người giữ chìa vẫn phải trả nó. RAII đặt trách nhiệm trả vào object quản lý, không rải lời gọi cleanup khắp các nhánh.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| exception | object báo thao tác không hoàn thành contract | invalid_argument |
| handler | đoạn nhận xử lý exception phù hợp | catch ở main |
| stack unwinding | rời scope giữa throw và handler, hủy object đã dựng | writer được cleanup |
| RAII | gắn tài nguyên với object chịu trách nhiệm thu hồi | ofstream member |
| strong guarantee | thất bại giữ nguyên state quan sát được | khác chỉ không leak |

### Ví dụ nhỏ — tính tay trước

Dựng writer → ghi A → phép tính B ném lỗi → hủy writer trước catch. File có thể vẫn chứa A; đóng file không tự xóa phần đã ghi để quay về state cũ.

Chương trình ghi đơn hàng ra file. Ba lỗi có thể xảy ra:

- đường dẫn không mở được;
- số lượng hoặc đơn giá không hợp lệ;
- phép nhân thành tiền vượt miền `long long`.

Nếu mỗi bước trả mã lỗi, caller dễ quên kiểm tra. Nguy hiểm hơn, nếu lỗi xuất hiện sau khi mở file, mọi đường thoát đều phải đóng file.

Ta sẽ dùng exception để chuyển quyền xử lý đến boundary của chương trình và RAII để cleanup không phụ thuộc đường đi.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```cpp
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

struct Order
{
    std::string id;
    long long total;
};

long long calculate_total(int quantity, long long unit_price)
{
    if (quantity <= 0)
    {
        throw std::invalid_argument{"Quantity must be positive"};
    }
    if (unit_price < 0)
    {
        throw std::invalid_argument{"Unit price must not be negative"};
    }
    if (unit_price > std::numeric_limits<long long>::max() / quantity)
    {
        throw std::overflow_error{"Order total is too large"};
    }

    return static_cast<long long>(quantity) * unit_price;
}

class ReportWriter
{
public:
    explicit ReportWriter(const std::string& path)
        : output_{path}
    {
        if (!output_)
        {
            throw std::runtime_error{"Cannot open report file"};
        }
    }

    void write(const Order& order)
    {
        output_ << order.id << ',' << order.total << '\n';
        if (!output_)
        {
            throw std::runtime_error{"Cannot write report file"};
        }
    }

private:
    std::ofstream output_;
};

int main()
{
    const std::string report_path = "order-report.txt";

    try
    {
        // Member ofstream sẽ tự đóng nếu stack unwinding rời try block.
        ReportWriter writer{report_path};

        const Order valid_order{
            "ORD-001",
            calculate_total(3, 250000)};
        writer.write(valid_order);
        std::cout << "Saved ORD-001: " << valid_order.total << '\n';

        const Order invalid_order{
            "ORD-002",
            calculate_total(0, 100000)};
        writer.write(invalid_order);
    }
    catch (const std::exception& error)
    {
        std::cout << "Error: " << error.what() << '\n';
    }

    std::cout << "Program continues\n";

    std::ifstream input{report_path};
    std::string saved_line;
    if (std::getline(input, saved_line))
    {
        std::cout << "Report file: " << saved_line << '\n';
    }

    return 0;
}
```

Biên dịch và chạy trong thư mục lab riêng có quyền ghi. Chương trình tạo hoặc
truncate `order-report.txt`, vì vậy không đặt dữ liệu thật cùng tên trong thư
mục chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o exception_raii
./exception_raii
```

Kết quả:

```text
Saved ORD-001: 750000
Error: Quantity must be positive
Program continues
Report file: ORD-001,750000
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20. File được mở ở chế độ mặc định của `std::ofstream`, nên nội dung cũ bị truncate khi chạy lại.

### Walkthrough — execution / state / cost

1. ReportWriter mở file trong thư mục lab riêng, ofstream member giữ tài nguyên.
2. Đơn hợp lệ 3 × 250000 được ghi; phép tính quantity 0 ném invalid_argument trước tạo xong đơn thứ hai.
3. Runtime hủy các automatic object đã dựng trong try trước khi vào catch; ofstream đóng file.
4. main báo lỗi rồi đọc dòng ORD-001. I/O theo byte; exception có chi phí riêng phụ thuộc toolchain, không dùng làm vòng lặp thường. State file đã thay dù resource được thu hồi.

### Mini-check

Dòng Saved được in trước khi ofstream đóng: nó đã chứng minh mọi dữ liệu ghi thành công và bền sau mất điện chưa?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. `throw` dừng đường đi hiện tại

Khi `calculate_total(0, 100000)` chạy:

```cpp
throw std::invalid_argument{"Quantity must be positive"};
```

tạo một exception object và dừng function hiện tại. Không có `Order invalid_order` hoàn chỉnh và `writer.write(invalid_order)` không chạy.

Runtime tìm handler phù hợp gần nhất theo call stack. `std::invalid_argument` kế thừa `std::exception`, nên:

```cpp
catch (const std::exception& error)
```

bắt được nó. Bắt theo const reference tránh copy/slicing exception và cho phép gọi virtual function `what()`.

### 4.2. Stack unwinding

Trước khi vào `catch`, runtime rời các scope giữa điểm throw và handler. Trong quá trình đó, destructor của mọi object tự động đã xây dựng hoàn chỉnh chạy theo thứ tự ngược.

```text
try block trước lỗi
├── writer: ReportWriter
│   └── output_: std::ofstream đang mở
└── valid_order: Order

throw
  |
  v
stack unwinding
├── hủy valid_order
└── hủy writer
    └── hủy output_ -> đóng file
  |
  v
catch
```

Vì file được đóng trước khi handler kết thúc, `std::ifstream` phía sau đọc được dòng đã ghi.

### 4.3. RAII gắn resource với lifetime object

RAII là *Resource Acquisition Is Initialization*:

- constructor thiết lập/acquire resource hoặc báo thất bại;
- object chỉ tồn tại ở state dùng được;
- destructor release resource;
- ownership bám theo scope/object lifetime.

`ReportWriter` sở hữu `std::ofstream` bằng value member. `std::ofstream` đã là RAII type; `ReportWriter` không cần tự viết destructor. Đây là Rule of Zero.

```text
ReportWriter sống  <=> member ofstream sống <=> file handle được sở hữu
ReportWriter hủy   => ofstream hủy           => file handle đóng
```

RAII không chỉ dành cho memory. Nó áp dụng cho file, mutex lock, socket, transaction guard và các resource phải release.

### 4.4. Constructor thất bại

Nếu mở file thất bại, constructor `ReportWriter` throw. Object `writer` chưa được xây dựng hoàn chỉnh nên destructor `~ReportWriter` không chạy. Tuy nhiên, member đã xây dựng như `output_` vẫn được hủy trong quá trình constructor unwinding.

Caller không bao giờ nhận một `ReportWriter` “nửa hợp lệ”.

### 4.5. Kiểm tra overflow trước phép nhân

Signed integer overflow là undefined behavior. Code không nhân trước rồi mới kiểm tra. Với `quantity > 0` và `unit_price >= 0`, điều kiện:

```cpp
unit_price > max / quantity
```

phát hiện trước khi phép nhân vượt miền. Thứ tự validation làm phép chia an toàn vì `quantity` đã được xác nhận dương.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Status return | caller kiểm tra kết quả tường minh | hợp thất bại thường gặp; dễ quên nếu API yếu |
| Exception | chuyển điều khiển tới handler | hợp lỗi cần vượt nhiều tầng; phải chọn boundary |
| RAII | cleanup theo lifetime | dùng được với cả status và exception; không tự rollback |

### Misconception check

**Đúng hay sai?** Constructor throw thì destructor của object chưa dựng xong sẽ chạy.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: member/base đã dựng được hủy, destructor của object hoàn chỉnh đó không chạy.

</details>

**Đúng hay sai?** RAII tự cung cấp strong guarantee cho mọi thao tác.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: nó quản lý cleanup; state có thể đã đổi trước khi lỗi.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace throw/catch và destructor.

- **Working Developer — dùng khi làm việc:** boundary lỗi và tài nguyên tự cleanup.

- **Deep Dive — có thể quay lại sau:** exception guarantees, chi phí và durability.

### Exception hierarchy chuẩn

Một số type thường gặp trong `<stdexcept>`:

| Type | Ý nghĩa thường dùng |
|---|---|
| `std::invalid_argument` | argument không đáp ứng contract |
| `std::out_of_range` | index/key nằm ngoài miền |
| `std::runtime_error` | lỗi runtime chung như I/O |
| `std::overflow_error` | kết quả số học vượt miền được kiểm tra |

Đừng chọn type chỉ vì tên nghe gần đúng; exception message và tài liệu contract phải giúp boundary quyết định cách xử lý.

### Bắt ở boundary có khả năng xử lý

Không catch rồi bỏ qua ở mọi function. Một tầng chỉ nên catch khi nó có thể:

- phục hồi hoặc thử phương án khác;
- thêm context rồi rethrow;
- chuyển lỗi sang contract của boundary;
- log/hiển thị và kết thúc operation.

`main` là boundary phù hợp trong console demo. Library code thường không in trực tiếp thay caller.

### `throw;` và `throw error;`

Trong `catch`, `throw;` rethrow exception hiện tại mà giữ dynamic type. `throw error;` có thể copy và slicing nếu biến có type base. Chỉ rethrow khi tầng hiện tại không xử lý hoàn chỉnh.

### Destructor không được để exception thoát ra

Nếu destructor ném trong lúc đang unwinding một exception khác, chương trình thường gọi `std::terminate`. Cleanup nên không-fail hoặc tự xử lý lỗi theo policy không ném. Đây là lý do flush/close có lỗi cần được xử lý rõ trước khi destructor nếu việc xác nhận ghi bền vững là requirement.

### Đào sâu (có thể quay lại sau)

Exception safety thường được mô tả theo các mức:

- **no-throw guarantee:** operation cam kết không ném;
- **strong guarantee:** thất bại thì state quan sát được không đổi;
- **basic guarantee:** không leak, invariant vẫn đúng nhưng state có thể đổi;
- **no guarantee:** thất bại có thể phá invariant.

RAII cung cấp nền cho basic guarantee nhưng không tự tạo strong guarantee. Muốn strong guarantee thường chuẩn bị state/resource mới trước, rồi commit bằng operation không ném.

Chi phí và cách triển khai exception phụ thuộc ABI/compiler. Nhiều toolchain tối ưu đường không lỗi rất tốt nhưng đường throw đắt. Không dùng exception làm control flow thường xuyên như kết thúc vòng lặp; dùng cho failure không thuộc đường thành công bình thường của contract.

## 6. Lỗi thường gặp

### Catch theo value

`catch (std::exception error)` copy và có thể slicing derived exception. Dùng `const std::exception&`.

### Catch rồi bỏ qua

Handler rỗng làm operation có vẻ thành công dù state thiếu. Phục hồi thật, thêm context/rethrow, hoặc báo lỗi tại boundary.

### Quản lý cleanup bằng nhiều `return`

Tự gọi `close` trên mọi nhánh rất dễ bỏ sót khi thêm exception/return mới. Đặt resource trong RAII object.

### Throw pointer hoặc kiểu tùy tiện

`throw new Error` tạo ownership khó quản lý. Throw exception object theo value; catch theo const reference.

### Dùng exception cho input sai bình thường trong loop nóng

Nếu input invalid là kết quả thường xuyên và caller cần rẽ nhánh, return type biểu đạt success/failure có thể rõ hơn. Chọn contract theo tần suất và boundary, không biến exception thành `if`.

### Cho rằng destructor `ofstream` báo được mọi lỗi ghi

Destructor đóng resource nhưng không phải kênh báo lỗi đáng tin cậy. Nếu durability quan trọng, chủ động `flush`/`close`, kiểm tra trạng thái và thiết kế transaction/file replacement phù hợp.

## 7. Khi nào KHÔNG dùng

Không dùng throw cho mỗi lần không tìm thấy trong một vòng tra cứu thường xuyên nếu status rõ hơn. Không catch rồi bỏ qua để biến thất bại thành thành công. Không tự viết destructor nếu member RAII đã làm đủ.

## 8. Production notes & scale check

Demo có một file và một lỗi dự kiến. Destructor không phải kênh báo lỗi ghi cuối đáng tin; nếu cần xác nhận ghi, thêm close/kiểm tra trước thông báo thành công, và xác định riêng yêu cầu durability. Test đường dẫn không mở được, số âm, tràn số và dữ liệu file thực tế.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Đơn giá âm

Gọi `calculate_total` với đơn giá âm và xác nhận message đúng.

**Gợi ý:** mỗi lần chỉ kích hoạt một validation branch.

### Bài 2 — Đường dẫn lỗi

Truyền một đường dẫn chắc chắn không mở được trên môi trường của bạn và quan sát constructor throw.

**Gợi ý:** không hard-code giả định hệ điều hành vào code production; đây là thí nghiệm cục bộ.

### Bài 3 — Nhiều exception cụ thể

Catch `std::invalid_argument` trước, rồi `std::exception` sau và in hai prefix khác nhau.

**Gợi ý:** handler cụ thể phải đứng trước handler base.

### Bài 4 — RAII cho timer

Tạo class in “start” ở constructor và “stop” ở destructor; dùng nó trong function có thể throw để quan sát cleanup.

**Gợi ý:** destructor không được throw.

### Bài 5 — Strong guarantee

Thiết kế operation thay nội dung report bằng cách ghi file tạm trước rồi mới commit; chỉ phân tích các failure point.

**Gợi ý:** đây là bài thiết kế; API filesystem và atomic rename phụ thuộc nền tảng sẽ học sâu hơn ở DevOps.

## 10. Bài tập tích hợp liên module — Judgment

So với cleanup label của kho C Module 02, RAII giảm trách nhiệm thủ công nào? Liệt kê phần vẫn cần thiết kế để load lỗi giữ state cũ; không nhầm cleanup với commit.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Object nào bị hủy trước catch trong sample?
2. Vì sao catch theo const reference?
3. Basic guarantee khác strong guarantee bằng ví dụ file thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] mô tả đường đi từ `throw` đến `catch`;
- [ ] vẽ destructor chạy trong stack unwinding;
- [ ] giải thích RAII cho resource không phải memory;
- [ ] bắt exception theo const reference;
- [ ] kiểm tra overflow trước phép toán nguy hiểm.

**Bài prerequisite:** [Iterator, algorithm và lambda](./10-iterator-algorithm-va-lambda.md)

**Bài tiếp theo:** [Smart pointer và quyền sở hữu](./12-smart-pointer-va-quyen-so-huu.md)
