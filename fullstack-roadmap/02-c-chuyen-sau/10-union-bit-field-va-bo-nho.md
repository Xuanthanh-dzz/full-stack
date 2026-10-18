# `union`, bit-field và bộ nhớ

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- union dùng chung storage cho các lựa chọn; tag cho biết lựa chọn nào đang có nghĩa.
- Dùng khi một giá trị chỉ ở một trong vài dạng, như giảm giá cố định hoặc phần trăm.
- Kích thước/layout không nên đoán; bit-field không phải định dạng file/network portable.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- dùng `union` khi một object chỉ cần giữ một trong nhiều dạng dữ liệu tại một thời điểm;
- ghép `enum` tag với `union` để biết member nào đang active;
- hiểu các member union dùng chung vùng lưu trữ;
- dùng bit-field cho cờ nội bộ có phạm vi nhỏ;
- biết vì sao không dùng layout union/bit-field thô làm file format hoặc network protocol.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một hộp có thể chứa phiếu “giảm 150 đồng” hoặc “giảm 20%”. Nhãn bên ngoài nói phải đọc phiếu theo cách nào. Nếu đổi nhãn mà không đổi nội dung tương ứng, người tính có thể dùng sai quy tắc.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| union | kiểu cho nhiều trường dùng chung storage | fixed_amount hoặc percent |
| tag | giá trị chỉ lựa chọn đang dùng | loại Adjustment |
| tagged union | union đi kèm tag và quy tắc nhất quán | hàm chỉ đọc nhánh được chọn |
| bit-field | trường số nguyên khai báo độ rộng theo bit | cờ sản phẩm |
| padding | phần đệm để đáp ứng layout/alignment | sizeof không chỉ là tổng kích thước nhìn thấy |

### Ví dụ nhỏ — tính tay trước

Giá 1000: tag FIXED, amount 150 → 850; tag PERCENT, percent 20 → 800. Không đọc cả hai trường rồi cộng hai giảm giá vì đây là lựa chọn loại trừ nhau.

Một điều chỉnh giá có đúng một trong hai dạng:

- giảm một số xu cố định;
- giảm theo phần trăm.

Nếu `struct` luôn chứa cả hai giá trị, một member sẽ không có ý nghĩa. Ta dùng `union` để chia sẻ vùng lưu trữ, nhưng phải kèm `enum` tag để code biết dữ liệu hiện tại thuộc dạng nào.

Sản phẩm còn có hai cờ boolean nội bộ: đang hoạt động và chịu thuế. Ta dùng bit-field để mô tả chúng, đồng thời giữ rõ giới hạn portability.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo `main.c`:

```c
#include <stdio.h>

typedef enum {
    ADJUST_FIXED,
    ADJUST_PERCENT
} AdjustmentKind;

typedef union {
    int fixed_cents;
    unsigned int percent;
} AdjustmentValue;

typedef struct {
    AdjustmentKind kind;
    AdjustmentValue value;
} Adjustment;

typedef struct {
    unsigned int active : 1;
    unsigned int taxable : 1;
    unsigned int reserved : 6;
} ProductFlags;

static int apply_adjustment(
    int unit_price,
    const Adjustment *adjustment,
    int *result
)
{
    if (unit_price < 0 || adjustment == NULL || result == NULL) {
        return 0;
    }

    /* The tag decides which union member is active and safe to read. */
    switch (adjustment->kind) {
        case ADJUST_FIXED:
            if (adjustment->value.fixed_cents < 0
                || adjustment->value.fixed_cents > unit_price) {
                return 0;
            }
            *result = unit_price - adjustment->value.fixed_cents;
            return 1;

        case ADJUST_PERCENT:
            if (adjustment->value.percent > 100U) {
                return 0;
            }
            {
                int kept_percent =
                    (int)(100U - adjustment->value.percent);
                int whole_hundreds = unit_price / 100;
                int remainder = unit_price % 100;
                *result = whole_hundreds * kept_percent
                    + remainder * kept_percent / 100;
            }
            return 1;
    }

    return 0;
}

int main(void)
{
    Adjustment fixed = {
        .kind = ADJUST_FIXED,
        .value.fixed_cents = 150
    };
    Adjustment percent = {
        .kind = ADJUST_PERCENT,
        .value.percent = 20U
    };
    ProductFlags flags = {
        .active = 1U,
        .taxable = 1U,
        .reserved = 0U
    };

    int fixed_result = 0;
    int percent_result = 0;

    if (!apply_adjustment(1000, &fixed, &fixed_result)
        || !apply_adjustment(1000, &percent, &percent_result)) {
        fprintf(stderr, "Dieu chinh khong hop le\n");
        return 1;
    }

    printf("Gia sau giam co dinh: %d xu\n", fixed_result);
    printf("Gia sau giam phan tram: %d xu\n", percent_result);
    printf(
        "Trang thai: active=%u taxable=%u\n",
        (unsigned int)flags.active,
        (unsigned int)flags.taxable
    );
    return 0;
}
```

