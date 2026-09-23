# Module 08 verification

SQL Server 2025 (17.x), compatibility level 170, sqlcmd tools18. The verifier requires a disposable container labelled `fullstack.module08.verifier=1`, a name in `MODULE08_SQL_CONTAINER`, and a lab password in `MODULE08_SA_PASSWORD`. It refuses unlabelled targets. Follow `.github/workflows/verify-module-08.yml` to create a fresh container without host ports or application volumes; never label an existing application container as a verifier target.

```bash
python scripts/verify_module_08.py --report artifacts/module08-verification.json
python -m unittest discover -s scripts/tests -v
python -m mkdocs build --strict --site-dir /tmp/fullstack-site
```

`--samples-only` is for initial runtime verification while freshness metadata is pending; it does not pass the full module gate. The regular command checks the v4 gate after SQL, saving runtime evidence first. Reports record engine build, image ID, compatibility, source and contract hashes. SQL stdout/stderr and actual plan XML are uploaded as CI artifacts.

The manifest executes all primary SQL blocks, both deadlock sessions and actual backup/restore/CHECKDB. Assertions cover query results/state, expected constraint/permission errors, trigger rowsets/rollback, RCSI committed reads and checkout failure variants. Five Failure Labs reproduce their documented faulty behavior. Fixed timings and physical plan choices are not correctness thresholds.

Local Docker access is unavailable in the authoring workspace; runtime evidence must come from the isolated GitHub runner. SQL exercises outside the manifest, international name parsing, every isolation anomaly, payment-provider integration and production RPO/RTO still require separate work/review.
