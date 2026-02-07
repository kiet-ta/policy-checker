"""Dynamic Rule Engine - Interpreter Pattern Implementation.

This module implements the core rule engine that loads rules from YAML
and evaluates them against project files using the Interpreter pattern.
"""
from __future__ import annotations
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

import yaml

from .schema import (
    Rule, RuleConfig, Condition, Severity, Platform,
    FileExistsCondition, FileNotExistsCondition,
    JsonPathExistsCondition, JsonPathEqualsCondition, JsonPathMatchesCondition,
    YamlPathExistsCondition, XmlXpathExistsCondition,
    RegexInFileCondition, CompositeCondition
)

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from jsonpath_ng import parse as jsonpath_parse
    HAS_JSONPATH = True
except ImportError:
    jsonpath_parse = None
    HAS_JSONPATH = False


class ConditionEvaluator(ABC):
    """Abstract base class for condition evaluation (Interpreter pattern)."""
    
    @abstractmethod
    def evaluate(self, project_path: Path) -> bool:
        """Evaluate the condition against the project.
        
        Args:
            project_path: Root path of the project to check
            
        Returns:
            True if condition is satisfied, False otherwise
        """
        pass


class FileExistsEvaluator(ConditionEvaluator):
    """Evaluator for file_exists condition."""
    
    def __init__(self, condition: FileExistsCondition):
        self.target = condition.target
    
    def evaluate(self, project_path: Path) -> bool:
        return (project_path / self.target).exists()


class FileNotExistsEvaluator(ConditionEvaluator):
    """Evaluator for file_not_exists condition."""
    
    def __init__(self, condition: FileNotExistsCondition):
        self.target = condition.target
    
    def evaluate(self, project_path: Path) -> bool:
        return not (project_path / self.target).exists()


class JsonPathExistsEvaluator(ConditionEvaluator):
    """Evaluator for json_path_exists condition."""
    
    def __init__(self, condition: JsonPathExistsCondition):
        self.target = condition.target
        self.path = condition.path
    
    def evaluate(self, project_path: Path) -> bool:
        file_path = project_path / self.target
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            
            return self._path_exists(data, self.path)
        except Exception as e:
            logger.debug(f"Error reading JSON {file_path}: {e}")
            return False
    
    def _path_exists(self, data: Any, path: str) -> bool:
        """Check if JSONPath exists in data."""
        if HAS_JSONPATH:
            try:
                expr = jsonpath_parse(path)
                matches = expr.find(data)
                return len(matches) > 0 and matches[0].value is not None
            except Exception:
                pass
        
        # Fallback: simple dot-notation path
        return self._simple_path_exists(data, path)
    
    def _simple_path_exists(self, data: Any, path: str) -> bool:
        """Fallback for when jsonpath_ng is not available."""
        # Convert $.expo.ios.bundleIdentifier to keys
        keys = path.replace("$.", "").replace("$", "").split(".")
        keys = [k for k in keys if k]  # Remove empty strings
        
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        return current is not None


class JsonPathEqualsEvaluator(ConditionEvaluator):
    """Evaluator for json_path_equals condition."""
    
    def __init__(self, condition: JsonPathEqualsCondition):
        self.target = condition.target
        self.path = condition.path
        self.value = condition.value
    
    def evaluate(self, project_path: Path) -> bool:
        file_path = project_path / self.target
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            
            actual_value = self._get_value(data, self.path)
            return actual_value == self.value
        except Exception as e:
            logger.debug(f"Error reading JSON {file_path}: {e}")
            return False
    
    def _get_value(self, data: Any, path: str) -> Any:
        """Get value at JSONPath."""
        if HAS_JSONPATH:
            try:
                expr = jsonpath_parse(path)
                matches = expr.find(data)
                if matches:
                    return matches[0].value
            except Exception:
                pass
        
        # Fallback: simple dot-notation
        keys = path.replace("$.", "").replace("$", "").split(".")
        keys = [k for k in keys if k]
        
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


