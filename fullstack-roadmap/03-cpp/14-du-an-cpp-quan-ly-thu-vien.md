# Dự án C++ quản lý thư viện

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Capstone ghép invariant, polymorphism, container và RAII thành thư viện console có ownership rõ.
- Dùng để chứng minh mượn/trả, duplicate, tìm kiếm và report qua cả đường lỗi.
- Report không phải persistence đầy đủ; các lượt quét lồng nhau có cost theo cả item và loan.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- ghép class, interface, STL, algorithm, exception, RAII và smart pointer vào một chương trình;
- thiết kế ownership rõ ràng cho danh mục polymorphic;
- duy trì invariant mượn/trả qua public operation;
- tìm kiếm, in trạng thái và lưu report ra file;
- build project C++20 sạch warning và giải thích automatic/dynamic storage, ownership và lifetime.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Thư viện giữ tài liệu, thành viên và lịch sử mượn. Trước khi thêm một phiếu mượn phải kiểm tra đủ người, sách và trạng thái. Một owner rõ giữ từng tài liệu; các thao tác chỉ mượn view để hỏi, không tự chia quyền sở hữu.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| polymorphic ownership | sở hữu object derived qua base có destructor phù hợp | unique_ptr<LibraryItem> |
| active loan | phiếu mượn chưa trả | returned == false |
| commit | đưa record hợp lệ vào state chính | push_back Loan sau validation |
| report | ảnh chụp dữ liệu để đọc, chưa có load/restore | library-report.txt |
| index | cấu trúc phụ để tra nhanh | chỉ cân nhắc khi lượt quét đo được là bottleneck |

### Ví dụ nhỏ — tính tay trước

Một sách A và thành viên M: borrow → một loan active; borrow lần hai bị từ chối giữ một loan; return → loan marked returned; borrow lại tạo lịch sử mới. Không xóa lịch sử để giả vờ chưa từng mượn.

Một thư viện cần ứng dụng console nhỏ để:

- thêm tài liệu và thành viên, không trùng mã;
- mượn một tài liệu đang available;
- từ chối mượn lại cùng tài liệu;
- trả tài liệu;
- tìm theo một phần title;
- in catalog và lưu report.

Thiết kế phải cho phép thêm loại tài liệu khác sau này mà `Library` vẫn làm việc qua contract chung. Không dùng owning raw pointer và không có `new`/`delete` thủ công.

Phạm vi checkpoint này chưa có ngày tháng, database hay giao diện nhập lệnh. `main` chạy một kịch bản deterministic để kiểm chứng toàn bộ đường nghiệp vụ đã học; các phần mở rộng nằm ở bài tập.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.cpp`. Bốn API nhỏ được dùng thêm và được giải thích ngay trong bài:

- `map.emplace(key, value)` xây entry key/value trong map;
- `string.find(text)` trả vị trí tìm thấy hoặc `std::string::npos`;
- `ofstream.close()` đóng file có chủ đích để caller kiểm tra lỗi trước khi báo thành công;
- `std::logic_error` biểu diễn operation không hợp lệ với state hiện tại.

```cpp
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

class LibraryItem
{
public:
    LibraryItem(std::string id, std::string title)
        : id_{std::move(id)}, title_{std::move(title)}
    {
        if (id_.empty() || title_.empty())
        {
            throw std::invalid_argument{"Item id and title must not be empty"};
        }
    }

    virtual ~LibraryItem() = default;

    const std::string& id() const
    {
        return id_;
    }

    const std::string& title() const
    {
        return title_;
    }

    virtual int loan_days() const = 0;

private:
    std::string id_;
    std::string title_;
};

class PrintedBook final : public LibraryItem
{
public:
    PrintedBook(std::string id, std::string title, int loan_days)
        : LibraryItem{std::move(id), std::move(title)},
          loan_days_{loan_days}
    {
        if (loan_days_ <= 0)
        {
            throw std::invalid_argument{"Loan days must be positive"};
        }
    }

