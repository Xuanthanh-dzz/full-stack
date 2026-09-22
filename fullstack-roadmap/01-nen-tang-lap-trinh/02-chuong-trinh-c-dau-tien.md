# Chương trình C đầu tiên

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Quy trình build biến file C thành executable; chạy executable mới thực hiện phép tính.
- Dùng khi tạo, sửa hoặc debug bất kỳ chương trình C nào.
- Build thành công và exit status 0 chưa chứng minh output đúng yêu cầu.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả đường đi từ source code C đến executable;
- đọc khung tối thiểu của một chương trình C11;
- phân biệt compile error, link error và lỗi khi chạy;
- dùng compiler với bộ cờ cảnh báo nghiêm ngặt;
- đọc diagnostic theo file, dòng và cột.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bản công thức và món ăn là hai thứ khác nhau: file C giống công thức, executable là thứ máy có thể chạy. Sửa công thức chưa làm executable cũ thay đổi. Cần dịch lại thành công rồi mới chạy bản mới.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| compiler | công cụ dịch và kiểm tra source | cc điều phối build |
| executable | file chương trình có thể chạy | ./temperature |
| linker | công cụ nối các phần mã đã dịch | nối lời gọi thư viện |
| diagnostic | thông báo lỗi hoặc cảnh báo | file, dòng, cột |
| exit status | mã kết thúc gửi cho chương trình gọi | 0 báo thành công |

### Ví dụ nhỏ — tính tay trước

Tính tay với 25 độ C: 25 × 9 / 5 + 32 = 77. Nếu executable vẫn in 86 sau khi sửa source, hãy kiểm tra bước build và đường dẫn file vừa chạy.

Bài trước đã in một phiếu cố định. Bây giờ một trạm thời tiết cần hiển thị nhiệt độ `30` độ C dưới cả hai đơn vị:

```text
Nhiet do C: 30.0
Nhiet do F: 86.0
```

Công thức là:

```text
F = C * 9 / 5 + 32
```

Trước khi học biến, ta dùng trực tiếp giá trị `30.0` để tập trung vào quy trình source → compiler → executable.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `temperature.c`:

```c
#include <stdio.h>

int main(void)
{
    printf("Nhiet do C: %.1f\n", 30.0);

    /* Các literal .0 giữ phép chia ở miền số thực, không làm mất phần lẻ. */
    printf("Nhiet do F: %.1f\n", 30.0 * 9.0 / 5.0 + 32.0);

    return 0;
}
```

Compile:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror temperature.c -o temperature
```

Nếu lệnh không in lỗi, chạy executable:

```bash
./temperature
```

Output:

```text
Nhiet do C: 30.0
Nhiet do F: 86.0
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. cc đọc temperature.c; lỗi cú pháp dừng bước build, chưa chạy main.
2. Sau build thành công, ./temperature được nạp; môi trường chạy C gọi main.
3. Biểu thức số thực tạo 86.0, printf ghi kết quả; giá trị tạm không được lưu qua lần chạy sau.
4. return 0 trả trạng thái; thời gian build thuộc công cụ phát triển, thời gian chạy thuộc process của sample.

### Mini-check

Build mới thất bại nhưng ./temperature vẫn chạy: bạn đang kiểm tra phiên bản nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Từng dòng source làm gì?

```c
#include <stdio.h>
```

Dòng này yêu cầu bước tiền xử lý đưa các khai báo cần thiết từ standard header `stdio.h` vào quá trình dịch. Nhờ đó compiler kiểm tra được lời gọi `printf`. Preprocessor sẽ được học sâu ở module 02; hiện tại chỉ dùng đúng mẫu của thư viện chuẩn.

```c
int main(void)
```

Đây là entry point. `void` trong cặp ngoặc nói rằng `main` không nhận parameter theo dạng này. `int` nói rằng `main` trả một số nguyên cho môi trường gọi.

```c
printf("Nhiet do F: %.1f\n", 30.0 * 9.0 / 5.0 + 32.0);
```

Đây là một lời gọi hàm:

