# CI and Package Modernization Implementation Plan

**Goal:** Release Django Shared Property 1.0.0 with an explicit, actively supported Python/Django matrix and distribution-first CI/tox verification.

**Architecture:** Package metadata establishes Python `>=3.10` and Django `>=5.2,<6.2` as the public contract. Tox and GitHub Actions enumerate only compatible interpreter/framework pairs, install a built wheel without source-path injection, and exercise each pair on SQLite and PostgreSQL.

**Tech Stack:** Poetry, tox, pytest, pytest-django, GitHub Actions, PostgreSQL, Python build frontend.

---

### Task 1: Establish the 1.0 package contract

**Files:**
- Modify: `pyproject.toml:1-54`
- Modify: `src/django_shared_property/__init__.py:1-7`
- Modify: `setup.cfg:1-15`
- Modify: `README.rst:20-35`
- Modify: `HISTORY.rst:1-5`
- Create: `tests/tests/test_package_metadata.py`

**Step 1: Write the failing metadata assertion**

Assert that the Poetry version is `1.0.0`, Python is `>=3.10`, Django is `>=5.2,<6.2`, and `django_shared_property.__version__` is `1.0.0`.

**Step 2: Run the new test to verify it fails**

Run: `uv run --with pytest --with 'Django>=5.2,<6.2' pytest tests/tests/test_package_metadata.py -q`

Expected: FAIL because the existing metadata does not define the new contract.

**Step 3: Implement the package contract**

Set the Poetry and module versions to `1.0.0`; update bump2version’s current version. Set `python = ">=3.10"` and add `Django = ">=5.2,<6.2"` under runtime dependencies. Replace the old Python classifiers with 3.10 through 3.14. Document the supported matrix in the README and breaking compatibility change in HISTORY.

**Step 4: Run the test to verify it passes**

Run: `uv run --with pytest --with 'Django>=5.2,<6.2' pytest tests/tests/test_package_metadata.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add pyproject.toml src/django_shared_property/__init__.py setup.cfg README.rst HISTORY.rst tests/tests/test_package_metadata.py && git commit -m 'feat!: define supported Python and Django versions'`

### Task 2: Make tox test installed artifacts on valid combinations

**Files:**
- Modify: `tox.ini:1-75`

**Step 1: Replace the legacy Cartesian environment list**

Use these factors:

```ini
envlist =
    py{310,311}-django52-{sqlite,postgres}
    py{312,313,314}-django{52,60,61}-{sqlite,postgres}
```

**Step 2: Remove source-path bypasses and pin framework factors**

Remove `skipsdist`, `skip_install`, and `PYTHONPATH`. Let tox build/install the wheel. Use factor constraints `django52: Django>=5.2,<5.3`, `django60: Django>=6.0,<6.1`, and `django61: Django>=6.1,<6.2`. Keep `DATABASE_URL=sqlite:memory:` only for SQLite; require an externally supplied `DATABASE_URL` for postgres.

**Step 3: Verify the environments and one installed-wheel run**

Run: `tox -l`

Expected: the 22 supported Python/Django/database environments, plus lint environments, and no old Python/Django factors.

Run: `tox -e py310-django52-sqlite`

Expected: PASS with the package imported from tox site-packages.

**Step 4: Commit**

Run: `git add tox.ini && git commit -m 'ci: test installed package across supported tox matrix'`

### Task 3: Replace GitHub Actions with a distribution-first matrix

**Files:**
- Modify: `.github/workflows/django.yml:1-55`

**Step 1: Define supported pairs explicitly**

Use `matrix.include` for Django 5.2 with Python 3.10–3.14 and Django 6.0/6.1 with Python 3.12–3.14. Expand every pair across `sqlite` and `postgres` for 22 jobs.

**Step 2: Add the clean artifact install check**

Remove global `PYTHONPATH` and the Python container. Build a wheel using `python -m build --wheel`, install it into the fresh job environment, then import both `django` and `django_shared_property`. This step runs before test-only dependencies and proves the wheel declares Django.

**Step 3: Run version-pinned tests using the wheel**

Install the exact matrix Django version and test requirements, reinstall `dist/*.whl` with `--no-deps`, then run `pytest --cov=django_shared_property -s tests/tests/`. SQLite uses `DATABASE_URL=sqlite:memory:`; PostgreSQL uses the named CI service URL with a health check.

**Step 4: Validate workflow syntax**

Run: `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/django.yml")'`

Expected: exit 0.

**Step 5: Commit**

Run: `git add .github/workflows/django.yml && git commit -m 'ci: verify built wheel on supported Django matrix'`

### Task 4: Refresh dependencies and validate the release artifact

**Files:**
- Modify: `poetry.lock`

**Step 1: Regenerate the lockfile**

Run: `poetry lock`

Expected: Django is recorded as a direct runtime dependency compatible with Python `>=3.10`.

**Step 2: Validate the lock and wheel**

Run: `poetry check --lock`

Expected: exit 0.

Run: `python -m build --wheel && python -m pip install --force-reinstall dist/*.whl && python -c 'import django; import django_shared_property'`

Expected: exit 0; Django is installed while resolving the built wheel.

**Step 3: Re-run a representative supported environment**

Run: `tox -e py310-django52-sqlite`

Expected: PASS. Run a PostgreSQL tox environment only with an intentionally supplied `DATABASE_URL`; CI supplies the full matrix evidence.

**Step 4: Commit**

Run: `git add poetry.lock && git commit -m 'build: refresh lockfile for Django 1.0 support policy'`

### Task 5: Final branch verification and handoff

**Files:**
- Verify: all changed files

**Step 1: Check the complete diff**

Run: `git diff main...HEAD --check && git status --short`

Expected: no whitespace errors and only intentional changes.

**Step 2: Run the fast verification set**

Run: `poetry check --lock && tox -e py310-django52-sqlite`

Expected: both commands pass.

**Step 3: Record CI-only evidence**

State that GitHub Actions supplies the complete 22-job SQLite/PostgreSQL matrix, and local PostgreSQL is intentionally opt-in via `DATABASE_URL`.