Build và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o union-bit-field
./union-bit-field
```

Output:

```text
Gia sau giam co dinh: 850 xu
Gia sau giam phan tram: 800 xu
Trang thai: active=1 taxable=1
```

### Walkthrough — execution / state / cost

1. main tạo hai Adjustment với tag và thành viên union tương ứng.
2. Hàm tính kiểm tra tag rồi chỉ xử lý nhánh đã chọn; percent ngoài 0..100 bị từ chối.
3. Kết quả 850 và 800 được ghi ra output; cờ bit-field được đọc riêng để in 1, 1.
4. Mọi object mẫu ở caller; không cấp phát động. Tính giá cost cố định, storage/layout do implementation quyết định nên không có output sizeof cố định.

### Mini-check

Nếu percent = 101, có nên clamp âm thầm hay báo lỗi theo contract mẫu? Output cũ có cần giữ nguyên không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### `struct` và `union` bố trí member khác nhau

Với `struct`, các member có vùng lưu trữ riêng, có thể xen padding:

```text
struct: [ member A ][ padding? ][ member B ]
```

Với `union`, mọi member bắt đầu tại cùng một vùng lưu trữ:

```text
AdjustmentValue
┌──────────────────────────────┐
│ fixed_cents                  │
│ percent       (cùng bắt đầu) │
└──────────────────────────────┘
```

Union đủ lớn và đủ alignment để chứa member lớn nhất, nhưng tại một thời điểm chương trình phải theo dõi member nào chứa giá trị có ý nghĩa.

### Active member

Khởi tạo:

```c
Adjustment fixed = {
    .kind = ADJUST_FIXED,
    .value.fixed_cents = 150
};
```

ghi member `fixed_cents`. Đây là active member của `fixed.value`. Hàm thấy tag `ADJUST_FIXED` rồi đọc đúng `fixed_cents`.

Với object `percent`, active member là `percent` và tag là `ADJUST_PERCENT`.

```text
fixed:
kind = ADJUST_FIXED
value bytes đang biểu diễn fixed_cents = 150

