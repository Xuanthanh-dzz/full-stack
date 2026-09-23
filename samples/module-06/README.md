# Module 06 verification

SDK 9.0.121, net9.0, C# 13. Verifier extracts published projects and primary sources directly from all 14 lessons, builds with warnings as errors and checks exact stdout, empty stderr and process exit. Independent contracts cover mutation guards, lifetime identity, business rejection, rounding/caps, seeded state transitions, characterization and report I/O failures. Negative compile cases verify access and capability restrictions. Three Failure Labs execute their documented failing behavior.

Run `python scripts/verify_module_06.py --report artifacts/module06-release.json`; repeat with `--configuration Debug`. Use `--dotnet /path/to/dotnet` for an isolated SDK. Reports hash published sources. These checks do not prove equivalence outside documented input domains, all exercise solutions, thread safety or crash durability. Human teaching review remains required.
