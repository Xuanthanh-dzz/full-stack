# Module 01 verification evidence

C11 programs remain in the lessons as the single source. The verifier extracts
section 3 explicitly, builds with warnings as errors, compares exact published
stdout, and checks selected boundary/failure contracts. It also reproduces the
three dedicated lab failures without publishing their repaired solutions.

Local run on 2026-09-22: GCC 16.2.1, normal and ASan/UBSan passes. JSON records
program hashes and individual assertions. This is not a GitHub Actions run and
not maintainer approval. Exercise solutions and exhaustive input coverage are
not implied by these reports.

From repository root:

```bash
python scripts/verify_module_01.py --report /tmp/module01.json
python scripts/verify_module_01.py --sanitize --report /tmp/module01-sanitizers.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict
```

The last command requires `requirements-docs.txt`. The workflow runs the same
checks on Ubuntu 24.04 and publishes fresh reports as Actions artifacts.
