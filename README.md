# 📱 Mobile App Policy Checker

[![CI](https://github.com/kiet-ta/policy-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/kiet-ta/policy-checker/actions/workflows/ci.yml)
[![Policy Update](https://github.com/kiet-ta/policy-checker/actions/workflows/policy-update.yml/badge.svg)](https://github.com/kiet-ta/policy-checker/actions/workflows/policy-update.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> CLI tool to validate **Expo** and **Flutter** mobile apps against **App Store** and **Google Play** policies before submission.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Auto-detect** | Automatically identifies Expo or Flutter projects |
| 📱 **Multi-platform** | Check iOS, Android, or both simultaneously |
| 🔄 **Live Updates** | Weekly auto-fetch of latest policies from Apple & Google |
| 🤖 **CI/CD Ready** | JSON output for pipeline integration |
| 🔧 **Auto-fix** | Automatically fix some common issues |

## 🚀 Quick Start

```bash
# Install
pip install policy-checker

# Check your app
policy-checker ./my-expo-app
policy-checker ./my-flutter-app --type flutter
```

## 📋 Example Output

```
======================================================================
📱 MOBILE APP POLICY CHECK RESULTS
======================================================================
Project: ./my-app
Type: EXPO | Platform: BOTH
======================================================================

🚫 CRITICAL (2)
----------------------------------------

[IOS_PRIVACY_001] Missing Privacy Manifest
   iOS 17+ requires PrivacyInfo.xcprivacy declaring API usage reasons
   📁 app.json
   💡 Add NSPrivacyAccessedAPITypes to ios.infoPlist
   🔧 Auto-fixable: Run with --fix

[ANDROID_SDK_001] Target SDK Too Low
   targetSdkVersion 33 is below required 34
   📁 build.gradle
   💡 Update targetSdkVersion to 34 or higher

======================================================================
Summary: 2 critical, 0 major, 1 minor
Status: 🚫 WILL BE REJECTED
======================================================================
```

## 📖 Usage

```bash
# Basic usage (auto-detect project type)
policy-checker ./my-app

# Specify project type
policy-checker ./my-app --type expo
policy-checker ./my-app --type flutter

# Check specific platform
policy-checker ./my-app --platform ios
policy-checker ./my-app --platform android

# Output formats
policy-checker ./my-app --output json      # For CI/CD
policy-checker ./my-app --output markdown  # For reports

# Update policies from Apple & Google
policy-checker update-policies
```

## 🔍 What Gets Checked

### iOS (App Store)
- ✅ Privacy Manifest (iOS 17+ requirement)
- ✅ Bundle Identifier
- ✅ App Icon (1024x1024)
- ✅ Privacy Policy URL
- ✅ Info.plist configuration

### Android (Google Play)
- ✅ Target SDK Version (API 34+)
- ✅ Package Name
- ✅ Dangerous Permissions
- ✅ AndroidManifest.xml
- ✅ build.gradle configuration

## 🔄 CI/CD Integration

```yaml
# .github/workflows/policy-check.yml
name: Policy Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install policy-checker
      - run: policy-checker . --output json > report.json
      - uses: actions/upload-artifact@v3
        with:
          name: policy-report
          path: report.json
```

## 📚 Documentation

Full documentation with Mermaid diagrams available at [docs/README.md](docs/README.md)

- Architecture diagrams
- Sequence flows
- API reference
- Best practices
- Troubleshooting guide

## 🛠️ Development

```bash
# Clone
git clone git@github.com:kiet-ta/policy-checker.git
cd policy-checker

# Install dev dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/ -v
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Resources

- [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Apple Privacy Manifest](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files)
- [Google Play Developer Policy](https://play.google.com/about/developer-content-policy/)
- [Android Target SDK Requirements](https://developer.android.com/google/play/requirements/target-sdk)
