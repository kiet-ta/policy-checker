#!/usr/bin/env python3
"""Script to update rules using AI from policy changes.

This script is designed to be run by GitHub Actions or manually.
It crawls Apple/Google policies, detects changes, and uses AI to
generate updated rule configurations.

Usage:
    python scripts/ai_update_rules.py [--force] [--dry-run]

Options:
    --force     Process all policies, not just changes
    --dry-run   Print generated rules without saving
"""
from __future__ import annotations
import argparse
import sys
import logging
from pathlib import Path

# Add src to path for imports
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

from scrapers import ApplePolicyScraper, GooglePolicyScraper  # noqa: E402
from ai.rule_generator import generate_rule_from_policy, update_rules_file, validate_rule  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RULES_PATH = SRC_PATH / "rules" / "rules.yaml"


def process_policy_updates(force: bool = False, dry_run: bool = False) -> int:
    """
    Process policy updates and generate rules.
    
    Args:
        force: If True, process all policies regardless of change detection.
        dry_run: If True, print rules without saving.
        
    Returns:
        int: Number of rules generated/updated.
    """
    logger.info("🔍 Fetching policies from Apple and Google...")
    
    # Initialize scrapers
    apple_scraper = ApplePolicyScraper()
    google_scraper = GooglePolicyScraper()
    
    # Fetch current policies
    apple_policies = apple_scraper.fetch_policies()
    google_policies = google_scraper.fetch_policies()
    
    logger.info(f"📱 Apple policies fetched: {len(apple_policies)}")
    logger.info(f"🤖 Google policies fetched: {len(google_policies)}")
    
    # Detect changes
    if not force:
        apple_updates = apple_scraper.detect_changes(apple_policies)
        google_updates = google_scraper.detect_changes(google_policies)
        logger.info(f"📝 Apple updates detected: {len(apple_updates)}")
        logger.info(f"📝 Google updates detected: {len(google_updates)}")
    else:
        # Force mode: treat all as updates
        from scrapers.base_scraper import PolicyUpdate
        from datetime import datetime
        
        apple_updates = [
            PolicyUpdate(
                rule_id=p.id, 
                change_type="added", 
                old_version=None, 
                new_version=p.version, 
                changelog="Force update", 
                date=datetime.now()
            )
            for p in apple_policies if p.checkable
        ]
        google_updates = [
            PolicyUpdate(
                rule_id=p.id, 
                change_type="added", 
                old_version=None, 
                new_version=p.version, 
                changelog="Force update", 
                date=datetime.now()
            )
            for p in google_policies if p.checkable
        ]
        logger.info(f"⚡ Force mode: processing {len(apple_updates)} Apple, {len(google_updates)} Google")
    
    new_rules = []
    
    # Process Apple updates
    for update in apple_updates:
        if update.change_type in ("added", "modified"):
            policy = next((p for p in apple_policies if p.id == update.rule_id), None)
            if policy and policy.checkable:
                logger.info(f"🍎 Processing Apple policy: {policy.title}")
                try:
                    rules = generate_rule_from_policy(
                        policy_text=f"{policy.title}\n\n{policy.description}",
                        source="apple",
                        change_type=update.change_type
                    )
                    if rules:
                        # Validate each rule
                        for rule in rules:
                            errors = validate_rule(rule)
                            if errors:
                                logger.warning(f"⚠️ Validation errors for rule: {errors}")
                            else:
                                new_rules.append(rule)
                                logger.info(f"✅ Generated rule: {rule.get('id', 'unknown')}")
                except Exception as e:
                    logger.exception(f"❌ Failed to generate rule for {policy.id}: {e}")
    
    # Process Google updates
    for update in google_updates:
        if update.change_type in ("added", "modified"):
            policy = next((p for p in google_policies if p.id == update.rule_id), None)
            if policy and policy.checkable:
                logger.info(f"🤖 Processing Google policy: {policy.title}")
                try:
                    rules = generate_rule_from_policy(
                        policy_text=f"{policy.title}\n\n{policy.description}",
                        source="google",
                        change_type=update.change_type
                    )
                    if rules:
                        for rule in rules:
                            errors = validate_rule(rule)
                            if errors:
                                logger.warning(f"⚠️ Validation errors for rule: {errors}")
                            else:
                                new_rules.append(rule)
                                logger.info(f"✅ Generated rule: {rule.get('id', 'unknown')}")
                except Exception as e:
                    logger.exception(f"❌ Failed to generate rule for {policy.id}: {e}")
    
    # Save or print rules
    if new_rules:
        if dry_run:
            import yaml
            logger.info("\n📋 Generated rules (dry-run):")
            print(yaml.dump(new_rules, default_flow_style=False, sort_keys=False))
        else:
            logger.info(f"\n💾 Updating rules file with {len(new_rules)} new/modified rules")
            update_rules_file(new_rules, RULES_PATH)
            logger.info("✅ Rules file updated successfully")
    else:
        logger.info("📭 No new rules to add")
    
    # Save updated cache (skip in dry-run)
    if not dry_run:
        apple_scraper.save_cache(apple_policies)
        google_scraper.save_cache(google_policies)
        logger.info("💾 Policy cache updated")
    
    return len(new_rules)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update policy rules using AI from crawled policy changes."
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Process all policies, not just detected changes"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print generated rules without saving"
    )
    
    args = parser.parse_args()
    
    try:
        count = process_policy_updates(force=args.force, dry_run=args.dry_run)
        logger.info(f"\n🎉 Done! Processed {count} rules.")
        return 0
    except ValueError as e:
        logger.error(f"❌ {e}")
        return 1
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
