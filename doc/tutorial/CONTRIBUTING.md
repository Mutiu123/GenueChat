# Contributing to GenueChat

Thank you for your interest in contributing to GenueChat. This guide explains the
development workflow, coding standards, and submission process.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Standards](#code-standards)
3. [Branch Strategy](#branch-strategy)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Code Review Checklist](#code-review-checklist)

---

## Development Setup

### Prerequisites

- Python 3.11 or later
- Docker and Docker Compose (for full-stack local development)
- Git

### Local Environment

```bash
# Clone the repository
git clone https://github.com/Mutiu123/GenueChat.git
cd GenueChat

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install all dependencies (production + dev)
pip install -r requirements.txt -r requirements-dev.txt

# Copy environment template
cp .env.example .env
# Edit .env with your local values

# Install pre-commit hooks
pre-commit install
```

### Running Locally

```bash
# Start dependencies (MongoDB, Prometheus, Grafana)
docker compose up -d mongodb prometheus grafana

# Run the application with hot-reload
uvicorn app:app --reload --port 8000
```

### Running with Docker Compose

```bash
docker compose up --build
```

---

## Code Standards

- **Formatter**: Black (line length 88)
- **Linters**: Flake8, Pylint, MyPy
- **Style**: PEP 8
- **Type hints**: Required for all public functions
- **Docstrings**: Required for modules and public classes/functions

Run all checks locally before pushing:

```bash
black .
flake8 src/ tests/ app.py
mypy src/ --ignore-missing-imports
pylint src/ --disable=C0114,C0115,C0116 --fail-under=7
```

---

## Branch Strategy

- `main` -- production-ready code
- `develop` -- integration branch for features
- `feature/<name>` -- individual feature branches
- `fix/<name>` -- bug fix branches
- `release/<version>` -- release preparation

Always branch from `main` or `develop` and open a pull request back into it.

---

## Making Changes

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-feature main
   ```
2. Make focused, atomic commits with clear messages.
3. Keep commits small -- one logical change per commit.
4. Write or update tests for every change.
5. Ensure all linters and tests pass before pushing.

---

## Testing

The project uses pytest. Tests are located in the `tests/` directory.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_security.py -v
```

### Test Categories

| Directory / File       | Scope                                  |
|------------------------|----------------------------------------|
| tests/test_config.py   | Configuration and settings             |
| tests/test_exceptions.py | Custom exception classes              |
| tests/test_schemas.py  | Pydantic request/response models       |
| tests/test_security.py | JWT, rate limiting, sanitization       |
| tests/test_monitoring.py | Logging and metrics                  |
| tests/test_api.py      | Integration tests for all endpoints    |

Coverage target: **80 %** or higher.

---

## Pull Request Process

1. Ensure your branch is up to date with `main`.
2. All CI checks must pass (lint, test, build).
3. Fill in the pull request template with:
   - Summary of changes
   - Related issue numbers
   - Testing performed
4. Request review from at least one maintainer.
5. Address all review comments before merge.
6. Squash-merge into `main`.

---

## Code Review Checklist

- [ ] Code follows PEP 8 and project conventions
- [ ] All public functions have type hints
- [ ] New functionality has corresponding tests
- [ ] No secrets or credentials committed
- [ ] Documentation updated if API surface changed
- [ ] No unnecessary dependencies added
- [ ] Error handling is appropriate
- [ ] Logging uses structured format

---

## Reporting Issues

Open an issue on GitHub with:
- Steps to reproduce
- Expected vs. actual behaviour
- Environment details (OS, Python version, Docker version)

---

## License

By contributing you agree that your contributions will be licensed under the
Apache 2.0 license that covers this project.
