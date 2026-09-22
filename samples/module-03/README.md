# Module 03 verification evidence

Run `python scripts/verify_module_03.py --report /tmp/module03.json` and repeat with `--sanitize`. Reports include compiler, date, source hashes and concrete checks.

The verifier extracts the single C++20 program from section 3 of each of 14 lessons. It checks exact stdout, stderr and status; lesson 01 uses piped stdin and therefore excludes terminal input echo from its transcript assertion. Lessons 11 and 14 also have exact file assertions in isolated temporary directories.

Contract tests cover invoice input rejection, output preservation, account limits, independent copy, self-copy/self-move through aliased helper arguments, moved-from IntBuffer reuse, slicing, wallet limits, stack boundaries, exception types, unique/weak lifetime, forwarding and library business rejections. Template tests require compilation to fail for zero capacity and nonnumeric clamp. File failure tests use nonexistent parent paths; they do not simulate every filesystem failure or power loss.

Three labs reproduce double free, vector reference invalidation and loss of state despite RAII. Deliberately faulty labs retain warnings without Werror to reach sanitizer evidence. Primary programs and contract harnesses build with Werror. The suite does not claim all explanatory fragments or exercise solutions are independent executable programs. Human clarity review remains a separate gate.
