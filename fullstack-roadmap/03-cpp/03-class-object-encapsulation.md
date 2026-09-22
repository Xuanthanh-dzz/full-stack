# Class, object và encapsulation

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Class mô tả dữ liệu và thao tác; mỗi object giữ state riêng.
- Dùng encapsulation để mọi thay đổi đi qua kiểm tra invariant.
- private không tự làm nghiệp vụ đúng; setter vô điều kiện vẫn phá contract.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- khai báo một `class` có dữ liệu `private` và hành vi `public`;
- tạo nhiều object độc lập từ cùng một class;
- dùng member function để bảo vệ invariant;
- giải thích `this` trỏ đến object đang nhận lời gọi;
- phân biệt class, object và member.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Phiếu điểm thưởng không nên cho mọi người xóa rồi viết số tùy ý. Một quầy nhận yêu cầu cộng điểm hoặc đổi quà, kiểm tra rồi mới sửa phiếu. Class gom phiếu với các cửa thao tác đó.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| class | mô tả dữ liệu và thao tác hợp lệ | LoyaltyAccount |
| object | một thực thể được tạo từ kiểu | an_account và binh_account |
| encapsulation | giữ việc thay state sau interface kiểm soát | add_points/redeem |
| invariant | điều kiện state phải giữ | 0 ≤ points ≤ 1000000 |
| this | con trỏ ngầm tới object nhận lời gọi | account đang cộng điểm |

### Ví dụ nhỏ — tính tay trước

A có 10 điểm, B có 5. A.redeem(7) → A còn 3, B vẫn 5. B.redeem(7) bị từ chối → cả hai không đổi thêm.

Một tài khoản điểm thưởng có hai dữ liệu: mã khách hàng và số điểm. Nếu chương trình để mọi nơi sửa trực tiếp số điểm, các trạng thái vô lý như điểm âm có thể xuất hiện.

Ta cần một kiểu dữ liệu:

- mỗi khách hàng có object riêng;
- điểm khởi đầu là `0`;
- chỉ cộng số điểm dương;
- chỉ đổi quà khi đủ điểm;
- code bên ngoài không thể gán tùy ý vào số điểm.

Bài này tập trung vào encapsulation. Constructor có parameter sẽ được học ở bài sau, nên object được tạo với trạng thái mặc định rồi nhận mã qua member function có kiểm tra.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```cpp
#include <iostream>
#include <string>

class LoyaltyAccount
{
public:
    bool set_customer_id(const std::string& customer_id)
    {
        if (customer_id.empty())
        {
            return false;
        }

        customer_id_ = customer_id;
        return true;
    }

    bool add_points(int amount)
    {
        constexpr int max_points = 1'000'000;
        // Kiểm tra trước phép cộng để vừa giữ invariant, vừa tránh overflow.
        if (amount <= 0 || amount > max_points - points_)
        {
            return false;
        }

        points_ += amount;
        return true;
    }

    bool redeem(int cost)
    {
        if (cost <= 0 || cost > points_)
        {
            return false;
        }

        points_ -= cost;
        return true;
    }

    const std::string& customer_id() const
    {
        return customer_id_;
    }

    int points() const
    {
        return points_;
    }

private:
    std::string customer_id_;
    int points_ = 0;
};

void print_account(const LoyaltyAccount& account)
{
    std::cout << account.customer_id()
              << ": " << account.points() << " points\n";
}

int main()
{
    LoyaltyAccount an_account;
    LoyaltyAccount binh_account;

    if (!an_account.set_customer_id("CUS-001")
        || !binh_account.set_customer_id("CUS-002"))
    {
        std::cerr << "Invalid customer id\n";
        return 1;
    }

    if (!an_account.add_points(120) || !binh_account.add_points(50))
    {
        std::cerr << "Cannot add loyalty points\n";
        return 1;
    }

    std::cout << "Redeem 80 from CUS-001: "
              << (an_account.redeem(80) ? "accepted" : "rejected") << '\n';
    std::cout << "Redeem 80 from CUS-002: "
              << (binh_account.redeem(80) ? "accepted" : "rejected") << '\n';

    print_account(an_account);
    print_account(binh_account);

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o loyalty
./loyalty
```

Kết quả:

