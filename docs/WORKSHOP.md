# Hands-on labs

Start with the local setup in the README and one connected CI platform. Work on
branches and open pull requests. Keep `main` healthy between exercises. The commands
below use `python` as shorthand for your development virtual environment's executable.
On Windows use `.\.venv\Scripts\python.exe`; on macOS / Linux use `.venv/bin/python`.

## 1. Follow a successful release

1. Run `python -m pytest --cov` locally.
2. Push the base project and open the CI run. Find the lint, tests, wheel build,
   installed-wheel smoke test, and artifact steps.
3. Download and extract `wheel-release`. Inspect `release.json` and the `.whl` filename.
4. Install it with `python scripts/release.py deploy --artifact-dir <extracted-directory>
   --target .deploy/downloaded-1`.
5. On the successful main run, download `staging-receipt`. Compare its version,
   commit, and checksum with `release.json`.

**Expected:** the receipt identifies the same wheel as the build. Ask which parts
would be difficult to audit if deployment simply copied a developer's working directory.

## 2. Introduce a regression and fix it

1. Run `git switch -c lab/shipping-boundary`.
2. In `src/cicd_demo/shipping.py`, change `>=` to `>` in the free-shipping comparison.
3. Run the tests. Observe that an order of exactly 5000 cents is now charged shipping.
4. Commit and push this change, then open a PR targeting `main`.
5. Find the failing test in the CI logs and reports. Confirm that the release wheel
   was not published and staging did not run.
6. Restore `>=`, commit and push. Watch the next run pass. Merge the repaired PR.

**Expected:** automation prevents a known regression from reaching staging. A
required merge check also prevents merging the failing PR. Without repository
protection, a user might still merge failing code even though deployment remains gated.

## 3. Catch a packaging mistake

1. Create `lab/missing-resource`.
2. In `pyproject.toml`, change package data from `resources/*.html` to
   `resources/*.missing`.
3. Run the normal source tests. They pass because the editable install can still
   read the HTML file from your checkout.
4. Build and deploy with `python scripts/release.py build` and
   `python scripts/release.py deploy --target .deploy/missing-resource-1`.
5. Observe the installed-wheel smoke test fail on `/`. Inspect the wheel as a ZIP
   file and notice that `resources/index.html` is absent.
6. Push the branch to see CI reject it before artifact publication. Restore the
   package-data pattern and use a fresh deployment target to confirm the fix.

**Expected:** testing source alone is insufficient. A clean wheel installation
validates the package you actually deploy. Source tests and packaging tests find
different classes of mistakes.

## 4. Add a feature with a clear contract

1. Create `lab/express-shipping`.
2. Add an optional `express` argument to `shipping_quote`, defaulting to `False`.
   Agree on the contract: express shipping costs 1200 cents regardless of subtotal;
   normal shipping keeps its existing behavior.
3. Write tests for express orders below and above 5000 cents before implementing it.
4. Extend `/api/quote` to accept `express=true` and reject unsupported values.
5. Update the packaged homepage and add an express case to `scripts/smoke_test.py`.
6. Change the package version in `pyproject.toml` to `0.2.0` and submit a PR.

**Expected:** the pipeline stays reusable while application behavior grows. Describe
which tests document business decisions and which checks prove deployability.

## 5. Make release approval visible

1. Configure a reviewer on the `staging` environment using `docs/PIPELINES.md`.
2. Merge a passing change to `main`.
3. Watch CI finish while staging waits for approval. Inspect the exact wheel and
   manifest while the deployment is waiting.
4. Approve the run and observe artifact download, installation, smoke testing, and receipt.
5. Repeat with another run and reject it. CI remains useful even though staging is blocked.

**Expected:** approval controls release, not compilation. GitHub reviewer availability
depends on repository visibility and plan. If unavailable, demonstrate Azure approvals
or discuss the same decision using the downloaded artifact.

## 6. Deploy and roll back without rebuilding

1. Before changing the version, build release A with
   `python scripts/release.py build --output-dir dist-v1`.
2. Change a visible homepage message and bump the version to `0.2.0` (or the next
   unused version if you already completed lab 4). Build release B into `dist-v2`.
3. Deploy A with `--artifact-dir dist-v1 --target .deploy/release-a`; deploy B with
   `--artifact-dir dist-v2 --target .deploy/release-b`.
4. Start B using its virtual environment's Python, visit `/health` and `/`, then stop it.
5. Start A using its virtual environment's Python. Confirm the old version and page return.
6. Compare both `installed-release.json` files. Neither rollback nor promotion needed
   a wheel rebuild.

**Expected:** retaining artifacts and selecting a previously verified release makes
rollback predictable. This lab has no database. Discuss why data migrations can make
real rollbacks more complicated.

## Further experiments

- Add a Python 3.11/3.12/3.13 test matrix, but build the promoted wheel once after
  the matrix passes. Separate compatibility tests from release packaging.
- Add an untested API branch, observe the coverage change, then add a meaningful
  test. Explain why merely raising a coverage number is not sufficient.
- Download a wheel, change its bytes, and run `release.py verify`. Observe the checksum
  failure. Explain why changing both the wheel and manifest would require stronger
  provenance controls to detect.
- Introduce a slow test and set a job timeout; discuss feedback speed and resource costs.
- Add an external runtime dependency. Explain why `--no-index --no-deps` deployment
  would need a tested wheelhouse or a controlled dependency installation strategy.
- Build the supplied Docker image from the downloaded wheel. Extend CD to a chosen
  durable host, with separate credentials and environment checks.
- Add a production environment that promotes the same artifact only after staging.
  Keep the source branch restrictions and release identity visible.
