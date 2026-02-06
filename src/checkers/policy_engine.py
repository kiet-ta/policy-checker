"""Policy Engine - Orchestrates policy checking with live updates."""
from pathlib import Path
from typing import Optional, List
from .base import CheckResult
from .expo_checker import ExpoChecker
from .flutter_checker import FlutterChecker

class PolicyEngine:
    """Main engine for running policy checks with auto-detection."""
    
    def __init__(self, auto_update: bool = True):
        self.auto_update = auto_update
        self.expo_checker = ExpoChecker()
        self.flutter_checker = FlutterChecker()
    
    def detect_project_type(self, path: Path) -> Optional[str]:
        """Auto-detect project type from directory structure."""
        if (path / "app.json").exists() or (path / "app.config.js").exists():
            return "expo"
        if (path / "pubspec.yaml").exists():
            return "flutter"
        return None
    
    def check(self, path: Path, project_type: str = "auto", platform: str = "both", verbose: bool = False) -> CheckResult:
        """Run policy checks on a mobile app project."""
        path = Path(path)
        
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        # Auto-detect project type
        if project_type == "auto":
            project_type = self.detect_project_type(path)
            if not project_type:
                raise ValueError("Could not detect project type. Use --type to specify.")
        
        # Select checker
        if project_type == "expo":
            return self.expo_checker.check(path, platform, verbose)
        elif project_type == "flutter":
            return self.flutter_checker.check(path, platform, verbose)
        else:
            raise ValueError(f"Unknown project type: {project_type}")
    
    def update_policies(self) -> dict:
        """Fetch latest policies from Apple and Google."""
        from ..scrapers import ApplePolicyScraper, GooglePolicyScraper
        
        apple = ApplePolicyScraper()
        google = GooglePolicyScraper()
        
        apple_policies = apple.fetch_policies()
        google_policies = google.fetch_policies()
        
        apple_updates = apple.detect_changes(apple_policies)
        google_updates = google.detect_changes(google_policies)
        
        return {
            "apple": {"policies": len(apple_policies), "updates": len(apple_updates)},
            "google": {"policies": len(google_policies), "updates": len(google_updates)}
        }
