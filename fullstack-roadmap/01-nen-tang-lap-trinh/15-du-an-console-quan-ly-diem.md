# Dự án console quản lý điểm

> **Last verified:** 2026-09-22
>
> **Baseline:** C11 · hosted implementation · compiler hỗ trợ C11 · -Wall -Wextra -Wpedantic -Werror
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** đổi sample/contract, compiler hoặc sanitizer; CI failure

## TL;DR

- Capstone ghép input, validation, mảng và hàm thành chương trình quản lý điểm trong RAM.
- Dùng để kiểm chứng khả năng giữ state nhất quán qua cả một session.
- Chỉ commit học sinh khi đủ dữ liệu; chương trình chưa lưu file và chỉ chứa 5 học sinh.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- ghép input, validation, điều kiện, loop, hàm, mảng và string;
- quản lý count tách biệt capacity;
- chỉ commit một học sinh sau khi toàn bộ input hợp lệ;
- liệt kê, tìm kiếm và tính trung bình;
- kiểm thử chương trình qua một session tái lập.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Điền một phiếu nháp trước rồi mới chép vào sổ chính khi đủ tên và ba điểm. Nếu người dùng bỏ dở, không tăng số học sinh. count là số phiếu hoàn tất; những ô còn lại của mảng không phải học sinh thật dù đã được điền zero.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| state | dữ liệu đang giữ giữa các thao tác | names, scores, count |
| commit | chấp nhận dữ liệu đã kiểm tra vào danh sách | copy candidate rồi tăng count |
| parsing | đọc text để tạo giá trị có type | parse_number |
| invariant | ràng buộc phải giữ qua mọi thao tác | 0 <= count <= 5 |

### Ví dụ nhỏ — tính tay trước

Danh sách rỗng, thêm An với 8,7 rồi EOF → count vẫn 0. Nếu đủ 8,7,9 → copy cả tên và điểm, count thành 1. Liệt kê chỉ đọc row 0.

Giáo viên cần chương trình giữ tối đa 5 học sinh trong một lần chạy. Mỗi học sinh có tên và ba điểm nguyên `0..10`. Menu cần:

1. thêm học sinh;
2. liệt kê;
3. tìm theo tên chính xác;
4. thoát.

Dữ liệu chưa cần lưu file vì file I/O thuộc module 02. Mục tiêu checkpoint là phối hợp đúng kiến thức module 01.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo file `grade_manager.c`:

