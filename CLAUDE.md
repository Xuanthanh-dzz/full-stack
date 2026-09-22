# Claude Code instructions for this repository

Before authoring or editing curriculum content, read in order:

1. `fullstack-roadmap/00-huong-dan/glossary-style-guide.md`
2. `fullstack-roadmap/00-huong-dan/lesson-authoring-standard.md`
3. `fullstack-roadmap/PROGRESS.md`
4. the previous and next lesson when they exist.

Mandatory rules:

- Treat the glossary/style guide as canonical.
- Module 09+ must follow Lesson Authoring Standard v4.
- Do not mark a lesson complete until its verifier/CI passes.
- Use the version baseline declared in lesson metadata.
- Separate “Lỗi thường gặp” from “Khi nào KHÔNG dùng”.
- Include TL;DR, scale context, judgment exercise and retrieval practice.
- Prefer the simplest solution that satisfies the stated scale.
- Never add architecture/patterns without a concrete driver.
- Update `Last verified` only after rerunning the relevant sample/tests.

- For Module 09+, add dedicated Failure Labs at the cadence defined by the standard.
- Add spaced review checkpoints after each 4–6 lesson cluster.
- Add at least one PR/code-review lab per technical module.
- Add the career checkpoint artifact when the module is a defined career milestone.

- Explain new concepts beginner-first: intuition → vocabulary → tiny example → execution trace → mechanism → production.
- Do not use a new technical term before defining it in plain language.
- For difficult concepts, include a comparison table, misconception check, and a step-by-step walkthrough.
- A lesson is not complete if a learner cannot explain where code runs, what state is kept, and where cost lives.
