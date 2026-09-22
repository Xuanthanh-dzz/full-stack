# Lesson Authoring Standard v2

> Áp dụng bắt buộc cho Module 09 trở đi. Module 01–08 sẽ được retrofit sau.
>
> Canonical style/terminology: [Glossary & Style Guide](./glossary-style-guide.md).

## 1. Definition of Done mới

Một bài chỉ được đánh dấu hoàn thành khi:

- file tồn tại đúng manifest;
- đủ cấu trúc bắt buộc;
- code chính chạy/compile;
- command tái tạo được;
- cross-link hợp lệ;
- có TL;DR;
- có mục **Khi nào KHÔNG dùng**;
- có production/scale note khi kỹ thuật có trade-off vận hành;
- có bài tập retrieval và ít nhất một bài judgment/tích hợp khi phù hợp;
- có metadata `Last verified`, version baseline và review cycle;
- verifier CI của module pass;
- MkDocs build pass.

## 2. Cấu trúc bắt buộc của mỗi bài

### Metadata — trước nội dung chính

Mẫu:

```markdown
> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.x · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** major SDK/provider update, breaking change, sample CI failure
```

Foundation ít biến động có thể dùng 180 ngày. Web/framework/cloud nên 90–120 ngày.

### TL;DR — đúng 3 dòng

Đặt trước “Bài toán mở đầu”.

Ba dòng phải trả lời:

1. Đây là gì?
2. Khi nào dùng?
3. Trade-off/rủi ro chính là gì?

Không biến TL;DR thành mục lục.

### 1. Mục tiêu

4–8 outcome có thể kiểm tra.

Tránh “hiểu X” nếu không nói người học phải làm được gì.

### 2. Bài toán mở đầu

Bắt đầu bằng vấn đề thật, không bắt đầu bằng định nghĩa API.

### 3. Lời giải chạy được

- Code hoàn chỉnh tối thiểu.
- Có command setup/build/run/test.
- Comment giải thích phần khó, không comment từng dòng hiển nhiên.
- Expected output hoặc assertion khi hợp lý.

### 4. Cơ chế hoạt động

Giải thích runtime/database/network mechanism.

Có sơ đồ text/memory/data-flow nếu giúp reasoning.

### 5. Kiến thức nền và prerequisites

Nêu dependency kiến thức, liên hệ bài/module trước.

### 6. Lỗi thường gặp

Đây là trường hợp **dùng đúng kỹ thuật nhưng triển khai sai**.

Ví dụ:

- query đúng intent nhưng materialize quá sớm;
- transaction đúng chỗ nhưng giữ quá lâu;
- async đúng use case nhưng sync-over-async.

### 7. Khi nào KHÔNG dùng

Đây là trường hợp **code có thể đúng nhưng chọn kỹ thuật sai ngữ cảnh**.

Bắt buộc tách khỏi “Lỗi thường gặp”.

Phải nêu:

- tín hiệu cho thấy kỹ thuật không đáng dùng;
- phương án đơn giản hơn;
- chi phí abstraction/ops/debug;
- ngưỡng hoặc câu hỏi quyết định nếu có.

### 8. Production notes & scale check

Tối thiểu trả lời:

- demo khác production ở đâu?
- performance/security/observability/concurrency có rủi ro nào?
- team 2–3 người / hệ thống vừa có cần kỹ thuật này chưa?
- khi nào nên nâng cấp sang giải pháp phức tạp hơn?

Với kỹ thuật enterprise như K8s, Saga, distributed lock, microservices:
phải có subsection **“Ở quy mô nhỏ có thật sự cần không?”**.

### 9. Bài tập kỹ thuật

3–5 bài, có hint nhưng không full solution.

Ít nhất một bài yêu cầu debug/fix code sai nếu chủ đề phù hợp.

### 10. Bài tập tích hợp liên module — Judgment

Không chỉ “hãy dùng kỹ thuật vừa học”.

Phải bắt người học quyết định **giải ở tầng nào** và bảo vệ lựa chọn.

Ví dụ:

- SQL hay LINQ in-memory?
- index hay cache?
- constraint DB hay validation application?
- DSA hay query SQL?
- transaction DB hay message/outbox?
- monolith hay microservice?