percent:
kind = ADJUST_PERCENT
value bytes đang biểu diễn percent = 20
```

Tag và active member phải luôn được cập nhật cùng nhau.

Nhánh phần trăm chia `unit_price` thành nhóm trăm và phần dư trước khi nhân. Mỗi tích trung gian không lớn hơn miền `int`, nên validation không vô tình tạo signed overflow với giá lớn.

### Tagged union

Một union đứng riêng không tự ghi “member nào active”. `Adjustment` dùng `kind` làm tag:

```c
typedef struct {
    AdjustmentKind kind;
    AdjustmentValue value;
} Adjustment;
```

`switch` theo tag trước khi đọc union là pattern cốt lõi. Nhánh mặc định sau `switch` từ chối tag không hợp lệ.

### Bit-field

```c
unsigned int active : 1;
```

khai báo member có độ rộng một bit trong đơn vị lưu trữ do implementation bố trí. Giá trị hợp lệ theo ý nghĩa ứng dụng là `0` hoặc `1`.

Bit-field phù hợp cho một nhóm cờ nội bộ khi layout chính xác không đi qua ranh giới process/file/network. Code truy cập bằng `flags.active` như member thường, nhưng không thể lấy địa chỉ bit-field bằng `&flags.active`.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| struct hai trường | giữ đồng thời cả hai giá trị | đơn giản nếu cả hai cùng có nghĩa; tốn storage cho cả hai |
| tagged union | một lựa chọn có nghĩa tại một thời điểm | cần giữ tag/content nhất quán; phù hợp dữ liệu nhiều dạng |
| bit mask tường minh | quy định vị trí bit bằng phép toán | hợp format trao đổi đã đặc tả; không thay bằng layout bit-field compiler |

### Misconception check

**Đúng hay sai?** sizeof(union) luôn đúng bằng thành viên lớn nhất.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Không được giả định bằng tuyệt đối: cần tính cả yêu cầu alignment/padding.

</details>

**Đúng hay sai?** Bit-field của mọi compiler có cùng thứ tự bit trong file.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: layout phụ thuộc implementation; cần định dạng tuần tự hóa tường minh.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** đọc đúng nhánh tag.

- **Working Developer — dùng khi làm việc:** validate tag/payload trước tính.

- **Deep Dive — có thể quay lại sau:** alignment và format byte độc lập compiler.

### Khi nào dùng `union`

Dùng khi các dạng dữ liệu loại trừ lẫn nhau và tiết kiệm representation có ý nghĩa, chẳng hạn:

- token parser mang số hoặc chuỗi;
- event mang payload theo loại;
- message nội bộ có nhiều variant.

Nếu mọi member đều cần tồn tại đồng thời, dùng `struct`.

### Invariant của tagged union

Invariant là điều phải luôn đúng:

```text
kind == ADJUST_FIXED   => active member là value.fixed_cents
kind == ADJUST_PERCENT => active member là value.percent
```

Tạo hàm khởi tạo riêng có thể giúp duy trì invariant khi code lớn. Không cho caller tùy ý sửa tag mà quên payload.

### Bit mask là lựa chọn khác

Khi cần layout byte rõ và thao tác protocol, thường dùng số nguyên có độ rộng xác định cùng bit mask, rồi encode/decode tường minh. Bit-field tiện cho member nội bộ nhưng thứ tự bit và packing phụ thuộc implementation.

### Alignment và padding

`sizeof(AdjustmentValue)` ít nhất đủ cho member lớn nhất, có thể chịu yêu cầu alignment. `sizeof(Adjustment)` có thể lớn hơn `sizeof(kind) + sizeof(value)` do padding.

Không dùng phép cộng kích thước thủ công để cấp phát `struct`; dùng `sizeof(Adjustment)` hoặc `sizeof *pointer`.

### Đào sâu (có thể quay lại sau)

Thứ tự cấp phát bit-field trong storage unit, việc một bit-field có vượt qua ranh giới unit hay không, và padding đều implementation-defined. Endianness cũng ảnh hưởng cách byte/bit được quan sát bên ngoài. Vì vậy dump raw object không tạo ra format portable.

Đọc member union khác active member có quy tắc tinh tế và dễ phụ thuộc implementation. Kỹ thuật “type punning” bằng union không cần cho mục tiêu bài này. Trong production portable, hãy chuyển đổi giá trị rõ ràng hoặc dùng `memcpy` với representation đã được quy định; tuyệt đối không dựa vào nó chỉ vì một compiler cho kết quả mong muốn.

## 6. Lỗi thường gặp

### Đọc member không khớp tag

Nếu tag là `ADJUST_FIXED` nhưng code đọc `value.percent`, kết quả không còn mang ý nghĩa đã ghi. Dùng một `switch` duy nhất theo tag và giữ invariant.

### Sửa tag mà không sửa payload

```c
adjustment.kind = ADJUST_PERCENT;
```

không tự chuyển `fixed_cents` thành phần trăm. Cần ghi payload mới cùng thao tác chuyển loại.

### Dùng bit-field làm protocol

Hai compiler/ABI có thể bố trí bit khác nhau. Serialize từng field thành format đã định nghĩa thay vì ghi raw `ProductFlags`.

### Lấy địa chỉ bit-field

Bit-field không nhất thiết có địa chỉ byte riêng, nên `&flags.active` không hợp lệ. Nếu API cần pointer tới cờ, dùng object số nguyên thông thường.

### Bỏ validation vì tag là `enum`

Tag vẫn có thể mang giá trị lạ từ file/input hoặc memory corruption. Có nhánh từ chối rõ ràng.

## 7. Khi nào KHÔNG dùng

Không dùng union để tiết kiệm vài byte nếu hai trường thực sự cần sống đồng thời. Không ghi thẳng bit-field ra network để làm protocol portable; định nghĩa byte/bit rõ ràng đơn giản hơn debug khác compiler.

## 8. Production notes & scale check

Ở kho nhỏ, tagged union làm rõ nghiệp vụ hơn tối ưu byte. Validate tag và payload tại đầu vào; test unknown tag, 0%, 100%, >100% và giá sát giới hạn. Đo sizeof trên baseline chỉ là quan sát của compiler đó, không thành cam kết chung.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Giá trị số hoặc text

Thiết kế tagged union lưu một `int` hoặc một mảng `char` cố định.

**Gợi ý:** enum tag phải được kiểm tra trước khi in active member.

### Bài 2 — Sự kiện kho

Tạo event `ITEM_ADDED` mang số lượng và `ITEM_RENAMED` mang tên mới.

**Gợi ý:** viết hai hàm khởi tạo để tag/payload không lệch nhau.

### Bài 3 — Cờ sản phẩm

Thêm cờ `featured` và `discontinued` bằng bit-field, rồi in từng cờ.

**Gợi ý:** vẫn dùng `unsigned int` và độ rộng `1`.

### Bài 4 — So sánh representation

In `sizeof` của union, struct chứa hai member riêng và tagged union trên máy bạn; giải thích kết quả mà không coi nó là hằng số portable.

**Gợi ý:** compiler có thể thêm padding vì alignment.

## 10. Bài tập tích hợp liên module — Judgment

So với enum trạng thái bài 09, Adjustment cần thêm dữ liệu theo loại. Chọn struct hai trường hay tagged union cho yêu cầu “mỗi đơn chỉ được một cách giảm”; nêu invariant và một test phá invariant.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Tag bảo vệ cách đọc union thế nào?
2. Vì sao layout memory khác format file?
3. Giảm 100% trên giá lớn cần tránh tràn ở bước nào?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt vùng lưu trữ member của `struct` và `union`.
- [ ] Tôi luôn ghép union nhiều dạng với tag rõ ràng.
- [ ] Tôi chỉ đọc member khớp tag.
- [ ] Tôi không dùng raw bit-field layout làm file/protocol.
- [ ] Tôi không giả định `sizeof` bằng tổng member.

**Bài prerequisite:** [Struct, enum và typedef](./09-struct-enum-typedef.md)

**Bài tiếp theo:** [File I/O](./11-file-io.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/02-alias-sau-free.md) · [Spaced Review](./reviews/review-02-lifetime-va-ownership.md).
