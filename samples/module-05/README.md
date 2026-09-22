# Module 05 verification evidence

Run `python scripts/verify_module_05.py --report /tmp/module05-release.json` and repeat with `--configuration Debug`. Use `--dotnet` for an isolated SDK executable. SDK 9.0.121 is pinned in temporary global.json; published projects target net9.0/C#13 with nullable and warnings as errors.

The verifier extracts each primary program from section 3, preserving the ten-file capstone manifest and published project XML. It compares exact documented output except lesson 18, whose measured timing/allocation values are validated structurally without speed thresholds. Process status and stderr are checked; capstone intentionally returns 1 for its invalid fixture and 2 for incorrect usage.

Independent contracts cover lookup identity/duplicate rejection, multicast stopping at exceptions, event threshold and committed state, closure storage, defensive copies, nullable boundaries, the documented public-init record limitation, pricing boundaries, controlled async completion, cancellation/timeout, deterministic lost updates, resource cleanup, reflection/dynamic errors, finite span parsing, variance identity, expression parameter binding, strict JSON and independent CSV output oracles.

Compiler-negative cases require specific diagnostics for generic constraints, external event assignment, static-lambda capture, nullable dereference, required members, Span across await, invalid variance/invariance and statement expression trees. Four Failure Labs reproduce documented faulty behavior.

Capstone contracts exercise malformed/null/missing files, decimal overflow, pre-cancellation, validation before scheduling, subscriber/validator faults, permit reuse, report preservation on canceled write, cleanup after failed move and disposal. No assertion depends on thread ID, arbitrary sleep or speedup. This does not certify all extension exercises, AOT/trimming, power-loss durability, concurrent report writers, every payload size or human competency. C# Foundation requires separate learner/reviewer evidence.
