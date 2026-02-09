"""Base scraper for policy sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path
from pydantic import BaseModel, Field

class PolicyRule(BaseModel):
    """
    Represents a single policy rule from a platform.
    """
    id: str = Field(..., description="Unique identifier for the rule")
    title: str = Field(..., description="Human-readable title of the rule")
    description: str = Field(..., description="Detailed description of the rule content")
    category: str = Field(..., description="Category (e.g., privacy, security)")
    severity: str = Field(..., description="Severity level: critical, major, minor")
    source_url: str = Field(..., description="URL source of the policy")
    last_updated: datetime = Field(..., description="Timestamp of last update")
    version: str = Field(..., description="Version string of the policy text")
    checkable: bool = Field(True, description="Whether this rule can be automatically checked")
    auto_fix: bool = Field(False, description="Whether an auto-fix is available")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PolicyUpdate(BaseModel):
    """
    Represents a detected change in a policy rule.
    """
    rule_id: str
    change_type: str = Field(..., description="added, modified, or removed")
    old_version: Optional[str]
    new_version: str
    changelog: str
    date: datetime

class BasePolicyScraper(ABC):
    """
    Abstract base class for all policy scrapers.
    Defines the interface for fetching and detecting changes in policies.
    """
    
    def __init__(self, cache_dir: Path = Path(".policy_cache")):
        """
        Initialize the scraper with a cache directory.
        
        Args:
            cache_dir (Path): Directory to store cached policy data.
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    @abstractmethod
    def fetch_policies(self) -> List[PolicyRule]:
        """
        Fetch latest policies from official source.
        
        Returns:
            List[PolicyRule]: A list of PolicyRule objects parsed from the source.
        """
        pass
    
    @abstractmethod
    def get_source_url(self) -> str:
        """
        Return official policy documentation URL.
        
        Returns:
            str: The source URL string.
        """
        pass
    
    def get_cache_path(self) -> Path:
        """
        Get the path to the cache file for this scraper.
        
        Returns:
            Path: Filesystem path to the JSON cache file.
        """
        return self.cache_dir / f"{self.__class__.__name__}.json"
    
    def load_cached(self) -> Optional[List[Dict]]:
        """
        Load policies from local disk cache.
        
        Returns:
            Optional[List[Dict]]: List of cached policy dicts or None if not found.
        """
        cache_path = self.get_cache_path()
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_cache(self, policies: List[PolicyRule]):
        """
        Save policies to local disk cache.
        
        Args:
            policies (List[PolicyRule]): List of policies to save.
        """
        with open(self.get_cache_path(), 'w', encoding='utf-8') as f:
            # Use model_dump (v2) or dict() (v1) depending on Pydantic version.
            # Assuming Pydantic v2 based on "pydantic" requirement, but v1 is often default in strict envs.
            # Using json.dump with default=str to handle datetime safely.
            data = [p.dict() for p in policies]
            json.dump(data, f, indent=2, default=str)
    
    def detect_changes(self, new_policies: List[PolicyRule]) -> List[PolicyUpdate]:
        """
        Compare with cached policies to detect changes.
        
        Args:
            new_policies (List[PolicyRule]): The newly fetched policies.
            
        Returns:
            List[PolicyUpdate]: A list of detected updates.
        """
        cached = self.load_cached()
        if not cached:
            return [
                PolicyUpdate(
                    rule_id=p.id, 
                    change_type="added", 
                    old_version=None, 
                    new_version=p.version, 
                    changelog="Initial policy", 
                    date=datetime.now()
                ) for p in new_policies
            ]
        
        cached_map = {p["id"]: p for p in cached}
        new_map = {p.id: p for p in new_policies}
        updates = []
        
        for pid, policy in new_map.items():
            if pid not in cached_map:
                updates.append(PolicyUpdate(
                    rule_id=pid, 
                    change_type="added", 
                    old_version=None, 
                    new_version=policy.version, 
                    changelog="New policy added", 
                    date=datetime.now()
                ))
            elif cached_map[pid]["version"] != policy.version:
                updates.append(PolicyUpdate(
                    rule_id=pid, 
                    change_type="modified", 
                    old_version=cached_map[pid]["version"], 
                    new_version=policy.version, 
                    changelog="Policy updated", 
                    date=datetime.now()
                ))
        
        for pid in cached_map:
            if pid not in new_map:
                updates.append(PolicyUpdate(
                    rule_id=pid, 
                    change_type="removed", 
                    old_version=cached_map[pid]["version"], 
                    new_version="", 
                    changelog="Policy removed", 
                    date=datetime.now()
                ))
        
        return updates
