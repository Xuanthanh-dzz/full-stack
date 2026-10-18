# Spaced Review 01 — LINQ core (bài 01–05)

Không nhìn lại bài trước khi làm.

## Retrieval

1. Query syntax và method syntax khác nhau ở runtime thế nào?
2. `Select` khác `SelectMany` về cardinality ra sao?
3. Vì sao pagination cần deterministic ordering?
4. Khi nào `ToLookup` hợp lý hơn `GroupBy`?
5. `GroupJoin` giữ outer element khác `Join` thế nào?

## Dự đoán output / query shape

1. Dự đoán output của pipeline `Where → OrderByDescending → Skip → Take` với 8 phần tử.
2. Một Order có 4 Items và 3 Payments. Nếu join cả hai collection, số combination tối đa cho một order là bao nhiêu?

## Debug

Một developer dùng hai `OrderBy` liên tiếp rồi thắc mắc vì sort key đầu không còn tác dụng. Viết review comment giải thích lỗi và fix nhỏ nhất.

## Judgment liên module

Bạn cần top 10 SKU doanh thu cao nhất từ 30 triệu OrderItems. Chọn SQL aggregate, EF-translated `GroupBy`, hay load in-memory rồi LINQ? Nêu tiêu chí về data movement, index và plan.

## Ôn Module trước

- Module 07: Big-O của nested lookup.
- Module 08: JOIN cardinality và `GROUP BY`.

## Self-score

- 9–10/10: tiếp tục.
- 7–8/10: ôn lại bài 03–05.
- dưới 7/10: quay lại bài 01–05 và làm Failure Lab 01 sau bài 06.
