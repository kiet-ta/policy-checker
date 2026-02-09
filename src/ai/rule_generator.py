"""AI-powered rule generator using LLM APIs.

This module provides functionality to convert policy text from Apple/Google
into machine-checkable rule YAML using LLM APIs (OpenAI or Anthropic).
"""
from __future__ import annotations
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "rule_generator.md"


def load_system_prompt() -> str:
    """Load the system prompt for rule generation.
    
    Returns:
        The system prompt content
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    raise FileNotFoundError(f"System prompt not found: {SYSTEM_PROMPT_PATH}")


def generate_rule_from_policy(
    policy_text: str,
    source: str = "apple",
    change_type: str = "added",
    model: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """Use LLM to convert policy text to rule YAML.
    
    Args:
        policy_text: The policy requirement text to convert
        source: Policy source, 'apple' or 'google'
        change_type: Type of change: 'added', 'modified', or 'deprecated'
        model: LLM model to use (defaults to gpt-4 for OpenAI, claude-sonnet for Anthropic)
    
    Returns:
        List of parsed rule dicts, or None on failure
        
    Raises:
        ValueError: If no LLM API key is found in environment
    """
    # Check for API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        raise ValueError(
            "No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        )
    
    try:
        system_prompt = load_system_prompt()
    except FileNotFoundError as e:
        logger.error(f"Failed to load system prompt: {e}")
        return None
    
    user_prompt = f"""Policy Source: {source.upper()}
Change Type: {change_type}
Policy Text:
---
{policy_text}
---

Convert this to a rule YAML."""
    
    # Use OpenAI if available, otherwise Anthropic
    if openai_key:
        return _call_openai(system_prompt, user_prompt, model or "gpt-4")
    else:
        return _call_anthropic(system_prompt, user_prompt, model)


def _call_openai(
    system_prompt: str, 
    user_prompt: str, 
    model: str
) -> Optional[List[Dict[str, Any]]]:
    """Call OpenAI API to generate rule YAML.
    
    Args:
        system_prompt: The system prompt
        user_prompt: The user prompt with policy text
        model: OpenAI model to use
        
    Returns:
        Parsed rule list or None on failure
    """
    try:
        from openai import OpenAI
        
        client = OpenAI()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent output
            max_tokens=2000
        )
        
        yaml_content = response.choices[0].message.content
        # Strip any markdown code fences if present
        yaml_content = yaml_content.strip()
        if yaml_content.startswith("```"):
            yaml_content = yaml_content.split("\n", 1)[1]
        if yaml_content.endswith("```"):
            yaml_content = yaml_content.rsplit("```", 1)[0]
        
        result = yaml.safe_load(yaml_content)
        
        # Ensure result is a list
        if isinstance(result, dict):
            return [result]
        return result
        
    except ImportError:
        logger.error("openai package not installed. Run: pip install openai")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _call_anthropic(
    system_prompt: str, 
    user_prompt: str,
    model: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """Call Anthropic API to generate rule YAML.
    
    Args:
        system_prompt: The system prompt
        user_prompt: The user prompt with policy text
        model: Anthropic model to use (optional)
        
    Returns:
        Parsed rule list or None on failure
    """
    try:
        import anthropic
        
        client = anthropic.Anthropic()
        
        response = client.messages.create(
            model=model or "claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        yaml_content = response.content[0].text
        # Strip any markdown code fences if present
        yaml_content = yaml_content.strip()
        if yaml_content.startswith("```"):
            yaml_content = yaml_content.split("\n", 1)[1]
        if yaml_content.endswith("```"):
            yaml_content = yaml_content.rsplit("```", 1)[0]
        
        result = yaml.safe_load(yaml_content)
        
        # Ensure result is a list
        if isinstance(result, dict):
            return [result]
        return result
        
    except ImportError:
        logger.error("anthropic package not installed. Run: pip install anthropic")
        return None
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return None


def update_rules_file(
    new_rules: List[Dict[str, Any]], 
    rules_path: Path,
    backup: bool = True
) -> None:
    """Merge new rules into existing rules file.
    
    This function handles:
    - Creating the file if it doesn't exist
    - Updating existing rules (matched by ID)
    - Appending new rules
    - Optionally creating a backup
    
    Args:
        new_rules: List of new rule dicts to add/update
        rules_path: Path to the rules.yaml file
        backup: Whether to create a backup before modifying
    """
    existing: Dict[str, Any] = {
        "version": "1.0",
        "last_updated": "",
        "rules": []
    }
    
    if rules_path.exists():
        # Create backup if requested
        if backup:
            backup_path = rules_path.with_suffix(f".yaml.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            backup_path.write_text(rules_path.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info(f"Created backup: {backup_path}")
        
        with open(rules_path, encoding="utf-8") as f:
            existing = yaml.safe_load(f) or existing
    
    existing_ids = {r["id"] for r in existing.get("rules", [])}
    
    for rule in new_rules:
        rule_id = rule.get("id")
        if not rule_id:
            logger.warning(f"Skipping rule without ID: {rule}")
            continue
        
        if rule_id in existing_ids:
            # Update existing rule
            existing["rules"] = [
                rule if r["id"] == rule_id else r
                for r in existing["rules"]
            ]
            logger.info(f"Updated existing rule: {rule_id}")
        else:
            # Add new rule
            existing["rules"].append(rule)
            logger.info(f"Added new rule: {rule_id}")
    
    # Update timestamp
    existing["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    # Write back to file
    with open(rules_path, "w", encoding="utf-8") as f:
        yaml.dump(existing, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Saved {len(existing['rules'])} rules to {rules_path}")


def validate_rule(rule: Dict[str, Any]) -> List[str]:
    """Validate a rule dict against the schema.
    
    Args:
        rule: Rule dict to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required = ["id", "title", "description", "conditions"]
    for field in required:
        if field not in rule:
            errors.append(f"Missing required field: {field}")
    
    # ID format
    if "id" in rule:
        rule_id = rule["id"]
        if not isinstance(rule_id, str) or "_" not in rule_id:
            errors.append(f"Invalid ID format: {rule_id}. Expected: PLATFORM_CATEGORY_XXX")
    
    # Severity values
    if "severity" in rule:
        valid_severities = ("critical", "major", "minor", "info")
        if rule["severity"] not in valid_severities:
            errors.append(f"Invalid severity: {rule['severity']}. Must be one of {valid_severities}")
    
    # Platform values
    if "platform" in rule:
        valid_platforms = ("ios", "android", "both")
        if rule["platform"] not in valid_platforms:
            errors.append(f"Invalid platform: {rule['platform']}. Must be one of {valid_platforms}")
    
    # Conditions must be a list
    if "conditions" in rule and not isinstance(rule["conditions"], list):
        errors.append("conditions must be a list")
    
    return errors
