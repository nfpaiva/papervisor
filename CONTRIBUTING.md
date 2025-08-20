# Contributing to Papervisor

Thank you for your interest in contributing to Papervisor! We welcome contributions from the community to improve the tool, add features, fix bugs, and enhance documentation.

## 📝 How to Pick Up or Propose an Issue

- **Want to work on an existing issue?**
  - Comment on the issue to let maintainers know you’d like to take it.
  - Wait for a maintainer to confirm or assign you before starting work. This avoids duplicate effort.
- **Have an idea or found a bug?**
  - Open a new issue describing your proposal or the problem.
  - Discuss with maintainers to confirm the scope and approach before you begin coding.

This helps keep the project organized and ensures your work is aligned with current priorities.

## 🚦 Contribution Workflow

1. **Fork the repository** and create a new branch for your feature or fix.
2. **Write clear, well-documented code** and add or update tests as needed.
3. **Run pre-commit hooks and tests locally** to ensure code quality and compliance:
   - Run `pre-commit run --all-files` to check formatting, linting, security, and hygiene.
   - Run `pytest --cov` to ensure tests pass and coverage is reported.
4. **Push your branch** and open a pull request (PR) with a clear description of your changes.
5. **Participate in code review** and address any feedback.
6. Once approved, your PR will be merged!

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

For details on running checks locally, see the pre-commit and test sections above.

## Need Help?

If you have questions or want to discuss ideas, open an issue or join the discussion tab. We look forward to your contributions!
