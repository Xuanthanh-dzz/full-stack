# PR Review — Hoàn thành việc và lỗi lưu

Một CLI cá nhân, một process ghi. Patch huấn luyện độc lập; Todo có Id và Done mutable, constructor Todo(int,bool); _items là List<Todo>; repository.Save ném IOException trước ghi khi đầy đĩa. Single là helper tìm duy nhất theo ID trong patch; không yêu cầu học LINQ để phát hiện lỗi alias. Contract: input không phải số trả2, Save lỗi giữ nguyên state service. Không áp trực tiếp patch này vào capstone.

## Diff

Đọc [todo.diff](./diffs/todo.diff) và trace từng hunk.

## Nhiệm vụ review

- Phân loại blocker/major/minor cho alias, điểm commit và parse.
- Viết test bằng repository cố ý ném; assertion phải kiểm tra item cũ và snapshot.
- Chỉ ra contract nào vẫn chưa được giải quyết nếu file đã ghi rồi repository mới throw.
- Đánh giá đề xuất tách bốn project và thêm database cho20 việc: driver nào thật sự có?
- Viết bản sửa nhỏ cùng expected exit code; không chỉ bắt mọi exception rồi trả0.

## Rubric

| Evidence | Điểm |
|---|---:|
| Bắt shallow copy và mutation chung | 30 |
| Chỉ đúng điểm commit, test lỗi lưu | 30 |
| Input/exit code và regression | 20 |
| Scale/judgment và phạm vi guarantee | 10 |
| Comment có vị trí, severity, giải thích | 10 |

Đạt80 và không bỏ sót lỗi mất state. Nhận xét style không thay bằng chứng.

## Submission format

Bảng file/hunk, severity, contract, expected/actual, đề xuất và test. Kết luận approve/request changes; sau đó nộp diff sửa và lệnh chạy. [Bản đồ](../index.md).
