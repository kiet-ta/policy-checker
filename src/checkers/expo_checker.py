"""Expo project policy checker with enhanced image validation."""
import json
from pathlib import Path
from typing import Optional, Dict
from .base import BaseChecker, CheckResult, PolicyViolation, Severity

class ExpoChecker(BaseChecker):
    """Validates Expo projects against App Store and Play Store policies with image processing."""
    
    # Dangerous permissions requiring justification
    DANGEROUS_PERMISSIONS = [
        "CAMERA", "RECORD_AUDIO", "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
        "READ_CONTACTS", "WRITE_CONTACTS", "READ_CALENDAR", "WRITE_CALENDAR",
        "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE", "READ_PHONE_STATE"
    ]
    
    def get_project_type(self) -> str:
        return "expo"
    
    def check(self, path: Path, platform: str = "both", verbose: bool = False) -> CheckResult:
        result = CheckResult(
            project_type="expo",
            project_path=str(path),
            platform=platform
        )
        
        # Load configuration
        config = self._load_expo_config(path)
        if not config:
            result.add_violation(PolicyViolation(
                rule_id="EXPO_001", title="Missing Configuration",
                message="Cannot find app.json or app.config.js",
                severity=Severity.CRITICAL, category="configuration",
                suggestion="Create app.json with expo configuration"
            ))
            return result
        
        result.metadata["config"] = config
        
        # Run all checks
        self._check_app_identity(config, result, platform)
        self._check_privacy_requirements(config, path, result, platform)
        self._check_assets_with_validation(config, path, result, platform)
        self._check_permissions(config, result, platform)
        self._check_sdk_version(config, result)
        
        return result
    
    def _load_expo_config(self, path: Path) -> Optional[Dict]:
        """Load Expo configuration from app.json or app.config.js."""
        app_json = path / "app.json"
        if app_json.exists():
            try:
                with open(app_json) as f:
                    data = json.load(f)
                    return data.get("expo", data)
            except Exception:
                pass
        return None
    
    def _check_app_identity(self, config: Dict, result: CheckResult, platform: str):
        """Check app identity requirements."""
        # App name
        if not config.get("name"):
            result.add_violation(PolicyViolation(
                rule_id="IDENTITY_001", title="Missing App Name",
                message="App name is required for store submission",
                severity=Severity.CRITICAL, category="identity",
                file="app.json", suggestion="Add 'name' field to expo config"
            ))
        
        # Version
        if not config.get("version"):
            result.add_violation(PolicyViolation(
                rule_id="IDENTITY_002", title="Missing Version",
                message="App version is required",
                severity=Severity.CRITICAL, category="identity",
                file="app.json", suggestion="Add 'version' field (e.g., '1.0.0')"
            ))
        
        # iOS Bundle Identifier
        if platform in ["ios", "both"]:
            ios_config = config.get("ios", {})
            if not ios_config.get("bundleIdentifier"):
                result.add_violation(PolicyViolation(
                    rule_id="IOS_001", title="Missing Bundle Identifier",
                    message="iOS apps require a unique bundle identifier",
                    severity=Severity.CRITICAL, category="identity",
                    file="app.json", suggestion="Add 'ios.bundleIdentifier' (e.g., 'com.company.appname')",
                    documentation_url="https://developer.apple.com/documentation/bundleresources/information_property_list/cfbundleidentifier"
                ))
        
        # Android Package Name
        if platform in ["android", "both"]:
            android_config = config.get("android", {})
            if not android_config.get("package"):
                result.add_violation(PolicyViolation(
                    rule_id="ANDROID_001", title="Missing Package Name",
                    message="Android apps require a unique package name",
                    severity=Severity.CRITICAL, category="identity",
                    file="app.json", suggestion="Add 'android.package' (e.g., 'com.company.appname')"
                ))
    
    def _check_privacy_requirements(self, config: Dict, path: Path, result: CheckResult, platform: str):
        """Check privacy policy and manifest requirements."""
        # Privacy Policy URL (required for both stores)
        has_privacy_policy = False
        ios_config = config.get("ios", {})
        android_config = config.get("android", {})
        
        # Check various locations for privacy policy
        if config.get("privacyPolicy") or ios_config.get("privacyPolicy") or android_config.get("privacyPolicy"):
            has_privacy_policy = True
        
        if not has_privacy_policy:
            result.add_violation(PolicyViolation(
                rule_id="PRIVACY_001", title="Missing Privacy Policy URL",
                message="Apps that collect user data must have a privacy policy",
                severity=Severity.MAJOR, category="privacy",
                file="app.json", suggestion="Add privacy policy URL to your app configuration",
                documentation_url="https://developer.apple.com/app-store/review/guidelines/#privacy"
            ))
        
        # iOS Privacy Manifest (iOS 17+)
        if platform in ["ios", "both"]:
            info_plist = ios_config.get("infoPlist", {})
            has_privacy_manifest = (
                info_plist.get("NSPrivacyAccessedAPITypes") or
                info_plist.get("NSPrivacyCollectedDataTypes") or
                (path / "ios" / "PrivacyInfo.xcprivacy").exists()
            )
            
            if not has_privacy_manifest:
                result.add_violation(PolicyViolation(
                    rule_id="IOS_PRIVACY_001", title="Missing Privacy Manifest",
                    message="iOS 17+ requires PrivacyInfo.xcprivacy declaring API usage reasons",
                    severity=Severity.CRITICAL, category="privacy",
                    file="app.json",
                    suggestion="Add NSPrivacyAccessedAPITypes to ios.infoPlist or create PrivacyInfo.xcprivacy",
                    documentation_url="https://developer.apple.com/documentation/bundleresources/privacy_manifest_files",
                    auto_fixable=True
                ))
    
    def _check_assets_with_validation(self, config: Dict, path: Path, result: CheckResult, platform: str):
        """Check app icons and assets with comprehensive image validation."""
        # Import image validator
        try:
            from ..validators import IconValidator, AssetValidator
            icon_validator = IconValidator()
            asset_validator = AssetValidator()
        except ImportError:
            # Fallback to basic checks if validators not available
            self._check_assets_basic(config, path, result, platform)
            return
        
        # App Icon with detailed validation
        icon_path = config.get("icon")
        if not icon_path:
            result.add_violation(PolicyViolation(
                rule_id="ASSET_001", title="Missing App Icon",
                message="App icon is required for store submission",
                severity=Severity.CRITICAL, category="assets",
                file="app.json", suggestion="Add 'icon' field pointing to a 1024x1024 PNG"
            ))
        else:
            full_icon_path = path / icon_path
            if not full_icon_path.exists():
                result.add_violation(PolicyViolation(
                    rule_id="ASSET_002", title="App Icon Not Found",
                    message=f"Icon file '{icon_path}' does not exist",
                    severity=Severity.CRITICAL, category="assets",
                    suggestion=f"Create icon file at {icon_path}"
                ))
            else:
                # Detailed icon validation
                icon_result = icon_validator.validate_icon(full_icon_path, platform)
                
                # Convert image validation results to policy violations
                for error in icon_result.errors:
                    result.add_violation(PolicyViolation(
                        rule_id="ICON_ERROR", title="Icon Validation Error",
                        message=error, severity=Severity.CRITICAL, category="assets",
                        file=icon_path, auto_fixable=True,
                        suggestion="Use policy-checker --fix to auto-generate correct icon sizes"
                    ))
                
                for warning in icon_result.warnings:
                    result.add_violation(PolicyViolation(
                        rule_id="ICON_WARNING", title="Icon Quality Issue",
                        message=warning, severity=Severity.MINOR, category="assets",
                        file=icon_path
                    ))
                
                # Add image info to metadata
                if icon_result.image_info:
                    result.metadata["icon_info"] = {
                        "width": icon_result.image_info.width,
                        "height": icon_result.image_info.height,
                        "format": icon_result.image_info.format,
                        "size_mb": icon_result.image_info.size_bytes / (1024 * 1024),
                        "has_transparency": icon_result.image_info.has_transparency
                    }
        
        # Comprehensive asset validation
        try:
            asset_report = asset_validator.validate_all_assets(path, platform)
            
            # Add missing assets as violations
            for missing in asset_report.missing_assets:
                result.add_violation(PolicyViolation(
                    rule_id="ASSET_MISSING", title="Missing Asset",
                    message=missing, severity=Severity.MAJOR, category="assets",
                    auto_fixable=True,
                    suggestion="Use policy-checker --fix to auto-generate missing assets"
                ))
            
            # Add asset recommendations
            for recommendation in asset_report.recommendations:
                result.add_violation(PolicyViolation(
                    rule_id="ASSET_RECOMMENDATION", title="Asset Recommendation",
                    message=recommendation, severity=Severity.INFO, category="assets"
                ))
            
            result.metadata["asset_report"] = {
                "icons_validated": len(asset_report.icon_results),
                "splashes_validated": len(asset_report.splash_results),
                "all_valid": asset_report.is_valid
            }
        
        except Exception as e:
            result.add_violation(PolicyViolation(
                rule_id="ASSET_VALIDATION_ERROR", title="Asset Validation Failed",
                message=f"Could not validate assets: {str(e)}",
                severity=Severity.MINOR, category="assets"
            ))
        
        # Splash screen
        splash = config.get("splash", {})
        if not splash.get("image"):
            result.add_violation(PolicyViolation(
                rule_id="ASSET_003", title="Missing Splash Screen",
                message="Splash screen improves user experience",
                severity=Severity.MINOR, category="assets",
                suggestion="Add 'splash.image' to your config"
            ))
    
    def _check_assets_basic(self, config: Dict, path: Path, result: CheckResult, platform: str):
        """Basic asset checking without image processing."""
        # App Icon
        icon_path = config.get("icon")
        if not icon_path:
            result.add_violation(PolicyViolation(
                rule_id="ASSET_001", title="Missing App Icon",
                message="App icon is required for store submission",
                severity=Severity.CRITICAL, category="assets",
                file="app.json", suggestion="Add 'icon' field pointing to a 1024x1024 PNG"
            ))
        elif icon_path:
            full_icon_path = path / icon_path
            if not full_icon_path.exists():
                result.add_violation(PolicyViolation(
                    rule_id="ASSET_002", title="App Icon Not Found",
                    message=f"Icon file '{icon_path}' does not exist",
                    severity=Severity.CRITICAL, category="assets",
                    suggestion=f"Create icon file at {icon_path}"
                ))
        
        # Splash screen
        splash = config.get("splash", {})
        if not splash.get("image"):
            result.add_violation(PolicyViolation(
                rule_id="ASSET_003", title="Missing Splash Screen",
                message="Splash screen improves user experience",
                severity=Severity.MINOR, category="assets",
                suggestion="Add 'splash.image' to your config"
            ))
    
    def _check_permissions(self, config: Dict, result: CheckResult, platform: str):
        """Check permission declarations and justifications."""
        if platform in ["android", "both"]:
            android_config = config.get("android", {})
            permissions = android_config.get("permissions", [])
            
            for perm in permissions:
                perm_name = perm.replace("android.permission.", "") if isinstance(perm, str) else perm
                if perm_name in self.DANGEROUS_PERMISSIONS:
                    result.add_violation(PolicyViolation(
                        rule_id=f"PERM_{perm_name}", title=f"Dangerous Permission: {perm_name}",
                        message=f"Permission {perm_name} requires justification in Play Store",
                        severity=Severity.MAJOR, category="permissions",
                        suggestion=f"Ensure you have a valid use case for {perm_name} and declare it in Data Safety"
                    ))
    
    def _check_sdk_version(self, config: Dict, result: CheckResult):
        """Check SDK version requirements."""
        sdk_version = config.get("sdkVersion", "")
        if sdk_version:
            try:
                major_version = int(sdk_version.split(".")[0])
                if major_version < 50:
                    result.add_violation(PolicyViolation(
                        rule_id="SDK_001", title="Outdated Expo SDK",
                        message=f"SDK {sdk_version} may not meet latest store requirements",
                        severity=Severity.MINOR, category="technical",
                        suggestion="Consider upgrading to Expo SDK 50+"
                    ))
            except Exception:
                pass
