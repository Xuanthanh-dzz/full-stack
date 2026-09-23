# Module 04 verification evidence

Run `python scripts/verify_module_04.py --report /tmp/module04-release.json` and repeat with `--configuration Debug`. The isolated verifier pins SDK 9.0.121 with global.json, targets net9.0/C#13 and builds published code with warnings as errors. Use `--dotnet /path/to/dotnet` for a separate SDK installation.

Each lesson's primary C# source is extracted from section 3. Lesson 14 uses the two published project files and builds a real solution; lesson 16 preserves the seven-file source manifest. A basic console project is supplied only when a lesson relies on template defaults. No NuGet test package is needed.

Expected output files were reviewed against the published examples and arithmetic/state trace. They include the entire output, including sections abbreviated in lessons 03 and 06. The environment selects en-US formatting. Only generated GUIDs and measured durations are normalized; other output, stderr and exit codes are checked. Lesson 02 deliberately keeps its introductory void Main and returns process status 0 for rejected input; rejection is asserted by exact error text and absence of a payable total. Capstone defines and checks explicit nonzero failure codes.

Contracts cover ref output/stock on overflow; transfer conservation and unchanged balances on destination overflow; inventory limits; virtual dispatch; struct default/copy and unknown enum bits; compensation after failed file persistence; hash equality/FIFO/undo; Release and Debug guards; and candidate/snapshot isolation on failed add/done/remove. Negative compilation must produce the expected diagnostics for required/init/private setters and internal access across assemblies.

Capstone tests execute separate processes for add/list/done/remove, inspect JSON, preserve timestamps, reject bad input/JSON/duplicate IDs/ID exhaustion without changing bytes, and force temporary-write failure by placing a directory at the temporary-file path. A fake repository throws before persistence to verify memory state. These tests do not simulate every I/O outcome, writes that succeed before a repository throws, concurrent writers or power loss.

Three Failure Labs compile and reproduce documented incorrect state/dispatch. The verifier does not certify manual IDE breakpoint/Watch work, every explanatory fragment or extension exercise, or human teaching quality. Maintainer review remains separate.
