"""Report models and output formatting."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class Evidence:
    path: str
    line: int
    excerpt: str


@dataclass(frozen=True)
class Finding:
    kind: str
    category: str
    title: str
    detail: str
    recommendation: str = ""
    evidence: List[Evidence] = field(default_factory=list)


@dataclass(frozen=True)
class CategoryScore:
    name: str
    score: int
    maximum: int
    summary: str


@dataclass
class AnalysisReport:
    repository: str
    score: int
    files_scanned: int
    category_scores: List[CategoryScore]
    strengths: List[Finding]
    risks: List[Finding]
    gaps: List[Finding]
    languages: Dict[str, int]
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def render_text(self) -> str:
        lines = [
            "Distributed Systems Architectural Readiness Report",
            f"Repository: {self.repository}",
            f"Readiness score: {self.score}/100",
            f"Files scanned: {self.files_scanned}",
        ]
        if self.languages:
            rendered = ", ".join(
                f"{language} ({count})"
                for language, count in sorted(
                    self.languages.items(), key=lambda item: (-item[1], item[0])
                )
            )
            lines.append(f"Detected file types: {rendered}")
        lines.extend(["", "Score breakdown"])
        for category in self.category_scores:
            lines.append(
                f"- {category.name}: {category.score}/{category.maximum} - "
                f"{category.summary}"
            )
        self._append_findings(lines, "Strengths", self.strengths)
        self._append_findings(lines, "Risks", self.risks)
        self._append_findings(lines, "Missing or unverified capabilities", self.gaps)
        lines.extend(["", "Static-analysis limitations"])
        lines.extend(f"- {item}" for item in self.limitations)
        return "\n".join(lines)

    @staticmethod
    def _append_findings(
        lines: List[str], heading: str, findings: List[Finding]
    ) -> None:
        lines.extend(["", heading])
        if not findings:
            lines.append("- None detected.")
            return
        for finding in findings:
            lines.append(f"- [{finding.category}] {finding.title}: {finding.detail}")
            for evidence in finding.evidence[:3]:
                lines.append(
                    f"  Evidence: {evidence.path}:{evidence.line}: {evidence.excerpt}"
                )
            if finding.recommendation:
                lines.append(f"  Recommendation: {finding.recommendation}")

