# Địa chỉ bộ nhớ và con trỏ

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · GCC/Clang với -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Con trỏ giữ địa chỉ của một object; đọc con trỏ khác với đọc giá trị tại địa chỉ đó.
- Dùng khi cần truy cập cùng một object qua tên khác hoặc chuyển địa chỉ cho hàm.
- Địa chỉ chỉ dùng được khi object còn sống và thao tác phù hợp kiểu, quyền ghi.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- phân biệt **giá trị của biến** với **địa chỉ của biến**;
- dùng toán tử `&` để lấy địa chỉ và khai báo pointer bằng `*`;
- dùng toán tử dereference `*` để đọc hoặc sửa object mà pointer đang trỏ tới;
- vẽ được quan hệ giữa một biến `int` và một pointer trỏ tới biến đó;
- nhận ra điều kiện tối thiểu trước khi dereference: pointer phải trỏ tới một object còn sống và đúng kiểu.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Biến thường giữ món đồ; con trỏ giống tờ giấy ghi vị trí món đồ. Sao chép tờ giấy không nhân đôi món đồ. Khi sửa món đồ theo địa chỉ, người nhìn qua tên ban đầu cũng thấy thay đổi.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| object | vùng lưu một giá trị trong chương trình C | quantity giữ số lượng |
| địa chỉ | vị trí dùng để truy cập object | &quantity |
| pointer — con trỏ | giá trị chỉ tới object hoặc hàm, hoặc giá trị rỗng | quantity_pointer |
| dereference | truy cập object mà con trỏ chỉ tới | *quantity_pointer |

### Ví dụ nhỏ — tính tay trước

Gọi vị trí của x là A: x = 10 → p = &x nghĩa là p giữ A → *p = 20 làm x thành 20. A là ký hiệu để trace, không phải địa chỉ để chép vào code.

Chương trình quản lý kho có biến `quantity`. Một hàm ở phần khác của chương trình cần giữ vị trí của chính biến này để sửa nó, thay vì chỉ nhận một bản sao giá trị.

Ở module trước, bạn đã biết tham số của hàm C được truyền bằng giá trị. Trước khi đưa địa chỉ qua hàm ở bài sau, ta cần trả lời chính xác:

1. `quantity` đang chứa gì?
2. `&quantity` là gì?
3. Một biến pointer chứa gì?
4. Khi viết `*pointer`, chương trình truy cập vùng nhớ nào?

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `main.c`:

```c
#include <stdio.h>

int main(void)
{
    int quantity = 12;
    int *quantity_pointer = &quantity;

    /* The pointer stores quantity's address, not a second quantity value. */
    printf("So luong ban dau: %d\n", quantity);
    printf("Gia tri doc qua pointer: %d\n", *quantity_pointer);
    printf(
        "Pointer co tro dung quantity: %s\n",
        quantity_pointer == &quantity ? "co" : "khong"
    );

    *quantity_pointer = 9;

    printf("So luong sau khi sua: %d\n", quantity);
    return 0;
}
```

Build và chạy bằng C11:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror main.c -o pointer-address
./pointer-address
```

Output:

```text
So luong ban dau: 12
Gia tri doc qua pointer: 12
Pointer co tro dung quantity: co
So luong sau khi sua: 9
```

Chương trình cố ý không in con số địa chỉ thật vì địa chỉ có thể khác ở mỗi lần chạy.

### Walkthrough — execution / state / cost

1. main tạo quantity = 12 và quantity_pointer trỏ tới quantity; đây là hai object khác nhau.
2. Hai lần đọc quantity và *quantity_pointer cùng cho 12; phép so sánh địa chỉ cho biết đang chỉ đúng object.
3. *quantity_pointer = 9 ghi vào quantity; bản thân giá trị con trỏ không đổi.
4. Chương trình chạy trong một process; hai object cục bộ hết vòng đời khi main kết thúc. Sample không cấp phát động; lượng state cố định, chi phí quan sát chủ yếu là printf.

### Mini-check

Có mấy object kiểu int sau int x = 10; int *p = &x;? Nếu sửa x, đọc *p thấy gì?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Bước 1: tạo object `quantity`

```c
int quantity = 12;
```

Trong lần gọi `main`, chương trình tạo một object kiểu `int` có tên `quantity`. Object có automatic storage duration. Stack frame là mô hình triển khai phổ biến để trace, không phải vị trí vật lý bắt buộc của chuẩn C; compiler có thể dùng register hoặc tối ưu storage nếu vẫn giữ hành vi chương trình.

Ta dùng địa chỉ minh họa, không phải địa chỉ thật:

```text
Stack frame của main