    int loan_days() const override
    {
        return loan_days_;
    }

private:
    int loan_days_;
};

class Member
{
public:
    Member(std::string id, std::string name)
        : id_{std::move(id)}, name_{std::move(name)}
    {
        if (id_.empty() || name_.empty())
        {
            throw std::invalid_argument{"Member id and name must not be empty"};
        }
    }

    const std::string& id() const
    {
        return id_;
    }

    const std::string& name() const
    {
        return name_;
    }

private:
    std::string id_;
    std::string name_;
};

struct Loan
{
    std::string item_id;
    std::string member_id;
    bool returned;
};

class Library
{
public:
    void add_item(std::unique_ptr<LibraryItem> item)
    {
        if (!item)
        {
            throw std::invalid_argument{"Item must not be null"};
        }

        const std::string item_id = item->id();
        if (find_item(item_id) != nullptr)
        {
            throw std::invalid_argument{"Duplicate item id: " + item_id};
        }

        items_.push_back(std::move(item));
    }

    void add_member(Member member)
    {
        const std::string member_id = member.id();
        if (members_.contains(member_id))
        {
            throw std::invalid_argument{"Duplicate member id: " + member_id};
        }

        members_.emplace(member_id, std::move(member));
    }

    void borrow(const std::string& item_id, const std::string& member_id)
    {
        if (!members_.contains(member_id))
        {
            throw std::invalid_argument{"Unknown member: " + member_id};
        }
        if (find_item(item_id) == nullptr)
        {
            throw std::invalid_argument{"Unknown item: " + item_id};
        }
        if (is_on_loan(item_id))
        {
            throw std::logic_error{"Item is already on loan: " + item_id};
        }

        loans_.push_back(Loan{item_id, member_id, false});
    }

    void return_item(const std::string& item_id)
    {
        const auto active_loan = std::find_if(
            loans_.begin(),
            loans_.end(),
            [&item_id](const Loan& loan)
            {
                return loan.item_id == item_id && !loan.returned;
            });

        if (active_loan == loans_.end())
        {
            throw std::logic_error{"Item is not on loan: " + item_id};
        }

        active_loan->returned = true;
    }

    void print_search(const std::string& keyword) const
    {
        std::cout << "Search \"" << keyword << "\":\n";
        bool found = false;

        for (const std::unique_ptr<LibraryItem>& item : items_)
        {
            if (item->title().find(keyword) != std::string::npos)
            {
                print_item(*item);
                found = true;
            }
        }

        if (!found)
        {
            std::cout << "(no items)\n";
        }
    }

    void print_catalog() const
    {
        std::cout << "Catalog:\n";
        for (const std::unique_ptr<LibraryItem>& item : items_)
        {
            print_item(*item);
        }
    }

    void save_report(const std::string& path) const
    {
        std::ofstream output{path};
        if (!output)
        {
            throw std::runtime_error{"Cannot open report: " + path};
        }

        for (const std::unique_ptr<LibraryItem>& item : items_)
        {
            output << item->id() << ','
                   << item->title() << ','
                   << (is_on_loan(item->id()) ? "on-loan" : "available") << ','
                   << item->loan_days() << '\n';
        }

        output.close();
        if (!output)
        {
            throw std::runtime_error{"Cannot write report: " + path};
        }
    }

private:
    const LibraryItem* find_item(const std::string& item_id) const
    {
        for (const std::unique_ptr<LibraryItem>& item : items_)
        {
            if (item->id() == item_id)
            {
                // Trả view không sở hữu; unique_ptr trong items_ vẫn là owner.
                return item.get();
            }
        }

        return nullptr;
    }

    bool is_on_loan(const std::string& item_id) const
    {
        return std::any_of(
            loans_.begin(),
            loans_.end(),
            [&item_id](const Loan& loan)
            {
                return loan.item_id == item_id && !loan.returned;
            });
    }

