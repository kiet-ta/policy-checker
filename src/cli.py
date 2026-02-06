#!/usr/bin/env python3
"""
Mobile App Policy Checker CLI
=============================
Validate Expo and Flutter apps against App Store and Google Play policies.

Usage:
    policy-checker <path> [options]
    policy-checker update-policies
    policy-checker --help
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="policy-checker",
        description="Check mobile apps against App Store & Google Play policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  policy-checker ./my-expo-app              # Auto-detect and check
  policy-checker ./my-app --type flutter    # Specify project type
  policy-checker ./my-app --platform ios    # Check iOS only
  policy-checker ./my-app --output json     # JSON output for CI/CD
  policy-checker update-policies            # Fetch latest policies
        """
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Check command (default)
    check_parser = subparsers.add_parser("check", help="Check a project")
    check_parser.add_argument("path", help="Path to mobile app project")
    check_parser.add_argument("-t", "--type", choices=["expo", "flutter", "auto"], default="auto")
    check_parser.add_argument("-p", "--platform", choices=["ios", "android", "both"], default="both")
    check_parser.add_argument("-o", "--output", choices=["text", "json", "markdown"], default="text")
    check_parser.add_argument("-v", "--verbose", action="store_true")
    check_parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    
    # Update policies command
    update_parser = subparsers.add_parser("update-policies", help="Fetch latest policies")
    
    # Version
    parser.add_argument("--version", action="version", version="policy-checker 0.2.0")
    
    # Handle direct path argument (no subcommand)
    args, remaining = parser.parse_known_args()
    
    if args.command is None and remaining:
        # Treat first remaining arg as path
        sys.argv = [sys.argv[0], "check"] + remaining
        args = parser.parse_args()
    elif args.command is None:
        parser.print_help()
        sys.exit(0)
    
    if args.command == "update-policies":
        from checkers.policy_engine import PolicyEngine
        engine = PolicyEngine()
        print("🔄 Fetching latest policies from Apple and Google...")
        result = engine.update_policies()
        print(f"✅ Apple: {result['apple']['policies']} policies ({result['apple']['updates']} updates)")
        print(f"✅ Google: {result['google']['policies']} policies ({result['google']['updates']} updates)")
        sys.exit(0)
    
    # Run check
    from checkers.policy_engine import PolicyEngine
    
    engine = PolicyEngine()
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    try:
        result = engine.check(path, args.type, args.platform, args.verbose)
        result.output(args.output)
        sys.exit(0 if result.passed else 1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
