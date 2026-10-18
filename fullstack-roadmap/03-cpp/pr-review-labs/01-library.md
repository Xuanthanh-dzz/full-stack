# PR Review — Move và thay danh mục

Thư viện một thread, vài chục sách. Đây là patch huấn luyện độc lập: Book có id(), books là vector<unique_ptr<Book>>, parse_all trả cùng kiểu hoặc throw, log ghi chẩn đoán. Precondition add nhận owner không rỗng; replace phải giữ danh mục cũ khi parse thất bại. Không áp patch trực tiếp vào capstone.

## Diff

Đọc [library.diff](./diffs/library.diff), trace mọi hunk trước khi sửa.

## Nhiệm vụ review

- Phân loại blocker/major/minor, chỉ ra state và quyền sở hữu trước/sau move.
- Đánh giá replace khi parser throw sau một record; RAII bảo đảm gì?
- Đề xuất regression test bắt từng lỗi, gồm dữ liệu cũ vẫn tồn tại.
- Nêu contract khi log throw sau khi đã thêm và cách báo kết quả; đừng tự hứa strong guarantee toàn hàm.
- Đánh giá đề xuất đổi tất cả unique_ptr thành shared_ptr: owner thứ hai thực sự ở đâu?

## Rubric

| Nhóm | Điểm |
|---|---:|
| Bắt dereference moved-from owner, có trace | 30 |
| Bắt mất state cũ và phân biệt cleanup/rollback | 30 |
| Test có expected và failure evidence | 20 |
| Sửa nhỏ, quyết định ownership có driver | 10 |
| Comment rõ vị trí/severity/contract | 10 |

Đạt từ 80, không bỏ sót lỗi ownership. Đếm keyword hoặc nhận xét style không thay evidence.

## Submission format

Bảng file/hunk, severity, evidence, đề xuất, test; kết luận approve/request changes; sau review mới nộp diff sửa và kết quả gate. [Module](../index.md).
