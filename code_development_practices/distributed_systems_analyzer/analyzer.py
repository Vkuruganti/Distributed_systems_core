"""Evidence-based static analyzer for distributed systems readiness."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .models import AnalysisReport, CategoryScore, Evidence, Finding


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
MAX_FILE_SIZE = 1_000_000
TEXT_FILENAMES = {
    "dockerfile",
    "makefile",
    "procfile",
    "requirements.txt",
    "terraform.lock.hcl",
}
TEXT_EXTENSIONS = {
    ".c",
    ".conf",
    ".cpp",
    ".cs",
    ".dockerfile",
    ".env",
    ".go",
    ".gradle",
    ".h",
    ".hcl",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".kt",
    ".md",
    ".php",
    ".properties",
    ".proto",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".sql",
    ".tf",
    ".toml",
    ".ts",
    ".tsx",
    ".xml",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Category:
    name: str
    maximum: int
    rationale: str
    missing_recommendation: str


@dataclass(frozen=True)
class Signal:
    name: str
    category: str
    points: int
    pattern: str
    detail: str


@dataclass(frozen=True)
class Risk:
    name: str
    category: str
    penalty: int
    pattern: str
    detail: str
    recommendation: str


CATEGORIES: Sequence[Category] = (
    Category(
        "Reliability and partial failures",
        20,
        "Fault tolerance, bounded waits, health signaling, and repeatable operations.",
        "Define timeouts, retry policy with backoff, idempotency boundaries, and health checks. Add tests for dependency failure and recovery.",
    ),
    Category(
        "Scalability and partitioning",
        15,
        "Horizontal growth, workload distribution, caching, and partition-aware design.",
        "Document expected load and hot spots. Show how stateless workers, routing, caching, or partitioning allow horizontal scaling.",
    ),
    Category(
        "Replication and availability",
        15,
        "Replica topology, failover, leader behavior, and availability controls.",
        "Document stateful dependencies and their replication, failover, and recovery behavior. Add deploy configuration where appropriate.",
    ),
    Category(
        "Consistency and correctness",
        15,
        "Transactions, concurrency control, deduplication, and integrity constraints.",
        "State consistency guarantees and failure semantics. Add transactions, version checks, deduplication, or an outbox where the workflow needs them.",
    ),
    Category(
        "Dataflow and evolution",
        10,
        "Versioned interfaces, schema evolution, asynchronous flows, and derived data.",
        "Describe API and schema compatibility. Add migrations or versioned contracts, and define delivery semantics for asynchronous flows.",
    ),
    Category(
        "Operability and observability",
        15,
        "Metrics, logs, traces, configuration, deployment, and run-time diagnostics.",
        "Add structured logs, metrics, tracing, externalized configuration, deploy descriptors, and operational runbooks.",
    ),
    Category(
        "Verification and maintainability",
        10,
        "Tests, fault injection, documentation, and automation that keep change manageable.",
        "Add automated tests, including integration and failure-mode coverage, plus architecture documentation and repeatable automation.",
    ),
)

SIGNALS: Sequence[Signal] = (
    Signal("timeouts", "Reliability and partial failures", 4, r"\b(timeout|deadline|connect_timeout|read_timeout)\b", "Bounded waits are represented in source or configuration."),
    Signal("retries", "Reliability and partial failures", 3, r"\b(retr(?:y|ies)|backoff|tenacity|retrytemplate)\b", "Retry behavior is represented."),
    Signal("idempotency", "Reliability and partial failures", 4, r"\b(idempoten|deduplicat|request[_-]?id)\w*", "Repeatable request handling or deduplication is represented."),
    Signal("health checks", "Reliability and partial failures", 3, r"\b(healthz|readiness|liveness|healthcheck|health[_ /-]?check)\b", "Health signaling is represented."),
    Signal("resilience controls", "Reliability and partial failures", 6, r"\b(circuit[_ -]?breaker|bulkhead|rate[_ -]?limit|graceful[_ -]?shutdown)\w*", "Resilience controls are represented."),
    Signal("horizontal execution", "Scalability and partitioning", 4, r"\b(horizontalpodautoscaler|autoscal|replicas?:|worker[s]?:|stateless|load[_ -]?balanc)\w*", "Horizontal execution or scaling configuration is represented."),
    Signal("partitioning", "Scalability and partitioning", 5, r"\b(partition|shard|consistent[_ -]?hash|hash[_ -]?ring|hot[_ -]?spot)\w*", "Partition-aware design is represented."),
    Signal("caching", "Scalability and partitioning", 3, r"\b(cache|redis|memcached|cdn)\b", "Caching is represented."),
    Signal("queueing", "Scalability and partitioning", 3, r"\b(kafka|rabbitmq|sqs|pubsub|message[_ -]?queue|consumer[_ -]?group)\w*", "Asynchronous workload distribution is represented."),
    Signal("replication", "Replication and availability", 5, r"\b(replica|replication|replicaset|read[_ -]?replica)\w*", "Replication is represented."),
    Signal("failover", "Replication and availability", 4, r"\b(failover|leader[_ -]?election|primary|follower|quorum|consensus)\w*", "Failover or node-role behavior is represented."),
    Signal("availability deployment", "Replication and availability", 3, r"\b(poddisruptionbudget|availability[_ -]?zone|multi[_ -]?az|anti[_ -]?affinity)\w*", "Availability-aware deployment is represented."),
    Signal("backup and recovery", "Replication and availability", 3, r"\b(backup|restore|disaster[_ -]?recovery|point[_ -]?in[_ -]?time)\w*", "Recovery planning is represented."),
    Signal("transactions", "Consistency and correctness", 4, r"\b(transaction|begin;|commit;|rollback|atomic)\w*", "Transactional boundaries are represented."),
    Signal("concurrency controls", "Consistency and correctness", 4, r"\b(lock|mutex|compare[_ -]?and[_ -]?swap|optimistic|etag|version[_ -]?check|serializ)\w*", "Concurrent update controls are represented."),
    Signal("delivery correctness", "Consistency and correctness", 4, r"\b(outbox|saga|deduplicat|exactly[_ -]?once|at[_ -]?least[_ -]?once|idempoten)\w*", "Cross-boundary delivery semantics are represented."),
    Signal("integrity constraints", "Consistency and correctness", 3, r"\b(unique|foreign key|constraint|check constraint)\b", "Data integrity constraints are represented."),
    Signal("versioned interfaces", "Dataflow and evolution", 3, r"\b(/v[0-9]+/|api[_ -]?version|schema[_ -]?version|protobuf|\.proto\b)\w*", "Versioned contracts are represented."),
    Signal("migrations", "Dataflow and evolution", 3, r"\b(migration|alembic|flyway|liquibase|schema[_ -]?registry)\w*", "Schema evolution tooling is represented."),
    Signal("stream or event flows", "Dataflow and evolution", 4, r"\b(event|stream|consumer|producer|cdc|change[_ -]?data[_ -]?capture)\w*", "Event or stream dataflow is represented."),
    Signal("logging", "Operability and observability", 3, r"\b(logging|logger|loglevel|structured[_ -]?log)\w*", "Logging is represented."),
    Signal("metrics", "Operability and observability", 3, r"\b(metrics?|prometheus|statsd|counter|histogram)\w*", "Metrics are represented."),
    Signal("tracing", "Operability and observability", 3, r"\b(opentelemetry|trace[_ -]?id|tracing|span[_ -]?id)\w*", "Distributed tracing is represented."),
    Signal("external configuration", "Operability and observability", 3, r"\b(os\.environ|getenv|configmap|secretkeyref|vault|environment:)\w*", "Externalized configuration is represented."),
    Signal("deployment descriptors", "Operability and observability", 3, r"\b(dockerfile|docker-compose|kind: deployment|terraform|helm|kubernetes)\w*", "Deployment automation is represented."),
    Signal("automated tests", "Verification and maintainability", 4, r"\b(pytest|unittest|jest|junit|rspec|go test|describe\(|test[_-])\w*", "Automated testing is represented."),
    Signal("failure testing", "Verification and maintainability", 3, r"\b(fault[_ -]?inject|chaos|toxiproxy|network[_ -]?partition|kill[_ -]?node|failure[_ -]?test)\w*", "Failure-mode testing is represented."),
    Signal("documentation", "Verification and maintainability", 2, r"\b(readme|architecture|runbook|adr|design[_ -]?doc)\w*", "Architecture or operations documentation is represented."),
    Signal("automation", "Verification and maintainability", 1, r"\b(makefile|github/workflows|gitlab-ci|jenkinsfile|tox\.ini|pre-commit)\w*", "Repeatable engineering automation is represented."),
)

RISKS: Sequence[Risk] = (
    Risk("unbounded network call", "Reliability and partial failures", 3, r"\brequests\.(get|post|put|patch|delete)\((?![^\n]*\btimeout\s*=)[^\n]*\)", "A Python HTTP request may wait without an explicit timeout.", "Set an explicit connect/read timeout and define retry behavior for transient failures."),
    Risk("hard-coded loopback dependency", "Scalability and partitioning", 2, r"\b(localhost|127\.0\.0\.1)\b", "A loopback address can couple components to one machine.", "Externalize service endpoints and document local-development defaults separately."),
    Risk("local durable state", "Replication and availability", 2, r"\b(sqlite|\.db\b|write_text\(|open\([^\n]*['\"]w)", "Local file-backed state may become a single-node dependency.", "Move shared durable state to a replicated service or explicitly document why the state is ephemeral."),
    Risk("sleep-based coordination", "Consistency and correctness", 2, r"\b(time\.sleep|thread\.sleep|settimeout)\s*\(", "Timing-based coordination is fragile under pauses and variable network delay.", "Use an explicit synchronization, lease, queue, or acknowledgement mechanism."),
)

LANGUAGE_NAMES = {
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".md": "Markdown",
    ".proto": "Protocol Buffers",
    ".py": "Python",
    ".rs": "Rust",
    ".sql": "SQL",
    ".tf": "Terraform",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".yaml": "YAML",
    ".yml": "YAML",
}


def analyze_repository(repository: str) -> AnalysisReport:
    """Analyze a local repository and return a scored architectural report."""
    root = Path(repository).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository is not a directory: {root}")
    documents = list(_read_documents(root))
    matches = {
        signal.name: _find_matches(
            documents,
            signal.pattern,
            include_tests=signal.category == "Verification and maintainability",
        )
        for signal in SIGNALS
    }
    scores: Dict[str, int] = {category.name: 0 for category in CATEGORIES}
    strengths: List[Finding] = []
    for signal in SIGNALS:
        evidence = matches[signal.name]
        if evidence:
            scores[signal.category] += signal.points
            strengths.append(
                Finding("strength", signal.category, signal.name, signal.detail, evidence=evidence[:3])
            )
    risks: List[Finding] = []
    for risk in RISKS:
        evidence = _find_matches(documents, risk.pattern)
        if evidence:
            scores[risk.category] -= risk.penalty
            risks.append(
                Finding("risk", risk.category, risk.name, risk.detail, risk.recommendation, evidence[:3])
            )
    gaps: List[Finding] = []
    category_scores: List[CategoryScore] = []
    for category in CATEGORIES:
        score = max(0, min(category.maximum, scores[category.name]))
        present = [signal.name for signal in SIGNALS if signal.category == category.name and matches[signal.name]]
        if not present:
            gaps.append(
                Finding("gap", category.name, "No static evidence found", category.rationale, category.missing_recommendation)
            )
        category_scores.append(
            CategoryScore(category.name, score, category.maximum, _category_summary(present))
        )
    languages: Dict[str, int] = {}
    for path, _ in documents:
        name = LANGUAGE_NAMES.get(path.suffix.lower(), path.suffix.lower().lstrip(".") or "text")
        languages[name] = languages.get(name, 0) + 1
    return AnalysisReport(
        repository=str(root),
        score=sum(category.score for category in category_scores),
        files_scanned=len(documents),
        category_scores=category_scores,
        strengths=strengths,
        risks=risks,
        gaps=gaps,
        languages=languages,
        limitations=[
            "This score measures architectural readiness evidence in the repository, not whether the running system is correct.",
            "Managed-service settings, production topology, traffic shape, SLOs, and operator practices may live outside the analyzed repository.",
            "Pattern matches are review prompts. Confirm each finding against the application's actual behavior and requirements.",
            "A small single-node application may be well designed without needing every distributed-systems capability.",
        ],
    )


def _read_documents(root: Path) -> Iterable[Tuple[Path, str]]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.stat().st_size > MAX_FILE_SIZE or not _is_text_candidate(path):
            continue
        try:
            yield path.relative_to(root), path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue


def _is_text_candidate(path: Path) -> bool:
    return path.name.lower() in TEXT_FILENAMES or path.suffix.lower() in TEXT_EXTENSIONS


def _find_matches(
    documents: Iterable[Tuple[Path, str]], pattern: str, include_tests: bool = False
) -> List[Evidence]:
    regex = re.compile(pattern, re.IGNORECASE)
    found: List[Evidence] = []
    for path, text in documents:
        if not include_tests and _is_test_path(path):
            continue
        if regex.search(str(path)):
            found.append(Evidence(str(path), 1, "<file path>"))
        for number, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                found.append(Evidence(str(path), number, _shorten(line.strip())))
                if len(found) >= 8:
                    return found
    return found


def _shorten(value: str, limit: int = 160) -> str:
    return value if len(value) <= limit else value[: limit - 3] + "..."


def _is_test_path(path: Path) -> bool:
    return (
        "tests" in path.parts
        or "test" in path.parts
        or path.name.startswith("test_")
        or path.name.endswith("_test.py")
    )


def _category_summary(present: Sequence[str]) -> str:
    if not present:
        return "No supporting source evidence detected."
    return "Evidence detected for " + ", ".join(present) + "."
