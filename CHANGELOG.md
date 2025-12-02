# CHANGELOG

<!-- version list -->

## v2.0.0-beta.1 (2025-12-02)

### Features

- Drop Python 3.9 and 3.10 support, require Python 3.11+
  ([`72de394`](https://github.com/mit-kavli-institute/data-product-tracker/commit/72de394662ce018dcb80f790c9bc3de8ca87df50))

### Refactoring

- Rename Dockerfile.test to Dockerfile
  ([`271d66d`](https://github.com/mit-kavli-institute/data-product-tracker/commit/271d66d59ffe8cdaa8fa4afa45fd5ccf3be1a06c))

### Breaking Changes

- Python 3.9 and 3.10 are no longer supported.


## v1.0.0 (2025-07-29)


## v1.0.0-beta.4 (2025-07-29)

### Features

- Add multi-database testing support
  ([`b7a3e10`](https://github.com/mit-kavli-institute/data-product-tracker/commit/b7a3e1019e10a1a8397420eb5d25006b6805d450))

- Optimize reflection performance with bulk operations and caching
  ([`970431d`](https://github.com/mit-kavli-institute/data-product-tracker/commit/970431d9e4768dbb72c60386749e58004ae24f9d))


## v1.0.0-beta.3 (2025-07-29)

### Bug Fixes

- Add comprehensive docstrings to core modules
  ([`15e06eb`](https://github.com/mit-kavli-institute/data-product-tracker/commit/15e06eb3419dff6806d425c70b6f36aafa5f514f))

- Add missing docstring to VariableEnvironmentMap.matching_env_id_q
  ([`84ae7fc`](https://github.com/mit-kavli-institute/data-product-tracker/commit/84ae7fc3d2f794d78b0ed539aecabd3c657a56ba))

- Address critical linting issues and add docstrings
  ([`af2c496`](https://github.com/mit-kavli-institute/data-product-tracker/commit/af2c496858b75d1c8b1a92fc5daf0d3f954582e4))

- Complete all docstrings in environment.py
  ([`ca2f45a`](https://github.com/mit-kavli-institute/data-product-tracker/commit/ca2f45a65864daaba2d2194fffd5d0ee1f4dcf3f))

- Configure flake8 to exclude docstring checks from test files
  ([`bbc44c3`](https://github.com/mit-kavli-institute/data-product-tracker/commit/bbc44c3f8babf27df18a910418b4420b941578e3))

- Eliminate redundant test runs in CI workflow
  ([`d547cc2`](https://github.com/mit-kavli-institute/data-product-tracker/commit/d547cc2d7bddb94a5f7bcda902e8309b40de6ddd))

- Resolve SQLite compatibility and test isolation issues
  ([`7d6fcf2`](https://github.com/mit-kavli-institute/data-product-tracker/commit/7d6fcf28d3eceb2168d324186b4809f8f2239e39))

- Resolve tracker test failures without breaking reflection API
  ([`622def9`](https://github.com/mit-kavli-institute/data-product-tracker/commit/622def9b43a6abe8ce30906f189926fff6557ebe))

- Update CI to use modern docker compose syntax
  ([`b58054c`](https://github.com/mit-kavli-institute/data-product-tracker/commit/b58054c2e368884a052194a5d4d9426897a475a7))

- Update coverage session to run tests before generating reports
  ([`17d70ad`](https://github.com/mit-kavli-institute/data-product-tracker/commit/17d70ad2d3802857f2b5e7de546174eece39af47))

### Chores

- Simplify Docker setup with thekevjames/nox image
  ([`c55ce6c`](https://github.com/mit-kavli-institute/data-product-tracker/commit/c55ce6c50ee4fbed829c9b5b309127f0394fc35d))

### Features

- Split CI linting into separate parallel jobs
  ([`9a86772`](https://github.com/mit-kavli-institute/data-product-tracker/commit/9a86772571949c7e5014999b25351833a5809b72))


## v1.0.0-beta.2 (2025-07-28)

### Features

- Migrate to nox with Docker and SQLite testing
  ([`d721763`](https://github.com/mit-kavli-institute/data-product-tracker/commit/d721763700345f30d8e5449d38fc84d45efe974d))

### Breaking Changes

- Replace tox with nox and PostgreSQL with SQLite for testing


## v1.0.0-beta.1 (2025-07-24)

- Initial Release
