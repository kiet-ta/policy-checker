# 📱 Mobile App Policy Checker CLI

A CLI tool to validate Expo and Flutter mobile apps against App Store and Google Play Store policies.

## Features

| Check | Expo | Flutter | App Store | Play Store |
|-------|------|---------|-----------|------------|
| App Identity | ✅ | ✅ | ✅ | ✅ |
| Privacy Manifest (iOS 17+) | ✅ | ✅ | ✅ | - |
| Target SDK Version | - | ✅ | - | ✅ |
| Permissions Audit | 🚧 | 🚧 | ✅ | ✅ |
| Icon Specifications | ✅ | 🚧 | ✅ | ✅ |
| Privacy Policy | 🚧 | 🚧 | ✅ | ✅ |

## Installation

```bash
pip install policy-checker
```

## Usage

```bash
# Auto-detect project type
policy-checker ./my-app

# Specify project type
policy-checker ./my-expo-app --type expo
policy-checker ./my-flutter-app --type flutter

# Check specific platform
policy-checker ./my-app --platform ios
policy-checker ./my-app --platform android

# Output formats
policy-checker ./my-app --output json
policy-checker ./my-app --output html
```

## Example Output

```
============================================================
📱 POLICY CHECK RESULTS
============================================================

❌ [IOS003] Missing Privacy Manifest (required since iOS 17)
   📁 File: app.json
   💡 Suggestion: Add NSPrivacyAccessedAPITypes to ios.infoPlist

⚠️ [IOS002] Missing iOS buildNumber
   📁 File: app.json

============================================================
Summary: 1 errors, 1 warnings
Status: ❌ FAILED
```

## License

MIT
