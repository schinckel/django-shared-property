# CI and Package Modernization Design

## Problem statement

The project currently advertises and tests incompatible Python/Django combinations,
does not declare Django as a runtime dependency, and runs CI and tox from the source
tree rather than from the built distribution. PostgreSQL tox runs also have no valid
default connection configuration. These gaps can hide broken package artifacts and
make the public support policy unclear.

## Chosen approach

Release version 1.0.0 with an actively supported compatibility policy:

- Python `>=3.10`
- Django `>=5.2,<6.2`

The upper Django bound represents the explicitly tested release series. It avoids
silently claiming compatibility with a future major/minor series before CI evidence
exists.

## Design details

### Package metadata and documentation

- Update the distribution version to `1.0.0` in all release-version sources.
- Declare Django as a required runtime dependency with the chosen range.
- Align Python classifiers and `Requires-Python` with Python 3.10 through 3.14.
- Document the support policy and standard installation path in the README.

### Compatibility matrix

CI and tox will cover only valid combinations:

| Django | Python |
| --- | --- |
| 5.2 | 3.10, 3.11, 3.12, 3.13, 3.14 |
| 6.0 | 3.12, 3.13, 3.14 |
| 6.1 | 3.12, 3.13, 3.14 |

Each pair runs against SQLite and PostgreSQL.

### Distribution-first verification

- Build a wheel from the repository.
- Install that wheel into an isolated test environment, without adding the source
  tree to `PYTHONPATH`.
- Run the suite using the installed package.
- Add an explicit package metadata/import validation so an undeclared Django
  dependency fails CI.

### Database configuration

- CI supplies a PostgreSQL service and a concrete connection URL.
- Local tox PostgreSQL environments require `DATABASE_URL` explicitly rather than
  relying on an invalid placeholder.

## Testing strategy

- Run every supported matrix pair for both database backends in GitHub Actions.
- Verify tox generates the same valid set of environments and installs the package.
- Build and inspect/install the wheel in a clean environment.
- Run a representative local SQLite tox environment and the package metadata check.

## Acceptance criteria

1. Version 1.0.0 is consistent across package metadata and source.
2. Installing the wheel brings in Django without a separate manual Django install.
3. CI and tox contain no unsupported Python/Django pairs.
4. CI executes tests from the installed wheel, not `src/` via `PYTHONPATH`.
5. PostgreSQL CI uses a working service URL; local PostgreSQL tox requires an
   intentional URL.
6. README and classifiers accurately state the supported matrix.

## Deferred work

- Parser support for arithmetic `CombinedExpression`s.
- Recursive handling of nested `Q` expressions and retargeting.
- JSON test expectation cleanup and related-property limitation coverage.
