# Spaced Review 03 — Refactor có bằng chứng

Làm sau cụm bài (11, 14); quay lại sau 2 ngày và 1 tuần. Không mở bài trong lượt đầu; ghi tự tin trước khi đối chiếu.

## Retrieval

1. Characterization khác correctness test thế nào?
2. Tại sao Money.Of không bảo vệ public positional constructor?
3. Receive dương có thể overflow không?
4. Folder Domain chặn File API không?
5. Liên hệ report temp/move Module05 với writer tuần tự Module06.

## Dự đoán output

1. Subtotal10: round riêng5%+3% khác round tổng thế nào?
2. Stock10→Reserve8→Ship3→Release5: OnHand,Reserved,Available?

## Debug

Harness4same nhưng ID/city/SKU rỗng ném; tách miền compatibility và yêu cầu sửa parser. Ghi input tối thiểu, trạng thái trước/sau, nguyên nhân và regression test trước khi sửa.

## Judgment liên module

Batch10000dòng, profiler thấy repeated subtotal: chọn đo/cache/stream theo time/memory và scope thay đổi. Nêu contract, nơi code chạy, state được giữ, cost và lựa chọn đơn giản nhất.

## Self-score

Retrieval10điểm (mỗi câu2), trace4điểm, debug3điểm, judgment3điểm. Đạt16/20 và không bỏ sót mutation/lifetime failure. Câu sai: ghi bài cần ôn rồi dùng ví dụ khác để kiểm lại sau2ngày.

[Bản đồ](../index.md).
