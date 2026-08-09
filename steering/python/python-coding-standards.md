---
inclusion: always
---

# Python Coding Standards

These standards apply to all Python development on Southwest Airlines AI Engineering projects. Follow them consistently when writing new code and when modifying existing code.

---

## Project Structure

- Use a `src/` layout for packages: `src/<package_name>/`, `tests/`.
- One module per logical concern. Keep modules focused and import-friendly.
- Use `__init__.py` to control public API surface — only export what consumers need.
- Configuration files at project root: `pyproject.toml` (preferred), `setup.cfg`, or `setup.py`.
- Separate test files mirror the source structure: `tests/unit/`, `tests/integration/`.

```
my-service/
├── src/
│   └── crewscheduler/
│       ├── __init__.py
│       ├── service.py
│       ├── repository.py
│       └── models.py
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── requirements.txt
```

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Module / Package | lowercase, underscores | `crew_scheduler`, `flight_utils` |
| Class | PascalCase | `CrewMember`, `FlightRepository` |
| Function / Method | snake_case, verb-first | `assign_crew()`, `find_by_flight_id()` |
| Variable | snake_case | `crew_member`, `departure_time` |
| Constant | UPPER_SNAKE_CASE | `MAX_FLIGHT_HOURS`, `DEFAULT_TIMEOUT_S` |
| Private | leading underscore | `_internal_state`, `_validate()` |
| Test function | prefix with `test_` | `test_assign_crew_when_unavailable` |

- Avoid single-letter names except for short-lived loop counters (`i`, `j`) or well-known math variables.
- Boolean variables and functions should read as predicates: `is_available`, `has_conflict`, `can_be_assigned`.

---

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) strictly.
- Use 4-space indentation. No tabs.
- Maximum line length: 100 characters. Use implicit line continuation inside brackets rather than backslash.
- Use a formatter — **Black** is the standard. Run it before every commit.
- Use **isort** to organize imports: standard library → third-party → local, each group separated by a blank line.
- Use **flake8** or **ruff** for linting. All warnings must be resolved before merging.

```python
# Good
from __future__ import annotations

import os
from pathlib import Path

import httpx

from crewscheduler.models import CrewMember
```

---

## Type Annotations

- All public functions and methods must have full type annotations (parameters and return type).
- Use `from __future__ import annotations` at the top of every module for forward reference support.
- Use `Optional[T]` (or `T | None` in Python 3.10+) when `None` is a valid return. Never return `None` silently from a function that callers expect to return a value.
- Use `TypedDict` for structured dicts passed between functions instead of plain `dict`.
- Run **mypy** in strict mode as part of CI. No unresolved type errors on changed files.

```python
from __future__ import annotations

def find_crew_member(member_id: int) -> CrewMember | None:
    ...

def assign_crew(flight_id: int, member_ids: list[int]) -> AssignmentResult:
    ...
```

---

## Functions and Methods

- Functions should do one thing. If you need a comment to describe each block, split the function.
- Maximum function length: 30 lines. Refactor anything longer.
- Maximum parameter count: 4. Use a dataclass or TypedDict for more.
- Return early to reduce nesting. Avoid deeply nested `if` blocks.
- Avoid mutable default arguments — use `None` as default and initialize inside the function.

```python
# Bad
def process(items=[]):
    items.append("new")
    return items

# Good
def process(items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append("new")
    return items
```

---

## Classes

- Use `@dataclass` or Pydantic `BaseModel` for data-holding classes. Avoid writing `__init__` manually for simple value types.
- Keep classes focused on a single responsibility.
- Prefer composition over inheritance. Use `Protocol` for structural subtyping instead of abstract base classes where practical.
- Mark implementation details with a leading underscore. Never expose internal state directly.
- Use `__slots__` on performance-sensitive, frequently-instantiated classes.

---

## Exception Handling

- Catch specific exceptions. Never `except Exception` or bare `except:` unless at a top-level boundary handler.
- Never swallow exceptions silently. At minimum, log before reraising.
- Define domain-specific exception classes when callers need to distinguish failure modes.
- Always include a descriptive message. Include relevant context (IDs, values).
- Use `raise ... from err` to preserve exception chains.

