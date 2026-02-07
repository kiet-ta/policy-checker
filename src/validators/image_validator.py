"""Image processing and validation for mobile app assets."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from PIL import Image, ImageStat
import hashlib

@dataclass
class ImageInfo:
    """Information about an image file."""
    path: Path
    width: int
    height: int
    format: str
    mode: str
    size_bytes: int
    has_transparency: bool
    is_animated: bool
    dpi: Tuple[int, int]
    color_count: Optional[int] = None
    file_hash: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of image validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    image_info: Optional[ImageInfo] = None

class ImageValidator:
    """Base class for image validation."""
    
    SUPPORTED_FORMATS = {'PNG', 'JPEG', 'JPG', 'WEBP'}
    MAX_FILE_SIZE_MB = 10
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []
    
    def validate_image(self, image_path: Union[str, Path]) -> ValidationResult:
        """Validate an image file."""
        self.errors.clear()
        self.warnings.clear()
        self.suggestions.clear()
        
        image_path = Path(image_path)
        
        if not image_path.exists():
            self.errors.append(f"Image file not found: {image_path}")
            return ValidationResult(False, self.errors, self.warnings, self.suggestions)
        
        try:
            image_info = self._analyze_image(image_path)
            self._validate_format(image_info)
            self._validate_size(image_info)
            self._validate_quality(image_info)
            
            return ValidationResult(
                is_valid=len(self.errors) == 0,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
                suggestions=self.suggestions.copy(),
                image_info=image_info
            )
        except Exception as e:
            self.errors.append(f"Failed to analyze image: {str(e)}")
            return ValidationResult(False, self.errors, self.warnings, self.suggestions)
    
    def _analyze_image(self, image_path: Path) -> ImageInfo:
        """Analyze image properties."""
        with Image.open(image_path) as img:
            # Get basic info
            width, height = img.size
            format_name = img.format or 'UNKNOWN'
            mode = img.mode
            
            # Check transparency
            has_transparency = (
                mode in ('RGBA', 'LA') or 
                'transparency' in img.info or
                (mode == 'P' and 'transparency' in img.info)
            )
            
            # Check if animated
            is_animated = getattr(img, 'is_animated', False)
            
            # Get DPI
            dpi = img.info.get('dpi', (72, 72))
            if isinstance(dpi, (int, float)):
                dpi = (int(dpi), int(dpi))
            
            # Count colors for palette images
            color_count = None
            if mode == 'P':
                color_count = len(img.getcolors() or [])
            
            # File size
            size_bytes = image_path.stat().st_size
            
            # File hash for duplicate detection
            file_hash = self._calculate_hash(image_path)
            
            return ImageInfo(
                path=image_path,
                width=width,
                height=height,
                format=format_name,
                mode=mode,
                size_bytes=size_bytes,
                has_transparency=has_transparency,
                is_animated=is_animated,
                dpi=dpi,
                color_count=color_count,
                file_hash=file_hash
            )
    
    def _calculate_hash(self, image_path: Path) -> str:
        """Calculate MD5 hash of image file."""
        hash_md5 = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _validate_format(self, image_info: ImageInfo):
        """Validate image format."""
        if image_info.format not in self.SUPPORTED_FORMATS:
            self.errors.append(f"Unsupported format: {image_info.format}. Use PNG, JPEG, or WebP")
        
        # PNG recommendations
        if image_info.format == 'PNG':
            if not image_info.has_transparency and image_info.mode == 'RGBA':
                self.suggestions.append("Consider using RGB mode for PNG without transparency")
        
        # JPEG recommendations
        if image_info.format in ('JPEG', 'JPG'):
            if image_info.has_transparency:
                self.warnings.append("JPEG doesn't support transparency. Use PNG instead")
    
    def _validate_size(self, image_info: ImageInfo):
        """Validate file size."""
        size_mb = image_info.size_bytes / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            self.errors.append(f"File too large: {size_mb:.1f}MB (max {self.MAX_FILE_SIZE_MB}MB)")
        elif size_mb > 5:
            self.warnings.append(f"Large file size: {size_mb:.1f}MB. Consider optimization")
    
    def _validate_quality(self, image_info: ImageInfo):
        """Validate image quality."""
        # Check DPI
        min_dpi = min(image_info.dpi)
        if min_dpi < 72:
            self.warnings.append(f"Low DPI: {min_dpi}. Recommended: 72+ DPI")
        
        # Check aspect ratio
        aspect_ratio = image_info.width / image_info.height
        if abs(aspect_ratio - 1.0) > 0.01:  # Not square
            self.warnings.append(f"Non-square aspect ratio: {aspect_ratio:.2f}")

class IconValidator(ImageValidator):
    """Specialized validator for app icons."""
    
    # Platform-specific requirements
    IOS_REQUIREMENTS = {
        'sizes': [(1024, 1024)],  # App Store requirement
        'formats': ['PNG'],
        'max_size_mb': 2,
        'requires_transparency': False,
        'min_dpi': 72
    }
    
    ANDROID_REQUIREMENTS = {
        'sizes': [(512, 512)],  # Play Store requirement
        'formats': ['PNG', 'JPEG'],
        'max_size_mb': 2,
        'requires_transparency': False,
        'min_dpi': 72
    }
    
    # Additional icon sizes for different contexts
    IOS_ICON_SIZES = [
        (1024, 1024),  # App Store
        (180, 180),    # iPhone 6 Plus, 6s Plus, 7 Plus, 8 Plus
        (167, 167),    # iPad Pro
        (152, 152),    # iPad, iPad mini
        (120, 120),    # iPhone, iPod Touch
        (87, 87),      # iPhone 6 Plus, 6s Plus, 7 Plus, 8 Plus (Settings)
        (80, 80),      # iPad, iPad mini (Settings)
        (76, 76),      # iPad
        (60, 60),      # iPhone (Settings)
        (58, 58),      # iPhone, iPod Touch (Settings)
        (40, 40),      # iPad, iPad mini (Settings)
        (29, 29),      # iPhone, iPad (Settings)
        (20, 20),      # iPad, iPhone (Notifications)
    ]
    
    ANDROID_ICON_SIZES = [
        (512, 512),    # Play Store
        (192, 192),    # xxxhdpi
        (144, 144),    # xxhdpi
        (96, 96),      # xhdpi
        (72, 72),      # hdpi
        (48, 48),      # mdpi
        (36, 36),      # ldpi
    ]
    
    def validate_icon(self, icon_path: Union[str, Path], platform: str = 'both') -> ValidationResult:
        """Validate app icon for specific platform."""
        result = self.validate_image(icon_path)
        
        if not result.is_valid or not result.image_info:
            return result
        
        image_info = result.image_info
        
        # Platform-specific validation
        if platform in ('ios', 'both'):
            self._validate_ios_icon(image_info)
        
        if platform in ('android', 'both'):
            self._validate_android_icon(image_info)
        
        # General icon validation
        self._validate_icon_quality(image_info)
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
            suggestions=self.suggestions.copy(),
            image_info=image_info
        )
    
    def _validate_ios_icon(self, image_info: ImageInfo):
        """Validate iOS-specific icon requirements."""
        req = self.IOS_REQUIREMENTS
        
        # Size validation
        size = (image_info.width, image_info.height)
        if size not in req['sizes']:
            self.errors.append(f"iOS icon size {size} not in required sizes: {req['sizes']}")
            self.suggestions.append(f"Resize to {req['sizes'][0]} for iOS App Store")
        
        # Format validation
        if image_info.format not in req['formats']:
            self.errors.append(f"iOS requires PNG format, got {image_info.format}")
        
        # File size
        size_mb = image_info.size_bytes / (1024 * 1024)
        if size_mb > req['max_size_mb']:
            self.errors.append(f"iOS icon too large: {size_mb:.1f}MB (max {req['max_size_mb']}MB)")
        
        # Transparency check
        if image_info.has_transparency:
            self.warnings.append("iOS app icons should not have transparency")
        
        # Additional iOS-specific checks
        if image_info.mode not in ('RGB', 'RGBA'):
            self.warnings.append(f"iOS prefers RGB/RGBA color mode, got {image_info.mode}")
    
    def _validate_android_icon(self, image_info: ImageInfo):
        """Validate Android-specific icon requirements."""
        req = self.ANDROID_REQUIREMENTS
        
        # Size validation
        size = (image_info.width, image_info.height)
        if size not in req['sizes']:
            self.errors.append(f"Android icon size {size} not in required sizes: {req['sizes']}")
            self.suggestions.append(f"Resize to {req['sizes'][0]} for Google Play Store")
        
        # Format validation
        if image_info.format not in req['formats']:
            self.errors.append(f"Android supports {req['formats']}, got {image_info.format}")
        
        # File size
        size_mb = image_info.size_bytes / (1024 * 1024)
        if size_mb > req['max_size_mb']:
            self.errors.append(f"Android icon too large: {size_mb:.1f}MB (max {req['max_size_mb']}MB)")
    
    def _validate_icon_quality(self, image_info: ImageInfo):
        """Validate general icon quality."""
        # Square aspect ratio (critical for icons)
        if image_info.width != image_info.height:
            self.errors.append(f"Icon must be square, got {image_info.width}x{image_info.height}")
        
        # Minimum size check
        min_size = 48
        if image_info.width < min_size or image_info.height < min_size:
            self.errors.append(f"Icon too small: {image_info.width}x{image_info.height} (min {min_size}x{min_size})")
        
        # Power of 2 recommendation
        if not self._is_power_of_2(image_info.width):
            self.suggestions.append("Consider using power-of-2 dimensions for better performance")
        
        # Color mode recommendations
        if image_info.mode == 'P':
            self.suggestions.append("Consider using RGB mode instead of palette mode")
        elif image_info.mode == 'L':
            self.warnings.append("Grayscale icons may not be suitable for all contexts")
    
    def _is_power_of_2(self, n: int) -> bool:
        """Check if number is power of 2."""
        return n > 0 and (n & (n - 1)) == 0
    
    def generate_icon_set(self, source_path: Union[str, Path], output_dir: Union[str, Path], 
                         platform: str = 'both') -> Dict[str, List[Path]]:
        """Generate complete icon set from source image."""
        source_path = Path(source_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated = {'ios': [], 'android': []}
        
        try:
            with Image.open(source_path) as source_img:
                # Ensure RGB mode
                if source_img.mode != 'RGB':
                    source_img = source_img.convert('RGB')
                
                # Generate iOS icons
                if platform in ('ios', 'both'):
                    for width, height in self.IOS_ICON_SIZES:
                        resized = source_img.resize((width, height), Image.Resampling.LANCZOS)
                        output_path = output_dir / f"ios_icon_{width}x{height}.png"
                        resized.save(output_path, 'PNG', optimize=True)
                        generated['ios'].append(output_path)
                
                # Generate Android icons
                if platform in ('android', 'both'):
                    for width, height in self.ANDROID_ICON_SIZES:
                        resized = source_img.resize((width, height), Image.Resampling.LANCZOS)
                        output_path = output_dir / f"android_icon_{width}x{height}.png"
                        resized.save(output_path, 'PNG', optimize=True)
                        generated['android'].append(output_path)
        
        except Exception as e:
            raise ValueError(f"Failed to generate icon set: {str(e)}")
        
        return generated
