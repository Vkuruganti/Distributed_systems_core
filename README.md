# Distributed Systems Core

This repository is a compact engineering workspace for infrastructure automation,
small operational experiments, and distributed-systems architecture analysis.

The main tool is `distributed_systems_analyzer`: a Python API and CLI that scans an
application repository, reports architectural strengths and risks, identifies
missing distributed-systems capabilities, and produces a readiness score out of
`100`.

The repository also contains a small collection of ad hoc scripts for
infrastructure and Python practice.

## Repository Primer

```text
Distributed_systems_core/
|-- adhoc_scripts/
|   |-- Install_IIS.yml
|   |-- return_http_code.py
|   |-- search_web_page.py
|   |-- sum_of_reverse_diagonal_elements_matrix.py
|   `-- test_file
|-- code_development_practices/
|   |-- distributed_systems_analyzer/
|   |-- tests/
|   |-- pyproject.toml
|   `-- README.md
|-- .gitignore
`-- README.md
```

| Area | Purpose |
| --- | --- |
| `code_development_practices/` | Installable distributed-systems architectural analyzer, tests, and detailed documentation |
| `adhoc_scripts/` | Small infrastructure, HTTP, and Python learning utilities |
| `.gitignore` | Excludes local virtual environments and Python cache files |

## Distributed-Systems Analyzer

The analyzer reviews source code, configuration, infrastructure definitions,
schemas, tests, and documentation for evidence that an application is prepared for
distributed operation.

It helps engineers ask:

- Are network calls bounded with timeouts and retry policies?
- Are requests idempotent when retries or duplicate delivery are possible?
- Can workloads scale horizontally or be partitioned?
- Are replication, failover, backup, and recovery represented?
- Are transactions, concurrency controls, and delivery semantics explicit?
- Can APIs and schemas evolve safely?
- Are logs, metrics, traces, configuration, and deployment descriptors present?
- Do tests include failure scenarios and repeatable automation?

The analyzer is an explainable static-analysis tool. Each finding includes source
evidence with a file path and line number. It does not inspect a running production
system, and its score is not a correctness certification.

### Quick Start

From the repository root, install the analyzer:

```bash
python3 -m pip install ./code_development_practices
```

Analyze another application repository:

```bash
ds-analyze /path/to/application/repository
```

Analyze the example scripts in this repository:

```bash
ds-analyze ./adhoc_scripts
```

Generate JSON for CI, dashboards, or custom reporting:

```bash
ds-analyze /path/to/application/repository --format json
```

Run without installing:

```bash
cd code_development_practices
python3 -m distributed_systems_analyzer /path/to/application/repository
```

### Python API

The same analysis can be called from Python:

```python
from distributed_systems_analyzer import analyze_repository

report = analyze_repository("/path/to/application/repository")

print(report.score)
print(report.render_text())

data = report.to_dict()
print(data["category_scores"])
print(data["risks"])
```

### Scoring Overview

The score is calculated from seven categories:

| Category | Maximum points | What it reviews |
| --- | ---: | --- |
| Reliability and partial failures | `20` | Timeouts, retries, idempotency, health checks, resilience controls |
| Scalability and partitioning | `15` | Horizontal execution, partitioning, caching, queues |
| Replication and availability | `15` | Replication, failover, availability-aware deployment, recovery |
| Consistency and correctness | `15` | Transactions, concurrency controls, delivery correctness, constraints |
| Dataflow and evolution | `10` | Versioned interfaces, migrations, streams, and event flows |
| Operability and observability | `15` | Logging, metrics, tracing, configuration, deployment descriptors |
| Verification and maintainability | `10` | Tests, failure testing, documentation, automation |
| **Total** | **`100`** | **Architectural readiness evidence found in the repository** |

Positive signals add points. Risky patterns subtract points from their categories.
Examples of risk penalties include HTTP calls without explicit timeouts,
hard-coded loopback dependencies, local durable state, and sleep-based
coordination.

Use the score to prioritize review work:

| Score | Suggested interpretation |
| ---: | --- |
| `0-24` | Little distributed-systems evidence is present. Confirm whether this is intentional. |
| `25-49` | Some practices are represented, but important gaps likely need review. |
| `50-74` | Meaningful readiness evidence exists. Focus on weaker categories and external production settings. |
| `75-100` | Broad architectural evidence exists. Validate quality with tests, load analysis, and operational review. |

For the complete scoring rubric, architecture diagrams, supported file types, risk
penalties, CI guidance, and limitations, read the
[analyzer documentation](code_development_practices/README.md).

## Ad Hoc Tools

The `adhoc_scripts/` folder contains small standalone examples. They are useful as
reference material and practice exercises rather than as a single deployable
application.

| Tool | Purpose | Usage notes |
| --- | --- | --- |
| `Install_IIS.yml` | Ansible playbook that installs the IIS web-server feature on the `windows2` host | Requires Ansible and a configured Windows inventory |
| `return_http_code.py` | Sends an HTTP `HEAD` request and prints status-code examples | Uses Python 2 syntax and the Python 2 `httplib` module |
| `search_web_page.py` | Downloads a web page and searches its content for the word `maintenance` | Uses Python 2 syntax and the Python 2 `urllib2` module |
| `sum_of_reverse_diagonal_elements_matrix.py` | Defines `reverse_d(a)` to sum the reverse diagonal of a `3 x 3` matrix | Function can be imported from Python; input is expected to be a `3 x 3` matrix |
| `test_file` | Scratch text file | No runtime behavior |

### IIS Installation Example

Run the Ansible playbook after configuring an inventory with a `windows2` host:

```bash
ansible-playbook -i /path/to/inventory adhoc_scripts/Install_IIS.yml
```

### Matrix Utility Example

Run the matrix helper with Python:

```bash
python3 - <<'PY'
from adhoc_scripts.sum_of_reverse_diagonal_elements_matrix import reverse_d

matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]

print(reverse_d(matrix))  # 15
PY
```

The two HTTP examples are legacy Python 2 snippets. Modernizing them to Python 3
would require replacing `httplib` with `http.client`, replacing `urllib2` with
`urllib.request`, and updating `print` statements.

## Analyzer Development

The analyzer requires Python `3.9` or newer and has no third-party runtime
dependencies.

Run its test suite:

```bash
cd code_development_practices
python3 -m unittest discover -s tests -v
```

Run its CLI help:

```bash
cd code_development_practices
python3 -m distributed_systems_analyzer --help
```

The analyzer's implementation is intentionally straightforward:

| Module | Responsibility |
| --- | --- |
| `analyzer.py` | File discovery, heuristic matching, category scoring, risk detection |
| `models.py` | Report, finding, evidence, and category-score data models |
| `cli.py` | Command-line argument parsing and text or JSON output |
| `__main__.py` | Support for `python3 -m distributed_systems_analyzer` |
| `tests/test_analyzer.py` | Focused tests for scoring, risks, excluded paths, and repository validation |

## Recommended Workflow

1. Install the analyzer from `code_development_practices/`.
2. Run `ds-analyze` against the application repository you want to review.
3. Read the weakest categories and inspect each evidence-backed finding.
4. Confirm repository findings against production topology, managed-service
   settings, traffic patterns, SLOs, and operational practices.
5. Add targeted improvements such as explicit timeouts, health checks, metrics,
   migrations, deployment descriptors, or failure-mode tests.
6. Generate JSON in CI to track architectural evidence over time.

The analyzer provides the checklist and evidence trail. Engineering judgment still
decides which distributed-systems capabilities the application actually needs.
