# papervisor
Papervisor is a modular, open-source pipeline for accelerating systematic literature reviews. It combines automation, NLP, and human-in-the-loop screening to help researchers move from raw academic search results to a curated, thematically structured review — fast and reproducibly.

## Continuous Integration & Code Quality

Papervisor uses a robust CI/CD pipeline and pre-commit hooks to ensure code quality, security, and maintainability. The following tools and checks are enforced both locally and in CI:

- **pytest & pytest-cov**: Runs all tests and enforces a minimum code coverage threshold (currently 20%). Coverage reports are uploaded as CI artifacts. The low threshold reflects the current focus on stabilization; it will be increased as the codebase matures.
- **Xenon**: Enforces strict cyclomatic complexity limits (hard gate).
- **Radon (Maintainability Index)**: Reports maintainability scores but does not block CI (report-only) due to current codebase state. This will be revisited after refactoring.
- **Bandit**: Scans for security issues in Python code. False positives are whitelisted with `# nosec` and tracked for future review.
- **Vulture**: Detects unused code. Whitelisting is managed in `vulture_whitelist.py` for intentional exclusions.
- **Eradicate**: Flags commented-out/dead code.
- **Interrogate**: Checks for missing docstrings.
- **Detect-secrets**: Prevents committing secrets. Baseline is tracked in `.secrets.baseline`.
- **Deptry**: Detects unused, missing, or misplaced dependencies. Dev tools are ignored as needed for pip compatibility.

### Rationale & Notes
- **Parity**: The order and configuration of checks are kept in sync between pre-commit and CI for reliability.
- **Coverage**: The 20% threshold is temporary and will be raised as more tests are added.
- **Maintainability**: Radon MI is report-only to avoid blocking on legacy code; Xenon is enforced for new complexity.
- **Whitelisting**: All whitelists (Bandit, Vulture, Detect-secrets, Deptry) are maintained in the repo for transparency and future cleanup.
- **Artifacts**: CI uploads HTML coverage reports for review.

For details on running checks locally, see the pre-commit and test sections below (to be expanded).
