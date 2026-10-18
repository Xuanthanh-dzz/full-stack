# Điều kiện với if và switch

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- if chọn theo điều kiện, switch chọn theo một giá trị rời rạc.
- Dùng để từ chối input sai và chạy đúng nhánh nghiệp vụ.
- Thứ tự ngưỡng và break quyết định nhánh thực sự chạy.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- rẽ nhánh bằng `if`, `else if`, `else`;
- chọn một trường hợp rời rạc bằng `switch`;
- dùng `break` để kết thúc một `case`;
- validate input trước khi chuyển đổi;
- chọn cấu trúc điều kiện phù hợp với bài toán.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một nhân viên đọc lựa chọn rồi đi đến đúng quầy. Trước khi báo giá, họ phải loại mã không có trong menu. if diễn đạt “có thỏa điều kiện không?”, switch diễn đạt “đây là mã nào?”. Máy chỉ chạy phần được chọn, không chạy tất cả nhánh.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| branch | nhánh được chọn theo điều kiện | mức giá |
| guard clause | kiểm tra rồi thoát sớm khi không hợp lệ | từ chối x |
| case | một nhãn giá trị trong switch | case '2' |
| fallthrough | chạy tiếp vào case sau | quên break |

### Ví dụ nhỏ — tính tay trước

Chọn '2' → qua guard → giá 30000 → không đạt 50000 → đạt 30000 → nhóm trung bình. Chọn 'x' → guard từ chối → không được tính giá.

Máy bán vé nhận một ký tự:

- `1`: vé thường, `50000` VND;
- `2`: vé sinh viên, `30000` VND;
- `3`: vé trẻ em, `20000` VND.

Input khác phải bị từ chối, không được âm thầm tạo giá. Với input `2`, chương trình phải in đúng loại vé và giá.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `ticket.c`:

```c
#include <stdio.h>

int main(void)
{
    printf("Chon ve (1-3): ");
    int choice = getchar();

    /* Từ chối input ngoài contract trước khi tính bất kỳ mức giá nào. */
    if (choice < '1' || choice > '3') {
        fprintf(stderr, "Lua chon khong hop le.\n");
        return 1;
    }

    int price = 0;

    switch (choice) {
    case '1':
        printf("Loai ve: Thuong\n");
        price = 50000;
        break;
    case '2':
        printf("Loai ve: Sinh vien\n");
        price = 30000;
        break;
    case '3':
        printf("Loai ve: Tre em\n");
        price = 20000;
        break;
    default:
        fprintf(stderr, "Loi logic khong mong doi.\n");
        return 2;
    }

    if (price >= 50000) {
        printf("Nhom gia: Cao\n");
    } else if (price >= 30000) {
        printf("Nhom gia: Trung binh\n");
    } else {
        printf("Nhom gia: Thap\n");
    }

    printf("Gia: %d VND\n", price);
    return 0;
}
```

