#!/usr/bin/env python3
"""
Validate AI-generated rules against schema and run dry-run tests.
"""
import argparse
import sys
import yaml
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.rules.schema import validate_ai_rule, PolicyRule, RuleConfig
from src.rules.rule_engine import RuleEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DUMMY_PROJECT_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "dummy_project"

def load_rules(file_path: str = None, stdin: bool = False) -> List[Dict[str, Any]]:
    """Load rules from file or stdin."""
    content = ""
    if stdin:
        content = sys.stdin.read()
    elif file_path:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        raise ValueError("Must provide either --rules-file or --stdin")

    # Try parsing as YAML (superset of JSON)
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse input: {e}")
        sys.exit(1)

    # Handle different input structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "rules" in data:
        return data["rules"]
    else:
        logger.error("Input must be a list of rules or a dict with 'rules' key")
        sys.exit(1)

def validate_schema(rules_data: List[Dict[str, Any]]) -> List[PolicyRule]:
    """Validate rules against Pydantic schema."""
    valid_rules = []
    has_errors = False

    logger.info(f"🔍 Validating schema for {len(rules_data)} rules...")

    for i, rule_data in enumerate(rules_data):
        try:
            # Use specific validator for AI rules
            rule = validate_ai_rule(rule_data)
            valid_rules.append(rule)
            logger.info(f"  ✅ Rule {rule.id} matches schema")
        except Exception as e:
            logger.error(f"  ❌ Rule #{i+1} failed validation: {e}")
            has_errors = True
    
    if has_errors:
        logger.error("Schema validation failed.")
        sys.exit(1)
    
    return valid_rules

def run_dry_run(rules: List[PolicyRule]):
    """Run rules against dummy project to ensure they don't crash."""
    logger.info("🧪 Starting Dry-Run Test...")
    
    if not DUMMY_PROJECT_PATH.exists():
        logger.error(f"Dummy project not found at {DUMMY_PROJECT_PATH}")
        sys.exit(1)

    # Create temporary rules file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        config = RuleConfig(rules=rules)
        # Convert models to dicts for YAML dumping
        rules_dict = {
            "version": config.version,
            "rules": [json.loads(r.model_dump_json()) for r in rules]
        }
        yaml.dump(rules_dict, tmp)
        tmp_path = Path(tmp.name)

    try:
        # Initialize engine with temp rules
        engine = RuleEngine(rules_path=tmp_path)
        
        # simple check to see if it loaded
        if not engine.config or len(engine.config.rules) != len(rules):
            logger.error("Failed to load rules into engine during dry-run")
            sys.exit(1)

        # Run check against dummy project
        # We don't care if it passes or fails, just that it doesn't crash
        violations = engine.check_all(DUMMY_PROJECT_PATH)
        
        logger.info(f"  ✅ Engine executed successfully (found {len(violations)} violations)")
        
    except Exception as e:
        logger.error(f"  ❌ Dry-run CRASHED: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if tmp_path.exists():
            tmp_path.unlink()

def main():
    parser = argparse.ArgumentParser(description="Validate AI-generated rules")
    parser.add_argument("--rules-file", help="Path to YAML/JSON file containing rules")
    parser.add_argument("--stdin", action="store_true", help="Read rules from stdin")
    
    args = parser.parse_args()
    
    try:
        raw_rules = load_rules(args.rules_file, args.stdin)
        valid_rules = validate_schema(raw_rules)
        run_dry_run(valid_rules)
        
        logger.info("✨ All validations passed!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