Chấm cả reasoning, không chỉ output.

### 11. Retrieval practice

3–5 câu không nhìn tài liệu:

- giải thích bằng lời;
- dự đoán output;
- sketch mechanism;
- nêu trade-off;
- chọn giữa hai giải pháp.

### 12. Checklist tự đánh giá & điều hướng

Checklist phải kiểm tra khả năng:

- build;
- debug;
- giải thích;
- đo;
- chọn đúng kỹ thuật.

Có link bài trước / bài sau / prerequisite liên module.

## 3. Failure-driven learning

Mỗi 3–5 bài phải có ít nhất một lab bắt người học sửa lỗi thật:

- N+1;
- stale tracking;
- race condition;
- deadlock;
- missing index;
- wrong lifetime;
- invalid cache;
- retry duplicate;
- memory leak/resource leak;
- auth/config mistake.

Không đưa đáp án ngay trước bài tập.

## 4. Must know / Should know / Deep dive

Khi bài dài, chia rõ:

- **Must know:** cần để đi tiếp/đi làm;
- **Should know:** tăng chất lượng implementation;
- **Deep dive:** dành cho Mid/Senior/Architect.

Không bắt beginner học thuộc Deep dive để qua module.

## 5. Project xuyên suốt

Từ Module 08 trở đi, ưu tiên cùng domain **CommerceLab**:

```text
SQL schema
→ EF Core data access
→ ASP.NET Core API
→ React/Angular
→ tests
→ Docker/CI
→ observability
→ architecture
```

Capstone module phải để lại artifact có thể dùng làm input cho module sau.

## 6. Rubric project

Mỗi capstone chấm tối thiểu:

| Nhóm | Trọng số gợi ý |
|---|---:|
| Correctness | 25% |
| Data/model/API design | 15% |
| Error handling & edge cases | 10% |
| Testability & tests | 15% |
| Performance | 10% |
| Security | 10% |
| Maintainability/readability | 10% |
| Documentation & reproducibility | 5% |

Không dùng điểm để “xếp hạng con người”; rubric dùng để chỉ ra gap kỹ năng.

## 7. Entry test / Exit test

Mỗi module mới nên có:

- Entry test: 10–15 câu/task ngắn từ prerequisites.
- Exit test: 1–3 task thực hành không copy sample.
- Capstone: tích hợp nhiều kỹ năng.

Fail entry test không cấm học; nó chỉ chỉ ra bài cần ôn.

## 8. Last verified & freshness

Mỗi bài mới phải có metadata.

Reverify khi:

- quá `Review cycle`;
- major .NET/EF/React/Angular/SQL/SDK thay đổi;
- breaking-change note ảnh hưởng API;
- sample CI fail;
- security advisory ảnh hưởng code mẫu.

CI freshness chạy định kỳ và báo bài stale.

## 9. Quy mô nhỏ trước, enterprise sau

Mọi nội dung Architect phải trả lời:

> Nếu team 2–3 người, traffic vừa, deployment đơn giản — giải pháp nhỏ nhất đủ tốt là gì?

Chỉ nâng cấp khi có driver cụ thể:

- scale;
- team ownership;
- isolation;
- compliance;
- availability;
- deploy independence;
- data boundary;
- measured bottleneck.

## 10. Không pattern worship

Mỗi pattern/technology phải có:

```text
Problem
→ simplest solution
→ failure mode
→ threshold/driver
→ stronger solution
→ operational cost
```

Nếu không chỉ ra driver, không được khuyến nghị abstraction phức tạp.

## 11. Quality gate cho AI tool

Trước khi commit bài mới, AI phải tự check:

- thuật ngữ canonical;
- style code;
- version baseline;
- links;
- runnable sample;
- TL;DR 3 dòng;
- section 7 “Khi nào KHÔNG dùng”;
- scale note;
- judgment exercise;
- retrieval practice;
- metadata freshness.

## 12. Quy tắc sửa bài cũ

Khi retrofit Module 01–08:

1. không đổi concept đúng chỉ để đồng nhất văn phong;
2. thêm metadata/TL;DR/sections thiếu;
3. chạy lại sample;
4. sửa terminology/style;
5. thêm judgment/production note;
6. chỉ tick verified sau CI.
