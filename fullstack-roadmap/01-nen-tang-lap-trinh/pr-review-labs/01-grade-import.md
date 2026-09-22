# PR Review Lab — Nhập tên và báo cáo điểm

> Sau bài 15. Pull request (PR) là đề nghị đưa thay đổi code vào dự án; reviewer đọc diff và nhận xét tác động trước khi chấp nhận.

## Bối cảnh

Team ba người muốn nhận tên từ stdin, báo cáo trung bình ba điểm và in nhãn Administrator **chỉ khi tên bằng `Admin`**. Dòng input có thể rỗng, quá dài hoặc kết thúc bằng EOF. Tên không phải thông tin xác thực; nhãn này chỉ phục vụ demo.

## Diff

Đọc [patch đề xuất](./diffs/01-grade-import.diff). Đây là code cố ý sai để review, không phải sample an toàn để chạy. Dùng kiến thức bài 06–15 để trace bằng tay trước.

## Nhiệm vụ review

Tìm 6–12 vấn đề thuộc nhiều nhóm. Mỗi nhận xét cần một dòng trong diff, một input chứng minh tác động và thay đổi nhỏ nhất. Phân biệt lỗi chắc chắn với câu hỏi về yêu cầu. Chưa sửa toàn bộ code trước khi review.

Ngoài correctness, xem giới hạn buffer, EOF, contract count, assertion khi build production, số thực và thông báo thành công. Không dùng yêu cầu “thêm microservice” làm cách chữa lỗi trong một file C.

## Rubric

| Nhóm | Trọng số | Bằng chứng |
|---|---:|---|
| Correctness | 30% | trace/ca cụ thể làm sai output |
| Memory và input safety | 25% | miền index, length, EOF |
| Performance | 10% | đường không dừng hoặc work thừa có cơ sở |
| Maintainability | 15% | trách nhiệm parsing/tính/in có rõ không |
| Operability | 20% | stderr, exit status, cách tái hiện và regression |

## Submission format

Mỗi comment theo mẫu:

```text
Severity: blocker / high / medium / low
Location: file và dòng thêm trong diff
Problem:
Impact:
Evidence: input + state/behavior dự đoán
Suggested smallest fix:
```

Kết thúc bằng `approve`, `comment` hoặc `request changes`, giải thích các lỗi chặn merge. Nộp thêm ba ca cần chạy trước khi chấp nhận bản sửa, nhưng không cần viết lại toàn bộ chương trình.

Ôn [chuỗi](../13-chuoi-ky-tu.md), [test](../14-debug-va-kiem-thu-chuong-trinh-c.md), [capstone](../15-du-an-console-quan-ly-diem.md).
