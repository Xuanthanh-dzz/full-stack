# Spaced Review 02 — Hợp đồng và lifetime

Làm sau cụm bài (6, 10); quay lại sau 2 ngày và 1 tuần. Không mở bài trong lượt đầu; ghi tự tin trước khi đối chiếu.

## Retrieval

1. False của IWithdrawable có nghĩa chỉ thiếu tiền không?
2. Role interface có là boundary bảo mật không?
3. Exists/Save giữ được uniqueness đồng thời không?
4. Scope giữ handler lâu thì context còn sống không?
5. Ôn event subscriber Module 05: reference nào kéo dài lifetime?

## Dự đoán output

1. Hai scopes dùng chung store: Place A ở cả hai trả gì?
2. Đơn 550.000, threshold 500.000 rồi 1 triệu: bản static và hai instance khác ra sao?

## Debug

Notifier ném sau Save; trace trạng thái và vì sao retry toàn service chưa chắc gửi lại được. Ghi input tối thiểu, trạng thái trước/sau, nguyên nhân và regression test trước khi sửa.

## Judgment liên module

100 request tuần tự hay đồng thời: chọn lifetime store/log, chỉ ra điều cần test trước khi thêm khóa. Nêu contract, nơi code chạy, state được giữ, cost và lựa chọn đơn giản nhất.

## Self-score

Retrieval 10 điểm (mỗi câu 2), trace 4 điểm, debug 3 điểm, judgment 3 điểm. Đạt 16/20 và không bỏ sót lỗi thay đổi state/vòng đời. Câu sai: ghi bài cần ôn rồi dùng ví dụ khác để kiểm lại sau 2 ngày.

[Bản đồ](../index.md).