```c
#include <stdio.h>
#include <string.h>

int read_line(char text[], int capacity)
{
    if (capacity <= 0) {
        return -2;
    }

    int length = 0;
    int overflow = 0;
    int character = getchar();
    while (character != '\n' && character != EOF) {
        if (length < capacity - 1) {
            text[length] = (char)character;
            length++;
        } else {
            overflow = 1;
        }
        character = getchar();
    }
    text[length] = '\0';
    if (overflow) {
        return -1;
    }
    if (character == EOF && length == 0) {
        return 0;
    }
    return 1;
}

int parse_number(const char text[], int maximum)
{
    if (text[0] == '\0') {
        return -1;
    }
    int value = 0;
    for (int index = 0; text[index] != '\0'; index++) {
        if (text[index] < '0' || text[index] > '9') {
            return -1;
        }
        int digit = text[index] - '0';
        if (value > maximum / 10 ||
            (value == maximum / 10 && digit > maximum % 10)) {
            return -1;
        }
        value = value * 10 + digit;
    }
    return value;
}

int read_number(const char prompt[], int minimum, int maximum)
{
    char line[32];
    while (1) {
        printf("%s", prompt);
        int status = read_line(line, 32);
        if (status == 0) {
            return minimum - 1;
        }
        int value = -1;
        if (status > 0) {
            value = parse_number(line, maximum);
        }
        if (value >= minimum && value <= maximum) {
            return value;
        }
        printf("Gia tri phai tu %d den %d.\n", minimum, maximum);
    }
}

int add_student(char names[][32], int scores[][3], int count)
{
    if (count >= 5) {
        printf("Danh sach da day.\n");
        return count;
    }

    /* Chỉ copy các candidate local sang row chính sau khi đủ ba điểm. */
    char candidate_name[32];
    printf("Ten: ");
    int name_status = read_line(candidate_name, 32);
    if (name_status <= 0 || candidate_name[0] == '\0') {
        printf("Ten khong hop le; chua them.\n");
        return count;
    }

    int candidate_scores[3];
    const char prompts[3][16] = {"Toan (0-10): ", "Ly (0-10): ", "Hoa (0-10): "};
    for (int subject = 0; subject < 3; subject++) {
        candidate_scores[subject] = read_number(prompts[subject], 0, 10);
        if (candidate_scores[subject] < 0) {
            printf("Het input; chua them.\n");
            return count;
        }
    }

    int index = 0;
    while (candidate_name[index] != '\0') {
        names[count][index] = candidate_name[index];
        index++;
    }
    names[count][index] = '\0';
    for (int subject = 0; subject < 3; subject++) {
        scores[count][subject] = candidate_scores[subject];
    }

    printf("Da them %s.\n", names[count]);
    return count + 1;
}

void list_students(char names[][32], int scores[][3], int count)
{
    if (count == 0) {
        printf("Danh sach rong.\n");
        return;
    }
    printf("Danh sach:\n");
    for (int student = 0; student < count; student++) {
        int total = 0;
        for (int subject = 0; subject < 3; subject++) {
            total += scores[student][subject];
        }
        printf("%d. %s | %d %d %d | TB %.2f\n",
               student + 1, names[student],
               scores[student][0], scores[student][1], scores[student][2],
               (double)total / 3);
    }
}

void find_student(char names[][32], int scores[][3], int count)
{
    char query[32];
    printf("Ten can tim: ");
    if (read_line(query, 32) <= 0) {
        printf("Ten tim khong hop le.\n");
        return;
    }
    for (int student = 0; student < count; student++) {
        if (strcmp(query, names[student]) == 0) {
            printf("Tim thay %s: %d %d %d\n", names[student],
                   scores[student][0], scores[student][1], scores[student][2]);
            return;
        }
    }
    printf("Khong tim thay.\n");
}

int main(void)
{
    char names[5][32] = {{0}};
    int scores[5][3] = {{0}};
    int count = 0;
    int running = 1;

    while (running) {
        printf("\n1. Them\n2. Liet ke\n3. Tim\n4. Thoat\n");
        int choice = read_number("Chon: ", 1, 4);
        if (choice < 1) {
            printf("Ket thuc do het input.\n");
            break;
        }
        switch (choice) {
        case 1:
            count = add_student(names, scores, count);
            break;
        case 2:
            list_students(names, scores, count);
            break;
        case 3:
            find_student(names, scores, count);
            break;
        case 4:
            running = 0;
            break;
        default:
            printf("Lua chon khong hop le.\n");
            break;
        }
    }

    printf("Tam biet. So hoc sinh: %d\n", count);
    return 0;
}
```

Compile và chạy session tái lập:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Werror grade_manager.c -o grade_manager
printf '1\nLan\n8\n7\n9\n2\n3\nLan\n4\n' | ./grade_manager
```

Output:

```text

1. Them
2. Liet ke
3. Tim
4. Thoat
Chon: Ten: Toan (0-10): Ly (0-10): Hoa (0-10): Da them Lan.

1. Them
2. Liet ke
3. Tim
4. Thoat
Chon: Danh sach:
1. Lan | 8 7 9 | TB 8.00

1. Them
2. Liet ke
3. Tim
4. Thoat
Chon: Ten can tim: Tim thay Lan: 8 7 9

1. Them
2. Liet ke
3. Tim
4. Thoat
Chon: Tam biet. So hoc sinh: 1
```

Chương trình đã được kiểm tra bằng `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0`.

### Walkthrough — execution / state / cost

1. main tạo hai mảng cố định và count=0; menu đọc cả dòng và parse lựa chọn.
2. add_student kiểm tra capacity rồi giữ tên/điểm trong candidate local.
3. Chỉ sau ba điểm hợp lệ, copy vào names[count], scores[count], trả count+1; main nhận count mới.
4. List/find chỉ duyệt row<count. State chính sống tới hết main; tìm kiếm đọc tối đa 5 tên, memory bị chặn bởi capacity. Thoát process làm mất dữ liệu.

### Mini-check

EOF khi đang nhập điểm Hóa: hàm trả count nào và row chính có thay đổi không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. State và invariant

```text
capacity = 5
count = số row đã commit, luôn 0 <= count <= 5

