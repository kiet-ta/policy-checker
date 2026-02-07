# Contributing to Policy Checker

Thank you for your interest in contributing to Policy Checker! We welcome contributions from the community to help make mobile app development compliant and secure.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kiet-ta/policy-checker.git
   cd policy-checker
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]  # Install dev dependencies
   ```

## 🧪 Running Tests

We use `pytest` for testing. Ensure all tests pass before submitting a PR.

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rule_engine.py

# Run with coverage
pytest --cov=src tests/
```

## 📝 Coding Standards

- **Code Style**: We follow PEP 8. Please run a linter (e.g., `flake8` or `ruff`) before committing.
- **Type Hinting**: All new code must have type hints.
- **Documentation**: Add docstrings to all public functions and classes.

## 🕷️ Adding a New Scraper

If you want to add support for a new policy source (e.g., Samsung Galaxy Store):

1. Create a new file in `src/scrapers/` (e.g., `samsung_scraper.py`).
2. Inherit from `BasePolicyScraper`.
3. Implement `fetch_policies()` and `get_source_url()`.
4. See [docs/scrapers.md](docs/scrapers.md) for detailed architecture.

## 🐛 Reporting Bugs

Please verify the bug exists on the latest `main` branch. Open an issue with:
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version)

## 📥 Submitting Pull Requests

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

> **Note**: For AI-generated rules, please use the provided PR template and ensure you've validated the source and reasoning.
