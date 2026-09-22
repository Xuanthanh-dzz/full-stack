# Reference, `const` và vòng đời object

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Reference là alias gắn với một object; const reference cung cấp đường đọc không copy.
- Dùng T& khi sửa caller, const T& khi mượn đọc, value cho số nhỏ.
- Reference không sở hữu và thường không kéo dài vòng đời object đích.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt truyền tham trị, pointer và reference;
- dùng `const T&` để đọc object mà không sao chép;
- dùng `T&` khi hàm cần sửa object của bên gọi;
- giải thích reference trỏ đến object nào và lifetime của object đó;
- tránh dangling reference khi trả hoặc lưu reference.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Hai nhãn trên cùng một hộp vẫn chỉ là một hộp. Reference thêm tên để thao tác hộp có sẵn; gán qua tên ấy thay dữ liệu trong hộp, không chuyển nhãn sang hộp khác.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| reference | tên truy cập cùng object | std::string& text |
| const reference | đường truy cập chỉ đọc | const std::string& name |
| dangling reference | alias tới object đã hết vòng đời | trả reference local |
| temporary | object tạm do biểu thức tạo | std::string{"temporary"} |

### Ví dụ nhỏ — tính tay trước

int x = 2, y = 9; int& r = x; r = y; kết quả x = 9, y = 9, r vẫn gắn x. Không giống gán một pointer sang địa chỉ y.

Ta cần chuẩn hóa tên sản phẩm và tính thành tiền. Nếu hàm nhận `std::string` theo giá trị, mỗi lần gọi có thể tạo một bản sao không cần thiết. Nếu dùng pointer như C, lời gọi phải truyền địa chỉ và hàm phải quyết định có chấp nhận `nullptr` hay không.

Yêu cầu thực tế là:

- hàm in chỉ đọc tên, không sao chép;
- hàm chuẩn hóa sửa đúng chuỗi của bên gọi;
- hàm tính tiền nhận số nhỏ theo giá trị;
- không có reference sống lâu hơn object mà nó tham chiếu.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```cpp
#include <cctype>
#include <iostream>
#include <string>

void trim_trailing_spaces(std::string& text)
{
    while (!text.empty() && text.back() == ' ')
    {
        text.pop_back();
    }
}

void make_first_letter_uppercase(std::string& text)
{
    if (!text.empty())
    {
        // cctype chỉ nhận EOF hoặc giá trị biểu diễn được bằng unsigned char.
        const unsigned char first = static_cast<unsigned char>(text.front());
        text.front() = static_cast<char>(std::toupper(first));
    }
}

bool try_calculate_subtotal(
    int quantity,
    long long unit_price,
    long long& subtotal)
{
    constexpr int max_quantity = 1'000'000;
    constexpr long long max_unit_price = 1'000'000'000'000LL;

    if (quantity <= 0
        || quantity > max_quantity
        || unit_price < 0
        || unit_price > max_unit_price)
    {
        return false;
    }

    subtotal = static_cast<long long>(quantity) * unit_price;
    return true;
}

void print_product(const std::string& name, long long subtotal)
{
    std::cout << "Product: " << name << '\n';
    std::cout << "Subtotal: " << subtotal << " VND\n";
}

int main()
{
    std::string product_name = "mechanical keyboard   ";

    trim_trailing_spaces(product_name);
    make_first_letter_uppercase(product_name);

    long long subtotal = 0;
    if (!try_calculate_subtotal(3, 250000, subtotal))
    {
        std::cerr << "Invalid price data\n";
        return 1;
    }

    print_product(product_name, subtotal);

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o references
./references
```

Kết quả:

```text
Product: Mechanical keyboard
Subtotal: 750000 VND
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

### Walkthrough — execution / state / cost

1. main tạo product_name có ba space cuối; trim mượn cùng object và pop từng space.
2. Hàm uppercase đổi byte đầu m thành M sau chuyển unsigned char cho cctype.
3. try_calculate_subtotal nhận hai số theo value, kiểm tra rồi ghi 750000 qua reference output.
4. Các lời gọi kết thúc trước khi main hủy string. Trim tốn số lượt theo phần đuôi bị xóa, không tạo bản sao chuỗi đầy đủ; output số cost cố định.

### Mini-check

Hàm trả const std::string& tới biến local có an toàn hơn trả std::string* không? Vẽ thời điểm return.

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Ba cách truyền dữ liệu

`try_calculate_subtotal` nhận hai input số theo giá trị và một output reference:

```cpp
bool try_calculate_subtotal(
    int quantity,
    long long unit_price,
    long long& subtotal)