names[row]  + scores[row] chỉ hợp lệ khi row < count
```

`count` là nguồn sự thật. Thêm thành công trả `count + 1`; thất bại trả count cũ.

### 4.2. Validate rồi mới commit

`add_student` đọc tên và ba điểm vào local tạm:

```text
add_student frame
├── candidate_name[32]
└── candidate_scores[3]

main frame
├── names[5][32]
├── scores[5][3]
└── count
```

Chỉ sau khi toàn bộ input hợp lệ, loop mới copy vào row `count`. EOF giữa chừng không để lại học sinh “nửa vời”.

### 4.3. Luồng menu

`main` sở hữu state và điều phối. Các hàm:

- `add_student`: validate và thêm;
- `list_students`: chỉ đọc và trình bày;
- `find_student`: đọc query, tìm bằng `strcmp`;
- `read_line`/`read_number`: cô lập parsing.

`read_line` yêu cầu caller truyền một mảng thực có ít nhất `capacity`
element. Nó trả `-2` ngay khi `capacity <= 0`, trước lần đọc/ghi đầu;
đồng thời ưu tiên báo overflow trước khi phân loại EOF rỗng. Các caller
trong project luôn truyền capacity thật của buffer.

### 4.4. Bộ nhớ

Tất cả mảng có capacity cố định trong frame `main`; không có `malloc`. Hàm nhận array parameter thao tác cùng element của mảng `main`, còn local candidate có storage riêng trong invocation. Module 02 sẽ chuyển dự án sang mô hình hiểu rõ pointer và sau đó lưu file.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Ghi từng trường trực tiếp | row chính có thể bị cập nhật nửa chừng | ít buffer tạm; không dùng khi EOF phải giữ danh sách cũ |
| Candidate rồi commit | giữ row chính tới khi đủ dữ liệu | tốn một tên và ba điểm tạm; hợp thêm học sinh |
| Mảng trong RAM / file | state lần chạy / dữ liệu lưu qua lần chạy | file thêm lỗi I/O và format; chỉ thêm khi có yêu cầu lưu |

### Misconception check

**Đúng hay sai?** Mảng đã zero-initialize thì có sẵn 5 học sinh hợp lệ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: count mới xác định row đã commit.

</details>

**Đúng hay sai?** Tăng count trước rồi báo lỗi cũng đủ vì input đã được đọc.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: danh sách có thể chứa row chưa đủ dữ liệu.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** chạy session và invariant.

- **Working Developer — dùng khi làm việc:** failure paths và tách parsing.

- **Deep Dive — có thể quay lại sau:** mở rộng lưu trữ khi có driver.

### Parsing không trộn với nghiệp vụ

`parse_number` chỉ nhận string và trả số hoặc `-1`. Vì không đọc stream, nó dễ test bằng nhiều chuỗi.

### Bảo vệ overflow trước phép nhân

Trước `value * 10 + digit`, code so phần đã đọc với `maximum / 10`; khi
hai phần nguyên bằng nhau, nó so tiếp chữ số cuối với `maximum % 10`.
Nhờ vậy expression nhân chỉ chạy khi kết quả kế tiếp không vượt
`maximum`:

```c
value > maximum / 10 ||
    (value == maximum / 10 && digit > maximum % 10)
