"""Expo project policy checker."""

import json
from pathlib import Path
from .base import BaseChecker, CheckResult, PolicyViolation, Severity

class ExpoChecker(BaseChecker):
    def check(self, path: Path, platform: str = "both", verbose: bool = False) -> CheckResult:
        result = CheckResult()
        
        # Check app.json
        app_json = path / "app.json"
        if app_json.exists():
            self._check_app_json(app_json, result, platform)
        else:
            result.violations.append(PolicyViolation("EXPO001", "app.json not found", Severity.ERROR))
        
        # Check assets
        self._check_assets(path, result, platform)
        
        # Check permissions
        self._check_permissions(path, result, platform)
        
        return result
    
    def _check_app_json(self, app_json: Path, result: CheckResult, platform: str):
        with open(app_json) as f:
            config = json.load(f).get("expo", {})
        
        # iOS checks
        if platform in ["ios", "both"]:
            ios = config.get("ios", {})
            if not ios.get("bundleIdentifier"):
                result.violations.append(PolicyViolation("IOS001", "Missing iOS bundleIdentifier", Severity.ERROR, "app.json"))
            if not ios.get("buildNumber"):
                result.violations.append(PolicyViolation("IOS002", "Missing iOS buildNumber", Severity.WARNING, "app.json"))
            infoPlist = ios.get("infoPlist", {})
            if not infoPlist.get("NSPrivacyAccessedAPITypes"):
                result.violations.append(PolicyViolation("IOS003", "Missing Privacy Manifest (required since iOS 17)", Severity.ERROR, "app.json", suggestion="Add NSPrivacyAccessedAPITypes to ios.infoPlist"))
        
        # Android checks
        if platform in ["android", "both"]:
            android = config.get("android", {})
            if not android.get("package"):
                result.violations.append(PolicyViolation("AND001", "Missing Android package name", Severity.ERROR, "app.json"))
            if not android.get("versionCode"):
                result.violations.append(PolicyViolation("AND002", "Missing Android versionCode", Severity.WARNING, "app.json"))
        
        # Common checks
        if not config.get("name"):
            result.violations.append(PolicyViolation("COM001", "Missing app name", Severity.ERROR, "app.json"))
        if not config.get("version"):
            result.violations.append(PolicyViolation("COM002", "Missing app version", Severity.ERROR, "app.json"))
        if not config.get("icon"):
            result.violations.append(PolicyViolation("COM003", "Missing app icon", Severity.ERROR, "app.json"))
    
    def _check_assets(self, path: Path, result: CheckResult, platform: str):
        assets = path / "assets"
        if not assets.exists():
            result.violations.append(PolicyViolation("AST001", "Assets folder not found", Severity.WARNING))
    
    def _check_permissions(self, path: Path, result: CheckResult, platform: str):
        pass  # TODO: Implement permission checks
