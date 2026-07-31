# Bài toán, thuật toán và pseudocode

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tách một yêu cầu thành input, các bước xử lý và output;
- viết một thuật toán tuần tự bằng pseudocode trước khi viết C;
- phân biệt thuật toán với source code;
- tự compile và chạy một chương trình C11 tối thiểu;
- đối chiếu từng dòng code với một bước trong thuật toán.

## 2. Bài toán mở đầu

Một quầy văn phòng phẩm chuẩn bị 3 quyển vở, mỗi quyển giá `12000` VND. Nhân viên cần biết tổng tiền và in một phiếu ngắn:

```text
So luong: 3
Don gia: 12000 VND
Tong tien: 36000 VND
```

Nếu viết code ngay, người mới dễ tập trung vào dấu `;` mà quên câu hỏi quan trọng hơn: chương trình nhận dữ liệu nào, xử lý gì và phải tạo kết quả nào?

Ta mô tả bài toán trước:

- **Input:** số lượng `3`, đơn giá `12000`.
- **Xử lý:** lấy số lượng nhân đơn giá.
- **Output:** số lượng, đơn giá, tổng tiền.

## 3. Lời giải bằng code

### 3.1. Thuật toán bằng pseudocode

Pseudocode là cách viết các bước bằng ngôn ngữ gần lời nói, chưa phụ thuộc cú pháp C:

```text
BAT_DAU
    GAN so_luong BANG 3
    GAN don_gia BANG 12000
    GAN tong_tien BANG so_luong NHAN don_gia

    IN so_luong
    IN don_gia
    IN tong_tien
KET_THUC
```

Đọc từ trên xuống, mỗi dòng tạo một thay đổi hoặc một output quan sát được.

### 3.2. Chương trình C11 hoàn chỉnh

Tạo file `receipt.c`:

```c
#include <stdio.h>

int main(void)
{
    /*
     * Bài đầu tiên dùng trực tiếp các giá trị đã biết.
     * Biến sẽ được học có hệ thống ở bài 03.
     */
    printf("So luong: 3\n");
    printf("Don gia: 12000 VND\n");
    printf("Tong tien: 36000 VND\n");

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror receipt.c -o receipt
./receipt
```

Output:

```text
So luong: 3
Don gia: 12000 VND
Tong tien: 36000 VND
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0` với đúng các cờ ở trên.

## 4. Giải thích cơ chế

### 4.1. Chương trình chạy từ đâu?

Hệ điều hành bắt đầu chương trình tại hàm:

```c
int main(void)
```

Trong bài này, chỉ cần hiểu:

- `main` là điểm bắt đầu;
- cặp `{ ... }` bao quanh các lệnh của `main`;
- các lệnh chạy từ trên xuống;
- dấu `;` kết thúc một lệnh;
- `return 0;` báo cho hệ điều hành rằng chương trình kết thúc thành công.

Ý nghĩa chi tiết của kiểu `int`, hàm và giá trị trả về sẽ lần lượt được học ở bài 03 và bài 09.

### 4.2. `printf` tạo output

`printf` là một hàm có sẵn dùng để ghi text ra terminal:

```c
printf("So luong: 3\n");
```

- Text nằm giữa hai dấu `"`.
- `\n` là ký hiệu xuống dòng.
- `#include <stdio.h>` cho compiler biết cách gọi `printf`.
- `// ...` hoặc `/* ... */` là comment dành cho người đọc; compiler không biến comment thành hành động của chương trình.

### 4.3. Đối chiếu thuật toán với code

```text
Pseudocode                         C
-------------------------------------------------------------
IN so_luong                       printf("So luong: 3\n");
IN don_gia                        printf("Don gia: 12000 VND\n");
IN tong_tien                      printf("Tong tien: 36000 VND\n");
KET_THUC thanh cong               return 0;
```

Code hiện đang in kết quả đã tính trước. Bài 03 sẽ lưu dữ liệu vào biến; bài 05 sẽ để máy thực hiện phép nhân. Việc tách nhỏ này giúp ta hiểu từng cơ chế trước khi ghép chúng.

## 5. Kiến thức nền

### Bài toán và đặc tả

