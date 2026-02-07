"""Comprehensive asset validation for mobile apps."""
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from .image_validator import IconValidator, ValidationResult

@dataclass
class AssetReport:
    """Complete asset validation report."""
    icon_results: Dict[str, ValidationResult]
    splash_results: Dict[str, ValidationResult]
    screenshot_results: Dict[str, ValidationResult]
    missing_assets: List[str]
    recommendations: List[str]
    
    @property
    def is_valid(self) -> bool:
        """Check if all assets are valid."""
        all_results = []
        all_results.extend(self.icon_results.values())
        all_results.extend(self.splash_results.values())
        all_results.extend(self.screenshot_results.values())
        return all(r.is_valid for r in all_results) and not self.missing_assets

class AssetValidator:
    """Validates all mobile app assets."""
    
    # Required asset specifications
    ASSET_SPECS = {
        'ios': {
            'icon': {'sizes': [(1024, 1024)], 'formats': ['PNG']},
            'splash': {'sizes': [(1242, 2688), (828, 1792)], 'formats': ['PNG']},
            'screenshots': {
                'iphone': {'sizes': [(1290, 2796), (1179, 2556)], 'count': (3, 10)},
                'ipad': {'sizes': [(2048, 2732), (1668, 2388)], 'count': (3, 10)}
            }
        },
        'android': {
            'icon': {'sizes': [(512, 512)], 'formats': ['PNG', 'JPEG']},
            'feature_graphic': {'sizes': [(1024, 500)], 'formats': ['PNG', 'JPEG']},
            'screenshots': {
                'phone': {'sizes': [(1080, 1920), (1440, 2560)], 'count': (2, 8)},
                'tablet': {'sizes': [(1200, 1920), (1600, 2560)], 'count': (1, 8)}
            }
        }
    }
    
    def __init__(self):
        self.icon_validator = IconValidator()
    
    def validate_all_assets(self, project_path: Path, platform: str = 'both') -> AssetReport:
        """Validate all assets for a mobile app project."""
        icon_results = {}
        splash_results = {}
        screenshot_results = {}
        missing_assets = []
        recommendations = []
        
        # Validate icons
        icon_paths = self._find_icons(project_path)
        for icon_type, icon_path in icon_paths.items():
            if icon_path:
                result = self.icon_validator.validate_icon(icon_path, platform)
                icon_results[icon_type] = result
            else:
                missing_assets.append(f"Missing {icon_type} icon")
        
        # Validate splash screens
        if platform in ('ios', 'both'):
            splash_paths = self._find_splash_screens(project_path, 'ios')
            for splash_type, splash_path in splash_paths.items():
                if splash_path:
                    result = self._validate_splash_screen(splash_path, 'ios')
                    splash_results[f"ios_{splash_type}"] = result
        
        if platform in ('android', 'both'):
            splash_paths = self._find_splash_screens(project_path, 'android')
            for splash_type, splash_path in splash_paths.items():
                if splash_path:
                    result = self._validate_splash_screen(splash_path, 'android')
                    splash_results[f"android_{splash_type}"] = result
        
        # Generate recommendations
        recommendations.extend(self._generate_recommendations(icon_results, platform))
        
        return AssetReport(
            icon_results=icon_results,
            splash_results=splash_results,
            screenshot_results=screenshot_results,
            missing_assets=missing_assets,
            recommendations=recommendations
        )
    
    def _find_icons(self, project_path: Path) -> Dict[str, Optional[Path]]:
        """Find icon files in project."""
        icons = {'main': None, 'adaptive': None, 'notification': None}
        
        # Common icon locations
        icon_locations = [
            project_path / "assets" / "icon.png",
            project_path / "assets" / "images" / "icon.png",
            project_path / "android" / "app" / "src" / "main" / "res" / "mipmap-xxxhdpi" / "ic_launcher.png",
            project_path / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset",
            project_path / "web" / "favicon.png"
        ]
        
        for location in icon_locations:
            if location.exists():
                if location.is_file():
                    icons['main'] = location
                    break
                elif location.is_dir():
                    # Look for largest icon in iconset
                    icon_files = list(location.glob("*.png"))
                    if icon_files:
                        # Sort by file size, take largest
                        largest = max(icon_files, key=lambda f: f.stat().st_size)
                        icons['main'] = largest
                        break
        
        return icons
    
    def _find_splash_screens(self, project_path: Path, platform: str) -> Dict[str, Optional[Path]]:
        """Find splash screen files."""
        splashes = {}
        
        if platform == 'ios':
            splash_locations = [
                project_path / "assets" / "splash.png",
                project_path / "ios" / "Runner" / "Assets.xcassets" / "LaunchImage.launchimage"
            ]
        else:  # android
            splash_locations = [
                project_path / "assets" / "splash.png",
                project_path / "android" / "app" / "src" / "main" / "res" / "drawable" / "launch_background.xml"
            ]
        
        for i, location in enumerate(splash_locations):
            if location.exists():
                splashes[f"splash_{i}"] = location
        
        return splashes
    
    def _validate_splash_screen(self, splash_path: Path, platform: str) -> ValidationResult:
        """Validate splash screen image."""
        return self.icon_validator.validate_image(splash_path)
    
    def _generate_recommendations(self, icon_results: Dict[str, ValidationResult], platform: str) -> List[str]:
        """Generate asset optimization recommendations."""
        recommendations = []
        
        for icon_type, result in icon_results.items():
            if not result.is_valid:
                recommendations.append(f"Fix {icon_type} icon issues: {', '.join(result.errors)}")
            
            if result.warnings:
                recommendations.append(f"Consider {icon_type} icon improvements: {', '.join(result.warnings)}")
        
        # Platform-specific recommendations
        if platform in ('ios', 'both'):
            recommendations.append("Ensure all iOS icon sizes are provided for optimal display")
            recommendations.append("Use PNG format for all iOS assets")
        
        if platform in ('android', 'both'):
            recommendations.append("Provide adaptive icons for Android 8.0+")
            recommendations.append("Include feature graphic for Play Store listing")
        
        return recommendations
    
    def generate_missing_assets(self, project_path: Path, platform: str = 'both') -> Dict[str, List[Path]]:
        """Generate missing asset files from existing icons."""
        generated = {'icons': [], 'splashes': []}
        
        # Find main icon
        icons = self._find_icons(project_path)
        main_icon = icons.get('main')
        
        if not main_icon:
            raise ValueError("No main icon found to generate assets from")
        
        # Generate icon sets
        output_dir = project_path / "generated_assets"
        icon_sets = self.icon_validator.generate_icon_set(main_icon, output_dir, platform)
        generated['icons'] = icon_sets.get('ios', []) + icon_sets.get('android', [])
        
        # Generate splash screens (simple colored background with icon)
        splash_dir = output_dir / "splash"
        splash_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            from PIL import Image, ImageDraw
            
            # Create simple splash screens
            splash_sizes = [(1242, 2688), (828, 1792)] if platform in ('ios', 'both') else []
            if platform in ('android', 'both'):
                splash_sizes.extend([(1080, 1920), (1440, 2560)])
            
            with Image.open(main_icon) as icon_img:
                for width, height in splash_sizes:
                    # Create background
                    splash = Image.new('RGB', (width, height), color='white')
                    
                    # Resize and center icon
                    icon_size = min(width, height) // 4
                    resized_icon = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                    
                    # Paste icon in center
                    x = (width - icon_size) // 2
                    y = (height - icon_size) // 2
                    
                    if resized_icon.mode == 'RGBA':
                        splash.paste(resized_icon, (x, y), resized_icon)
                    else:
                        splash.paste(resized_icon, (x, y))
                    
                    # Save splash
                    splash_path = splash_dir / f"splash_{width}x{height}.png"
                    splash.save(splash_path, 'PNG')
                    generated['splashes'].append(splash_path)
        
        except Exception as e:
            print(f"Warning: Could not generate splash screens: {e}")
        
        return generated
