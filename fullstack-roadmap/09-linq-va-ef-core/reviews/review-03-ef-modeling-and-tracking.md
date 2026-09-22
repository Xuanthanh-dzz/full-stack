# Spaced Review 03 — EF model, migration và tracking (bài 11–15)

## Retrieval

1. Vì sao `DbContext` không nên singleton?
2. Convention, Data Annotation và Fluent API khác nhau ở ownership nào?
3. Migration snapshot dùng để làm gì?
4. `DbContext` đã cung cấp behavior nào của Unit of Work?
5. Khi nào many-to-many cần explicit join entity?

## Dự đoán behavior

1. Một entity tracked được sửa property rồi `SaveChanges`. EF cần những state/original value nào?
2. Migration rename bị generate thành drop/add. Rủi ro production là gì?

## Debug

Developer dùng `context.Update(mappedDto)` trên detached entity và vô tình overwrite field không có trong request. Hãy mô tả root cause và chiến lược update an toàn hơn.

## Judgment liên module

DB production 500GB cần đổi column nullable → NOT NULL. Bạn chọn migration một bước hay expand-contract? Liên hệ Module 08 backup/restore và lock.

## Ôn Module trước

- Module 08: PK/FK/constraint, migration và transaction.
- Module 06: invariant và coupling.

## Self-score

- 9–10/10: tiếp tục.
- 7–8/10: ôn bài 12–15.
- dưới 7/10: dựng lại model CommerceLab từ database sạch.