```

`quantity` và `unit_price` là hai parameter object riêng có automatic storage duration; sửa chúng không sửa argument của bên gọi. Triển khai thường giữ parameter trong register hoặc stack frame, nhưng chuẩn C++ không bắt buộc vị trí vật lý. Với kiểu số nhỏ, truyền giá trị đơn giản và phù hợp.

`subtotal` là reference đến biến `subtotal` của `main`. Function chỉ ghi output sau khi hai input nằm trong giới hạn nghiệp vụ. Các giới hạn bảo đảm phép nhân không vượt miền `long long`; `false` nói caller không được dùng output như kết quả mới.

`trim_trailing_spaces` nhận reference có thể sửa:

```cpp
void trim_trailing_spaces(std::string& text)
```

`text` là tên khác của chính object `product_name`; hàm không tạo một `std::string` thứ hai. `pop_back()` thay đổi object của `main`.

`print_product` nhận const reference:

```cpp
void print_product(const std::string& name, long long subtotal)
```

`name` vẫn tham chiếu đến `product_name`, nhưng compiler không cho hàm sửa chuỗi qua reference này.

### 4.2. Sơ đồ automatic object và reference

Khi đang chạy `trim_trailing_spaces(product_name)`, mô hình triển khai phổ biến dùng stack frame như sau. Compiler vẫn có thể dùng register hoặc tối ưu object nếu hành vi quan sát được không đổi:

```text
stack (mô hình triển khai phổ biến)
┌─ frame main ───────────────────────────────┐
│ product_name: object std::string           │
│   value = "mechanical keyboard   "         │
└───────────────────▲────────────────────────┘
                    │ cùng object
┌─ frame trim_trailing_spaces ───────────────┐
│ text: std::string& ────────────────────────┘
└────────────────────────────────────────────┘
```

Reference không tạo bản sao của `product_name`. Về mặt ngôn ngữ, reference là alias phải gắn với một object hợp lệ khi khởi tạo và không thể “đổi sang tham chiếu object khác” sau đó.

Biểu diễn reference trong machine code là chi tiết triển khai. Compiler thường dùng địa chỉ bên dưới, nhưng mô hình C++ cần nhớ là alias, không phải một object pointer có thể gán `nullptr`.

### 4.3. Lifetime phải bao trùm thời gian dùng reference

`product_name` được tạo khi luồng chạy qua khai báo trong `main` và bị hủy khi ra khỏi block `main`. Mọi lời gọi trong ví dụ đều kết thúc trước thời điểm đó, nên các reference hợp lệ.

Quy tắc cốt lõi:

```text
lifetime object đích:  [------------------------)
lúc dùng reference:         [---------)
                              hợp lệ
```

Nếu object đích đã bị hủy:

```text
lifetime object đích:  [---------)
lúc dùng reference:               [------)
                                  dangling reference