- chuỗi đầu là format;
- `%.1f` yêu cầu in một số thực với một chữ số sau dấu thập phân;
- expression sau dấu phẩy tính giá trị cần đặt vào `%.1f`;
- chi tiết operator và thứ tự tính sẽ được hệ thống hóa ở bài 05.

### 4.2. Source trở thành executable như thế nào?

```text
temperature.c
      |
      v
preprocessor xử lý #include
      |
      v
compiler kiểm tra cú pháp/kiểu và tạo object code
      |
      v
linker nối object code với phần thư viện cần dùng
      |
      v
temperature (executable)
      |
      v
hệ điều hành nạp và bắt đầu tại main
```

Lệnh `cc` điều phối các bước này. File `.c` là text dành cho compiler; file `temperature` là executable dành cho hệ điều hành.

### 4.3. Exit status

`return 0;` kết thúc `main` với trạng thái thành công. Trong shell, có thể xem trạng thái của lệnh vừa chạy:

```bash
./temperature
echo $?
```

Kết quả `0` nghĩa là chương trình tự báo thành công. Output đúng hay sai về nghiệp vụ vẫn phải được kiểm tra riêng.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Compile error | source không dịch được | sửa diagnostic đầu tiên; chạy lại không chữa được |
| Link error | thiếu phần định nghĩa cần nối | kiểm tra file/thư viện trong lệnh build |
| Logic error | chương trình chạy nhưng kết quả sai | so với kết quả tính tay; compiler không biết nghiệp vụ |

### Misconception check

**Đúng hay sai?** Sửa source sẽ thay executable đang có.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phải build lại thành công.

</details>

**Đúng hay sai?** return 0 đảm bảo công thức đổi nhiệt độ đúng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: đó là thông báo của chính chương trình, cần kiểm tra output độc lập.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** build/run và đọc lỗi đầu tiên.

- **Working Developer — dùng khi làm việc:** ghi compiler, command, output trong bug report.

- **Deep Dive — có thể quay lại sau:** phân biệt các giai đoạn dịch khi chương trình nhiều file.

### C11 là gì?

C có nhiều phiên bản chuẩn. `-std=c11` yêu cầu compiler áp dụng quy tắc của chuẩn C11 cho source trong lộ trình này. Extension riêng của compiler có thể làm code kém di động; `-Wpedantic` giúp phát hiện nhiều trường hợp đó.

### Vai trò của các cờ compiler

| Cờ | Vai trò |
|---|---|
| `-std=c11` | Chọn chuẩn ngôn ngữ C11 |
| `-Wall` | Bật nhóm warning phổ biến |
| `-Wextra` | Bật thêm warning hữu ích |
| `-Wpedantic` | Cảnh báo lệch chuẩn được chọn |
| `-Werror` | Coi warning là lỗi build |
| `-o temperature` | Đặt tên executable |

### Ba lớp lỗi khác nhau

- **Compile error:** source vi phạm cú pháp hoặc type rule; chưa có object code hợp lệ.
- **Link error:** từng phần đã compile nhưng linker không tìm thấy định nghĩa cần nối.
- **Runtime/logic error:** đã có executable, nhưng chương trình dừng bất thường hoặc cho kết quả sai.

Trong một file nhỏ, bạn gặp compile error nhiều nhất. Link error sẽ rõ hơn khi module 02 tách chương trình thành nhiều phần.

### Format của `printf`

`printf` không tự biết ý nghĩa của text format:

- `%d` dành cho `int`;
- `%f` nhận giá trị số thực được truyền cho `printf`;
- `%.1f` in một chữ số sau dấu thập phân;
- `\n` xuống dòng;
- `%%` in ký tự `%`.

Format phải khớp kiểu của argument. Bài 03 sẽ ghép từng kiểu dữ liệu với format phù hợp.

## 6. Lỗi thường gặp

### Chạy source như executable

`./temperature.c` không phải quy trình chuẩn. Hãy compile thành `temperature`, rồi chạy `./temperature`.

### Thiếu `stdio.h`

Gọi `printf` mà không có khai báo hợp lệ là lỗi với bộ cờ nghiêm ngặt. Thêm `#include <stdio.h>`.

