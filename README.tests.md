# Testing Infrastructure for Django Finance

This document explains the automated testing setup added in June 2025.

---
## 1  Tools & Libraries

| Purpose                | Package                     |
|------------------------|-----------------------------|
| Test runner / assertions | **pytest** (≥ 8.0)          |
| Django integration       | **pytest-django**           |
| Mock helpers             | **pytest-mock**             |
| HTTP mocking             | **responses**               |
| Time control             | **freezegun**               |
| Object factories         | **factory-boy**             |
| Coverage reports         | **coverage.py**             |

Development dependencies live in `requirements-dev.txt`. Install with:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

---
## 2  Project Layout

```
.
├── pytest.ini              # pytest configuration (points to Django settings)
├── requirements-dev.txt    # dev-only packages
├── tests/                  # top-level test suite
│   ├── __init__.py         # marks directory as package
│   ├── conftest.py         # shared fixtures
│   ├── test_prompts.py     # unit tests for prompt helpers
│   ├── test_parsing.py     # unit tests for quantity parsing
│   └── test_views.py       # integration tests for API endpoints
└── portfolio/tests.py      # legacy file → skipped placeholder
```

### 2.1 `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = financial_advisor.settings
python_files = tests.py test_*.py *_tests.py
addopts = -ra --strict-markers --tb=short
```

* Ensures Django settings are loaded for every test.
* Uses strict markers to avoid typos.

### 2.2 Fixtures (`tests/conftest.py`)

* `sample_portfolio_data` – minimal portfolio payload.
* `investment_goals` – example user goals.
* `cash_available` – example cash figure.

These are auto-discovered by pytest and can be injected into any test.

---
## 3  Test Suites

### 3.1 `test_prompts.py`
Verifies that:
* Investment goals are injected into analysis prompts.
* Recommendation prompt contains the required *RESPONSE FORMAT* scaffold.

### 3.2 `test_parsing.py`
Validates robust quantity parsing:
* Handles `$` signs and embedded commas (e.g. `2,300`).
* Raises on non-numeric values (fallback logic).

### 3.3 `test_views.py`
Integration-style tests using REST Framework’s `APIClient`.

* `test_analyze_portfolio_endpoint`
  * Mocks **yfinance** and **openai** to avoid network calls.
  * Posts a sample payload to `/api/analyze/` and inspects JSON response.

* `test_recommendations_endpoint`
  * Posts to the `/api/recommendations/` endpoint.
  * Ensures response contains either `recommendations` or a handled `error`.

Both are marked with `@pytest.mark.django_db` so database access is automatically managed by pytest-django.

---
## 4  CI Workflow (GitHub Actions)
File: `.github/workflows/ci.yml`

* Spins up MySQL 8 in a service container.
* Installs prod + dev requirements.
* Executes `pytest --cov=.` with coverage reporting.

Note: pushing workflows requires a PAT with `workflow` scope.

---
## 5  Running Tests Locally

```bash
# 1. Activate venv (recommended)
source venv/bin/activate

# 2. Run entire suite
pytest -q             # quiet mode

# 3. View coverage
pytest --cov=.

# 4. Run a single file / test
pytest tests/test_views.py::test_analyze_portfolio_endpoint
```

All current tests should pass:

```
..s....  [100%]
6 passed, 1 skipped in <3s
```

The single skipped test is a legacy placeholder in `portfolio/tests.py` retained for historical reasons; it is explicitly marked with `@pytest.mark.skip`.

---
## 6  Extending the Suite

1. **Add fixtures** in `conftest.py` or use `factory-boy` to create model instances.
2. **Mock external APIs** with `pytest-mock`, **responses**, or DRF’s `override_settings`.
3. **Write behavioural tests** for edge cases (e.g., negative cash, large portfolios, malformed input).
4. **Raise coverage thresholds** in CI once confidence grows.

Happy testing!