```text
Redeem 80 from CUS-001: accepted
Redeem 80 from CUS-002: rejected
CUS-001: 40 points
CUS-002: 50 points
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

### Walkthrough — execution / state / cost

1. main tạo hai account độc lập, mặc định ID rỗng và points = 0.
2. Gán ID hợp lệ rồi cộng 120 cho An và 50 cho Bình qua public operation.
3. Redeem 80 trên An được chấp nhận còn 40; trên Bình bị từ chối giữ 50.
4. State thuộc từng object, không có biến điểm static chung. Validation/cộng/trừ cost cố định; gán ID có cost theo chuỗi.

### Mini-check

Khi add_points thất bại vì vượt hạn mức, points_ giữ giá trị nào? Kiểm tra trước hay sau phép cộng?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Class là bản mô tả, object là thực thể trong bộ nhớ

`class LoyaltyAccount` mô tả dữ liệu và các operation hợp lệ. Hai dòng:

```cpp
LoyaltyAccount an_account;
LoyaltyAccount binh_account;
```

tạo hai automatic object riêng. Compiler thường biểu diễn chúng trong stack frame, nhưng chuẩn C++ chỉ bắt buộc chúng có lifetime độc lập theo scope:

```text
stack frame main (mô hình triển khai phổ biến)
├── an_account: LoyaltyAccount object
│   ├── customer_id_ = "CUS-001"
│   └── points_      = 40
└── binh_account: LoyaltyAccount object
    ├── customer_id_ = "CUS-002"
    └── points_      = 50
