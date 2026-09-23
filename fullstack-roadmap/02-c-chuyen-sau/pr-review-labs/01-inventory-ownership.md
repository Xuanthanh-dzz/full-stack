# PR Review — Quyền sở hữu trong kho C

Bối cảnh: dự án một process, một writer, vài chục sản phẩm. PR rút ngắn các thao tác với kho; test happy path đang xanh. Đây là diff huấn luyện độc lập, không áp trực tiếp vào repo. Product nằm trong mảng do Inventory sở hữu; code/name là hai allocation riêng. `reserve` chỉ đổi sức chứa, không đổi số phần tử đang dùng; caller đã kiểm tra giới hạn capacity. `load` lỗi phải giữ dữ liệu cũ. Mã sản phẩm khớp chính xác; kết quả `save` phải phản ánh cả lỗi đóng stream.

## Diff

Đọc [patch inventory-ownership.diff](./diffs/inventory-ownership.diff). Review toàn bộ patch; không chỉ tìm warning compiler.

## Nhiệm vụ review

- Vẽ state và owner trước/sau mỗi thao tác ở đường thành công và thất bại.
- Phân loại blocker/major/minor; mỗi finding phải có vị trí, input hoặc điều kiện tái hiện và hậu quả cụ thể.
- Kiểm tra implementation có giữ các contract nêu trong bối cảnh không; phân biệt lỗi của PR với giả định caller phải đáp ứng.
- Đề xuất regression test có expected behavior rõ và sửa nhỏ nhất sau lượt review độc lập.
- Đánh giá đề xuất dùng hash table với vài chục sản phẩm: cần evidence nào trước khi tăng độ phức tạp?

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Trong review, xét correctness, performance, security, maintainability và operability; nếu một nhóm không có finding, ghi lý do thay vì bịa lỗi. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

| Tiêu chí | Điểm |
|---|---:|
| Correctness của state, lookup và I/O | 35 |
| Ownership và failure trace | 25 |
| Regression test có expected behavior rõ | 20 |
| Chọn sửa nhỏ phù hợp quy mô | 10 |
| Comment rõ mức độ, vị trí, đề xuất kiểm chứng | 10 |

Từ 80/100 và không bỏ sót lỗi giải phóng sai mới đạt. Nhận xét chỉ nói “code smell” không có evidence không được điểm correctness.

</details>

## Submission format

Nộp bảng `file/hunk | severity | evidence | đề xuất | test`, kết luận approve/request changes và diff sửa tối thiểu sau khi review. Không đưa lời giải đầy đủ trước lượt review độc lập. [Quay lại module](../index.md).
