# Kế thừa và đa hình

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tạo derived class từ base class bằng public inheritance;
- override virtual function đúng cách;
- gọi hành vi đa hình qua base reference;
- mô tả base subobject nằm trong derived object;
- tránh object slicing và thiếu virtual destructor.

## 2. Bài toán mở đầu

Hệ thống giao hàng có hai cách tính phí:

- giao tiêu chuẩn: `30000` VND, miễn phí từ `500000` VND;
- giao hỏa tốc: luôn `60000` VND.

Code in hóa đơn không nên có chuỗi `if` kiểm tra từng loại giao hàng. Nó chỉ cần yêu cầu “hãy tính phí cho subtotal này”, còn mỗi loại tự thực hiện quy tắc của mình.

Ta sẽ bắt đầu bằng một base class có implementation mặc định. Pure virtual function và interface được dành cho bài tiếp theo.

## 3. Lời giải bằng code

```cpp
#include <iostream>
#include <string>

class Delivery
{
public:
    explicit Delivery(const std::string& name)
        : name_{name}
    {
    }

    virtual ~Delivery() = default;

    const std::string& name() const
    {
        return name_;
    }

    virtual long long fee(long long subtotal) const
    {
        return subtotal >= 500000 ? 0 : 30000;
    }

private:
    std::string name_;
};

class ExpressDelivery final : public Delivery
{
public:
    ExpressDelivery()
        : Delivery{"Express"}
    {
    }

    long long fee(long long subtotal) const override
    {
        // Signature phải giữ subtotal để override dù chính sách này không dùng.
        static_cast<void>(subtotal);
        return 60000;
    }
};

void print_quote(const Delivery& delivery, long long subtotal)
{
    std::cout << delivery.name()
              << " for " << subtotal
              << ": " << delivery.fee(subtotal) << " VND\n";
}

int main()
{
    Delivery standard{"Standard"};
    ExpressDelivery express;

    print_quote(standard, 400000);
    print_quote(standard, 600000);
    print_quote(express, 600000);

    return 0;
}
```

Biên dịch và chạy:

```bash
c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror main.cpp -o polymorphism
./polymorphism
```

Kết quả:

```text
Standard for 400000: 30000 VND
Standard for 600000: 0 VND
Express for 600000: 60000 VND
```

Mẫu đã được kiểm tra bằng `g++ 15.2.0` ở chế độ C++20.

## 4. Giải thích cơ chế

### 4.1. Public inheritance biểu diễn quan hệ “là một”

```cpp
class ExpressDelivery final : public Delivery
```

nói `ExpressDelivery` là một `Delivery` theo public interface. Vì vậy reference `const Delivery&` có thể gắn với object `ExpressDelivery`.

Không dùng inheritance chỉ để tái sử dụng vài dòng code. Quan hệ phải giữ đúng contract: nơi nào cần `Delivery`, object derived phải hoạt động hợp lệ.

### 4.2. Derived object chứa base subobject

`express` là một automatic object duy nhất, bên trong có base subobject. Sơ đồ dùng stack frame là mô hình triển khai phổ biến, không phải layout vật lý do chuẩn bắt buộc:

```text
stack frame main (mô hình triển khai phổ biến)
└── express: ExpressDelivery object
    └── Delivery base subobject
        └── name_ = "Express"
```

Constructor base chạy trước constructor derived. `ExpressDelivery()` gọi rõ:

```cpp
Delivery{"Express"}
```

để khởi tạo base subobject. Khi hủy, thứ tự ngược lại: phần derived bị hủy trước, base subobject bị hủy sau.

### 4.3. Dynamic dispatch

Trong:

```cpp
void print_quote(const Delivery& delivery, long long subtotal)
```

parameter có kiểu tĩnh là `const Delivery&`. Khi caller truyền `express`, reference trỏ đến base subobject nằm trong `ExpressDelivery`, nhưng object hoàn chỉnh vẫn có kiểu động `ExpressDelivery`.

Vì `fee` là `virtual`, lời gọi:

```cpp
delivery.fee(subtotal)
```

chọn implementation theo kiểu động:

```text
delivery trỏ Delivery object         -> Delivery::fee
delivery trỏ base part của Express   -> ExpressDelivery::fee
```

`name()` không virtual vì mọi loại dùng chung implementation và state ở base.

### 4.4. `override` và `final`

`override` yêu cầu compiler xác nhận member function thực sự override một virtual function của base. Nếu viết sai parameter hoặc thiếu `const`, build thất bại thay vì âm thầm tạo function khác.

`final` trên class nói không cho class khác kế thừa tiếp từ `ExpressDelivery`. Chỉ dùng khi đây là quyết định thiết kế thật, không thêm máy móc.

### 4.5. Vì sao base destructor phải `virtual`?

