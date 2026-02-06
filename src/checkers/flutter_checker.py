"""Flutter project policy checker."""

import re
from pathlib import Path
from .base import BaseChecker, CheckResult, PolicyViolation, Severity

class FlutterChecker(BaseChecker):
    def check(self, path: Path, platform: str = "both", verbose: bool = False) -> CheckResult:
        result = CheckResult()
        
        # Check pubspec.yaml
        pubspec = path / "pubspec.yaml"
        if pubspec.exists():
            self._check_pubspec(pubspec, result)
        else:
            result.violations.append(PolicyViolation("FLT001", "pubspec.yaml not found", Severity.ERROR))
        
        # iOS checks
        if platform in ["ios", "both"]:
            self._check_ios(path, result)
        
        # Android checks
        if platform in ["android", "both"]:
            self._check_android(path, result)
        
        return result
    
    def _check_pubspec(self, pubspec: Path, result: CheckResult):
        content = pubspec.read_text()
        if "name:" not in content:
            result.violations.append(PolicyViolation("FLT002", "Missing app name in pubspec.yaml", Severity.ERROR))
        if "version:" not in content:
            result.violations.append(PolicyViolation("FLT003", "Missing version in pubspec.yaml", Severity.ERROR))
    
    def _check_ios(self, path: Path, result: CheckResult):
        info_plist = path / "ios" / "Runner" / "Info.plist"
        if not info_plist.exists():
            result.violations.append(PolicyViolation("IOS001", "iOS Info.plist not found", Severity.ERROR))
            return
        
        content = info_plist.read_text()
        if "NSPrivacyAccessedAPITypes" not in content:
            result.violations.append(PolicyViolation("IOS003", "Missing Privacy Manifest (required since iOS 17)", Severity.ERROR, str(info_plist), suggestion="Add PrivacyInfo.xcprivacy file"))
    
    def _check_android(self, path: Path, result: CheckResult):
        manifest = path / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
        if not manifest.exists():
            result.violations.append(PolicyViolation("AND001", "AndroidManifest.xml not found", Severity.ERROR))
            return
        
        build_gradle = path / "android" / "app" / "build.gradle"
        if build_gradle.exists():
            content = build_gradle.read_text()
            if "targetSdkVersion" in content:
                match = re.search(r'targetSdkVersion\s+(\d+)', content)
                if match and int(match.group(1)) < 34:
                    result.violations.append(PolicyViolation("AND003", f"targetSdkVersion {match.group(1)} is below required 34", Severity.ERROR, str(build_gradle), suggestion="Update targetSdkVersion to 34 or higher"))