### Viết `Main` thay cho `main`

C phân biệt chữ hoa và chữ thường. Entry point phải tên `main`.

### Quên dấu `;` hoặc dấu đóng

Compiler có thể báo lỗi ở dòng sau vị trí thật. Đọc diagnostic đầu tiên rồi kiểm tra cả cuối dòng trước.

### Format không khớp argument

Ví dụ `printf("%d", 30.0)` là sai vì `%d` không khớp số thực. Warning trở thành error nhờ `-Werror`.

### Dùng phép chia nguyên ngoài ý muốn

`30 * 9 / 5` cho bài này vẫn ra `54`, nhưng input khác có thể mất phần lẻ. Các literal `30.0`, `9.0`, `5.0` buộc phép tính số thực; bài 05 giải thích kỹ.

### Compile xong nhưng chạy executable cũ

Nếu lần compile mới thất bại, executable từ lần trước có thể vẫn còn. Chỉ tin kết quả chạy sau một lệnh compile thành công.

## 7. Khi nào KHÔNG dùng

Không rebuild chỉ để đổi input khi chương trình đã hỗ trợ nhập dữ liệu. Không dùng chạy executable cũ như bằng chứng cho source mới. Với một file, lệnh cc rõ ràng là đủ; hệ thống build nhiều tầng chỉ đáng thêm khi có nhiều file/phụ thuộc.

## 8. Production notes & scale check

Sample chạy cục bộ, không có network. Team nhỏ nên lưu đúng lệnh build và phiên bản compiler; máy khác phải tái tạo được kết quả. Với nhiều file, chuyển sang Makefile ở Module 02 để theo dõi file cần build. Đo riêng thời gian build và runtime trước khi gọi chương trình “chậm”.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Lời chào hai dòng

Viết chương trình in tên và mục tiêu học C trên hai dòng.

**Gợi ý:** dùng hai lần `printf`, mỗi chuỗi kết thúc bằng `\n`.

### Bài 2 — Đổi nhiệt độ khác

Đổi chương trình sang `25` độ C và dự đoán output trước khi chạy.

**Gợi ý:** chỉ thay hai literal `30.0`; kết quả là `77.0` độ F.

### Bài 3 — In ký hiệu phần trăm

In dòng `Do am: 65%`.

**Gợi ý:** trong format của `printf`, dùng `%%`.

### Bài 4 — Tạo compile error có chủ đích

Mỗi lần chỉ xóa một ký tự: dấu `;`, dấu `"` hoặc dấu `}`. Ghi lại diagnostic đầu tiên rồi hoàn tác.

**Gợi ý:** chú ý tên file, dòng, cột và cụm `error:`.

### Bài 5 — Kiểm tra exit status

Đổi `return 0` thành `return 7`, chạy rồi xem `$?`; sau đó trả code về `0`.

**Gợi ý:** exit status không tự in ra bởi chương trình.

## 10. Bài tập tích hợp liên module — Judgment

Một bạn sẽ học Makefile ở Module 02 đề xuất thêm hệ thống build cho temperature.c. Với một file và một lệnh, chọn giữ cc hay thêm công cụ? Nêu thay đổi quy mô nào khiến quyết định khác đi.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ source → executable → output.
2. Build lỗi nhưng file executable còn thì có thể kết luận gì?
3. Đặt một test phát hiện công thức sai dù status bằng 0.

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi mô tả được source → preprocess/compile → link → executable.
- [ ] Tôi biết vai trò tối thiểu của `#include`, `main`, `printf` và `return`.
- [ ] Tôi compile bằng đủ năm cờ đã quy định.
- [ ] Tôi phân biệt compile error, link error và logic/runtime error.
- [ ] Tôi đọc được diagnostic đầu tiên thay vì đoán lỗi.
- [ ] Tôi kiểm tra được exit status trong terminal.

Điều hướng:

- Prerequisite: [Bài toán, thuật toán và pseudocode](./01-bai-toan-thuat-toan-va-pseudocode.md)
- Bài tiếp theo: [Biến, hằng số và kiểu dữ liệu](./03-bien-hang-so-kieu-du-lieu.md)
