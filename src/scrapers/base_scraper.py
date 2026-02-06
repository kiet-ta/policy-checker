"""Base scraper for policy sources."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import json
from pathlib import Path

@dataclass
class PolicyRule:
    id: str
    title: str
    description: str
    category: str
    severity: str  # critical, major, minor
    source_url: str
    last_updated: datetime
    version: str
    checkable: bool = True
    auto_fix: bool = False

@dataclass
class PolicyUpdate:
    rule_id: str
    change_type: str  # added, modified, removed
    old_version: Optional[str]
    new_version: str
    changelog: str
    date: datetime

class BasePolicyScraper(ABC):
    def __init__(self, cache_dir: Path = Path(".policy_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    @abstractmethod
    def fetch_policies(self) -> List[PolicyRule]:
        """Fetch latest policies from official source."""
        pass
    
    @abstractmethod
    def get_source_url(self) -> str:
        """Return official policy documentation URL."""
        pass
    
    def get_cache_path(self) -> Path:
        return self.cache_dir / f"{self.__class__.__name__}.json"
    
    def load_cached(self) -> Optional[List[Dict]]:
        cache_path = self.get_cache_path()
        if cache_path.exists():
            with open(cache_path) as f:
                return json.load(f)
        return None
    
    def save_cache(self, policies: List[PolicyRule]):
        with open(self.get_cache_path(), 'w') as f:
            json.dump([self._rule_to_dict(p) for p in policies], f, indent=2, default=str)
    
    def _rule_to_dict(self, rule: PolicyRule) -> Dict:
        return {
            "id": rule.id, "title": rule.title, "description": rule.description,
            "category": rule.category, "severity": rule.severity, "source_url": rule.source_url,
            "last_updated": rule.last_updated.isoformat(), "version": rule.version,
            "checkable": rule.checkable, "auto_fix": rule.auto_fix
        }
    
    def detect_changes(self, new_policies: List[PolicyRule]) -> List[PolicyUpdate]:
        """Compare with cached policies to detect changes."""
        cached = self.load_cached()
        if not cached:
            return [PolicyUpdate(p.id, "added", None, p.version, "Initial policy", datetime.now()) for p in new_policies]
        
        cached_map = {p["id"]: p for p in cached}
        new_map = {p.id: p for p in new_policies}
        updates = []
        
        for pid, policy in new_map.items():
            if pid not in cached_map:
                updates.append(PolicyUpdate(pid, "added", None, policy.version, "New policy added", datetime.now()))
            elif cached_map[pid]["version"] != policy.version:
                updates.append(PolicyUpdate(pid, "modified", cached_map[pid]["version"], policy.version, "Policy updated", datetime.now()))
        
        for pid in cached_map:
            if pid not in new_map:
                updates.append(PolicyUpdate(pid, "removed", cached_map[pid]["version"], "", "Policy removed", datetime.now()))
        
        return updates
