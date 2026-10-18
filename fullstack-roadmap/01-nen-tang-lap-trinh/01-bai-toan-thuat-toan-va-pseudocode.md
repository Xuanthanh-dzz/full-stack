# Bài toán, thuật toán và pseudocode

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Thuật toán là các bước biến dữ liệu đầu vào thành kết quả; pseudocode ghi các bước đó bằng lời.
- Dùng trước khi code để thống nhất cách tính và kết quả cần kiểm tra.
- In sẵn một đáp án chỉ minh họa output, chưa phải chương trình tính được cho input khác.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tách một yêu cầu thành input, các bước xử lý và output;
- viết một thuật toán tuần tự bằng pseudocode trước khi viết C;
- phân biệt thuật toán với source code;
- tự compile và chạy một chương trình C11 tối thiểu;
- đối chiếu từng dòng code với một bước trong thuật toán.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Hãy đưa cho một người khác tờ hướng dẫn tính tiền. Nếu họ vẫn phải hỏi “nhân những số nào?”, hướng dẫn chưa đủ rõ. Máy cũng cần các bước cụ thể như vậy. Ta tính bằng tay trước rồi mới chuyển hướng dẫn sang C.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| input | dữ liệu đã có trước khi xử lý | 3 quyển, 12000 đồng |
| output | kết quả cần tạo | 36000 đồng |
| thuật toán | các bước xử lý có thứ tự và kết thúc | nhân số lượng với đơn giá |
| source code | văn bản viết theo quy tắc ngôn ngữ | file receipt.c |
| compile | dịch source thành chương trình máy chạy được | lệnh cc |

### Ví dụ nhỏ — tính tay trước

Với 2 quyển giá 5 đồng: nhận 2 và 5 → nhân được 10 → in 10. Đổi số lượng thành 3 thì kết quả phải là 15; đây là phép thử phân biệt tính thật với in kết quả cố định.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Pseudocode giữ hai giá trị 3 và 12000; bước nhân tạo 36000.
2. Sample C hiện chỉ ghi ba chuỗi cố định; nó KHÔNG thực hiện bước nhân của pseudocode.
3. Khi chạy executable trên máy, ba lời gọi printf ghi lần lượt vào stdout; chưa có dữ liệu nhập hoặc dữ liệu lưu lâu dài.
4. return 0 kết thúc; chi phí chính của sample là khởi động chương trình và ghi ba dòng, không phải tính toán.

### Mini-check

Nếu đổi yêu cầu thành 4 quyển nhưng chỉ sửa dòng “So luong”, dòng tổng có tự đổi không? Vì sao?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Chương trình chạy từ đâu?

Trong môi trường C có hệ điều hành, phần khởi động của chương trình gọi hàm:

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Pseudocode | mô tả cách giải cho người đọc | tốn công viết nhưng sửa logic sớm; dùng khi yêu cầu chưa rõ |
| Code C | chỉ dẫn theo cú pháp để compiler dịch | cần build/run; dùng khi đã có output kiểm tra |
| In đáp án cố định | chỉ tái hiện một ví dụ | rất ít code; không dùng cho input thay đổi |

### Misconception check

**Đúng hay sai?** In đúng 36000 chứng minh chương trình nhân đúng với mọi input.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample chỉ in chuỗi; phải đổi input và kiểm tra phép tính ở bài 03–05.

</details>

**Đúng hay sai?** Pseudocode cần có cú pháp C mới chạy được.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: pseudocode dành cho con người, không đưa trực tiếp cho compiler.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** tách input/xử lý/output.

- **Working Developer — dùng khi làm việc:** viết ca kiểm tra trước khi đổi yêu cầu.

- **Deep Dive — có thể quay lại sau:** đánh giá tính kết thúc khi thuật toán có lặp.

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

## 7. Khi nào KHÔNG dùng

Không viết pseudocode nhiều trang cho việc in một dòng đã rõ. Một ví dụ input/output đủ. Cũng không dùng in đáp án cố định thay cho phép tính trong công cụ bán hàng; việc đồng bộ tay ba dòng dễ tạo hóa đơn sai.

## 8. Production notes & scale check

Demo có một bộ dữ liệu đã biết và không lưu hóa đơn. Với quầy nhỏ, team 2–3 người chỉ cần xác nhận quy tắc tính và kiểm thử vài ca; chưa cần cơ sở dữ liệu hay kiến trúc nhiều tầng. Khi input thay đổi, ưu tiên biến và phép tính trước. Lưu output đối chiếu với yêu cầu là bằng chứng ban đầu.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Bạn bàn giao quy tắc tổng tiền cho người sẽ viết C# ở Module 04. Chọn bàn giao pseudocode + 3 ví dụ hay chỉ receipt.c? Nêu phần độc lập ngôn ngữ và ca 0 sản phẩm. Không cần biết C# để trả lời.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Giải thích input khác output bằng ví dụ mới.
2. Dự đoán điều gì xảy ra nếu đổi một chuỗi in mà không đổi các chuỗi khác.
3. Chỉ ra bước pseudocode chưa được C sample thực hiện.

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi tách được input, xử lý và output của một bài toán nhỏ.
- [ ] Tôi viết được pseudocode có thứ tự và điểm kết thúc rõ ràng.
- [ ] Tôi phân biệt thuật toán với source code.
- [ ] Tôi biết chương trình C bắt đầu ở `main`.
- [ ] Tôi compile được file bằng đầy đủ cờ C11 của tài liệu.
- [ ] Tôi đối chiếu được output thực tế với output yêu cầu.

Điều hướng:

- Prerequisite: [Roadmap tổng và cách học](../00-huong-dan/roadmap.md)
- Bài tiếp theo: [Chương trình C đầu tiên](./02-chuong-trinh-c-dau-tien.md)
