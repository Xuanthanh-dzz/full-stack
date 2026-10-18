# PR Review — Quyền sở hữu trong kho C

Bối cảnh: dự án một process, một writer, vài chục sản phẩm. PR rút ngắn reserve/destroy/load; test happy path đang xanh. Đây là diff huấn luyện độc lập, không áp trực tiếp vào repo. Product nằm trong mảng do Inventory sở hữu; code/name là hai allocation riêng. Caller cần dữ liệu cũ nguyên vẹn khi load lỗi. Giới hạn capacity đã được caller kiểm tra trước reserve; tập trung cả lỗi mới lẫn giả định contract cần xác minh.

## Diff

Đọc [patch inventory-ownership.diff](./diffs/inventory-ownership.diff). Phải review cả ba hunk; không chỉ tìm warning compiler.

## Nhiệm vụ review

- Phân loại blocker/major/minor với vị trí, cách tái hiện và hậu quả cụ thể.
- Vẽ owner của items, Product và hai chuỗi; đánh giá free(product) khi product là &items[1].
- Trace realloc thất bại và load lỗi giữa file; chỉ rõ state nào mất.
- Đề xuất test allocation failure, remove phần tử giữa, malformed file giữ destination; chỉ thêm test có thể bắt regression.
- Đánh giá yêu cầu “dùng hash table ngay để nhanh hơn”: cần đo gì trước khi chấp nhận với quy mô này?

## Rubric

| Tiêu chí | Điểm |
|---|---:|
| Bắt đúng mất owner và invalid free, có trace | 30 |
| Contract load và giữ state khi lỗi | 25 |
| Regression test có expected behavior rõ | 20 |
| Chọn sửa nhỏ phù hợp quy mô | 15 |
| Comment rõ mức độ, vị trí, đề xuất kiểm chứng | 10 |

Từ 80/100 và không bỏ sót lỗi giải phóng sai mới đạt. Nhận xét chỉ nói “code smell” không có evidence không được điểm correctness.

## Submission format

Nộp bảng `file/hunk | severity | evidence | đề xuất | test`, kết luận approve/request changes và diff sửa tối thiểu sau khi review. Không đưa lời giải đầy đủ trước lượt review độc lập. [Quay lại module](../index.md).
