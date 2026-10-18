# Mảng hai chiều

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Mảng hai chiều là mảng gồm các row; hai index chọn một phần tử.
- Dùng cho bảng chữ nhật có ý nghĩa row/column rõ.
- Bảng vuông dễ che lỗi đảo hai trục; phải kiểm tra biên từng chiều.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- biểu diễn bảng bằng mảng hai chiều;
- truy cập element theo row và column;
- duyệt bảng bằng nested loop;
- truyền một row vào hàm xử lý mảng một chiều;
- giải thích layout row-major của C.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một bảng điểm có học sinh theo hàng và môn theo cột. Chọn hàng trước rồi ô trong hàng giống chọn một mảng một chiều rồi chọn phần tử. C giữ các ô của hàng đầu liên tiếp trước khi tới hàng sau.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| row | hàng trong bảng | một học sinh |
| column | cột trong bảng | một môn |
| nested loop | vòng lặp nằm trong vòng khác | mỗi row duyệt các column |
| row-major | lưu trọn một row rồi row kế | layout của mảng C |

### Ví dụ nhỏ — tính tay trước

Bảng [[8,6,10],[4,5,6]] có 2 row, 3 column. [1][2]=6; trung bình row 0 là 8. Đảo [1][2] thành [2][1] sẽ vượt biên dù ví dụ 3×3 có thể che lỗi.

Ba học sinh có điểm ba môn:

```text
Lan:  8 7 9
Minh: 6 8 7
An:   9 9 8
```

Ta cần in bảng và trung bình từng học sinh. Dữ liệu có hai trục cố định: row là học sinh, column là môn.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `score_table.c`:

```c
#include <stdio.h>

double row_average(const int row[], int column_count)
{
    if (column_count <= 0) {
        return -1.0;
    }

    double total = 0.0;
    for (int column = 0; column < column_count; column++) {
        if (row[column] < 0 || row[column] > 10) {
            return -1.0;
        }
        total += row[column];
    }
    return total / column_count;
}

int main(void)
{
    int scores[3][3] = {
        {8, 7, 9},
        {6, 8, 7},
        {9, 9, 8}
    };

    /* Duyệt trọn từng row phù hợp với layout row-major của C. */
    for (int row = 0; row < 3; row++) {
        double average = row_average(scores[row], 3);
        if (average < 0.0) {
            fprintf(stderr, "Row diem khong hop le.\n");
            return 1;
        }

        printf("Hoc sinh %d:", row + 1);
        for (int column = 0; column < 3; column++) {
            printf(" %d", scores[row][column]);
        }
        printf(" | TB %.2f\n", average);
    }

    return 0;
}
```

Compile và chạy:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror score_table.c -o score_table
./score_table
```

Output:

```text
Hoc sinh 1: 8 7 9 | TB 8.00
Hoc sinh 2: 6 8 7 | TB 7.00
Hoc sinh 3: 9 9 8 | TB 8.67
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. main giữ 3 row, mỗi row 3 int.
2. row=0 truyền scores[0] cùng 3 vào row_average; total=24.0, average=8.0.
3. Sau khi kiểm tra sentinel, loop column in 8,7,9; hai row sau tương tự.
4. Duyệt R row × C column làm số lượt đọc tỷ lệ R*C; storage dữ liệu cũng R*C phần tử. Hàm average chỉ giữ total và vị trí hiện tại.

### Mini-check

Để tính tổng từng môn, biến nào cần cố định trong một lượt tính tổng?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Hai index chọn đúng một element

```text
              column
             0   1   2
row 0       [8] [7] [9]
row 1       [6] [8] [7]
row 2       [9] [9] [8]
```

`scores[1][2]` là `7`: row thứ hai, column thứ ba. Cả hai index đều bắt đầu 0.

### 4.2. Nested loop bám theo hai trục

Loop ngoài chọn row. Với mỗi row, loop trong duyệt toàn bộ column. Tên `row`, `column` rõ hơn `i`, `j` khi người học đang audit biên.

### 4.3. Một row là một mảng

`scores[row]` biểu diễn row hiện tại gồm ba `int`, nên truyền được vào
`row_average` cùng `column_count`. Hàm chỉ đọc vì parameter có `const`.

Contract yêu cầu `column_count > 0` và từng điểm thuộc `0..10`. Hàm trả
`-1.0` nếu contract sai; caller kiểm tra sentinel **trước khi in row**.
Accumulator là `double`, nên sample không thực hiện chuỗi phép cộng
trong `int` rồi mới cast. Với điểm đã giới hạn và số element thực tế của
mảng, average hợp lệ nằm trong `0..10`.

### 4.4. Layout row-major

Các element được lưu liên tiếp theo từng row:

```text
[0][0] [0][1] [0][2] [1][0] [1][1] [1][2] [2][0] ...
```

Vì vậy loop row ngoài, column trong vừa tự nhiên vừa thường có locality tốt. Chi tiết địa chỉ và phép tính offset thuộc module 02.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| 1D | một trục index | hợp một danh sách; không tự mang ý nghĩa hàng/cột |
| 2D chữ nhật | mỗi row có cùng số column | hợp bảng điểm; không dùng để ép các row dài khác nhau |
| Row trước / column trước | cùng dữ liệu, khác thứ tự duyệt | row trước thường gần layout hơn; đo trước khi tối ưu |