Một yêu cầu chỉ có thể lập trình được khi đủ rõ để kiểm tra. “In hóa đơn đẹp” còn mơ hồ; “in đúng ba dòng với số lượng, đơn giá và tổng tiền” có output kiểm chứng được.

Trước khi viết thuật toán, hãy hỏi:

1. Input là gì và lấy từ đâu?
2. Output chính xác là gì?
3. Các bước nào biến input thành output?
4. Trường hợp nào có thể làm yêu cầu không hợp lệ?

### Thuật toán

Thuật toán là một dãy bước:

- có thứ tự rõ ràng;
- mỗi bước đủ cụ thể để thực hiện;
- kết thúc sau hữu hạn bước đối với input hợp lệ;
- tạo đúng output đã yêu cầu.

Cùng một thuật toán có thể được viết bằng C, C# hoặc ngôn ngữ khác. Source code là cách biểu diễn thuật toán theo quy tắc của một ngôn ngữ cụ thể.

### Pseudocode không có một cú pháp bắt buộc

Các từ `BAT_DAU`, `GAN`, `IN` chỉ là quy ước của bài. Điều quan trọng là nhất quán và không bỏ qua bước xử lý. Pseudocode không được compiler chạy; con người dùng nó để kiểm tra logic.

## 6. Lỗi thường gặp

### Viết code khi chưa xác định output

Nếu chưa biết chương trình phải in gì, bạn không có tiêu chí kết luận code đúng. Hãy viết một output mẫu trước.

### Pseudocode quá chung chung

`XU_LY_DON_HANG` không nói cần làm gì. Viết rõ `tong_tien = so_luong * don_gia`.

### Pseudocode lẫn quá nhiều cú pháp C

Mục tiêu của pseudocode là nhìn logic. Không cần dấu `;`, kiểu dữ liệu hay `printf`.

### Quên `\n`

Không có `\n`, các lần `printf` tiếp theo có thể nối trên cùng một dòng.

### Gõ “dấu ngoặc thông minh”

Source code phải dùng dấu ASCII `"`, không dùng `“` và `”` do trình soạn thảo văn bản tự thay.

### Bỏ qua cảnh báo compiler

Bộ tài liệu dùng `-Werror`, vì vậy warning cũng làm build thất bại. Đây là chủ ý: sửa nguyên nhân thay vì tập bỏ qua tín hiệu.

## 7. Bài tập

### Bài 1 — Phiếu mua bút

Viết input, xử lý, output và pseudocode cho 5 cây bút giá `7000` VND/cây.

**Gợi ý:** tổng tiền là một bước xử lý, không phải input.

### Bài 2 — Chu vi hình chữ nhật

Với chiều dài `8`, chiều rộng `5`, hãy viết pseudocode in chu vi.

**Gợi ý:** ghi rõ thứ tự cộng và nhân trong bước tính.

### Bài 3 — Đổi phút

Viết pseudocode đổi `135` phút thành số giờ và số phút còn lại.

**Gợi ý:** tách hai output; phép chia và phần dư sẽ học ở bài 05.

### Bài 4 — Sửa đặc tả mơ hồ

Biến câu “tính điểm tốt” thành yêu cầu có input và output kiểm tra được.

**Gợi ý:** xác định bao nhiêu điểm thành phần và quy tắc làm tròn.

### Bài 5 — Thay output của chương trình

Sửa `receipt.c` để in phiếu 2 chiếc thước, đơn giá `15000`, tổng `30000`.

**Gợi ý:** giữ nguyên khung `main`, chỉ đổi ba chuỗi.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi tách được input, xử lý và output của một bài toán nhỏ.
- [ ] Tôi viết được pseudocode có thứ tự và điểm kết thúc rõ ràng.
- [ ] Tôi phân biệt thuật toán với source code.
- [ ] Tôi biết chương trình C bắt đầu ở `main`.
- [ ] Tôi compile được file bằng đầy đủ cờ C11 của tài liệu.
- [ ] Tôi đối chiếu được output thực tế với output yêu cầu.

Điều hướng:

- Prerequisite: [Roadmap tổng và cách học](../00-huong-dan/roadmap.md)
- Bài tiếp theo: [Chương trình C đầu tiên](./02-chuong-trinh-c-dau-tien.md)
