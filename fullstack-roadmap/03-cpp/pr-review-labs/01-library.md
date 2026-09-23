# PR Review — Move và thay danh mục

Thư viện một thread, vài chục sách. Đây là patch huấn luyện độc lập: Book có `id()`, `books` là `vector<unique_ptr<Book>>`, `parse_all` trả cùng kiểu hoặc ném exception, `log` ghi chẩn đoán. `add` nhận owner không rỗng và từ chối ID trùng; `replace` giữ danh mục cũ khi parse thất bại. Tra cứu ID phải khớp chính xác; sắp xếp và xóa không được làm hỏng danh mục. Không áp patch trực tiếp vào capstone.

## Diff

Đọc [library.diff](./diffs/library.diff), trace mọi hunk trước khi sửa.

## Nhiệm vụ review

- Trace state và quyền sở hữu qua từng dòng ở cả đường thành công và khi collaborator ném exception.
- Phân loại blocker/major/minor; dẫn vị trí, điều kiện tái hiện, contract bị ảnh hưởng và hậu quả.
- Đề xuất test cho từng finding; chỉ rõ guarantee nào test bảo vệ và guarantee nào chưa được yêu cầu.
- Đánh giá đề xuất đổi tất cả unique_ptr thành shared_ptr: owner thứ hai thực sự ở đâu?
- Nộp review trước khi viết bản sửa; giải pháp phải phù hợp một thread và vài chục sách.

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Trong review, xét correctness, performance, security, maintainability và operability; nếu một nhóm không có finding, ghi lý do thay vì bịa lỗi. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

| Nhóm | Điểm |
|---|---:|
| Correctness của ID, sắp xếp và xóa | 30 |
| Ownership, state và exception trace | 30 |
| Test có expected và failure evidence | 20 |
| Sửa nhỏ, quyết định ownership có driver | 10 |
| Comment rõ vị trí/severity/contract | 10 |

Đạt từ 80, không bỏ sót lỗi ownership. Đếm keyword hoặc nhận xét style không thay evidence.

</details>

## Submission format

Bảng file/hunk, severity, evidence, đề xuất, test; kết luận approve/request changes; sau review mới nộp diff sửa và kết quả gate. [Module](../index.md).