### Misconception check

**Đúng hay sai?** Bảng 2×3 có index cuối [2][3].

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: index cuối là [1][2].

</details>

**Đúng hay sai?** Duyệt column trước luôn sai kết quả.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể đúng nếu index và mục tiêu đúng; khác thứ tự truy cập và chi phí.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** hai index và loop.

- **Working Developer — dùng khi làm việc:** contract số cột, test không vuông.

- **Deep Dive — có thể quay lại sau:** layout, locality và giới hạn stack.

### Khởi tạo theo row

Mỗi cặp `{ ... }` bên trong khởi tạo một row. Thiếu initializer thì element còn lại được zero-initialize.

### Kích thước mỗi chiều

Với `int scores[3][3]`, chiều đầu có 3 row, chiều sau có 3 column. Trong bài toán thực tế hai con số có thể khác nhau.

### Capacity bảng

Project bài 15 sẽ tạo capacity cho số học sinh và giữ `student_count` riêng. Số môn cố định là 3. Chỉ các row `< student_count` chứa dữ liệu nghiệp vụ.

### Đào sâu (có thể quay lại sau)

Khi khai báo parameter là mảng nhiều chiều, compiler cần biết các chiều sau để tính bước từ row này sang row kế. Có thể dùng fixed column count hoặc parameter kích thước theo C11. Project dùng fixed `[][3]` để giữ code dễ đọc; module 02 giải thích type và địa chỉ đầy đủ.

## 6. Lỗi thường gặp

### Đảo row và column

`scores[column][row]` có thể vẫn trong biên nhưng mang nghĩa khác, đặc biệt khó phát hiện với bảng vuông.

### Dùng cùng biến cho hai loop

Loop trong làm hỏng counter loop ngoài. Khai báo `row`, `column` riêng.

### Truy cập row/column bằng size

Với size 3, index cuối là 2.

### Tính average bằng accumulator `int` chưa bảo vệ

Cộng `int` trước rồi cast có thể overflow nếu contract bị mở rộng.
Validate domain và dùng accumulator `double` như sample.

### Chia khi column count bằng 0

Không có average hợp lệ cho row không có column. Guard trước loop và
phép chia; caller xử lý sentinel.

### Duyệt cả capacity chưa dùng

Sẽ trộn zero/default vào nghiệp vụ. Duyệt theo count thực.

## 7. Khi nào KHÔNG dùng

Không ép danh sách có số phần tử mỗi row khác nhau vào bảng chữ nhật nếu phần trống gây lãng phí đáng kể. Với 3 môn cố định, mảng 2D đơn giản nhất. Chưa cần mô hình database chỉ để tính trung bình một bảng nhỏ.

## 8. Production notes & scale check

Demo 9 ô; bảng lớn cần ước lượng bộ nhớ trước khi đặt local lớn trên stack. Team nhỏ dùng test không vuông 2×4 để bắt đảo trục. Khi dữ liệu phải lưu lâu dài và nhiều người sửa, vấn đề vượt khỏi layout mảng; Module 08 sẽ mô hình hóa quan hệ. Không lấy tốc độ của 9 ô để khẳng định hiệu năng bảng lớn.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Tổng từng column

Tính tổng điểm từng môn.

**Gợi ý:** đổi vai trò loop ngoài/loop trong theo output cần tạo.

### Bài 2 — Maximum toàn bảng

Tìm điểm cao nhất và in cả row, column.

**Gợi ý:** khởi tạo bằng `[0][0]`.

### Bài 3 — Bảng không vuông

Đổi thành 2 học sinh, 4 môn.

**Gợi ý:** audit riêng hai điều kiện biên.

### Bài 4 — Đếm đạt từng học sinh

In số môn có điểm `>= 5` ở mỗi row.

**Gợi ý:** reset counter khi bắt đầu row mới.

## 10. Bài tập tích hợp liên module — Judgment

Bảng điểm hiện chỉ dùng trong một lần chạy. Khi sang Module 08, nhu cầu lưu qua lần chạy có bắt buộc đổi công thức trung bình không? Tách quyết định lưu trữ khỏi thuật toán duyệt; chưa cần viết SQL.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Trace average cho row [2,4,9].
2. Giải thích row-major bằng thứ tự 6 ô của bảng 2×3.
3. Vì sao test bảng không vuông có giá trị?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi phân biệt row và column.
- [ ] Tôi truy cập đúng `scores[row][column]`.
- [ ] Tôi viết nested loop không vượt biên.
- [ ] Tôi truyền được một row vào hàm một chiều.
- [ ] Tôi mô tả layout row-major.
- [ ] Tôi phân biệt row capacity với row count đã dùng.

Điều hướng:

- Prerequisite: [Mảng một chiều](./11-mang-mot-chieu.md)
- Bài tiếp theo: [Chuỗi ký tự](./13-chuoi-ky-tu.md)
