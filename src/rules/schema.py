"""Pydantic models for dynamic rule configuration."""
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Severity levels for rule violations."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class Platform(str, Enum):
    """Target platform for rule evaluation."""
    IOS = "ios"
    ANDROID = "android"
    BOTH = "both"


# --- Condition Types ---

class FileExistsCondition(BaseModel):
    """Check if a file exists in the project."""
    type: Literal["file_exists"] = "file_exists"
    target: str = Field(..., description="Relative path to the file")


class FileNotExistsCondition(BaseModel):
    """Check if a file does NOT exist in the project."""
    type: Literal["file_not_exists"] = "file_not_exists"
    target: str


class JsonPathExistsCondition(BaseModel):
    """Check if a JSONPath exists in a JSON file."""
    type: Literal["json_path_exists"] = "json_path_exists"
    target: str = Field(..., description="Relative path to the JSON file")
    path: str = Field(..., description="JSONPath expression (e.g., $.expo.ios.bundleIdentifier)")


class JsonPathEqualsCondition(BaseModel):
    """Check if a JSONPath equals a specific value."""
    type: Literal["json_path_equals"] = "json_path_equals"
    target: str
    path: str
    value: Union[str, int, bool, list, None]


class JsonPathMatchesCondition(BaseModel):
    """Check if a JSONPath value matches a regex pattern."""
    type: Literal["json_path_matches"] = "json_path_matches"
    target: str
    path: str
    pattern: str


class YamlPathExistsCondition(BaseModel):
    """Check if a path exists in a YAML file."""
    type: Literal["yaml_path_exists"] = "yaml_path_exists"
    target: str
    path: str


class XmlXpathExistsCondition(BaseModel):
    """Check if an XPath exists in an XML file."""
    type: Literal["xml_xpath_exists"] = "xml_xpath_exists"
    target: str
    xpath: str


class RegexInFileCondition(BaseModel):
    """Check if a regex pattern exists in a file."""
    type: Literal["regex_in_file"] = "regex_in_file"
    target: str
    pattern: str


class CompositeCondition(BaseModel):
    """
    Composite condition that combines multiple conditions.
    - all_of: All conditions must pass
    - any_of: At least one condition must pass
    - none_of: No conditions should pass
    """
    type: Literal["all_of", "any_of", "none_of"]
    checks: List["Condition"]


# Union of all condition types
Condition = Union[
    FileExistsCondition,
    FileNotExistsCondition,
    JsonPathExistsCondition,
    JsonPathEqualsCondition,
    JsonPathMatchesCondition,
    YamlPathExistsCondition,
    XmlXpathExistsCondition,
    RegexInFileCondition,
    CompositeCondition,
]

# Required for forward reference resolution in CompositeCondition
CompositeCondition.model_rebuild()


class Rule(BaseModel):
    """A single policy rule definition."""
    id: str = Field(..., description="Unique rule identifier (e.g., IOS_PRIV_001)")
    platform: Platform = Platform.BOTH
    title: str = Field(..., description="Human-readable rule title")
    description: str = Field(..., description="Detailed description of the policy requirement")
    severity: Severity = Severity.MAJOR
    category: str = Field(..., description="Category: privacy, identity, assets, permissions, etc.")
    source_url: Optional[str] = Field(None, description="Link to official documentation")
    auto_fixable: bool = False
    conditions: List[Condition] = Field(..., description="Conditions that must be met to pass")
    suggestion: Optional[str] = Field(None, description="How to fix the violation")


class RuleMetadata(BaseModel):
    """Metadata for AI-generated rules to ensure traceability."""
    source_url: str = Field(..., description="Link to official documentation")
    quote: str = Field(..., description="Exact quote from the policy")
    ai_reasoning: str = Field(..., description="Explanation of why this rule was generated")


class PolicyRule(Rule):
    """Stricter Rule definition for AI output validation."""
    metadata: RuleMetadata = Field(..., description="Traceability metadata")

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("ID must be uppercase")
        if not v.replace("_", "").isalnum():
            raise ValueError("ID must only contain letters, numbers, and underscores")
        return v


def validate_ai_rule(rule_data: dict) -> PolicyRule:
    """Validate raw dictionary from AI against PolicyRule schema."""
    return PolicyRule(**rule_data)


class RuleConfig(BaseModel):
    """Root configuration containing all rules."""
    version: str = "1.0"
    last_updated: str = ""
    rules: List[Rule] = Field(default_factory=list)
