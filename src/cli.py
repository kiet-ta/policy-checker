#!/usr/bin/env python3
"""
Mobile App Policy Checker CLI with Image Processing
==================================================
Validate Expo and Flutter apps against App Store and Google Play policies.
Includes comprehensive image validation and auto-generation features.

Usage:
    policy-checker <path> [options]
    policy-checker update-policies
    policy-checker generate-icons <source> [options]
    policy-checker validate-icon <icon> [options]
    policy-checker --help
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="policy-checker",
        description="Check mobile apps against App Store & Google Play policies with image processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  policy-checker ./my-expo-app                    # Auto-detect and check
  policy-checker ./my-app --type flutter         # Specify project type
  policy-checker ./my-app --platform ios         # Check iOS only
  policy-checker ./my-app --output json --fix    # JSON output with auto-fix
  policy-checker update-policies                 # Fetch latest policies
  policy-checker generate-icons icon.png         # Generate all icon sizes
  policy-checker validate-icon assets/icon.png   # Validate single icon
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
    
    # Generate icons command
    icons_parser = subparsers.add_parser("generate-icons", help="Generate icon sets from source image")
    icons_parser.add_argument("source", help="Source icon file (PNG, JPEG)")
    icons_parser.add_argument("-o", "--output", default="./generated_icons", help="Output directory")
    icons_parser.add_argument("-p", "--platform", choices=["ios", "android", "both"], default="both")
    icons_parser.add_argument("--optimize", action="store_true", help="Optimize generated icons")
    
    # Validate icon command
    validate_parser = subparsers.add_parser("validate-icon", help="Validate single icon file")
    validate_parser.add_argument("icon", help="Icon file to validate")
    validate_parser.add_argument("-p", "--platform", choices=["ios", "android", "both"], default="both")
    validate_parser.add_argument("-o", "--output", choices=["text", "json"], default="text")
    
    # Generate assets command
    assets_parser = subparsers.add_parser("generate-assets", help="Generate missing assets")
    assets_parser.add_argument("project", help="Project directory")
    assets_parser.add_argument("-p", "--platform", choices=["ios", "android", "both"], default="both")
    
    # Version
    parser.add_argument("--version", action="version", version="policy-checker 0.3.0")
    
    # Handle direct path argument (no subcommand)
    args, remaining = parser.parse_known_args()
    
    if args.command is None and remaining:
        # Treat first remaining arg as path
        sys.argv = [sys.argv[0], "check"] + remaining
        args = parser.parse_args()
    elif args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Execute commands
    if args.command == "update-policies":
        return update_policies()
    elif args.command == "generate-icons":
        return generate_icons(args)
    elif args.command == "validate-icon":
        return validate_icon(args)
    elif args.command == "generate-assets":
        return generate_assets(args)
    else:
        return check_project(args)

def update_policies():
    """Update policies from Apple and Google."""
    from checkers.policy_engine import PolicyEngine
    engine = PolicyEngine()
    print("🔄 Fetching latest policies from Apple and Google...")
    result = engine.update_policies()
    print(f"✅ Apple: {result['apple']['policies']} policies ({result['apple']['updates']} updates)")
    print(f"✅ Google: {result['google']['policies']} policies ({result['google']['updates']} updates)")
    return 0

def generate_icons(args):
    """Generate icon sets from source image."""
    try:
        from validators import IconValidator
        validator = IconValidator()
        
        source_path = Path(args.source)
        output_dir = Path(args.output)
        
        if not source_path.exists():
            print(f"❌ Error: Source icon '{args.source}' not found")
            return 1
        
        print(f"🖼️ Generating icon sets from {source_path}")
        print(f"📁 Output directory: {output_dir}")
        
        # Validate source first
        result = validator.validate_image(source_path)
        if not result.is_valid:
            print("⚠️ Source image has issues:")
            for error in result.errors:
                print(f"   ❌ {error}")
            for warning in result.warnings:
                print(f"   ⚠️ {warning}")
            
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1
        
        # Generate icon sets
        generated = validator.generate_icon_set(source_path, output_dir, args.platform)
        
        print(f"\n✅ Generated {len(generated.get('ios', []))} iOS icons")
        print(f"✅ Generated {len(generated.get('android', []))} Android icons")
        
        if args.optimize:
            print("🔧 Optimizing generated icons...")
            # TODO: Add optimization logic
        
        print(f"\n📁 Icons saved to: {output_dir}")
        return 0
        
    except ImportError:
        print("❌ Error: Image processing not available. Install Pillow: pip install Pillow")
        return 1
    except Exception as e:
        print(f"❌ Error generating icons: {e}")
        return 1

def validate_icon(args):
    """Validate single icon file."""
    try:
        from validators import IconValidator
        validator = IconValidator()
        
        icon_path = Path(args.icon)
        if not icon_path.exists():
            print(f"❌ Error: Icon '{args.icon}' not found")
            return 1
        
        print(f"🔍 Validating icon: {icon_path}")
        result = validator.validate_icon(icon_path, args.platform)
        
        if args.output == "json":
            import json
            output = {
                "valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "suggestions": result.suggestions,
                "image_info": result.image_info.__dict__ if result.image_info else None
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            # Text output
            if result.is_valid:
                print("✅ Icon validation passed!")
            else:
                print("❌ Icon validation failed!")
            
            if result.errors:
                print("\n🚫 Errors:")
                for error in result.errors:
                    print(f"   • {error}")
            
            if result.warnings:
                print("\n⚠️ Warnings:")
                for warning in result.warnings:
                    print(f"   • {warning}")
            
            if result.suggestions:
                print("\n💡 Suggestions:")
                for suggestion in result.suggestions:
                    print(f"   • {suggestion}")
            
            if result.image_info:
                info = result.image_info
                print(f"\n📊 Image Info:")
                print(f"   Size: {info.width}x{info.height}")
                print(f"   Format: {info.format}")
                print(f"   File size: {info.size_bytes / 1024:.1f} KB")
                print(f"   Has transparency: {info.has_transparency}")
        
        return 0 if result.is_valid else 1
        
    except ImportError:
        print("❌ Error: Image processing not available. Install Pillow: pip install Pillow")
        return 1
    except Exception as e:
        print(f"❌ Error validating icon: {e}")
        return 1

def generate_assets(args):
    """Generate missing assets for project."""
    try:
        from validators import AssetValidator
        validator = AssetValidator()
        
        project_path = Path(args.project)
        if not project_path.exists():
            print(f"❌ Error: Project '{args.project}' not found")
            return 1
        
        print(f"🎨 Generating missing assets for: {project_path}")
        generated = validator.generate_missing_assets(project_path, args.platform)
        
        print(f"✅ Generated {len(generated.get('icons', []))} icons")
        print(f"✅ Generated {len(generated.get('splashes', []))} splash screens")
        
        return 0
        
    except ImportError:
        print("❌ Error: Image processing not available. Install Pillow: pip install Pillow")
        return 1
    except Exception as e:
        print(f"❌ Error generating assets: {e}")
        return 1

def check_project(args):
    """Run policy checks on a project."""
    from checkers.policy_engine import PolicyEngine
    
    engine = PolicyEngine()
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ Error: Path '{args.path}' does not exist")
        return 1
    
    try:
        result = engine.check(path, args.type, args.platform, args.verbose)
        
        # Auto-fix if requested
        if args.fix and hasattr(result, 'violations'):
            print("🔧 Auto-fixing issues...")
            fixed_count = auto_fix_issues(result, path)
            if fixed_count > 0:
                print(f"✅ Fixed {fixed_count} issues")
                # Re-run check to see improvements
                result = engine.check(path, args.type, args.platform, args.verbose)
        
        result.output(args.output)
        return 0 if result.passed else 1
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1

def auto_fix_issues(result, project_path):
    """Auto-fix fixable issues."""
    fixed_count = 0
    
    try:
        from validators import IconValidator, AssetValidator
        
        for violation in result.violations:
            if not violation.auto_fixable:
                continue
            
            if violation.rule_id == "IOS_PRIVACY_001":
                # Generate basic Privacy Manifest
                privacy_manifest = create_privacy_manifest()
                manifest_path = project_path / "ios" / "PrivacyInfo.xcprivacy"
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(manifest_path, 'w') as f:
                    f.write(privacy_manifest)
                fixed_count += 1
                print(f"   ✅ Created Privacy Manifest at {manifest_path}")
            
            elif violation.rule_id in ["ICON_ERROR", "ASSET_MISSING"]:
                # Generate missing icons/assets
                try:
                    asset_validator = AssetValidator()
                    generated = asset_validator.generate_missing_assets(project_path, result.platform)
                    if generated.get('icons') or generated.get('splashes'):
                        fixed_count += 1
                        print(f"   ✅ Generated missing assets")
                except Exception as e:
                    print(f"   ⚠️ Could not generate assets: {e}")
    
    except ImportError:
        print("   ⚠️ Auto-fix requires image processing libraries")
    
    return fixed_count

def create_privacy_manifest():
    """Create basic Privacy Manifest content."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
        <dict>
            <key>NSPrivacyAccessedAPIType</key>
            <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
            <key>NSPrivacyAccessedAPITypeReasons</key>
            <array>
                <string>CA92.1</string>
            </array>
        </dict>
    </array>
    <key>NSPrivacyCollectedDataTypes</key>
    <array>
        <!-- Add your data collection types here -->
    </array>
    <key>NSPrivacyTrackingDomains</key>
    <array>
        <!-- Add tracking domains here if applicable -->
    </array>
</dict>
</plist>'''

if __name__ == "__main__":
    sys.exit(main())