địa chỉ 0x1000
┌─────────────────────┐
│ quantity (int) = 12 │
└─────────────────────┘
```

### Bước 2: lấy địa chỉ bằng `&`

Biểu thức `&quantity` cho ra địa chỉ của object `quantity`. Kiểu của biểu thức đó là `int *`, đọc là “pointer tới `int`”.

```c
int *quantity_pointer = &quantity;
```

Dòng này tạo thêm một object tên `quantity_pointer`. Object pointer không chứa số lượng `12`; nó chứa địa chỉ của `quantity`.

```text
Stack frame của main

0x1000                         0x1010
┌─────────────────────┐       ┌──────────────────────────┐
│ quantity (int) = 12 │◄──────│ quantity_pointer = 0x1000│
└─────────────────────┘       └──────────────────────────┘
              object được trỏ tới        object pointer
```

Hai object có vùng nhớ riêng. Việc pointer chứa địa chỉ của `quantity` không làm `quantity` chuyển vào bên trong pointer.

### Bước 3: dereference bằng `*`

Trong biểu thức `*quantity_pointer`, toán tử `*` yêu cầu chương trình:

1. đọc địa chỉ đang lưu trong `quantity_pointer`;
2. tới vùng nhớ tại địa chỉ đó;
3. xem vùng nhớ như một object `int`.

Vì vậy:

```c
*quantity_pointer = 9;
```

không đổi địa chỉ chứa trong pointer. Nó sửa object `quantity` tại địa chỉ mà pointer đang giữ.

```text
Trước: quantity_pointer ──► quantity = 12
Sau:   quantity_pointer ──► quantity = 9
```

### Điều kiện an toàn

Chỉ dereference khi pointer:

- đang giữ địa chỉ hợp lệ;
- trỏ đúng loại object mà kiểu pointer mô tả;
- object đó vẫn còn trong lifetime;
- phép truy cập nằm trong phạm vi object.

Các bài tiếp theo sẽ làm rõ từng điều kiện. Ở bài này, `quantity` còn sống đến cuối `main`, nên `quantity_pointer` hợp lệ trong toàn bộ đoạn code sau khai báo.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| quantity | giá trị số lượng | đọc/ghi trực tiếp; dùng khi đã có tên object |
| &quantity | địa chỉ của số lượng | không sao chép số lượng; dùng để truyền vị trí |
| *quantity_pointer | object được chỉ tới | cần địa chỉ hợp lệ; không dùng pointer chưa khởi tạo |

### Misconception check

**Đúng hay sai?** Sửa *p sẽ sửa giá trị địa chỉ trong p.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sửa object được chỉ tới; gán p mới đổi con trỏ.

</details>

**Đúng hay sai?** Địa chỉ giống nhau giữa hai lần chạy là điều chương trình cần dựa vào.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: trace dùng quan hệ giữa object; địa chỉ thực có thể thay đổi.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** đọc được & và * trong ví dụ.

- **Working Developer — dùng khi làm việc:** kiểm tra object còn sống và quyền ghi.

- **Deep Dive — có thể quay lại sau:** phân biệt mô hình địa chỉ với vị trí vật lý do compiler quyết định.

### Object, giá trị và địa chỉ

Trong C, **object** là một vùng lưu trữ có kích thước, kiểu và lifetime. Biến là tên mà source code dùng để truy cập một object.

- `quantity` trong biểu thức đọc giá trị `12`.
- `&quantity` lấy địa chỉ của object.
- `quantity_pointer` đọc địa chỉ đang chứa trong object pointer.
- `*quantity_pointer` truy cập object ở địa chỉ đó.

### Dấu `*` có hai vai trò

Trong khai báo:

```c
int *quantity_pointer;
```

`*` cho biết `quantity_pointer` có kiểu “pointer tới `int`”.

Trong biểu thức:

```c
*quantity_pointer
```

`*` là toán tử dereference. Hai cách dùng liên quan nhau nhưng xuất hiện trong hai ngữ cảnh khác nhau.

### In địa chỉ khi debug

Nếu cần quan sát địa chỉ, `%p` của `printf` yêu cầu đối số kiểu `void *`:

```c
printf("%p\n", (void *)&quantity);
printf("%p\n", (void *)quantity_pointer);
```

Hai dòng sẽ in cùng một địa chỉ trong ví dụ này, nhưng chuỗi địa chỉ cụ thể phụ thuộc lần chạy và hệ thống. Cast sang `void *` là cách truyền đối số đúng cho `%p`.

### Một pointer chỉ trỏ tới một địa chỉ tại một thời điểm

Pointer có thể được gán lại:

```c
int first = 10;
int second = 20;
int *selected = &first;

