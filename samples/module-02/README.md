# Module 02 verification evidence

Run from repository root:

```bash
python scripts/verify_module_02.py --report /tmp/module02.json
python scripts/verify_module_02.py --sanitize --report /tmp/module02-sanitizers.json
```

The reports record the actual compiler, date, source SHA-256 and checks. Sources are extracted from section 3 with an explicit per-lesson file manifest; no largest-block heuristic. All 15 published primary programs have exact stdout/empty stderr/exit-status assertions. Both trace configurations, the two published Makefiles and header dependencies are exercised; sanitizers compile translation units directly. The supplemental `try_divide` function is compiled with zero/overflow/NULL tests.

Contract harnesses cover selected boundary and failure cases. The capstone injects failure into each of its three initial allocation sites, checks growth/removal/disposal, roundtrips a file and rejects malformed files while preserving the destination. These tests do not simulate power loss, every OS I/O failure, concurrent writers or hostile paths. The sample persistence contract remains one writer in a private trusted directory.

Three Failure Labs reproduce their documented bugs. The use-after-free lab deliberately keeps compiler warnings nonfatal to reach the AddressSanitizer report; all primary programs and contracts use `-Werror`. The buggy labs are not fixed learner submissions.

Mechanism fragments, declarations, deliberately invalid examples and exercise prompts outside section 3 are teaching excerpts, not all standalone programs. They were reviewed in context; this report does not claim every fragment or possible exercise solution was executed. Automated clarity/link checks do not replace human teaching-quality review.