```

Đọc hoặc ghi qua dangling reference gây undefined behavior.

### 4.4. `const` áp dụng ở đâu?

```cpp
const std::string& name
```

đọc là “reference tới `const std::string`”. Reference không cho sửa object qua tên `name`. Object gốc có thể vốn không `const`; `const` ở đây là cam kết của hàm.

```cpp
const long long subtotal = ...;
```

`subtotal` là object số nguyên không thể gán lại sau khởi tạo. Đây không phải reference.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| T value | object/bản giá trị riêng | hợp số nhỏ hoặc cần sở hữu; copy object lớn có cost |
| T& / const T& | alias sửa/đọc object có sẵn | tránh copy; phải giữ đích sống |
| T* | địa chỉ có thể rỗng hoặc đổi đích | hợp optional view; cần kiểm tra trước dereference |

### Misconception check

**Đúng hay sai?** r = y đổi reference r sang y.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: gán giá trị y vào object r đang gắn.

</details>

**Đúng hay sai?** const T& luôn giữ object sống đến hết mọi nơi lưu reference.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: lifetime extension có điều kiện hẹp; reference qua hàm không gia hạn tùy ý.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** chọn value/reference/pointer.

- **Working Developer — dùng khi làm việc:** trace borrow và output khi lỗi.

- **Deep Dive — có thể quay lại sau:** giới hạn lifetime extension của temporary.

### Chọn parameter theo ý nghĩa

Một quy tắc khởi đầu hữu ích:

| Nhu cầu | Cách truyền |
|---|---|
| kiểu nhỏ, hàm cần bản sao | `T value` |
| object lớn, chỉ đọc | `const T& value` |
| phải sửa object bên gọi | `T& value` |
| “không có object” là trạng thái hợp lệ | `T* value`, kiểm tra `nullptr` |

Đây là điểm xuất phát, không phải luật tối ưu tuyệt đối. [Bài 05](./05-copy-move-rule-of-zero-five.md) và [bài 13](./13-move-semantics-va-perfect-forwarding.md) sẽ bổ sung truyền bằng giá trị kết hợp move.

### Reference phải được khởi tạo

```cpp
int score = 10;
int& score_ref = score;
score_ref = 20; // score trở thành 20
```

Không có cú pháp hợp lệ để khai báo `int& ref;` rồi gắn sau. Phép gán `score_ref = other` gán giá trị vào `score`, không đổi đích của reference.

### Temporary và kéo dài lifetime cục bộ

Một `const` reference cục bộ có thể kéo dài lifetime của temporary mà nó gắn trực tiếp:

```cpp
const std::string& label = std::string{"temporary"};
std::cout << label << '\n'; // hợp lệ đến cuối block của label
```

Quy tắc này có nhiều giới hạn; nó không làm mọi temporary được truyền qua hàm sống lâu tùy ý. Với người mới, không lưu reference đến temporary vào object hoặc biến sống lâu.

### `std::toupper` và miền giá trị

Các hàm trong `<cctype>` yêu cầu giá trị có thể biểu diễn bằng `unsigned char` hoặc bằng `EOF`. Vì `char` có thể là signed, code chuyển sang `unsigned char` trước khi gọi, rồi chuyển kết quả về `char`. Đây là cách tránh undefined behavior với byte có bit cao.

## 6. Lỗi thường gặp

### Trả reference đến biến cục bộ

Code sau sai:

```cpp
const std::string& make_name()
{
    std::string name = "Book";
    return name; // name bị hủy khi hàm kết thúc
}
```

Reference trả về bị dangling. Hãy trả `std::string` theo giá trị; C++ tối ưu việc trả object và có move semantics.

### Dùng `T&` dù hàm không sửa dữ liệu

Reference không `const` làm caller khó biết hàm có sửa object hay không và không nhận được temporary. Nếu chỉ đọc, dùng `const T&`.

### Dùng reference để biểu diễn “có thể không có”

Reference bình thường phải gắn với object hợp lệ. Nếu `null` là một trạng thái nghiệp vụ, dùng pointer và kiểm tra `nullptr`, hoặc dùng kiểu biểu diễn tùy chọn sẽ học sau trong lộ trình.

### Cho rằng `const T&` tạo một object `const` mới

Nó chỉ tạo một đường truy cập chỉ đọc đến object hiện có. Không có bản sao `std::string` thứ hai.

### Trả reference đến phần tử có thể bị thay đổi vị trí

Một số container có thể di chuyển phần tử khi tăng dung lượng. [Bài 09](./09-stl-container.md) sẽ dạy container và quy tắc invalidation; hiện tại không lưu reference vào cấu trúc có thể đổi vị trí phần tử.

### Nhân số tiền mà không giới hạn miền

Phép nhân signed integer vượt miền là undefined behavior. `try_calculate_subtotal` kiểm tra giới hạn trước khi nhân và caller phải xử lý `false`; không thay nó bằng phép nhân trực tiếp trên input tùy ý.

## 7. Khi nào KHÔNG dùng

Không truyền mọi int bằng const int& để tránh copy; số nhỏ thường nên theo value. Không dùng reference cho trạng thái có thể không có object; pointer hoặc kiểu tùy chọn sẽ rõ contract hơn.

## 8. Production notes & scale check

Tên ngắn không cần tối ưu sớm. cctype xử lý byte theo locale, không phải bộ chuẩn hóa Unicode đầy đủ; bài chỉ minh họa ASCII. Test chuỗi rỗng/toàn space, input ngoài miền và output không đổi khi thất bại.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Sửa số tại chỗ

Viết `void apply_discount(long long& price, int percent)` để sửa `price`.

**Gợi ý:** kiểm tra `percent` trong khoảng `0..100` trước khi tính.

### Bài 2 — Chỉ đọc không sao chép

Viết hàm đếm số ký tự của `std::string` và nhận parameter bằng `const` reference.

**Gợi ý:** `text.size()` trả số phần tử; không cần tự duyệt để giải bài này.

### Bài 3 — So sánh ba cách truyền

Viết ba hàm nhận `int` theo value, pointer và reference; mỗi hàm thử tăng giá trị. In biến gốc sau từng lời gọi.

**Gợi ý:** reset biến gốc về cùng giá trị trước mỗi thử nghiệm.

### Bài 4 — Tìm dangling reference

Viết lại hàm `make_name` sai ở trên để trả theo giá trị, rồi build với warning nghiêm ngặt.

**Gợi ý:** signature đúng là `std::string make_name()`.

### Bài 5 — Chuẩn hóa hai đầu

Mở rộng hàm trim để xóa cả space ở đầu và cuối chuỗi.

**Gợi ý:** xử lý một đầu tại một thời điểm; chưa cần algorithm thư viện.

## 10. Bài tập tích hợp liên module — Judgment

Đối chiếu output int* Module 02 với long long&: viết cách gọi, nơi state được sửa và cách biểu diễn không có output. Việc bỏ NULL có loại bỏ dangling không?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Reference có thể đổi đích bằng assignment không?
2. const ở đường truy cập khác const object thế nào?
3. Ai giữ product_name sống trong sample?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] chọn value, `const T&`, `T&` hoặc pointer theo contract;
- [ ] vẽ reference `text` trỏ đến đúng object `product_name`;
- [ ] giải thích vì sao reference không được sống lâu hơn object đích;
- [ ] nhận ra hàm trả reference đến biến cục bộ là sai;
- [ ] dùng `const` để biểu đạt hàm chỉ đọc.

**Bài prerequisite:** [Từ C sang C++20](./01-tu-c-sang-cpp20.md)

**Bài tiếp theo:** [Class, object và encapsulation](./03-class-object-encapsulation.md)