```python
# Good
try:
    result = fetch_flight_data(flight_id)
except httpx.TimeoutException as err:
    log.error("Timeout fetching flight %s", flight_id)
    raise FlightDataUnavailableError(f"Timeout for flight {flight_id}") from err

# Bad
try:
    result = fetch_flight_data(flight_id)
except Exception:
    pass
```

---

## Logging

- Use the standard `logging` module. Never use `print()` for diagnostic output in production code.
- Get a module-level logger: `log = logging.getLogger(__name__)`.
- Use `%`-style lazy formatting in log calls — never f-strings or concatenation.
- Log levels:
  - `ERROR`: System failures requiring immediate attention.
  - `WARNING`: Unexpected but recoverable conditions.
  - `INFO`: Key business events.
  - `DEBUG`: Diagnostic details for development.
- Never log passwords, tokens, PII, or card numbers at any level.

```python
import logging

log = logging.getLogger(__name__)

# Good
log.debug("Assigning crew member %s to flight %s", member_id, flight_id)

# Bad
print(f"Assigning crew member {member_id} to flight {flight_id}")
log.debug(f"Assigning crew member {member_id} to flight {flight_id}")
```

---

## Dependency Management

- Pin all dependencies to exact versions in `requirements.txt` for applications. Use `~=` (compatible release) in `pyproject.toml` for libraries.
- Separate runtime and dev dependencies: `requirements.txt` vs `requirements-dev.txt`.
- Use a virtual environment for every project. Never install project dependencies globally.
- Audit dependencies with `pip-audit` before adding new packages. Prefer well-maintained packages with active communities.

---

## Security

- Never hardcode credentials, API keys, or secrets. Use environment variables or a secrets manager.
- Validate and sanitize all external input (HTTP requests, file contents, CLI args).
- Use parameterized queries with your ORM or `psycopg2`. Never concatenate user input into SQL.
- Use `secrets` module for cryptographic randomness, not `random`.
- Set `httpx` / `requests` timeouts explicitly. Never make unbounded network calls.

---

## Testing Standards

- Use **pytest** as the test runner. No `unittest.TestCase` for new tests.
- Every public function must have at least one test for the happy path and one for failure/edge cases.
- Use `pytest-mock` (`mocker` fixture) for mocking. Avoid patching globally — patch at the narrowest scope.
- Test function names describe the scenario: `test_assign_crew_raises_when_member_unavailable`.
- Aim for 80%+ line coverage on `src/` packages. Test behavior, not implementation details.
- Use `pytest.mark.parametrize` for data-driven tests instead of loops inside test functions.
- Keep tests independent and idempotent. No shared mutable state between tests.

```python
import pytest

def test_assign_crew_raises_when_member_unavailable(mocker):
    repo = mocker.Mock(spec=CrewRepository)
    repo.find_by_id.return_value = CrewMember(available=False)
    scheduler = CrewScheduler(repo)

    with pytest.raises(CrewUnavailableError):
        scheduler.assign(flight_id=42, member_id=7)
```

---

## Documentation

- Every public module, class, and function must have a docstring.
- Use Google-style docstrings (consistent with most Southwest tooling).
- Docstrings explain **what** the function does and **why** non-obvious decisions were made — not a restatement of the code.
- Keep docstrings current. A stale docstring is worse than none.

```python
def assign_crew(flight_id: int, member_id: int) -> Assignment:
    """Assign a crew member to a flight.

    Args:
        flight_id: The ID of the flight to assign.
        member_id: The ID of the crew member being assigned.

    Returns:
        The created Assignment record.

    Raises:
        CrewUnavailableError: If the crew member is not available for the flight window.
        FlightNotFoundError: If no flight exists with the given ID.
    """
```

---

## Linting and CI Checklist

Before opening a pull request, all of the following must pass locally:

| Tool | Purpose | Command |
|---|---|---|
| `black` | Formatting | `black src/ tests/` |
| `isort` | Import order | `isort src/ tests/` |
| `ruff` / `flake8` | Linting | `ruff check src/ tests/` |
| `mypy` | Type checking | `mypy src/` |
| `pytest` | Tests + coverage | `pytest --cov=src --cov-report=term-missing` |
| `pip-audit` | Dependency security | `pip-audit` |
