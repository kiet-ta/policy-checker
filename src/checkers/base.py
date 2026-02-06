"""Base checker class for policy validation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from enum import Enum

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class PolicyViolation:
    rule_id: str
    message: str
    severity: Severity
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class CheckResult:
    violations: List[PolicyViolation] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        return not any(v.severity == Severity.ERROR for v in self.violations)
    
    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)
    
    def output(self, format: str = "text"):
        if format == "text":
            self._output_text()
        elif format == "json":
            self._output_json()
    
    def _output_text(self):
        print(f"\n{'='*60}")
        print(f"📱 POLICY CHECK RESULTS")
        print(f"{'='*60}")
        
        if not self.violations:
            print("✅ All checks passed!")
            return
        
        for v in self.violations:
            icon = "❌" if v.severity == Severity.ERROR else "⚠️" if v.severity == Severity.WARNING else "ℹ️"
            print(f"\n{icon} [{v.rule_id}] {v.message}")
            if v.file:
                print(f"   📁 File: {v.file}" + (f":{v.line}" if v.line else ""))
            if v.suggestion:
                print(f"   💡 Suggestion: {v.suggestion}")
        
        print(f"\n{'='*60}")
        print(f"Summary: {self.error_count} errors, {self.warning_count} warnings")
        print(f"Status: {'❌ FAILED' if not self.passed else '✅ PASSED'}")
    
    def _output_json(self):
        import json
        print(json.dumps({
            "passed": self.passed,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "violations": [{"rule_id": v.rule_id, "message": v.message, "severity": v.severity.value} for v in self.violations]
        }, indent=2))

class BaseChecker(ABC):
    @abstractmethod
    def check(self, path: Path, platform: str = "both", verbose: bool = False) -> CheckResult:
        pass
