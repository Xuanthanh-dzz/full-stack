# PR Review — Hoàn thành việc và lỗi lưu

Một CLI cá nhân, một process ghi. Patch huấn luyện độc lập; `Todo` có `Id` và `Done` có thể sửa, constructor `Todo(int, bool)`; `_items` là `List<Todo>`; `repository.Save` ném `IOException` trước ghi khi đầy đĩa. `Single` là helper tìm duy nhất theo ID trong patch; không yêu cầu học LINQ để phát hiện lỗi alias. Contract: input không phải số trả mã 2; Save lỗi giữ nguyên state service; danh sách trả về không cho caller sửa state; ID không trùng; Remove ID không có trả false. Không áp trực tiếp patch này vào capstone.

## Diff

Đọc [todo.diff](./diffs/todo.diff) và trace từng hunk.

## Nhiệm vụ review

- Trace Complete và Run với input hợp lệ, input sai và repository thất bại; vẽ state được quan sát qua từng reference.
- Phân loại blocker/major/minor, kèm dòng và expected/actual theo contract đã nêu.
- Đề xuất regression test có thể làm bản lỗi thất bại; không chỉ kiểm thông báo cuối.
- Nêu ranh giới của guarantee nếu repository có failure behavior khác bối cảnh.
- Đánh giá đề xuất tách bốn project và thêm database cho 20 việc; chỉ chấp nhận khi có driver cụ thể.

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Trong review, xét correctness, performance, security, maintainability và operability; nếu một nhóm không có finding, ghi lý do thay vì bịa lỗi. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

| Evidence | Điểm |
|---|---:|
| State, alias và commit khi lỗi lưu | 30 |
| Input, ID và kết quả thao tác | 30 |
| Regression có expected behavior | 20 |
| Scale/judgment và phạm vi guarantee | 10 |
| Comment có vị trí, severity, giải thích | 10 |

Đạt 80 và không bỏ sót lỗi mất state. Nhận xét style không thay bằng chứng.

</details>

## Submission format

Bảng file/hunk, severity, contract, expected/actual, đề xuất và test. Kết luận approve/request changes; sau đó nộp diff sửa và lệnh chạy. [Bản đồ](../index.md).