```

Sửa `points_` của `an_account` không ảnh hưởng `binh_account`. Mỗi object có vùng lưu trữ cho các non-static data member của chính nó.

### 4.2. Encapsulation bảo vệ invariant

`points_` nằm sau nhãn `private`, nên code trong `main` không thể viết:

```cpp
// an_account.points_ = -100; // lỗi compile
```

Mọi thay đổi phải đi qua `add_points` hoặc `redeem`. Hai member function kiểm tra input trước khi đổi state. Invariant của class là:

```text
customer_id_ không rỗng sau khi thiết lập thành công
0 <= points_ <= 1000000
```

Encapsulation không chỉ là “giấu field”. Mục tiêu là gom dữ liệu với những operation duy trì trạng thái hợp lệ.

### 4.3. `this` trỏ đến object nhận lời gọi

Lời gọi:

```cpp
an_account.add_points(120);
```

vào member function với một pointer ngầm định tên là `this`, trỏ đến `an_account`. Bên trong, `points_ += amount` tương đương về ý nghĩa với:

```cpp
this->points_ += amount;
```

Ở lời gọi kế tiếp trên `binh_account`, `this` trỏ đến object khác. Không cần viết `this->` khi tên member không bị che khuất.

### 4.4. Member function `const`

```cpp
int points() const
```

Từ `const` sau danh sách parameter cam kết member function không sửa trạng thái quan sát được của object. Vì `print_account` nhận `const LoyaltyAccount&`, nó chỉ gọi được các member function `const`.

Hai vị trí `const` có nghĩa khác nhau:

```cpp
const std::string& customer_id() const
// ^ trả reference chỉ đọc          ^ không sửa object nhận lời gọi
```

Reference trả về hợp lệ trong lúc object `LoyaltyAccount` còn sống và member `customer_id_` chưa bị operation khác làm mất hiệu lực. Caller không được lưu reference đó lâu hơn account.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| public data | caller gán trực tiếp | đủ cho record không có invariant phức tạp; không hợp điểm cần bảo vệ |
| private + setter bất kỳ | giấu tên nhưng cho ghi tùy ý | không tự bảo vệ nghiệp vụ |
| operation nghiệp vụ | kiểm tra rồi commit | giữ invariant tại một nơi; tránh wrapper không có trách nhiệm |

### Misconception check

**Đúng hay sai?** Hai object cùng class dùng chung points_.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: non-static member thuộc từng object.

</details>

**Đúng hay sai?** Bài này đảm bảo ID không rỗng ngay sau default construction.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: ID chỉ hợp lệ sau setter; constructor có kiểm tra sẽ hoàn thiện quy trình sau.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** vẽ state riêng và public/private.

- **Working Developer — dùng khi làm việc:** giữ invariant, không commit trước validation.

- **Deep Dive — có thể quay lại sau:** thiết kế thao tác nhiều object khi có driver.

### `public` và `private`

- Member `public` tạo interface mà caller được dùng.
- Member `private` chỉ được code thuộc class và các thành phần được cấp quyền đặc biệt truy cập.
- Với `class`, access mặc định là `private`.
- Với `struct`, access mặc định là `public`; ngoài khác biệt mặc định này, cả hai đều có thể có member function và access modifier.

Quy ước hậu tố `_` trong `customer_id_` chỉ là style để nhận ra data member, không phải cú pháp bắt buộc.

### Getter không phải lúc nào cũng là thiết kế tốt

`points()` và `customer_id()` là query hợp lệ cho bài toán. Nhưng tạo getter/setter công khai cho mọi field sẽ làm mất ý nghĩa encapsulation. Ưu tiên operation nghiệp vụ như `add_points` và `redeem` thay vì `set_points`.

### Object mặc định trong bài này

Khi tạo `LoyaltyAccount an_account;`:

- `customer_id_` là `std::string` mặc định rỗng;
- `points_ = 0` là *default member initializer*;
- compiler cung cấp constructor mặc định vì class chưa khai báo constructor riêng.

[Bài 04](./04-constructor-destructor-va-bo-nho.md) sẽ thay quy trình “tạo rồi set ID” bằng constructor để object hợp lệ ngay từ lúc sinh ra.

### Toán tử điều kiện

Biểu thức:

```cpp
condition ? "accepted" : "rejected"
```

chọn một trong hai giá trị dựa trên `condition`. Đây là conditional operator; chỉ nên dùng khi biểu thức ngắn và dễ đọc.

## 6. Lỗi thường gặp

### Để field ở `public`

Nếu `points_` là public, bất kỳ code nào cũng có thể tạo điểm âm. Khi quy tắc thay đổi, không còn một nơi duy nhất để sửa.

### Setter chấp nhận mọi giá trị

Một setter chỉ gán field chưa tạo ra bảo vệ. Nếu có `set_points(int)`, nó phải giữ invariant; tốt hơn là mô hình hóa operation nghiệp vụ cụ thể.

### Quên `const` ở query member function

Nếu `points()` không có `const` phía sau, `print_account(const LoyaltyAccount&)` không gọi được nó. Thêm `const` cho operation chỉ đọc.

### Trả reference đến dữ liệu không tồn tại lâu

Không tạo một biến cục bộ trong getter rồi trả reference đến nó. Getter hiện tại trả reference đến member của object; reference chỉ hợp lệ theo lifetime của object đó.

### Hiểu nhầm hai object dùng chung field

Non-static data member thuộc từng object. Chỉ `static` data member mới được dùng chung; bài này không cần `static`.

## 7. Khi nào KHÔNG dùng

Không tạo class nhiều getter/setter chỉ để bọc một cặp số không có hành vi. Không thêm kế thừa để dùng chung tên field; trước hết xác định invariant thực sự cần bảo vệ.

## 8. Production notes & scale check

Team nhỏ với điểm thưởng cần test sát hạn mức, đổi quá số dư và hai object độc lập. Bài chưa có giao dịch chuyển điểm nguyên tử: trừ bên gửi rồi cộng bên nhận có thể thất bại giữa chừng. Không coi public interface đơn lẻ là transaction nhiều object.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Chặn tràn hạn mức

Đổi hạn mức hiện tại thành `1000` điểm. `add_points` phải từ chối nếu kết quả vượt hạn mức.

**Gợi ý:** kiểm tra trước phép cộng; giữ invariant ở bên trong class.

### Bài 2 — Operation chuyển điểm

Viết hàm tự do chuyển điểm giữa hai account mà chỉ dùng public interface hiện có.

**Gợi ý:** cần xử lý trường hợp cộng cho người nhận thất bại; suy nghĩ cách hoàn tác an toàn.

### Bài 3 — Lịch sử số lần đổi quà

Thêm member đếm số lần `redeem` thành công và query `redemption_count() const`.

**Gợi ý:** chỉ tăng bộ đếm sau khi mọi điều kiện đã qua.

### Bài 4 — So sánh object độc lập

Tạo ba account, thực hiện operation khác nhau và vẽ vùng nhớ cho từng object.

**Gợi ý:** ghi riêng giá trị từng data member; không vẽ một `points_` dùng chung.

## 10. Bài tập tích hợp liên module — Judgment

So với Product struct trong C Module 02, compiler của class ngăn được kiểu sửa sai nào? Thiết kế chuyển điểm giữa hai account và nêu state phải giữ nếu người nhận hết hạn mức.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Class khác object ở chỗ nào?
2. this đổi ra sao giữa hai lời gọi?
3. Vì sao getter const không tự biến mọi alias thành const?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] phân biệt class với từng object cụ thể;
- [ ] dùng `private` để bảo vệ invariant;
- [ ] giải thích `this` trỏ đến object nào ở mỗi lời gọi;
- [ ] viết query member function có `const`;
- [ ] vẽ hai object với hai vùng state độc lập.

**Bài prerequisite:** [Reference, const và vòng đời object](./02-reference-const-va-vong-doi-doi-tuong.md)

**Bài tiếp theo:** [Constructor, destructor và bộ nhớ](./04-constructor-destructor-va-bo-nho.md)
