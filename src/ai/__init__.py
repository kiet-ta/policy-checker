"""AI Module for policy-to-rule conversion.

This module provides LLM-powered functionality to convert policy text
from Apple and Google into machine-checkable rule configurations.
"""
from .rule_generator import (
    generate_rule_from_policy,
    update_rules_file,
    validate_rule,
    load_system_prompt
)

__all__ = [
    "generate_rule_from_policy",
    "update_rules_file",
    "validate_rule",
    "load_system_prompt"
]