class JsonPathMatchesEvaluator(ConditionEvaluator):
    """Evaluator for json_path_matches condition."""
    
    def __init__(self, condition: JsonPathMatchesCondition):
        self.target = condition.target
        self.path = condition.path
        self.pattern = condition.pattern
    
    def evaluate(self, project_path: Path) -> bool:
        file_path = project_path / self.target
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            
            value = self._get_value(data, self.path)
            if value is None:
                return False
            
            return bool(re.search(self.pattern, str(value)))
        except Exception as e:
            logger.debug(f"Error reading JSON {file_path}: {e}")
            return False
    
    def _get_value(self, data: Any, path: str) -> Any:
        """Get value at JSONPath using simple dot notation."""
        keys = path.replace("$.", "").replace("$", "").split(".")
        keys = [k for k in keys if k]
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


class YamlPathExistsEvaluator(ConditionEvaluator):
    """Evaluator for yaml_path_exists condition."""
    
    def __init__(self, condition: YamlPathExistsCondition):
        self.target = condition.target
        self.path = condition.path
    
    def evaluate(self, project_path: Path) -> bool:
        file_path = project_path / self.target
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # Use simple dot-notation path
            keys = self.path.replace("$.", "").replace("$", "").split(".")
            keys = [k for k in keys if k]
            
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False
            return current is not None
        except Exception as e:
            logger.debug(f"Error reading YAML {file_path}: {e}")
            return False


class XmlXpathExistsEvaluator(ConditionEvaluator):
    """Evaluator for xml_xpath_exists condition."""
    
    def __init__(self, condition: XmlXpathExistsCondition):
        self.target = condition.target
        self.xpath = condition.xpath
    
    def evaluate(self, project_path: Path) -> bool:
        file_path = project_path / self.target
        if not file_path.exists():
            return False
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle namespaces in plist files
            matches = root.findall(self.xpath)
            return len(matches) > 0
        except Exception as e:
            logger.debug(f"Error reading XML {file_path}: {e}")
            return False


class RegexInFileEvaluator(ConditionEvaluator):
    """Evaluator for regex_in_file condition."""
    
    def __init__(self, condition: RegexInFileCondition):
        self.target = condition.target
        self.pattern = condition.pattern
    
    def evaluate(self, project_path: Path) -> bool:
        file_path = project_path / self.target
        if not file_path.exists():
            return False
        
        try:
            content = file_path.read_text(encoding="utf-8")
            return bool(re.search(self.pattern, content))
        except Exception as e:
            logger.debug(f"Error reading file {file_path}: {e}")
            return False


class CompositeEvaluator(ConditionEvaluator):
    """Evaluator for composite conditions (all_of, any_of, none_of)."""
    
    def __init__(self, condition: CompositeCondition):
        self.logic_type = condition.type
        self.evaluators = [create_evaluator(c) for c in condition.checks]
    
    def evaluate(self, project_path: Path) -> bool:
        results = [e.evaluate(project_path) for e in self.evaluators]
        
        if self.logic_type == "all_of":
            return all(results)
        elif self.logic_type == "any_of":
            return any(results)
        elif self.logic_type == "none_of":
            return not any(results)
        
        return False


