# 🖼️ Image Processing & Validation

The Policy Checker includes a robust image processing engine powered by **Pillow (PIL)**. This module handles validation and generation of app assets, ensuring compliance with strict App Store and Google Play requirements.

## 1. Architecture

The image processing logic is contained in `src/validators/`:

- `ImageValidator` (`image_validator.py`): Base class acting as a facade for Pillow. Handles generic image analysis (format, size, mode, hash).
- `IconValidator`: Inherits from `ImageValidator`. Enforces platform-specific rules for app icons.
- `AssetValidator`: (Conceptual) Handles splash screens and other assets.

## 2. Validation Logic

### 2.1 Generic Checks
Applied to all images:
- **Existence**: File must exist.
- **Format**: Must be PNG, JPEG, or WEBP.
- **File Size**: 
  - Max 10MB (Error if exceeded).
  - Warning if > 5MB.
- **Quality**:
  - **DPI**: Warning if < 72 DPI.
  - **Aspect Ratio**: Warning if not exactly square (1.0).

### 2.2 iOS App Store Rules (Icon)
- **Size**: Must be exactly **1024x1024** pixels.
- **Format**: Must be **PNG**.
- **Transparency**: **Not Allowed**. Alpha channel triggers a warning (Apple removes it automatically, but best practice is to provide opaque).
- **Color Mode**: RGB or RGBA preferred.

### 2.3 Google Play Rules (Icon)
- **Size**: Must be **512x512** pixels.
- **Format**: PNG or JPEG.
- **Max Size**: 1024KB (1MB) recommended.

## 3. Asset Generation

The tool can auto-generate a complete set of required icons from a single high-quality source image (preferably 1024x1024).

### 3.1 Resampling Algorithm
We use `Image.Resampling.LANCZOS` for high-quality downscaling. This preserves sharpness and details better than `BICUBIC` for icon-sized assets.

### 3.2 Generated Sizes

| Platform | Context | Size (px) |
|----------|---------|-----------|
| **iOS** | App Store | 1024x1024 |
| | iPhone Home | 180x180, 120x120 |
| | iPad Pro | 167x167 |
| | Settings | 87x87, 58x58, 29x29 |
| | Notification | 40x40, 20x20 |
| **Android** | Play Store | 512x512 |
| | xxxhdpi | 192x192 |
| | xxhdpi | 144x144 |
| | xhdpi | 96x96 |
| | hdpi | 72x72 |
| | mdpi | 48x48 |
| | ldpi | 36x36 |

## 4. Usage in CLI

### Validation
```bash
# JSON output gives full analysis details including DPI and color mode
policy-checker validate-icon ./assets/icon.png --output json
```

### Generation
```bash
# Generate for both platforms
policy-checker generate-icons ./master-icon.png --output ./assets/generated
```

## 5. Implementation Details

```python
# Hashing for duplicate detection
def _calculate_hash(self, image_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

The system calculates MD5 hashes of images to efficiently detect duplicates or unchanged assets during incremental builds (planned feature).
