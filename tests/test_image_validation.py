"""Tests for image validation functionality."""
import pytest
from pathlib import Path
import tempfile
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def create_test_icon(width, height, format='PNG', mode='RGB'):
    """Create a test icon with specified dimensions."""
    img = Image.new(mode, (width, height), color='red')
    return img

def test_icon_validator_valid_ios_icon():
    """Test IconValidator with valid iOS icon."""
    from validators import IconValidator
    
    validator = IconValidator()
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create valid iOS icon
        img = create_test_icon(1024, 1024)
        img.save(tmp.name, 'PNG')
        
        result = validator.validate_icon(tmp.name, 'ios')
        
        # Should pass validation
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.image_info.width == 1024
        assert result.image_info.height == 1024

def test_icon_validator_invalid_size():
    """Test IconValidator with invalid icon size."""
    from validators import IconValidator
    
    validator = IconValidator()
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create invalid size icon
        img = create_test_icon(512, 512)
        img.save(tmp.name, 'PNG')
        
        result = validator.validate_icon(tmp.name, 'ios')
        
        # Should fail validation
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any('size' in error.lower() for error in result.errors)

def test_icon_generator():
    """Test icon set generation."""
    from validators import IconValidator
    
    validator = IconValidator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source icon
        source_path = Path(tmpdir) / "source.png"
        img = create_test_icon(1024, 1024)
        img.save(source_path, 'PNG')
        
        # Generate icon sets
        output_dir = Path(tmpdir) / "output"
        generated = validator.generate_icon_set(source_path, output_dir, 'both')
        
        # Check generated icons
        assert len(generated['ios']) > 0
        assert len(generated['android']) > 0
        
        # Verify some generated files exist
        for icon_path in generated['ios'][:3]:  # Check first 3
            assert icon_path.exists()
            
        for icon_path in generated['android'][:3]:  # Check first 3
            assert icon_path.exists()

def test_asset_validator():
    """Test AssetValidator functionality."""
    from validators import AssetValidator
    
    validator = AssetValidator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        
        # Create basic project structure
        assets_dir = project_path / "assets"
        assets_dir.mkdir()
        
        # Create test icon
        icon_path = assets_dir / "icon.png"
        img = create_test_icon(1024, 1024)
        img.save(icon_path, 'PNG')
        
        # Validate assets
        report = validator.validate_all_assets(project_path, 'both')
        
        # Should find the icon
        assert len(report.icon_results) > 0
        assert 'main' in report.icon_results