def create_evaluator(condition: Condition) -> ConditionEvaluator:
    """Factory function to create the appropriate evaluator for a condition.
    
    Args:
        condition: The condition to create an evaluator for
        
    Returns:
        An evaluator instance for the condition type
        
    Raises:
        ValueError: If condition type is unknown
    """
    evaluator_map = {
        "file_exists": (FileExistsCondition, FileExistsEvaluator),
        "file_not_exists": (FileNotExistsCondition, FileNotExistsEvaluator),
        "json_path_exists": (JsonPathExistsCondition, JsonPathExistsEvaluator),
        "json_path_equals": (JsonPathEqualsCondition, JsonPathEqualsEvaluator),
        "json_path_matches": (JsonPathMatchesCondition, JsonPathMatchesEvaluator),
        "yaml_path_exists": (YamlPathExistsCondition, YamlPathExistsEvaluator),
        "xml_xpath_exists": (XmlXpathExistsCondition, XmlXpathExistsEvaluator),
        "regex_in_file": (RegexInFileCondition, RegexInFileEvaluator),
    }
    
    # Handle dict-based conditions (from YAML parsing)
    if isinstance(condition, dict):
        cond_type = condition.get("type")
        if cond_type in ("all_of", "any_of", "none_of"):
            return CompositeEvaluator(CompositeCondition(**condition))
        if cond_type in evaluator_map:
            model_cls, evaluator_cls = evaluator_map[cond_type]
            return evaluator_cls(model_cls(**condition))
        raise ValueError(f"Unknown condition type: {cond_type}")
    
    # Handle Pydantic model conditions
    if isinstance(condition, CompositeCondition):
        return CompositeEvaluator(condition)
    
    for cond_type, (model_cls, evaluator_cls) in evaluator_map.items():
        if isinstance(condition, model_cls):
            return evaluator_cls(condition)
    
    raise ValueError(f"Unknown condition type: {type(condition)}")


class RuleEngine:
    """Main engine for loading and executing dynamic policy rules.
    
    The RuleEngine loads rules from a YAML configuration file and provides
    methods to evaluate those rules against a project directory.
    
    Attributes:
        rules_path: Path to the rules YAML file
        config: The loaded RuleConfig, or None if loading failed
    """
    
    def __init__(self, rules_path: Optional[Path] = None):
        """Initialize the RuleEngine.
        
        Args:
            rules_path: Optional path to rules YAML. Defaults to rules.yaml
                        in the same directory as this module.
        """
        if rules_path is None:
            rules_path = Path(__file__).parent / "rules.yaml"
        
        self.rules_path = rules_path
        self.config: Optional[RuleConfig] = None
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load rules from YAML configuration."""
        if not self.rules_path.exists():
            logger.warning(f"Rules file not found: {self.rules_path}")
            self.config = RuleConfig(rules=[])
            return
        
        try:
            with open(self.rules_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self.config = RuleConfig(**data)
            logger.info(f"Loaded {len(self.config.rules)} rules from {self.rules_path}")
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            self.config = RuleConfig(rules=[])
    
    def reload_rules(self) -> None:
        """Reload rules from the YAML file."""
        self._load_rules()
    
    def get_rules_for_platform(self, platform: str) -> List[Rule]:
        """Get all rules applicable to a specific platform.
        
        Args:
            platform: Target platform ('ios', 'android', or 'both')
            
        Returns:
            List of rules that apply to the platform
        """
        if not self.config:
            return []
        
        return [
            r for r in self.config.rules
            if r.platform.value in (platform, "both") or platform == "both"
        ]
    
    def evaluate_rule(self, rule: Rule, project_path: Path) -> bool:
        """Evaluate if a single rule passes (all conditions met).
        
        Args:
            rule: The rule to evaluate
            project_path: Root path of the project
            
        Returns:
            True if all conditions are satisfied, False otherwise
        """
        for condition in rule.conditions:
            try:
                evaluator = create_evaluator(condition)
                if not evaluator.evaluate(project_path):
                    return False
            except Exception as e:
                logger.error(f"Error evaluating condition in rule {rule.id}: {e}")
                return False
        
        return True
    
    def check_all(self, project_path: Path, platform: str = "both") -> List[Rule]:
        """Check all applicable rules and return violated ones.
        
        Args:
            project_path: Root path of the project to check
            platform: Target platform to check ('ios', 'android', or 'both')
            
        Returns:
            List of rules that were violated (conditions not met)
        """
        violations = []
        project_path = Path(project_path)
        
        for rule in self.get_rules_for_platform(platform):
            if not self.evaluate_rule(rule, project_path):
                violations.append(rule)
                logger.debug(f"Rule violated: {rule.id} - {rule.title}")
        
        return violations
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by its ID.
        
        Args:
            rule_id: The unique rule identifier
            
        Returns:
            The rule if found, None otherwise
        """
        if not self.config:
            return None
        
        for rule in self.config.rules:
            if rule.id == rule_id:
                return rule
        return None
