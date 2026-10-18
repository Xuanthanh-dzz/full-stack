# Abstract class và interface trong C++

> **Last verified:** 2026-09-22
>
> **Baseline:** C++20 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Abstract class có operation bắt buộc derived cung cấp; interface C++ là quy ước contract nhỏ.
- Dùng khi có nhiều implementation và mỗi caller chỉ cần một khả năng.
- Một object thực hiện hai interface vẫn có một state; nhiều kế thừa state cần cân nhắc riêng.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- khai báo pure virtual function bằng `= 0`;
- dùng abstract class làm contract không thể khởi tạo trực tiếp;
- mô hình hóa interface trong C++ bằng class thuần trừu tượng;
- triển khai nhiều interface bằng multiple inheritance có kiểm soát;
- gọi implementation qua reference đến interface.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một ví có thể thanh toán và hoàn tiền; tiền mặt khi giao chỉ cần thanh toán trong mô hình bài. Tách hai cửa phục vụ để caller không phải hỏi loại object hay gọi operation giả không hỗ trợ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| pure virtual | operation chưa có implementation bắt buộc cho concrete type | pay(...) = 0 |
| abstract class | class chưa thể tạo object trực tiếp vì còn pure virtual | PaymentMethod |
| interface | contract công khai nhỏ theo quy ước thiết kế | Refundable |
| capability | khả năng một object cung cấp | refund khác pay |

### Ví dụ nhỏ — tính tay trước

Ví có 100, pay(60) → 40; pay(50) bị từ chối giữ 40; refund(10) → 50. PaymentMethod& và Refundable& đều nhìn cùng số dư.

Checkout chấp nhận nhiều phương thức thanh toán. Một “phương thức thanh toán chung chung” không có cách xử lý mặc định hợp lý; mọi loại cụ thể bắt buộc phải cung cấp:

- tên hiển thị;
- operation `pay(amount)`.

Ví điện tử còn hỗ trợ hoàn tiền, nhưng thanh toán khi nhận hàng thì không. Ta cần hai contract độc lập để caller chỉ phụ thuộc đúng khả năng nó sử dụng.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```cpp
#include <iostream>
#include <string>

class PaymentMethod
{
public:
    virtual ~PaymentMethod() = default;

    virtual const std::string& name() const = 0;
    virtual bool pay(long long amount) = 0;
};

class Refundable
{
public:
    virtual ~Refundable() = default;

    virtual bool refund(long long amount) = 0;
};

class DigitalWallet final : public PaymentMethod, public Refundable
{
public:
    explicit DigitalWallet(const std::string& name)
        : name_{name}
    {
    }

    const std::string& name() const override
    {
        return name_;
    }

    bool pay(long long amount) override
    {
        if (amount <= 0 || amount > balance_)
        {
            return false;
        }

        balance_ -= amount;
        return true;
    }

    bool refund(long long amount) override
    {
        return top_up(amount);
    }

    bool top_up(long long amount)
    {
        constexpr long long max_balance = 1'000'000'000'000LL;
        // Trừ trước trong miền hợp lệ để không cộng rồi mới phát hiện overflow.
        if (amount <= 0 || amount > max_balance - balance_)
        {
            return false;
        }

        balance_ += amount;
        return true;
    }

    long long balance() const
    {
        return balance_;
    }

private:
    std::string name_;
    long long balance_ = 0;
};

class CashOnDelivery final : public PaymentMethod
{
public:
    const std::string& name() const override
    {
        return name_;
    }

    bool pay(long long amount) override
    {
        return amount > 0;
    }

private:
    std::string name_ = "Cash on delivery";
};

void checkout(PaymentMethod& method, long long amount)
{
    std::cout << method.name() << ": "
              << (method.pay(amount) ? "paid" : "rejected") << '\n';
}

int main()
{
    DigitalWallet wallet{"Team Wallet"};
    CashOnDelivery cash;

    if (!wallet.top_up(500000))
    {
        std::cerr << "Cannot fund wallet\n";
        return 1;
    }

    checkout(wallet, 320000);
    checkout(wallet, 250000);
    checkout(cash, 250000);

    Refundable& refundable = wallet;
    std::cout << "Refund 50000: "
              << (refundable.refund(50000) ? "accepted" : "rejected") << '\n';
    std::cout << "Wallet balance: " << wallet.balance() << " VND\n";

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o interfaces
./interfaces
```