Các object trong primary sample có automatic storage duration, nhưng `Delivery` là polymorphic base. Nếu sau này một `Delivery*` sở hữu địa chỉ của derived object cấp phát động và code gọi `delete delivery`, base destructor phải virtual để destructor derived chạy đúng. Quy tắc an toàn: base class dùng đa hình và cho phép xóa qua base phải có public virtual destructor, hoặc phải cấm việc xóa đó bằng thiết kế khác. [Bài 12](./12-smart-pointer-va-quyen-so-huu.md) sẽ thay owning raw pointer bằng smart pointer; đoạn này chỉ giải thích contract destructor.

## 5. Kiến thức nền

### Static type và dynamic type

- **Static type** được compiler biết từ declaration, ví dụ `const Delivery&`.
- **Dynamic type** là loại object thật đang được tham chiếu lúc chạy, ví dụ `ExpressDelivery`.
- Chỉ virtual dispatch dựa trên dynamic type; non-virtual call dựa trên static type.

### `static_cast<void>(subtotal)`

Implementation hỏa tốc không cần `subtotal`, nhưng parameter phải giữ cùng signature để override. Dòng cast sang `void` biểu thị có chủ đích rằng parameter không dùng và giữ build sạch với warning nghiêm ngặt.

### Composition hay inheritance?

Chọn inheritance khi caller thực sự cần thay thế các implementation qua cùng contract. Chọn composition khi một object chỉ “có một” component để ủy quyền công việc. Module 06 sẽ phân tích sâu coupling, cohesion và thiết kế OOP; ở đây chỉ dùng inheritance cho đúng bài toán đa hình.

### Đào sâu (có thể quay lại sau)

Chuẩn C++ quy định hành vi virtual dispatch nhưng không bắt buộc cách triển khai. Compiler phổ biến đặt một pointer ẩn trong polymorphic object, thường gọi là `vptr`, trỏ đến bảng function thường gọi là `vtable`.

```text
ExpressDelivery object (một cách triển khai phổ biến)
├── vptr ──> bảng có ExpressDelivery::fee
└── Delivery::name_
```

Đây là chi tiết ABI, không nên viết code phụ thuộc kích thước hay layout cụ thể. Chi phí thường gồm một indirection cho virtual call và dữ liệu quản lý dispatch trong object, nhưng compiler có thể *devirtualize* khi biết chính xác dynamic type.

## 6. Lỗi thường gặp

### Quên `virtual` ở base

Nếu `Delivery::fee` không virtual, lời gọi qua `Delivery&` luôn chọn implementation base dù object thật là derived.

### Quên `override`

Code vẫn có thể build nhưng một lỗi nhỏ trong signature làm function không override. Luôn dùng `override` khi có ý định override.

### Object slicing

```cpp
Delivery sliced = express;
```

chỉ copy base subobject vào một `Delivery` mới; phần derived bị “cắt”. Dynamic type của `sliced` là `Delivery`, nên mất hành vi hỏa tốc. Truyền đa hình qua reference hoặc pointer.

### Base destructor không virtual

Xóa derived object cấp phát động qua base pointer khi base destructor không virtual gây undefined behavior. Đừng chờ đến lúc thêm dynamic allocation mới sửa contract base.

### Public inheritance chỉ để lấy code dùng chung

Nếu derived không thay thế base đúng nghĩa, hierarchy sẽ vi phạm contract. Cân nhắc member object và ủy quyền.

### Gọi virtual function trong constructor/destructor

Trong quá trình base constructor/destructor chạy, phần derived chưa tồn tại hoặc đã bị hủy. Virtual call không dispatch như khi object hoàn chỉnh. Tránh thiết kế dựa vào virtual call ở đây.

## 7. Bài tập

### Bài 1 — Giao trong ngày

Thêm `SameDayDelivery` có phí `90000` VND và in qua `print_quote`.

**Gợi ý:** kế thừa public, gọi constructor base và dùng `override`.

### Bài 2 — Phụ phí đơn nhỏ

Sửa express để phí là `70000` khi subtotal dưới `200000`, còn lại `60000`.

**Gợi ý:** chỉ thay implementation derived; `print_quote` không đổi.

### Bài 3 — Quan sát slicing

Tạo một bản `Delivery sliced = express`, in phí và giải thích kết quả.

**Gợi ý:** vẽ object mới chỉ có base subobject.

### Bài 4 — Composition

Thiết kế `Checkout` chứa reference đến `Delivery` và dùng nó để tính tổng.

**Gợi ý:** account lifetime: `Delivery` phải sống lâu hơn `Checkout` nếu lưu reference.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể:

- [ ] vẽ base subobject bên trong derived object;
- [ ] giải thích static type và dynamic type;
- [ ] dùng `virtual`/`override` đúng;
- [ ] nhận ra object slicing;
- [ ] giải thích vai trò virtual destructor.

**Bài prerequisite:** [Copy, move và Rule of Zero/Five](./05-copy-move-rule-of-zero-five.md)

**Bài tiếp theo:** [Abstract class và interface trong C++](./07-abstract-class-va-interface-trong-cpp.md)