Compile và kiểm tra input `2`:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror ticket.c -o ticket
printf '2\n' | ./ticket
```

Output:

```text
Chon ve (1-3): Loai ve: Sinh vien
Nhom gia: Trung binh
Gia: 30000 VND
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`; input `x` trả exit status `1` và ghi lỗi vào `stderr`.

### Walkthrough — execution / state / cost

1. choice giữ mã ký tự, không phải số lượng.
2. switch chọn case '2', đặt price=30000; break chỉ thoát switch.
3. Chuỗi if thử ngưỡng cao trước; chỉ một nhóm được in.
4. price và choice nằm trong lần chạy main. Số điều kiện nhỏ, cố định; chi phí đọc/ghi thường lớn hơn chọn nhánh.

### Mini-check

Nếu bỏ break của vé sinh viên, price cuối cùng có thể nhận giá từ case nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. `if` chỉ chạy block khi điều kiện đúng

```c
if (choice < '1' || choice > '3') {
    ...
}
```

Điều kiện đúng khi ký tự nằm ngoài range. `return 1` kết thúc `main` ngay, nên phần tính giá không chạy với input sai. Đây là **guard clause**: từ chối trạng thái không hợp lệ sớm.

### 4.2. Chuỗi `if` / `else if` / `else`

Các điều kiện được thử từ trên xuống. Chỉ block đầu tiên có điều kiện đúng được chạy; `else` nhận mọi trường hợp còn lại.

Thứ tự quan trọng: kiểm tra `>= 50000` trước `>= 30000`. Đảo lại sẽ phân loại `50000` vào nhóm trung bình rồi dừng.

### 4.3. `switch` chọn theo một giá trị

`switch (choice)` so giá trị với từng nhãn `case`. `break` thoát khỏi `switch`. Nếu bỏ `break`, execution tiếp tục sang case sau; đó gọi là fallthrough và thường gây bug nếu không có chủ ý.

`default` là hàng rào phòng thủ. Guard phía trên đã giới hạn `choice`, nên nhánh này không dự kiến xảy ra; giữ nó giúp code rõ invariant và an toàn khi được sửa về sau.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| if/else | kiểm tra range hoặc nhiều biểu thức | hợp ngưỡng giá; thứ tự dễ sai nếu điều kiện chồng nhau |
| switch | so một giá trị với các nhãn integer | hợp menu; không dùng trực tiếp cho khoảng giá |
| break / return | thoát switch / kết thúc hàm | không thay lẫn nhau khi còn code sau switch |

### Misconception check

**Đúng hay sai?** break trong switch kết thúc main.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: execution tiếp tục sau switch.

</details>

**Đúng hay sai?** Đặt >=30000 trước >=50000 vẫn phân loại giống nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: giá 50000 đã khớp nhánh đầu và không tới nhánh sau.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** guard, if, switch.

- **Working Developer — dùng khi làm việc:** test ngưỡng và thông báo lỗi.

- **Deep Dive — có thể quay lại sau:** code sinh cho switch nếu đo cho thấy cần.

### Truth trong C

Trong vị trí điều kiện:

- `0` là false;
- giá trị khác `0` là true.

Các operator so sánh và logic tạo `0` hoặc `1`. Dùng biểu thức thể hiện ý định, thay vì so sánh thừa như `if (valid == true)`.

### Khi dùng `if`, khi dùng `switch`?

- Dùng `if` cho range, nhiều điều kiện kết hợp, hoặc nhánh dựa trên biểu thức khác nhau.
- Dùng `switch` khi so cùng một giá trị integer/character với các lựa chọn rời rạc.

`switch` không biểu diễn trực tiếp `price >= 30000`.

### Block luôn có dấu ngoặc

C cho phép bỏ `{}` khi chỉ có một statement. Bộ tài liệu vẫn dùng block đầy đủ để việc thêm dòng sau này không vô tình nằm ngoài điều kiện.

### Error output và exit status

`fprintf(stderr, ...)` có format giống `printf` nhưng ghi vào standard error. Exit status khác `0` cho script gọi biết chương trình thất bại, ngay cả khi text lỗi bị chuyển hướng.

## 6. Lỗi thường gặp

### Dùng `=` trong điều kiện

`if (choice = '1')` gán rồi xét giá trị, không so sánh. Dùng `==`.

### Quên `break`

Case tiếp theo chạy ngoài ý muốn. Chỉ dùng fallthrough khi thật cần và comment rõ.

### Xếp range sai thứ tự

Kiểm tra điều kiện rộng trước làm nhánh hẹp không bao giờ tới. Đi từ điều kiện cụ thể/cao hơn phù hợp logic.

### Không xử lý `EOF`

`EOF` cũng nằm ngoài `'1'..'3'`, nên sample từ chối đúng. Với thông báo production, nên phân biệt hết input với ký tự sai.

### Không có đường thất bại

In lỗi nhưng vẫn `return 0` khiến automation hiểu nhầm thành công. Trả status khác `0`.

### Lồng `if` quá sâu

Validate và return sớm; tách hàm sau khi học bài 09.

## 7. Khi nào KHÔNG dùng

Không dùng switch để giả lập hàng loạt khoảng liên tục; if rõ hơn. Không lồng nhánh nhiều tầng chỉ để báo lỗi; guard rồi xử lý đường hợp lệ. Chưa cần bảng luật động cho ba loại vé.

## 8. Production notes & scale check

Ba loại vé đủ dùng switch. Khi chính sách được sửa thường xuyên, giữ test tại mỗi ngưỡng trước khi đổi cách biểu diễn. Team nhỏ cần thống nhất exit status và stderr để script nhận lỗi. Việc compiler tối ưu switch thế nào không quyết định nghiệp vụ đúng; quan sát output và status trước.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Chẵn/lẻ

Dùng `if/else` in một số cố định là chẵn hay lẻ.

**Gợi ý:** dùng `% 2`.

### Bài 2 — Xếp loại điểm

Phân loại điểm `0–100` thành A/B/C/D/F và từ chối ngoài range.

**Gợi ý:** validate trước, rồi kiểm tra từ ngưỡng cao xuống thấp.

### Bài 3 — Menu bốn phép tính

Dùng `switch` với ký tự `+`, `-`, `*`, `/` trên hai số cố định.

**Gợi ý:** ở case `/`, bảo vệ mẫu số khác `0`.

### Bài 4 — Test lỗi

Chạy sample với `1`, `3`, `x` và input rỗng; ghi output cùng exit status.

**Gợi ý:** dùng `echo $?` ngay sau mỗi lần chạy.

## 10. Bài tập tích hợp liên module — Judgment

Khi menu trở thành hàm ở bài 09 và được chuyển sang C# Module 04, chọn nơi từ chối mã sai: hàm tính giá hay chỉ giao diện? Nêu điều kiện để mọi caller được bảo vệ.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Trace lựa chọn 3 qua từng nhánh.
2. Vì sao default vẫn khác input validation?
3. break khác return thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi viết được guard clause bằng `if`.
- [ ] Tôi sắp xếp đúng chuỗi `else if`.
- [ ] Tôi dùng `switch`, `case`, `break`, `default`.
- [ ] Tôi giải thích truth trong C.
- [ ] Tôi ghi lỗi ra `stderr` và trả status thất bại.
- [ ] Tôi biết khi nào `if` rõ hơn `switch`.

Điều hướng:

- Prerequisite: [Nhập xuất với stdio](./06-nhap-xuat-voi-stdio.md)
- Bài tiếp theo: [Vòng lặp for, while và do-while](./08-vong-lap-for-while-do-while.md)
