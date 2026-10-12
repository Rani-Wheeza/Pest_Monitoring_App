# Code quality, testing and CI (Part 2, Tasks 3 and 4)

All of these run automatically in `azure-pipelines.yml` on every pull request. Run them locally before pushing.

## Task 3 – Testing and code quality

| Brief asks for | Tool | Run locally (from `backend/` or `frontend/`) | Build fails when |
|---|---|---|---|
| Code analysis (errors, spelling, security, performance) | **ruff** (pyflakes, pycodestyle, bugbear, bandit security rules, Django rules) | `ruff check .` (`ruff check . --fix` fixes simple ones) | Any problem is reported |
| | **codespell** (spelling mistakes in code and comments) | `codespell .` | A misspelling is found |
| | **ESLint** with angular-eslint (incl. accessibility rules) | `npm run lint` | Any error |
| Code metrics | **radon**: cyclomatic complexity and maintainability index per function/module | `radon cc . -a -s` · `radon mi . -s` | – (report only) |
| | **xenon**: complexity gate | `xenon --max-absolute B --max-modules B --max-average A .` | A function is rank C or worse (complexity > 10) |
| Unit tests in the IDE | **pytest** (+ pytest-django) / **Jasmine + Karma** | VS Code Testing panel, `pytest`, `npm test` | A test fails |
| *Higher grade:* duplicate detection | **pylint duplicate-code** | `pylint --disable=all --enable=duplicate-code domain reference accounts sightings alerts` | 8+ similar lines are found in two places |
| *Higher grade:* architecture validation on every build | **import-linter** (contracts in `pyproject.toml`) | `lint-imports` | A layer imports a layer above it, or `domain` imports Django |
| *Higher grade:* robust test harness | Pure `domain` package tested without a database (like IntelliTest's generated inputs, the tests cover every rule and boundary value) | `python -m pytest tests/domain` | – |

### The architecture rules checked on every build

1. `domain` (business rules) is plain Python: it may not import Django, DRF or any app.
2. In the `sightings` app, imports only go down: `views → serializers → services → repositories → models`.
3. `reference` data does not depend on the feature apps.

### What the tests cover

| Area | Tests | File |
|---|---|---|
| Sighting validation rules (US-02) | 22 | `tests/domain/test_validation.py` |
| Alert rules, seasons, invasive species (US-06) | 13 | `tests/domain/test_alerts.py` |
| Photo checks and GPS/EXIF removal (US-03) | 9 | `tests/domain/test_images.py` |
| Entra ID token checks and roles (US-01) | 10 | `tests/domain/test_identity.py` |
| Map helpers: bounding box, GeoJSON (US-04/05) | 6 | `tests/domain/test_geo.py` |
| Notification Hubs signing | 5 | `tests/domain/test_notification_hub.py` |
| Submit, photo upload, review API | 24 | `tests/api/test_sightings_api.py` |
| Map API and filters | 8 | `tests/api/test_map_api.py` |
| Threshold job and notifications | 8 | `tests/api/test_alerts_api.py` |
| Sign-in and profile API | 8 | `tests/api/test_auth_api.py` |
| Notification sender and seed data | 7 | `tests/api/test_senders_and_seed.py` |
| Angular: rules, API service, report form, location picker, my reports, map, shell | 35 | `frontend/src/**/*.spec.ts` |

**Total: 120 backend tests and 35 frontend tests.**

Coverage gates: **backend ≥ 80 %** (`pyproject.toml`), **frontend ≥ 60 %** (`karma.conf.js`).

## Task 4 – CI build pipeline

### Create the pipeline (once)

1. *Pipelines → New pipeline → Azure Repos Git → Pest Monitoring → Existing Azure Pipelines YAML file* → `/azure-pipelines.yml` → **Run**.
2. Rename it to **Pest Monitoring CI**.
3. Add it as a **Build validation** branch policy on `main` and `develop` (see [BRANCHING.md](BRANCHING.md)).

### Manual steps mapped to pipeline tasks

| Manual step | Pipeline step |
|---|---|
| Install Python/Node packages | *Install dependencies* (pip cache / `npm ci`) |
| Check database changes were committed | *Check migrations are committed* |
| Look for errors and style problems | *Code analysis* (ruff, ESLint), *Spelling check* |
| Check the design rules | *Architecture validation (import-linter)* |
| Check complexity and duplication | *Code metrics*, *Duplicate code detection* |
| Check packages for known vulnerabilities | *pip-audit*, *npm audit* |
| Run the tests | *Unit and API tests with coverage*, *Unit tests (Karma)* |
| See how much code the tests cover | *Publish coverage* (Cobertura) → **Code Coverage** tab |
| Build the app | *Production build*, *Build image* (Docker, `main` only) |

### Visualise test runs over time (dashboard widgets)

*Overview → Dashboards → New dashboard* (e.g. "Quality"), then **Edit → Add widget**:

1. **Test Results Trend (Advanced)**: pipeline *Pest Monitoring CI*, stage *Build*, last 30 days. Shows passed/failed tests per run.
2. **Code Coverage**: pipeline *Pest Monitoring CI*.
3. **Build History**: pipeline *Pest Monitoring CI*.
4. Optional: **Query Results** for the Sprint 1 work items.

### When a test fails in the pipeline (Task 4.6)

1. Open the run → **Tests** tab → click the failed test to see the message and stack trace.
2. Create a **Bug** work item from the failed test (*Create bug* button), so it's tracked.
3. Reproduce locally (`pytest -k <test name>` / `npm test`), fix it on a `bugfix/AB<id>-…` branch, push and open a PR.
4. The PR build must pass before it can be merged. That build is the proof the failure was fixed.