Kết quả:

```text
Team Wallet: paid
Team Wallet: rejected
Cash on delivery: paid
Refund 50000: accepted
Wallet balance: 230000 VND
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

### Walkthrough — execution / state / cost

1. main dựng wallet và cash; top_up đưa số dư ví lên 500000.
2. checkout qua PaymentMethod& trừ 320000 thành 180000, từ chối 250000 tiếp theo.
3. CashOnDelivery demo chấp nhận amount dương; không thực hiện cổng thanh toán thật.
4. Refundable& gọi refund 50000 trên cùng wallet thành 230000. State thuộc wallet; virtual call và kiểm tra số cố định, không có request mạng.

### Mini-check

checkout chỉ nhận PaymentMethod& có gọi refund được không? Đây là thiếu chức năng hay giới hạn dependency có chủ đích?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Pure virtual function tạo abstract class

Declaration:

```cpp
virtual bool pay(long long amount) = 0;
```

là pure virtual function. Class còn ít nhất một pure virtual function là abstract và không thể tạo object trực tiếp:

```cpp
// PaymentMethod method; // lỗi compile
```

Derived class chỉ trở thành concrete khi override mọi pure virtual function còn thiếu.

### 4.2. Interface trong C++ là một quy ước thiết kế

C++ không có keyword `interface`. Một class thường được dùng như interface khi:

- chỉ công bố contract qua pure virtual function;
- không giữ state nghiệp vụ;
- có virtual destructor;
- không ép implementation kế thừa chi tiết không liên quan.

`PaymentMethod` và `Refundable` theo mẫu đó. Tên interface không bắt buộc bắt đầu bằng `I`; repository nên chọn một convention nhất quán.

### 4.3. Một object thực hiện nhiều contract

`DigitalWallet` kế thừa public từ hai interface:

```text
DigitalWallet object
├── PaymentMethod base subobject
├── Refundable base subobject
├── name_
└── balance_
```

Reference `PaymentMethod&` nhìn object qua contract thanh toán. Reference `Refundable&` nhìn cùng object qua contract hoàn tiền:

```text
PaymentMethod& ──┐
                 ├──> cùng DigitalWallet object
