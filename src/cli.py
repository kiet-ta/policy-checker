#!/usr/bin/env python3
"""Mobile App Policy Checker CLI - Check Expo & Flutter apps against App Store & Play Store policies."""

import argparse
import sys
from pathlib import Path
from checkers.expo_checker import ExpoChecker
from checkers.flutter_checker import FlutterChecker

def main():
    parser = argparse.ArgumentParser(
        description="Check mobile apps against App Store & Google Play policies",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", help="Path to mobile app project")
    parser.add_argument("-t", "--type", choices=["expo", "flutter", "auto"], default="auto", help="Project type")
    parser.add_argument("-p", "--platform", choices=["ios", "android", "both"], default="both", help="Target platform")
    parser.add_argument("-o", "--output", choices=["text", "json", "html"], default="text", help="Output format")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    project_path = Path(args.path)
    
    if not project_path.exists():
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    # Auto-detect project type
    project_type = args.type
    if project_type == "auto":
        if (project_path / "app.json").exists() or (project_path / "expo.json").exists():
            project_type = "expo"
        elif (project_path / "pubspec.yaml").exists():
            project_type = "flutter"
        else:
            print("Error: Could not detect project type. Use --type to specify.")
            sys.exit(1)
    
    # Run checker
    checker = ExpoChecker() if project_type == "expo" else FlutterChecker()
    results = checker.check(project_path, platform=args.platform, verbose=args.verbose)
    results.output(format=args.output)
    
    sys.exit(0 if results.passed else 1)

if __name__ == "__main__":
    main()
