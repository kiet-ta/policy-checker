"""Tests for policy checkers."""
import pytest
from pathlib import Path
import tempfile
import json

def test_expo_checker_missing_config():
    """Test Expo checker with missing app.json."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from checkers.expo_checker import ExpoChecker
    
    checker = ExpoChecker()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = checker.check(Path(tmpdir))
        assert not result.passed
        assert result.critical_count > 0

def test_flutter_checker_missing_pubspec():
    """Test Flutter checker with missing pubspec.yaml."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from checkers.flutter_checker import FlutterChecker
    
    checker = FlutterChecker()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = checker.check(Path(tmpdir))
        assert not result.passed
        assert result.critical_count > 0

def test_expo_checker_valid_config():
    """Test Expo checker with valid minimal config."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from checkers.expo_checker import ExpoChecker
    
    checker = ExpoChecker()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal valid app.json
        app_json = {
            "expo": {
                "name": "TestApp",
                "version": "1.0.0",
                "icon": "./assets/icon.png",
                "ios": {
                    "bundleIdentifier": "com.test.app",
                    "infoPlist": {
                        "NSPrivacyAccessedAPITypes": []
                    }
                },
                "android": {
                    "package": "com.test.app"
                }
            }
        }
        
        # Write app.json
        with open(Path(tmpdir) / "app.json", "w") as f:
            json.dump(app_json, f)
        
        # Create assets folder and icon
        assets = Path(tmpdir) / "assets"
        assets.mkdir()
        (assets / "icon.png").touch()
        
        result = checker.check(Path(tmpdir))
        # Should have fewer critical errors now
        assert result.critical_count < 5