```

`digit` đã được chứng minh nằm trong `0..9`, nên phép kiểm tra không cần
thử phép nhân có nguy cơ vượt range trước.

### Exact-name search

`strcmp == 0` phân biệt hoa/thường và khoảng trắng. Đây là contract rõ, chưa phải search thân thiện. Normalization Unicode thuộc phần frontend/backend sau.

### Giới hạn chủ ý

Dữ liệu mất khi process kết thúc; capacity chỉ 5; điểm là integer; không sửa/xóa. Đây là scope của module nền tảng, không phải sản phẩm production.

## 6. Lỗi thường gặp

### Tăng count trước khi input hoàn tất

Failure sẽ để row rác. Chỉ commit rồi tăng count ở cuối đường thành công.

### Duyệt theo capacity

Sẽ in các row zero-initialized chưa có học sinh. Luôn dùng `count`.

### Không tiêu thụ dòng quá dài

Input sau bị lệch. `read_line` vẫn đọc đến newline rồi báo overflow.

### So tên bằng `==`

Dùng `strcmp`.

### Dùng `assert` cho input

Input sai là tình huống vận hành, phải báo và cho nhập lại/thoát; assertion không phù hợp.

### Thêm feature chưa có invariant

Trước chức năng sửa/xóa, xác định count, cách dịch row và behavior khi trùng tên.

## 7. Khi nào KHÔNG dùng

Không dùng sample này cho sổ điểm thật cần lưu qua lần chạy hoặc nhiều người đồng thời sửa. Với demo 5 học sinh, không thêm database hay kiến trúc nhiều tầng. Driver tiếp theo là lưu file ở Module 02; giữ công thức và parsing tách để đổi nơi lưu ít ảnh hưởng.

## 8. Production notes & scale check

Team nhỏ cần test session rỗng, đầy, nhập sai, tên dài và EOF giữa chừng. Chi phí demo chủ yếu là I/O; tìm tuyến tính tối đa 5 row đủ. Tên trùng hiện tìm kết quả đầu; muốn thay phải xác định contract. Dữ liệu điểm thật cần lưu bền và kiểm soát quyền; capstone chỉ chứng minh cơ chế trong một process.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Xếp loại

Trong danh sách, in `Dat` nếu average `>= 5`, ngược lại `Chua dat`.

**Gợi ý:** tính average một lần rồi dùng `if`.

### Bài 2 — Tìm học sinh cao điểm nhất

In tên và average lớn nhất.

**Gợi ý:** từ chối khi count 0; khởi tạo từ row 0.

### Bài 3 — Chặn tên trùng

Không cho thêm nếu tên đã tồn tại.

**Gợi ý:** tìm trước khi commit, không tăng count khi trùng.

### Bài 4 — Thêm chức năng xóa

Xóa theo tên và dịch các row sau sang trái.

**Gợi ý:** copy cả name và ba điểm; giảm count đúng một lần.

### Bài 5 — Bộ test regression

Viết test cho `parse_number`: rỗng, chữ, `0`, `10`, `11`, chuỗi rất dài.

**Gợi ý:** hàm không đọc stdin nên gọi trực tiếp trong test.

## 10. Bài tập tích hợp liên module — Judgment

Chuẩn bị dự án kho Module 02: giáo viên yêu cầu đóng app rồi mở vẫn có điểm. Chọn thêm lưu file hay thay toàn bộ cấu trúc chương trình? Viết quyết định gồm dữ liệu nào cần lưu, lỗi ghi xử lý ra sao và lý do chưa cần nhiều service.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vẽ state trước/sau một lần thêm bị EOF.
2. Vì sao capacity khác số học sinh?
3. Phần nào giữ nguyên nếu đổi nơi lưu sang file?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi trace được nơi code chạy, state còn sống và chi phí chính.
- [ ] Tôi chọn được phương án đơn giản hơn khi kỹ thuật này không phù hợp.

- [ ] Tôi mô tả invariant `0 <= count <= capacity`.
- [ ] Tôi validate toàn bộ trước khi commit.
- [ ] Tôi tách parsing, điều phối và trình bày.
- [ ] Tôi không đọc row có index `>= count`.
- [ ] Tôi xử lý EOF, dòng quá dài và giá trị ngoài range.
- [ ] Tôi tự compile/chạy session kiểm thử được.

Điều hướng:

- Prerequisite: [Debug và kiểm thử chương trình C](./14-debug-va-kiem-thu-chuong-trinh-c.md)
- Bài tiếp theo: [Địa chỉ bộ nhớ và con trỏ](../02-c-chuyen-sau/01-dia-chi-bo-nho-va-con-tro.md)

- Spaced review: [Review 15](./reviews/review-03-state-va-debug.md)
- Failure Lab: [Điều tra lỗi](./failure-labs/03-count-vuot-mang.md)
- PR Review: [Grade Import](./pr-review-labs/01-grade-import.md)
- Rubric: [Module 01 overview](./index.md#rubric-capstone)
