"""Apple App Store Review Guidelines Scraper."""
import re
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
import logging
import requests
from .base_scraper import BasePolicyScraper, PolicyRule

class ApplePolicyScraper(BasePolicyScraper):
    GUIDELINES_URL = "https://developer.apple.com/app-store/review/guidelines/"
    
    # Core policies that are programmatically checkable
    CHECKABLE_POLICIES = {
        "2.1": {"title": "App Completeness", "severity": "critical", "category": "functionality"},
        "2.3.7": {"title": "App Icon", "severity": "critical", "category": "metadata"},
        "2.3.8": {"title": "Privacy Policy", "severity": "critical", "category": "privacy"},
        "4.2.3": {"title": "Minimum Functionality", "severity": "major", "category": "functionality"},
        "5.1.1": {"title": "Data Collection and Storage", "severity": "critical", "category": "privacy"},
        "5.1.2": {"title": "Data Use and Sharing", "severity": "critical", "category": "privacy"},
    }
    
    # iOS 17+ Privacy Manifest requirements
    PRIVACY_MANIFEST_APIS = [
        "NSPrivacyAccessedAPICategoryFileTimestamp",
        "NSPrivacyAccessedAPICategorySystemBootTime",
        "NSPrivacyAccessedAPICategoryDiskSpace",
        "NSPrivacyAccessedAPICategoryActiveKeyboards",
        "NSPrivacyAccessedAPICategoryUserDefaults",
    ]
    
    def get_source_url(self) -> str:
        return self.GUIDELINES_URL
    
    def fetch_policies(self) -> List[PolicyRule]:
        """
        Fetch and parse Apple's App Store Review Guidelines.
        
        Returns:
            List[PolicyRule]: List of scraped policy rules.
        """
        policies = []
        try:
            logging.info(f"Connecting to {self.GUIDELINES_URL}...")
            response = requests.get(self.GUIDELINES_URL, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            version = self._extract_version(soup)
            logging.info(f"Detected Apple Policy Version: {version}")
            
            for rule_id, meta in self.CHECKABLE_POLICIES.items():
                policies.append(PolicyRule(
                    id=f"APPLE_{rule_id.replace('.', '_')}",
                    title=meta["title"],
                    description=self._get_rule_description(rule_id),
                    category=meta["category"],
                    severity=meta["severity"],
                    source_url=f"{self.GUIDELINES_URL}#{rule_id}",
                    last_updated=datetime.now(),
                    version=version,
                    checkable=True
                ))
            
            # Add Privacy Manifest specific rules
            policies.append(PolicyRule(
                id="APPLE_PRIVACY_MANIFEST",
                title="Privacy Manifest Required (iOS 17+)",
                description="Apps must include PrivacyInfo.xcprivacy declaring API usage reasons",
                category="privacy",
                severity="critical",
                source_url="https://developer.apple.com/documentation/bundleresources/privacy_manifest_files",
                last_updated=datetime.now(),
                version="2024.1",
                checkable=True
            ))
            
        except Exception as e:
            logging.exception(f"Failed to scrape Apple policies: {e}")
            policies = self._get_fallback_policies()
            logging.warning("Using fallback policies due to scraper failure.")
        
        self.save_cache(policies)
        return policies
    
    def _extract_version(self, soup: BeautifulSoup) -> str:
        version_elem = soup.find(string=re.compile(r'Updated|Version'))
        if version_elem:
            match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d+\.\d+)', str(version_elem))
            if match:
                return match.group(1)
        return datetime.now().strftime("%Y.%m")
    
    def _get_rule_description(self, rule_id: str) -> str:
        descriptions = {
            "2.1": "App must be complete and functional when submitted",
            "2.3.7": "App icons must be unique and not misleading",
            "2.3.8": "Apps must have a privacy policy URL",
            "4.2.3": "App must provide minimum useful functionality",
            "5.1.1": "Apps must describe data collection practices",
            "5.1.2": "Apps must explain how data is used and shared",
        }
        return descriptions.get(rule_id, "")
    
    def _get_fallback_policies(self) -> List[PolicyRule]:
        """Return hardcoded policies when scraping fails."""
        return [PolicyRule(
            id=f"APPLE_{rid.replace('.', '_')}", title=meta["title"],
            description=self._get_rule_description(rid), category=meta["category"],
            severity=meta["severity"], source_url=f"{self.GUIDELINES_URL}#{rid}",
            last_updated=datetime.now(), version="fallback", checkable=True
        ) for rid, meta in self.CHECKABLE_POLICIES.items()]
