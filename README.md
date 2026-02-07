# 📱 Mobile App Policy Checker

[![CI](https://github.com/kiet-ta/policy-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/kiet-ta/policy-checker/actions/workflows/ci.yml)
[![Policy Update](https://github.com/kiet-ta/policy-checker/actions/workflows/policy-update.yml/badge.svg)](https://github.com/kiet-ta/policy-checker/actions/workflows/policy-update.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> CLI tool to validate **Expo** and **Flutter** mobile apps against **App Store** and **Google Play** policies before submission. Now with **comprehensive image processing** and **auto-generation** features!

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Auto-detect** | Automatically identifies Expo or Flutter projects |
| 📱 **Multi-platform** | Check iOS, Android, or both simultaneously |
| 🔄 **Live Updates** | Weekly auto-fetch of latest policies from Apple & Google |
| 🤖 **CI/CD Ready** | JSON output for pipeline integration |
| 🔧 **Auto-fix** | Automatically fix common issues |
| 🖼️ **Image Processing** | Comprehensive icon validation and generation |
| 🎨 **Asset Generation** | Auto-generate missing icons and splash screens |

## 🚀 Quick Start

```bash
# Install with image processing support
pip install policy-checker

# Check your app
policy-checker ./my-expo-app
policy-checker ./my-flutter-app --type flutter

# Generate icon sets from source
policy-checker generate-icons source-icon.png

# Validate single icon
policy-checker validate-icon assets/icon.png
```

## 🖼️ Image Processing Features

### Icon Validation
- ✅ Size validation (1024x1024 for iOS, 512x512 for Android)
- ✅ Format validation (PNG, JPEG, WebP)
- ✅ Quality checks (DPI, aspect ratio, transparency)
- ✅ File size optimization recommendations

### Auto-Generation
- 🎯 Generate complete icon sets for iOS (13 sizes) and Android (7 sizes)
- 🎨 Create splash screens with centered icons
- 🔧 Auto-fix missing assets with `--fix` flag
- 📐 Proper resizing with high-quality algorithms

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

[ICON_ERROR] Icon Validation Error
   iOS icon size (512, 512) not in required sizes: [(1024, 1024)]
   📁 assets/icon.png
   💡 Resize to (1024, 1024) for iOS App Store
   🔧 Auto-fixable: Run with --fix

======================================================================
Summary: 2 critical, 0 major, 1 minor
Status: 🚫 WILL BE REJECTED
======================================================================
```

## 📖 Usage

### Basic Commands

```bash
# Auto-detect project type and check
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

# Auto-fix issues
policy-checker ./my-app --fix
```

### Image Processing Commands

```bash
# Generate complete icon sets
policy-checker generate-icons source.png
policy-checker generate-icons source.png --platform ios
policy-checker generate-icons source.png --output ./icons

# Validate single icon
policy-checker validate-icon assets/icon.png
policy-checker validate-icon icon.png --output json

# Generate missing assets for project
policy-checker generate-assets ./my-project
```

### Policy Management

```bash
# Update policies from Apple & Google
policy-checker update-policies
```

## 🔍 What Gets Checked

### iOS (App Store)
- ✅ Privacy Manifest (iOS 17+ requirement)
- ✅ Bundle Identifier
- ✅ App Icon (1024x1024, PNG format)
- ✅ Privacy Policy URL
- ✅ Info.plist configuration
- 🖼️ **Icon quality and specifications**

### Android (Google Play)
- ✅ Target SDK Version (API 34+)
- ✅ Package Name
- ✅ Dangerous Permissions
- ✅ AndroidManifest.xml
- ✅ build.gradle configuration
- 🖼️ **Icon quality and specifications**

### Image Validation
- 📐 **Size Requirements**: Platform-specific dimensions
- 🎨 **Format Support**: PNG, JPEG, WebP
- 🔍 **Quality Checks**: DPI, transparency, color mode
- 📊 **File Size**: Optimization recommendations
- ⚡ **Performance**: Power-of-2 dimensions

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
      - run: policy-checker . --output json --fix > report.json
      - uses: actions/upload-artifact@v3
        with:
          name: policy-report
          path: report.json
```

## 🎯 Auto-Fix Capabilities

The `--fix` flag can automatically resolve:

| Issue | Auto-Fix Action |
|-------|-----------------|
| Missing Privacy Manifest | Generate PrivacyInfo.xcprivacy |
| Wrong icon sizes | Generate correct icon sets |
| Missing splash screens | Create basic splash screens |
| Missing assets | Generate from existing icons |

## 📚 Documentation

Full documentation with Mermaid diagrams available at [docs/README.md](docs/README.md)

- Architecture diagrams
- Sequence flows  
- API reference
- Best practices
- Troubleshooting guide
- Image processing workflows

## 🛠️ Development

```bash
# Clone
git clone git@github.com:kiet-ta/policy-checker.git
cd policy-checker

# Install with dev dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Test image processing
policy-checker validate-icon tests/fixtures/test-icon.png
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Resources

- [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Apple Privacy Manifest](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files)
- [Google Play Developer Policy](https://play.google.com/about/developer-content-policy/)
- [Android Target SDK Requirements](https://developer.android.com/google/play/requirements/target-sdk)
- [iOS Icon Guidelines](https://developer.apple.com/design/human-interface-guidelines/app-icons)
- [Android Icon Guidelines](https://developer.android.com/guide/practices/ui_guidelines/icon_design)