selected = &second;
```

Sau dòng cuối, `selected` trỏ tới `second`; `first` vẫn tồn tại và giữ giá trị `10`.

## 6. Lỗi thường gặp

### Nhầm giá trị với địa chỉ

Sai:

```c
int quantity = 12;
int *pointer = quantity;
```

`quantity` là `int`, không phải địa chỉ của `int`. Phải dùng:

```c
int *pointer = &quantity;
```

### Quên dereference khi muốn sửa object đích

```c
pointer = &other_quantity;
```

Dòng trên đổi nơi pointer trỏ tới. Nó không sửa `quantity`.

```c
*pointer = 9;
```

Dòng này mới sửa object đang được trỏ tới.

### Dereference pointer chưa được khởi tạo

Đoạn sau có undefined behavior và **không được chạy**:

```c
int *pointer;
*pointer = 9;
```

Pointer chưa có địa chỉ hợp lệ. Khi chưa có object đích, khởi tạo pointer bằng `NULL`; bài sau sẽ giải thích cách kiểm tra `NULL`.

### Cho rằng địa chỉ luôn giống nhau

Không ghi cứng địa chỉ lấy từ một lần debug vào code hoặc bài kiểm thử. Hệ điều hành, compiler và mỗi lần chạy có thể bố trí địa chỉ khác nhau.

## 7. Khi nào KHÔNG dùng

Không thêm con trỏ chỉ để tính một tổng cục bộ đã có đủ giá trị. Một biến và phép cộng rõ hơn. Không giữ địa chỉ biến cục bộ để dùng sau khi hàm tạo nó kết thúc.

## 8. Production notes & scale check

Ở demo một số lượng, chi phí thêm là lưu một con trỏ, không phải nhân đôi dữ liệu. Trong code team nhỏ, ghi rõ hàm được đọc hay được ghi object và ai giữ nó sống. Debug quan hệ p == &quantity và giá trị trước/sau; không dùng con số địa chỉ cố định làm assertion.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Đọc qua pointer

Tạo biến `temperature = 28`, pointer trỏ tới biến đó, rồi in giá trị trực tiếp và qua pointer.

**Gợi ý:** so sánh `temperature` với `*temperature_pointer`.

### Bài 2 — Sửa qua pointer

Tạo `score = 70`, dùng pointer cộng thêm `5`, rồi in `score`.

**Gợi ý:** vế trái phép gán cần là `*score_pointer`.

### Bài 3 — Đổi object đích

Tạo hai biến `morning_stock` và `evening_stock`. Cho một pointer lần lượt trỏ tới từng biến và giảm mỗi biến một đơn vị.

**Gợi ý:** vẽ lại mũi tên sau mỗi phép gán pointer.

### Bài 4 — Quan sát địa chỉ

In `&value` và pointer đang trỏ tới `value` bằng `%p`; kiểm tra chúng giống nhau.

**Gợi ý:** cast cả hai đối số sang `void *`. Không kiểm tra một chuỗi địa chỉ cố định.

## 10. Bài tập tích hợp liên module — Judgment

Liên hệ scope Module 01: một hàm muốn trả về địa chỉ điểm trung bình cục bộ cho caller. Vẽ vòng đời trước/sau return; chọn trả giá trị hay trả địa chỉ và giải thích, chưa cần cấp phát động.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ x, p và mũi tên khi x = 7.
2. Phân biệt p = &y và *p = y.
3. Vì sao output không cần in địa chỉ thật?

<a id="8-checklist-tu-anh-gia-va-lien-ket"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt được giá trị của `quantity`, địa chỉ `&quantity` và giá trị `*quantity_pointer`.
- [ ] Tôi vẽ được hai object riêng: object `int` và object pointer.
- [ ] Tôi giải thích được dòng `*quantity_pointer = 9`.
- [ ] Tôi không dereference pointer chưa có địa chỉ hợp lệ.
- [ ] Tôi biết địa chỉ thật có thể đổi giữa các lần chạy.

**Bài prerequisite:** [Dự án console quản lý điểm](../01-nen-tang-lap-trinh/15-du-an-console-quan-ly-diem.md)

**Bài tiếp theo:** [Con trỏ và biến](./02-con-tro-va-bien.md)
