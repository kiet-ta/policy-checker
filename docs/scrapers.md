# 🕷️ Policy Scrapers & Caching Architecture

The Policy Checker includes a modular scraping engine to fetch and track policy changes from official sources (Apple App Store & Google Play). This document details the architecture, caching mechanism, and how to implement new scrapers.

## 1. Architecture

The scraping logic is built on the **Strategy Pattern**, defined in `src/scrapers/base_scraper.py`.

### 1.1 Base Classes

- **`BasePolicyScraper` (ABC)**: Abstract base class that defines the contract for all scrapers.
  - `fetch_policies() -> List[PolicyRule]`: Must be implemented by subclasses to retrieve current policies.
  - `get_source_url() -> str`: Returns the official documentation URL.
  - `detect_changes(...) -> List[PolicyUpdate]`: Compares fetched policies with the local cache.
  - `save_cache(...)`: Serializes policies to JSON.

- **`PolicyRule` (Dataclass)**:
  - `id`: Unique identifier (e.g., `IOS_PRIVACY_001`).
  - `version`: String version or hash of the content to track changes.
  - `severity`: Normalized severity level.
  - `source_url`: Deep link to the specific section.

- **`PolicyUpdate` (Dataclass)**:
  - Represents a detected change (`added`, `modified`, `removed`).
  - Contains `old_version`, `new_version`, and a `changelog` summary.

## 2. Caching Mechanism

To avoid redundant API calls and processing, scrapers use a local file-based cache.

- **Location**: `.policy_cache/` directory in the project root.
- **Format**: JSON files named after the scraper class (e.g., `ApplePolicyScraper.json`).
- **Structure**: List of `PolicyRule` objects serialized to JSON.

### Change Detection Algorithm
1. Load `cached_policies` from JSON.
2. Fetch `new_policies` from live source.
3. Compare IDs:
   - **New ID**: Marked as `added`.
   - **Missing ID**: Marked as `removed`.
   - **Existing ID**: Check `version` field. If different -> `modified`.

## 3. Implementing a New Scraper

To add a new policy source (e.g., Samsung Galaxy Store), create a class inheriting from `BasePolicyScraper`:

```python
from scrapers.base_scraper import BasePolicyScraper, PolicyRule

class SamsungPolicyScraper(BasePolicyScraper):
    def get_source_url(self) -> str:
        return "https://seller.samsungapps.com/guide/..."

    def fetch_policies(self) -> List[PolicyRule]:
        # 1. Fetch HTML/JSON
        # 2. Parse content
        # 3. Return List[PolicyRule]
        pass
```

## 4. Usage

The scrapers are primarily used by the `update-policies` CLI command and the CI/CD workflow:

```python
engine = PolicyEngine()
updates = engine.update_policies()
# updates = {'apple': {'policies': 150, 'updates': 2}, ...}
```
