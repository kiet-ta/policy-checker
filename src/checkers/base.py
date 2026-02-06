"""Base checker class with comprehensive policy validation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum
import json

class Severity(Enum):
    CRITICAL = "critical"  # Will cause rejection
    MAJOR = "major"        # Likely rejection
    MINOR = "minor"        # Warning only
    INFO = "info"          # Informational

@dataclass
class PolicyViolation:
    """Represents a single policy violation."""
    rule_id: str
    title: str
    message: str
    severity: Severity
    category: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id, "title": self.title, "message": self.message,
            "severity": self.severity.value, "category": self.category,
            "file": self.file, "line": self.line, "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable, "documentation_url": self.documentation_url
        }

@dataclass
class CheckResult:
    """Aggregated results from policy checks."""
    project_type: str
    project_path: str
    platform: str
    violations: List[PolicyViolation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def passed(self) -> bool:
        return not any(v.severity in [Severity.CRITICAL, Severity.MAJOR] for v in self.violations)
    
    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.CRITICAL)
    
    @property
    def major_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.MAJOR)
    
    @property
    def minor_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.MINOR)
    
    def add_violation(self, violation: PolicyViolation):
        self.violations.append(violation)
    
    def output(self, format: str = "text") -> str:
        if format == "json":
            return self._output_json()
        elif format == "markdown":
            return self._output_markdown()
        return self._output_text()
    
    def _output_text(self) -> str:
        lines = [
            f"\n{'='*70}",
            f"📱 MOBILE APP POLICY CHECK RESULTS",
            f"{'='*70}",
            f"Project: {self.project_path}",
            f"Type: {self.project_type.upper()} | Platform: {self.platform.upper()}",
            f"{'='*70}"
        ]
        
        if not self.violations:
            lines.append("\n✅ All policy checks passed! Ready for submission.\n")
            print("\n".join(lines))
            return "\n".join(lines)
        
        # Group by severity
        for severity in [Severity.CRITICAL, Severity.MAJOR, Severity.MINOR, Severity.INFO]:
            violations = [v for v in self.violations if v.severity == severity]
            if violations:
                icon = {"critical": "🚫", "major": "❌", "minor": "⚠️", "info": "ℹ️"}[severity.value]
                lines.append(f"\n{icon} {severity.value.upper()} ({len(violations)})")
                lines.append("-" * 40)
                for v in violations:
                    lines.append(f"\n[{v.rule_id}] {v.title}")
                    lines.append(f"   {v.message}")
                    if v.file:
                        lines.append(f"   📁 {v.file}" + (f":{v.line}" if v.line else ""))
                    if v.suggestion:
                        lines.append(f"   💡 {v.suggestion}")
                    if v.auto_fixable:
                        lines.append(f"   🔧 Auto-fixable: Run with --fix")
        
        lines.extend([
            f"\n{'='*70}",
            f"Summary: {self.critical_count} critical, {self.major_count} major, {self.minor_count} minor",
            f"Status: {'🚫 WILL BE REJECTED' if self.critical_count > 0 else '❌ LIKELY REJECTED' if self.major_count > 0 else '✅ SHOULD PASS'}",
            f"{'='*70}\n"
        ])
        
        output = "\n".join(lines)
        print(output)
        return output
    
    def _output_json(self) -> str:
        result = json.dumps({
            "passed": self.passed,
            "project_type": self.project_type,
            "platform": self.platform,
            "summary": {"critical": self.critical_count, "major": self.major_count, "minor": self.minor_count},
            "violations": [v.to_dict() for v in self.violations],
            "metadata": self.metadata
        }, indent=2)
        print(result)
        return result
    
    def _output_markdown(self) -> str:
        lines = [
            "# 📱 Policy Check Report\n",
            f"| Property | Value |",
            f"|----------|-------|",
            f"| Project | `{self.project_path}` |",
            f"| Type | {self.project_type} |",
            f"| Platform | {self.platform} |",
            f"| Status | {'✅ Pass' if self.passed else '❌ Fail'} |",
            ""
        ]
        
        if self.violations:
            lines.append("## Violations\n")
            for v in self.violations:
                icon = {"critical": "🚫", "major": "❌", "minor": "⚠️", "info": "ℹ️"}[v.severity.value]
                lines.append(f"### {icon} [{v.rule_id}] {v.title}\n")
                lines.append(f"- **Severity:** {v.severity.value}")
                lines.append(f"- **Message:** {v.message}")
                if v.suggestion:
                    lines.append(f"- **Fix:** {v.suggestion}")
                lines.append("")
        
        output = "\n".join(lines)
        print(output)
        return output

class BaseChecker(ABC):
    """Abstract base class for platform-specific checkers."""
    
    @abstractmethod
    def check(self, path: Path, platform: str = "both", verbose: bool = False) -> CheckResult:
        pass
    
    @abstractmethod
    def get_project_type(self) -> str:
        pass
    
    def _file_exists(self, path: Path, filename: str) -> bool:
        return (path / filename).exists()
    
    def _read_json(self, path: Path) -> Optional[Dict]:
        try:
            with open(path) as f:
                return json.load(f)
        except:
            return None
    
    def _read_file(self, path: Path) -> Optional[str]:
        try:
            return path.read_text()
        except:
            return None
