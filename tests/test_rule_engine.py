"""Tests for the dynamic rule engine."""
import pytest
import tempfile
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestRuleEngineLoading:
    """Tests for RuleEngine initialization and loading."""
    
    def test_rule_engine_loads_yaml(self):
        """Test RuleEngine loads YAML configuration."""
        from rules.rule_engine import RuleEngine
        
        engine = RuleEngine()
        assert engine.config is not None
        assert len(engine.config.rules) > 0
    
    def test_rule_engine_handles_missing_file(self):
        """Test RuleEngine handles missing rules file gracefully."""
        from rules.rule_engine import RuleEngine
        
        engine = RuleEngine(rules_path=Path("/nonexistent/rules.yaml"))
        assert engine.config is not None
        assert len(engine.config.rules) == 0
    
    def test_get_rules_for_platform(self):
        """Test filtering rules by platform."""
        from rules.rule_engine import RuleEngine
        
        engine = RuleEngine()
        
        ios_rules = engine.get_rules_for_platform("ios")
        android_rules = engine.get_rules_for_platform("android")
        
        # iOS rules should include ios and both platform rules
        for rule in ios_rules:
            assert rule.platform.value in ("ios", "both")
        
        # Android rules should include android and both platform rules
        for rule in android_rules:
            assert rule.platform.value in ("android", "both")


class TestFileExistsCondition:
    """Tests for file_exists condition evaluator."""
    
    def test_file_exists_positive(self):
        """Test file_exists returns True when file exists."""
        from rules.rule_engine import FileExistsEvaluator
        from rules.schema import FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            (Path(tmpdir) / "test.txt").touch()
            
            cond = FileExistsCondition(target="test.txt")
            evaluator = FileExistsEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is True
    
    def test_file_exists_negative(self):
        """Test file_exists returns False when file missing."""
        from rules.rule_engine import FileExistsEvaluator
        from rules.schema import FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cond = FileExistsCondition(target="missing.txt")
            evaluator = FileExistsEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is False


class TestJsonPathCondition:
    """Tests for JSON path condition evaluators."""
    
    def test_json_path_exists_positive(self):
        """Test json_path_exists returns True when path exists."""
        from rules.rule_engine import JsonPathExistsEvaluator
        from rules.schema import JsonPathExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create app.json with nested structure
            app_json = {
                "expo": {
                    "name": "TestApp",
                    "ios": {
                        "bundleIdentifier": "com.test.app"
                    }
                }
            }
            with open(Path(tmpdir) / "app.json", "w") as f:
                json.dump(app_json, f)
            
            cond = JsonPathExistsCondition(
                target="app.json",
                path="$.expo.ios.bundleIdentifier"
            )
            evaluator = JsonPathExistsEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is True
    
    def test_json_path_exists_negative(self):
        """Test json_path_exists returns False when path missing."""
        from rules.rule_engine import JsonPathExistsEvaluator
        from rules.schema import JsonPathExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            app_json = {"expo": {"name": "TestApp"}}
            with open(Path(tmpdir) / "app.json", "w") as f:
                json.dump(app_json, f)
            
            cond = JsonPathExistsCondition(
                target="app.json",
                path="$.expo.android.package"
            )
            evaluator = JsonPathExistsEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is False
    
    def test_json_path_missing_file(self):
        """Test json_path_exists returns False when file missing."""
        from rules.rule_engine import JsonPathExistsEvaluator
        from rules.schema import JsonPathExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cond = JsonPathExistsCondition(
                target="app.json",
                path="$.expo.name"
            )
            evaluator = JsonPathExistsEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is False


