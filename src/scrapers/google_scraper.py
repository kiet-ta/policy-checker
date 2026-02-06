"""Google Play Store Policy Scraper."""
from datetime import datetime
from typing import List
import requests
from bs4 import BeautifulSoup
from .base_scraper import BasePolicyScraper, PolicyRule

class GooglePolicyScraper(BasePolicyScraper):
    POLICY_URL = "https://support.google.com/googleplay/android-developer/answer/9859455"
    DEVELOPER_POLICY_URL = "https://play.google.com/about/developer-content-policy/"
    
    # Core checkable policies
    CHECKABLE_POLICIES = {
        "TARGET_SDK": {"title": "Target API Level", "severity": "critical", "category": "technical",
                       "description": "Apps must target Android 14 (API 34) or higher"},
        "PERMISSIONS": {"title": "Permissions Policy", "severity": "critical", "category": "privacy",
                       "description": "Apps must declare and justify all permissions"},
        "DATA_SAFETY": {"title": "Data Safety Section", "severity": "critical", "category": "privacy",
                       "description": "Apps must complete Data Safety form accurately"},
        "PACKAGE_NAME": {"title": "Package Name", "severity": "critical", "category": "identity",
                        "description": "Package name must be unique and follow conventions"},
        "VERSION_CODE": {"title": "Version Code", "severity": "major", "category": "versioning",
                        "description": "Version code must increment with each release"},
        "DECEPTIVE_BEHAVIOR": {"title": "Deceptive Behavior", "severity": "critical", "category": "policy",
                              "description": "Apps must not contain deceptive functionality"},
        "ADS_POLICY": {"title": "Ads Policy", "severity": "major", "category": "monetization",
                      "description": "Ads must comply with Google's advertising policies"},
    }
    
    # Current requirements (2024)
    MIN_TARGET_SDK = 34
    MIN_COMPILE_SDK = 34
    
    def get_source_url(self) -> str:
        return self.DEVELOPER_POLICY_URL
    
    def fetch_policies(self) -> List[PolicyRule]:
        """Fetch Google Play policies."""
        policies = []
        version = self._fetch_current_version()
        
        for rule_id, meta in self.CHECKABLE_POLICIES.items():
            policies.append(PolicyRule(
                id=f"GOOGLE_{rule_id}",
                title=meta["title"],
                description=meta["description"],
                category=meta["category"],
                severity=meta["severity"],
                source_url=self.DEVELOPER_POLICY_URL,
                last_updated=datetime.now(),
                version=version,
                checkable=True
            ))
        
        self.save_cache(policies)
        return policies
    
    def _fetch_current_version(self) -> str:
        try:
            response = requests.get(self.POLICY_URL, timeout=30)
            return datetime.now().strftime("%Y.%m")
        except:
            return "2024.1"