Refundable& ─────┘
```

Không có object wallet thứ hai và không copy state khi đổi góc nhìn.

### 4.4. Interface thu hẹp dependency

`checkout` chỉ biết `PaymentMethod&`, nên không gọi được `refund` hoặc đọc `balance`. Điều này là chủ đích: hàm chỉ phụ thuộc khả năng nó cần.

Cash on delivery không implements `Refundable`; compiler ngăn code coi nó là refundable. Contract trong type system thay cho một cờ runtime như `supports_refund`.

### 4.5. State thay đổi qua non-const interface

`pay` và `refund` sửa balance nên interface nhận qua reference không `const`. `name()` chỉ đọc và có `const`. `top_up` giữ invariant `0 <= balance_ <= 1000000000000` bằng cách kiểm tra trước phép cộng; `refund` tái sử dụng đúng operation tăng số dư đó.

Lifetime vẫn theo quy tắc reference đã học: `wallet` và `cash` phải sống cho đến khi `checkout` hoặc reference `refundable` dùng xong.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Concrete class | có implementation để tạo object | đơn giản khi chỉ một cách làm |
| Abstract base có state | chia sẻ contract và invariant thực sự chung | có coupling state; không ép lên mọi implementation |
| Interface nhỏ | công bố khả năng cần thiết | dễ ghép; thêm indirection, không tạo hàng chục interface không có caller |

### Misconception check

**Đúng hay sai?** C++ cần keyword interface mới viết được contract.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: class với pure virtual và destructor phù hợp là cách thông dụng.

</details>

**Đúng hay sai?** Hai interface reference tạo hai bản balance.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cùng một DigitalWallet, qua các base subobject khác nhau.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** pure virtual và lời gọi qua contract.

- **Working Developer — dùng khi làm việc:** tách capability theo caller.

- **Deep Dive — có thể quay lại sau:** multiple inheritance layout và destructor contract.

### Abstract base có thể có implementation

Một abstract class vẫn có thể có:

- constructor cho base state;
- data member;
- non-pure member function;
- thậm chí implementation cho pure virtual function trong một số trường hợp.

Khi mục tiêu là interface nhỏ, không state thường dễ ghép và dễ kiểm thử hơn. Khi nhiều derived type thật sự chia sẻ invariant/state, abstract base có implementation có thể hợp lý.

### Interface Segregation ở mức nhập môn

Tách `Refundable` khỏi `PaymentMethod` giúp class không hỗ trợ refund khỏi phải tạo implementation giả. Đây là trực giác của Interface Segregation Principle; module 06 sẽ học SOLID đầy đủ.

### Multiple inheritance nên giới hạn ở contract

Kế thừa nhiều class có state và implementation tạo ra layout, ambiguity và ownership phức tạp. Kế thừa nhiều interface nhỏ thường dễ kiểm soát hơn vì chúng biểu diễn các capability độc lập.

### Virtual destructor mặc định

```cpp
virtual ~PaymentMethod() = default;
```

vừa làm destructor virtual, vừa yêu cầu compiler sinh implementation mặc định. Interface không trực tiếp sở hữu tài nguyên nên không cần cleanup tùy chỉnh.

## 6. Lỗi thường gặp

### Quên virtual destructor trong interface

Nếu object sau này được sở hữu và hủy qua pointer interface, thiếu virtual destructor gây undefined behavior.

### Tạo implementation giả

Cho `CashOnDelivery::refund` luôn trả `false` chỉ để vừa một interface lớn khiến contract không trung thực. Tách capability thành interface riêng.

### Dùng `dynamic_cast` để hỏi loại liên tục

Nếu caller cứ kiểm tra concrete type rồi rẽ nhánh, đa hình chưa được sử dụng đúng. Đưa operation vào contract hoặc tách interface theo capability. `dynamic_cast` có trường hợp dùng hợp lệ nhưng không phải công cụ mặc định.

### Interface giữ mutable state chung không cần thiết

State làm các implementation bị coupling vào layout và lifecycle của base. Chỉ đưa state lên abstract base khi nó thật sự là invariant chung.

### Signature override không khớp

Thiếu `const`, sai kiểu parameter hoặc return type có thể làm derived vẫn abstract. Dùng `override` để compiler báo ngay.

## 7. Khi nào KHÔNG dùng

Không tạo interface cho mọi class ngay từ đầu. Không bắt lớp không hoàn tiền triển khai refund giả chỉ để đủ một interface lớn. Tách capability khi thật sự có caller và khác biệt nghiệp vụ.

## 8. Production notes & scale check

Demo không gửi tiền thật, không xử lý network/retry/idempotency. Với ví in-memory, test amount âm/0, sát hạn mức và giữ state khi từ chối. Những driver thanh toán thật cần contract bổ sung; không tuyên bố đa hình đã giải quyết giao dịch.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Thanh toán thẻ

Thêm `BankCard` implements `PaymentMethod`, từ chối amount vượt hạn mức.

**Gợi ý:** caller `checkout` không cần đổi.

### Bài 2 — Contract hủy giao dịch

Tạo interface `Cancellable` với operation `cancel()` và cho một phương thức phù hợp implements.

**Gợi ý:** interface chỉ chứa destructor virtual và pure virtual function.

### Bài 3 — Tách query số dư

Tạo interface `BalanceReadable` thay vì để caller phụ thuộc concrete `DigitalWallet`.

**Gợi ý:** operation chỉ đọc phải là `const`.

### Bài 4 — Sơ đồ object

Vẽ một `DigitalWallet` và hai base reference trỏ vào các base subobject tương ứng.

**Gợi ý:** vẫn chỉ có một state `balance_`.

## 10. Bài tập tích hợp liên module — Judgment

So với enum lựa chọn trong Module 02, khi thêm phương thức thanh toán cần sửa nơi nào ở hai cách thiết kế? Chọn theo số implementation, nhu cầu test và team nhỏ, không chấm theo số interface.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Điều gì khiến derived vẫn abstract?
2. Ai giữ wallet sống cho refundable?
3. Vì sao refund và top_up dùng cùng validation trong demo?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] khai báo và override pure virtual function;
- [ ] giải thích vì sao không tạo được object abstract class;
- [ ] mô hình hóa interface C++ không cần keyword riêng;
- [ ] tách capability thành interface nhỏ;
- [ ] chỉ ra hai interface reference vẫn nhìn cùng một concrete object.

**Bài prerequisite:** [Kế thừa và đa hình](./06-ke-thua-va-da-hinh.md)

**Bài tiếp theo:** [Template và generic programming](./08-template-va-generic-programming.md)