class TestCompositeCondition:
    """Tests for composite condition evaluators (any_of, all_of, none_of)."""
    
    def test_any_of_one_passes(self):
        """Test any_of returns True when at least one condition passes."""
        from rules.rule_engine import CompositeEvaluator
        from rules.schema import CompositeCondition, FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only one of two possible files
            (Path(tmpdir) / "file_a.txt").touch()
            
            cond = CompositeCondition(
                type="any_of",
                checks=[
                    FileExistsCondition(target="file_a.txt"),
                    FileExistsCondition(target="file_b.txt")
                ]
            )
            evaluator = CompositeEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is True
    
    def test_any_of_none_passes(self):
        """Test any_of returns False when no conditions pass."""
        from rules.rule_engine import CompositeEvaluator
        from rules.schema import CompositeCondition, FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cond = CompositeCondition(
                type="any_of",
                checks=[
                    FileExistsCondition(target="file_a.txt"),
                    FileExistsCondition(target="file_b.txt")
                ]
            )
            evaluator = CompositeEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is False
    
    def test_all_of_all_pass(self):
        """Test all_of returns True when all conditions pass."""
        from rules.rule_engine import CompositeEvaluator
        from rules.schema import CompositeCondition, FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file_a.txt").touch()
            (Path(tmpdir) / "file_b.txt").touch()
            
            cond = CompositeCondition(
                type="all_of",
                checks=[
                    FileExistsCondition(target="file_a.txt"),
                    FileExistsCondition(target="file_b.txt")
                ]
            )
            evaluator = CompositeEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is True
    
    def test_all_of_one_fails(self):
        """Test all_of returns False when one condition fails."""
        from rules.rule_engine import CompositeEvaluator
        from rules.schema import CompositeCondition, FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file_a.txt").touch()
            
            cond = CompositeCondition(
                type="all_of",
                checks=[
                    FileExistsCondition(target="file_a.txt"),
                    FileExistsCondition(target="file_b.txt")
                ]
            )
            evaluator = CompositeEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is False
    
    def test_none_of_all_fail(self):
        """Test none_of returns True when all conditions fail."""
        from rules.rule_engine import CompositeEvaluator
        from rules.schema import CompositeCondition, FileExistsCondition
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cond = CompositeCondition(
                type="none_of",
                checks=[
                    FileExistsCondition(target="file_a.txt"),
                    FileExistsCondition(target="file_b.txt")
                ]
            )
            evaluator = CompositeEvaluator(cond)
            
            assert evaluator.evaluate(Path(tmpdir)) is True


class TestRuleEngineIntegration:
    """Integration tests for full rule evaluation."""
    
    def test_check_all_with_violations(self):
        """Test check_all returns violated rules for incomplete project."""
        from rules.rule_engine import RuleEngine
        
        engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal app.json missing required fields
            app_json = {"expo": {"name": "TestApp"}}
            with open(Path(tmpdir) / "app.json", "w") as f:
                json.dump(app_json, f)
            
            violations = engine.check_all(Path(tmpdir), "ios")
            
            # Should have violations for missing fields
            assert len(violations) > 0
            
            # Check that version rule is violated
            violation_ids = [v.id for v in violations]
            assert "COMMON_VERSION_001" in violation_ids
    
    def test_check_all_with_complete_project(self):
        """Test check_all returns fewer violations for complete project."""
        from rules.rule_engine import RuleEngine
        
        engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create complete app.json
            app_json = {
                "expo": {
                    "name": "TestApp",
                    "version": "1.0.0",
                    "icon": "./assets/icon.png",
                    "ios": {
                        "bundleIdentifier": "com.test.app",
                        "infoPlist": {
                            "NSPrivacyAccessedAPITypes": []
                        }
                    },
                    "android": {
                        "package": "com.test.app"
                    },
                    "privacyPolicy": "https://example.com/privacy"
                }
            }
            with open(Path(tmpdir) / "app.json", "w") as f:
                json.dump(app_json, f)
            
            violations = engine.check_all(Path(tmpdir), "both")
            
            # Should have fewer violations than empty project
            violation_ids = [v.id for v in violations]
            
            # These should NOT be violated
            assert "COMMON_NAME_001" not in violation_ids
            assert "COMMON_VERSION_001" not in violation_ids
            assert "IOS_BUNDLE_001" not in violation_ids


class TestSchemaValidation:
    """Tests for Pydantic schema validation."""
    
    def test_rule_validation(self):
        """Test Rule model validates correctly."""
        from rules.schema import Rule, Severity, Platform, FileExistsCondition
        
        rule = Rule(
            id="TEST_001",
            platform=Platform.IOS,
            title="Test Rule",
            description="A test rule",
            severity=Severity.MAJOR,
            category="test",
            conditions=[FileExistsCondition(target="test.txt")]
        )
        
        assert rule.id == "TEST_001"
        assert rule.platform == Platform.IOS
        assert rule.severity == Severity.MAJOR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
