# Module 07 verification

SDK 9.0.121, net9.0, C# 13. All 19 published projects and primary sources build with warnings as errors in Release and Debug. Verifier checks stdout, stderr and exit; stopwatch values are not performance thresholds and equal-priority tickets may be reordered.

Independent contracts compare arrays/lists/trees with standard collections, sorting/search with independent oracles, greedy/backtracking with small exhaustive cases, coin change with BFS and route distances with Floyd–Warshall. Boundary cases cover normalization, overflow, snapshots and rejected inputs. Four Failure Labs reproduce documented faults.

Run `python scripts/verify_module_07.py --report artifacts/module07-release.json`; repeat with `--configuration Debug`. Use `--dotnet /path/to/dotnet` for an isolated SDK. Reports hash published source/project files. Checks do not certify all exercises, a runtime MST implementation, benchmarks or concurrent mutations. Maintainer teaching review remains pending.