    void print_item(const LibraryItem& item) const
    {
        std::cout << "- " << item.id()
                  << " | " << item.title()
                  << " | " << (is_on_loan(item.id()) ? "on-loan" : "available")
                  << " | " << item.loan_days() << " days\n";
    }

    std::vector<std::unique_ptr<LibraryItem>> items_;
    std::map<std::string, Member> members_;
    std::vector<Loan> loans_;
};

int main()
{
    try
    {
        Library library;

        library.add_item(std::make_unique<PrintedBook>(
            "BK-001", "C++20 Essentials", 14));
        library.add_item(std::make_unique<PrintedBook>(
            "BK-002", "RAII in Practice", 21));

        library.add_member(Member{"MEM-001", "An"});
        library.add_member(Member{"MEM-002", "Binh"});

        library.borrow("BK-001", "MEM-001");
        std::cout << "Borrowed: BK-001 -> MEM-001\n";

        try
        {
            library.borrow("BK-001", "MEM-002");
        }
        catch (const std::logic_error& error)
        {
            std::cout << "Borrow rejected: " << error.what() << '\n';
        }

        library.print_search("RAII");

        library.return_item("BK-001");
        std::cout << "Returned: BK-001\n";

        library.print_catalog();

        const std::string report_path = "library-report.txt";
        library.save_report(report_path);
        std::cout << "Report saved: " << report_path << '\n';
    }
    catch (const std::exception& error)
    {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
```

Biên dịch và chạy trong thư mục lab riêng có quyền ghi. Chương trình tạo hoặc
truncate `library-report.txt`, vì vậy không đặt dữ liệu thật cùng tên trong thư
mục chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o library
./library
```

Kết quả console:

```text
Borrowed: BK-001 -> MEM-001
Borrow rejected: Item is already on loan: BK-001
Search "RAII":
- BK-002 | RAII in Practice | available | 21 days
Returned: BK-001
Catalog:
- BK-001 | C++20 Essentials | available | 14 days
- BK-002 | RAII in Practice | available | 21 days
Report saved: library-report.txt
```

File `library-report.txt`:

```text
BK-001,C++20 Essentials,available,14
BK-002,RAII in Practice,available,21
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0`, C++20 và `-Wall -Wextra -Wpedantic -Werror`.

### Walkthrough — execution / state / cost

1. main dựng Library, thêm hai PrintedBook qua unique_ptr và hai Member trong map.
2. borrow kiểm tra member/item/active loan trước khi append; lần mượn thứ hai bị bắt lỗi không đổi state.
3. Search RAII quét title; return đánh dấu phiếu active, catalog cho cả hai available.
4. save_report mở stream, ghi từng item rồi close/kiểm tra trước báo saved. Library sở hữu containers và Books; destructor cleanup khi hết scope.
5. find_item O(I), tìm loan O(L); report gọi tìm loan cho mỗi item nên O(I×L) chưa tính độ dài text. Vector pointer dời không dời Book phía sau.

### Mini-check

Nếu add_item nhận unique_ptr theo value rồi phát hiện duplicate, owner nào hủy object bị từ chối? Caller có được giả định còn giữ nó không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Mỗi class giữ một trách nhiệm rõ

```text
LibraryItem  contract chung của tài liệu
PrintedBook  quy tắc số ngày mượn của sách in
Member       invariant mã/tên thành viên
Loan         dữ liệu một lần mượn
Library      điều phối catalog, member và loan
```

`Library` không kiểm tra concrete type để tính `loan_days`; virtual dispatch gọi implementation của `PrintedBook`. Có thể thêm `ReferenceBook` trả số ngày khác mà không sửa các vòng in report.

### 4.2. Ownership và bộ nhớ

`Library library` là automatic object. Implementation thường biểu diễn nó trong stack frame của `main`, nhưng standard chỉ quy định storage duration/lifetime chứ không bắt buộc vị trí vật lý. Các container là member và sở hữu dynamic storage của chúng khi cần.

Mỗi lời gọi `make_unique<PrintedBook>` tạo một allocation/object riêng:

```text
automatic storage (thường stack)
library: Library
└── items_: vector<unique_ptr<LibraryItem>>
    └── dynamic array của vector
        ├── unique_ptr[0] ─────> dynamic PrintedBook #1 (thường ở heap)
        │                        └── LibraryItem base subobject
        └── unique_ptr[1] ─────> dynamic PrintedBook #2 (thường ở heap)
                                 └── LibraryItem base subobject
```

Vector sở hữu các `unique_ptr`; mỗi `unique_ptr` sở hữu đúng một polymorphic object. Khi vector reallocate, nó move các `unique_ptr`, không move các `PrintedBook` phía sau. Địa chỉ object sách giữ nguyên cho đến khi owner xóa/reset nó.

`find_item` trả `const LibraryItem*` **non-owning**. Pointer chỉ được dùng trong lời gọi hiện tại; caller không `delete` và không lưu qua operation xóa item.

### 4.3. Invariant mượn/trả

`borrow` kiểm tra theo thứ tự:

1. member tồn tại;
2. item tồn tại;
3. item chưa có active loan;
4. mới append một `Loan`.

Nếu validation throw, `loans_` chưa đổi. Nếu `push_back` throw khi allocation, vector giữ invariant theo bảo đảm của operation thư viện cho type này. Không có trạng thái “mượn nửa chừng”.

`return_item` chỉ đánh dấu active loan đầu tiên khớp. Sau đó `is_on_loan` bỏ qua record đã returned. Lịch sử vẫn còn trong vector thay vì bị xóa.

### 4.4. Algorithm và lambda

`std::find_if` tìm active loan cần trả. `std::any_of` dừng ngay khi gặp một active loan, nên không cần quét phần còn lại.

Hai lambda capture `item_id` bằng const reference trong phạm vi lời gọi algorithm đồng bộ. `item_id` vẫn sống suốt lời gọi, nên không dangling.

`string::find(keyword)`:

- trả index đầu tiên nếu thấy substring;
- trả hằng `std::string::npos` nếu không thấy.

Tìm kiếm hiện phân biệt chữ hoa/thường và quét tuyến tính; đây là constraint được ghi rõ, không phải bug ẩn.

### 4.5. Exception boundary và file RAII

Lỗi dự kiến của lần mượn thứ hai được bắt gần operation để demo tiếp tục. Các lỗi không dự kiến đi đến outer `catch` ở `main`, in fatal error và trả exit code `1`.

`save_report` tạo `std::ofstream` cục bộ. Dù write thành công hay throw:

- destructor đóng file nếu stream còn mở khi function kết thúc/unwind;
- không có file handle leak;
- `Library` không giữ resource file lâu hơn operation.

Ở đường thành công, code chủ động `close()` rồi kiểm tra stream trước khi trả về, thay vì báo “saved” trước khi buffer được đóng. Destructor vẫn là cleanup fallback cho mọi đường exception trước đó. Với hệ thống cần atomic/durable report, cần chiến lược file tạm, flush/fsync và rename theo nền tảng; checkpoint này chỉ bảo đảm cleanup và phát hiện lỗi stream cơ bản.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| vector<Book> | giữ object đồng nhất theo value | ít allocation/indirection; đủ nếu không cần đa hình |
| vector<unique_ptr<Base>> | giữ dynamic type với owner duy nhất | thêm allocation; phù hợp contract nhiều loại tài liệu |
| Thêm index active loan | tránh quét lặp | tốn memory và invariant đồng bộ; không thêm trước đo workload |

### Misconception check

**Đúng hay sai?** Mỗi lần vector unique_ptr reallocate thì địa chỉ Book đổi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: smart pointer được move, object Book độc lập vẫn ở chỗ cũ tới khi bị hủy.

</details>

**Đúng hay sai?** File report hiện tại đủ khôi phục toàn bộ Library sau restart.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chưa lưu/load member và lịch sử, còn giới hạn escaping/title.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** chạy và trace mượn/trả.

- **Working Developer — dùng khi làm việc:** test rejection, ownership và stream failure.

- **Deep Dive — có thể quay lại sau:** đo quét lồng nhau và thiết kế persistence theo driver.

### `map::emplace`

```cpp
members_.emplace(member_id, std::move(member));
```

xây entry từ key và value arguments. Code kiểm tra `contains` trước để tạo message duplicate rõ ràng. Map vẫn là nơi bảo đảm key duy nhất.

Trong code concurrent, “check rồi insert” riêng rẽ không tự atomic; module hiện tại là single-thread. Concurrency được học ở C# nâng cao và kiến trúc sau.

### By-value rồi move

Constructor và `add_member` nhận object/string theo value rồi move vào state:

- caller lvalue chịu một copy cần thiết để `Library` sở hữu bản riêng;
- caller rvalue có thể move;
- implementation chỉ có một overload dễ đọc.

Đây là ứng dụng có chủ đích của bài 13, không cần perfect-forwarding mọi function.

### Polymorphic ownership

Container không thể lưu abstract `LibraryItem` theo value. Lưu `unique_ptr<LibraryItem>`:

- giữ dynamic type;
- tránh slicing;
- biểu đạt ownership duy nhất;
- virtual destructor bảo đảm hủy đủ derived rồi base.

Shared ownership không cần thiết vì `Library` là owner duy nhất; các operation chỉ mượn reference/pointer ngắn hạn.

### Giới hạn hiện tại

Để trở thành ứng dụng production, cần quyết định thêm:

- lưu/load dữ liệu và schema version;
- ngày mượn, hạn trả, timezone và tiền phạt;
- nhiều bản copy cho cùng đầu sách;
- escaping hoặc schema rõ ràng cho title có dấu phẩy/xuống dòng trong report;
- authentication/authorization;
- transaction/concurrency nếu nhiều process;
- logging, test tự động và migration.

Không nhồi các concern chưa học vào project nền tảng. Mỗi phần sẽ xuất hiện ở module database, backend, testing và kiến trúc.

### Đào sâu (có thể quay lại sau)

`save_report` gọi `is_on_loan` cho từng item, và mỗi lần quét toàn bộ loans: độ phức tạp O(items × loans). Với dữ liệu lớn, có thể duy trì index active loan theo item ID, nhưng index thứ hai tạo yêu cầu giữ hai cấu trúc nhất quán.

Quyết định tối ưu phải dựa trên số lượng, tần suất đọc/ghi và profiling. Ở quy mô checkpoint, implementation tuyến tính dễ chứng minh đúng hơn.

Tách code sang `.h`/`.cpp` cần chú ý template, include dependency, One Definition Rule và build system. Module 02 đã dạy compilation/linking; bài tập cuối cho phép áp dụng lại mà không đổi design.

## 6. Lỗi thường gặp

### Lưu `LibraryItem` theo value

Base là abstract nên không tạo được; với base concrete còn có slicing. Dùng `unique_ptr<LibraryItem>` cho polymorphic ownership.

### Dùng `shared_ptr` không có shared owner

Library là owner rõ ràng. `shared_ptr` chỉ làm lifetime khó suy luận hơn; reference/raw pointer ngắn hạn đủ cho view.

### Move trước khi lấy ID

Sau `items_.push_back(std::move(item))`, parameter `item` empty. Code copy `item_id` trước, rồi mới move.

### Cập nhật state trước validation

Nếu append loan rồi mới kiểm tra member/item, exception để lại record sai. Validate tất cả precondition trước commit.

### Giữ raw pointer qua operation xóa

Pointer từ `find_item` không sở hữu object. Nếu sau này thêm `remove_item`, mọi view đến item bị xóa thành dangling.

### Quên kiểm tra output stream

Mở file thành công không bảo đảm mọi write thành công. Kiểm tra stream và báo lỗi tại boundary.

### Bắt mọi exception rồi báo thành công

Expected rejection được bắt riêng. Fatal error trả non-zero; không in “saved” nếu operation thất bại.

## 7. Khi nào KHÔNG dùng

Không dùng shared_ptr khi Library là owner duy nhất. Không thêm database chỉ để demo hai sách. Ngược lại, không dùng report CSV giản lược như kho dữ liệu thật nhiều người sửa hoặc coi đóng stream là transaction bền.

## 8. Production notes & scale check

Team nhỏ, vài chục sách dùng quét tuyến tính dễ kiểm chứng. Gate thử duplicate, unknown ID, borrow/return lặp, path lỗi và file giữ state nghiệp vụ hợp lệ. Title có dấu phẩy/newline chưa được escape; báo cáo hiện chỉ phù hợp dữ liệu mẫu. Driver mở rộng là yêu cầu lưu/load hoặc workload đo được.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Loại tài liệu mới

Thêm `ReferenceBook` chỉ cho mượn `1` ngày và xác nhận report dùng virtual dispatch.

**Gợi ý:** kế thừa `LibraryItem`, override `loan_days`, không sửa `Library::print_item`.

### Bài 2 — In người đang mượn

Thêm operation in active loan gồm item ID, member ID và member name.

**Gợi ý:** dùng `find` rồi so với `end()`, hoặc `at` nếu invariant bảo đảm member tồn tại (`at` ném `std::out_of_range` khi thiếu). Không dùng `operator[]`: operation này có nhánh chèn value mặc định và vì thế yêu cầu mapped type phải default-constructible ngay khi compile; `Member` không có default constructor, nên biểu thức đó không compile kể cả lúc key chạy thực tế đã tồn tại.

### Bài 3 — Xóa item an toàn

Chỉ cho xóa item nếu không on-loan, dùng `std::erase_if`.

**Gợi ý:** validate trước; khi `unique_ptr` bị erase, concrete object tự bị hủy.

### Bài 4 — Command loop

Thêm menu `add-member`, `borrow`, `return`, `search`, `quit` và tiếp tục sau input nghiệp vụ sai.

**Gợi ý:** catch expected exception ở boundary từng command; trạng thái input stream phải được phục hồi nếu parse thất bại.

### Bài 5 — Tách nhiều file và kiểm thử thủ công

Tách declaration/definition thành `library-item.h/.cpp`, `library.h/.cpp`, `main.cpp`; tạo script input hoặc scenario kiểm tra duplicate, unknown ID, borrow hai lần và return hai lần.

**Gợi ý:** header có include guard; lệnh link phải chứa mọi `.cpp`.

## 10. Bài tập tích hợp liên module — Judgment

So sánh load kho C Module 02 với report thư viện: cái nào là roundtrip persistence, cái nào chỉ export? Đề xuất một bước nhỏ tiếp theo và failure test trước khi nghĩ tới database hay nhiều service.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ ownership từ Library xuống từng Book.
2. Trace borrow lỗi và state loans trước/sau.
3. Vì sao report O(I×L) dù chỉ có một vòng for nhìn ở save_report?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành module khi có thể:

- [ ] build project C++20 sạch warning trên môi trường mới;
- [ ] vẽ toàn bộ `Library`, container, `unique_ptr` và từng dynamic object, kèm caveat về vị trí vật lý;
- [ ] giải thích raw pointer nào chỉ là non-owning view;
- [ ] chứng minh validation xảy ra trước state mutation;
- [ ] thêm một derived item mà không sửa code in polymorphic;
- [ ] theo dõi exception và destructor ở đường lỗi file/nghiệp vụ.

**Bài prerequisite:** [Move semantics và perfect forwarding](./13-move-semantics-va-perfect-forwarding.md)

**Bài tiếp theo:** [.NET 9 và chương trình C# đầu tiên](../04-csharp-co-ban/01-dotnet-9-va-chuong-trinh-csharp.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/03-raii-khong-rollback.md) · [Review](./reviews/review-03.md).

**Trước khi sang C#:** [PR Review](./pr-review-labs/01-library.md).
