# Địa chỉ bộ nhớ và con trỏ

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- phân biệt **giá trị của biến** với **địa chỉ của biến**;
- dùng toán tử `&` để lấy địa chỉ và khai báo pointer bằng `*`;
- dùng toán tử dereference `*` để đọc hoặc sửa object mà pointer đang trỏ tới;
- vẽ được quan hệ giữa một biến `int` và một pointer trỏ tới biến đó;
- nhận ra điều kiện tối thiểu trước khi dereference: pointer phải trỏ tới một object còn sống và đúng kiểu.

## 2. Bài toán mở đầu

Chương trình quản lý kho có biến `quantity`. Một hàm ở phần khác của chương trình cần giữ vị trí của chính biến này để sửa nó, thay vì chỉ nhận một bản sao giá trị.

Ở module trước, bạn đã biết tham số của hàm C được truyền bằng giá trị. Trước khi đưa địa chỉ qua hàm ở bài sau, ta cần trả lời chính xác:

1. `quantity` đang chứa gì?
2. `&quantity` là gì?
3. Một biến pointer chứa gì?
4. Khi viết `*pointer`, chương trình truy cập vùng nhớ nào?

## 3. Lời giải bằng code

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

## 4. Giải thích cơ chế

### Bước 1: tạo object `quantity`

```c
int quantity = 12;
```

Trong lần gọi `main`, chương trình tạo một object kiểu `int` có tên `quantity`. Với biến cục bộ thông thường như ví dụ này, object nằm trong stack frame của `main`.

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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và liên kết

- [ ] Tôi phân biệt được giá trị của `quantity`, địa chỉ `&quantity` và giá trị `*quantity_pointer`.
- [ ] Tôi vẽ được hai object riêng: object `int` và object pointer.
- [ ] Tôi giải thích được dòng `*quantity_pointer = 9`.
- [ ] Tôi không dereference pointer chưa có địa chỉ hợp lệ.
- [ ] Tôi biết địa chỉ thật có thể đổi giữa các lần chạy.

**Bài prerequisite:** [Dự án console quản lý điểm](../01-nen-tang-lap-trinh/15-du-an-console-quan-ly-diem.md)

**Bài tiếp theo:** [Con trỏ và biến](./02-con-tro-va-bien.md)
