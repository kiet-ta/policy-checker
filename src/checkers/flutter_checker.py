"""Flutter project policy checker - Comprehensive validation."""
import re
import yaml
from pathlib import Path
from typing import Optional, Dict
from .base import BaseChecker, CheckResult, PolicyViolation, Severity

class FlutterChecker(BaseChecker):
    """Validates Flutter projects against App Store and Play Store policies."""
    
    MIN_TARGET_SDK = 34  # Google Play requirement 2024
    MIN_COMPILE_SDK = 34
    
    DANGEROUS_PERMISSIONS = [
        "android.permission.CAMERA", "android.permission.RECORD_AUDIO",
        "android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.READ_CONTACTS", "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.READ_PHONE_STATE"
    ]
    
    def get_project_type(self) -> str:
        return "flutter"
    
    def check(self, path: Path, platform: str = "both", verbose: bool = False) -> CheckResult:
        result = CheckResult(project_type="flutter", project_path=str(path), platform=platform)
        
        # Check pubspec.yaml
        pubspec = self._load_pubspec(path)
        if not pubspec:
            result.add_violation(PolicyViolation(
                rule_id="FLUTTER_001", title="Missing pubspec.yaml",
                message="pubspec.yaml is required for Flutter projects",
                severity=Severity.CRITICAL, category="configuration"
            ))
            return result
        
        result.metadata["pubspec"] = pubspec
        self._check_pubspec(pubspec, result)
        
        if platform in ["ios", "both"]:
            self._check_ios(path, result)
        
        if platform in ["android", "both"]:
            self._check_android(path, result)
        
        return result
    
    def _load_pubspec(self, path: Path) -> Optional[Dict]:
        pubspec_path = path / "pubspec.yaml"
        if pubspec_path.exists():
            try:
                with open(pubspec_path) as f:
                    return yaml.safe_load(f)
            except Exception:
                pass
        return None
    
    def _check_pubspec(self, pubspec: Dict, result: CheckResult):
        if not pubspec.get("name"):
            result.add_violation(PolicyViolation(
                rule_id="FLUTTER_002", title="Missing App Name",
                message="App name is required in pubspec.yaml",
                severity=Severity.CRITICAL, category="identity", file="pubspec.yaml"
            ))
        
        if not pubspec.get("version"):
            result.add_violation(PolicyViolation(
                rule_id="FLUTTER_003", title="Missing Version",
                message="Version is required in pubspec.yaml",
                severity=Severity.CRITICAL, category="identity", file="pubspec.yaml",
                suggestion="Add version: 1.0.0+1"
            ))
        
        if not pubspec.get("description"):
            result.add_violation(PolicyViolation(
                rule_id="FLUTTER_004", title="Missing Description",
                message="Description helps with store listing",
                severity=Severity.MINOR, category="metadata", file="pubspec.yaml"
            ))
    
    def _check_ios(self, path: Path, result: CheckResult):
        info_plist = path / "ios" / "Runner" / "Info.plist"
        
        if not info_plist.exists():
            result.add_violation(PolicyViolation(
                rule_id="IOS_001", title="Missing Info.plist",
                message="iOS Info.plist not found",
                severity=Severity.CRITICAL, category="configuration"
            ))
            return
        
        content = info_plist.read_text()
        
        # Check Privacy Manifest
        privacy_manifest = path / "ios" / "Runner" / "PrivacyInfo.xcprivacy"
        has_privacy_manifest = privacy_manifest.exists() or "NSPrivacyAccessedAPITypes" in content
        
        if not has_privacy_manifest:
            result.add_violation(PolicyViolation(
                rule_id="IOS_PRIVACY_001", title="Missing Privacy Manifest",
                message="iOS 17+ requires PrivacyInfo.xcprivacy",
                severity=Severity.CRITICAL, category="privacy",
                file="ios/Runner/PrivacyInfo.xcprivacy",
                suggestion="Create PrivacyInfo.xcprivacy with required API declarations",
                documentation_url="https://developer.apple.com/documentation/bundleresources/privacy_manifest_files",
                auto_fixable=True
            ))
        
        # Check Bundle Identifier
        if "CFBundleIdentifier" not in content:
            result.add_violation(PolicyViolation(
                rule_id="IOS_002", title="Missing Bundle Identifier",
                message="CFBundleIdentifier not found in Info.plist",
                severity=Severity.CRITICAL, category="identity"
            ))
    
    def _check_android(self, path: Path, result: CheckResult):
        manifest = path / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
        build_gradle = path / "android" / "app" / "build.gradle"
        build_gradle_kts = path / "android" / "app" / "build.gradle.kts"
        
        # Check AndroidManifest.xml
        if not manifest.exists():
            result.add_violation(PolicyViolation(
                rule_id="ANDROID_001", title="Missing AndroidManifest.xml",
                message="AndroidManifest.xml not found",
                severity=Severity.CRITICAL, category="configuration"
            ))
        else:
            manifest_content = manifest.read_text()
            
            # Check package name
            if 'package="' not in manifest_content and 'package = "' not in manifest_content:
                result.add_violation(PolicyViolation(
                    rule_id="ANDROID_002", title="Missing Package Name",
                    message="Package name not found in AndroidManifest.xml",
                    severity=Severity.CRITICAL, category="identity"
                ))
            
            # Check dangerous permissions
            for perm in self.DANGEROUS_PERMISSIONS:
                if perm in manifest_content:
                    perm_name = perm.split(".")[-1]
                    result.add_violation(PolicyViolation(
                        rule_id=f"PERM_{perm_name}", title=f"Dangerous Permission: {perm_name}",
                        message=f"{perm_name} requires justification in Play Store Data Safety",
                        severity=Severity.MAJOR, category="permissions",
                        file="AndroidManifest.xml"
                    ))
        
        # Check build.gradle
        gradle_file = build_gradle if build_gradle.exists() else build_gradle_kts
        if gradle_file.exists():
            gradle_content = gradle_file.read_text()
            
            # Check targetSdkVersion
            target_match = re.search(r'targetSdk(?:Version)?\s*[=:]?\s*(\d+)', gradle_content)
            if target_match:
                target_sdk = int(target_match.group(1))
                if target_sdk < self.MIN_TARGET_SDK:
                    result.add_violation(PolicyViolation(
                        rule_id="ANDROID_SDK_001", title="Target SDK Too Low",
                        message=f"targetSdkVersion {target_sdk} is below required {self.MIN_TARGET_SDK}",
                        severity=Severity.CRITICAL, category="technical",
                        file=str(gradle_file.name),
                        suggestion=f"Update targetSdkVersion to {self.MIN_TARGET_SDK} or higher",
                        documentation_url="https://developer.android.com/google/play/requirements/target-sdk"
                    ))
            
            # Check compileSdkVersion
            compile_match = re.search(r'compileSdk(?:Version)?\s*[=:]?\s*(\d+)', gradle_content)
            if compile_match:
                compile_sdk = int(compile_match.group(1))
                if compile_sdk < self.MIN_COMPILE_SDK:
                    result.add_violation(PolicyViolation(
                        rule_id="ANDROID_SDK_002", title="Compile SDK Too Low",
                        message=f"compileSdkVersion {compile_sdk} should be {self.MIN_COMPILE_SDK}+",
                        severity=Severity.MAJOR, category="technical",
                        file=str(gradle_file.name)
                    ))
