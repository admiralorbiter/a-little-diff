# A Little Diff — V0 Evaluation & Real-World Validation Report

This report evaluates **A Little Diff (`alittlediff`) V0**, assessing both its **technical compatibility** across Git/RDF snapshots and its **product usefulness** on real project memory from the [Trivyn/moosedev](https://github.com/Trivyn/moosedev) repository.

---

## 1. Evaluation Objectives

1. **Technical Compatibility:** Can A Little Diff load and parse real, version-controlled knowledge graphs from arbitrary Git commits without repository checkouts, model dependencies, or runtime crashes?
2. **Structural Coherence:** In real development commit ranges, does the diff engine isolate human-level architectural changes without low-level graph substrate noise leaking into the primary change set?
3. **Product Usefulness:** Do the flagged downstream impacts identify decisions, constraints, lessons, or consequences that a developer would genuinely need to reconsider?

---

## 2. Test Architecture & Code Coverage

The synthetic test suite contains **49 automated tests** passing with **95% code coverage**:

| Test Suite | Focus Area | Tests | Pass Rate |
|---|---|---|---|
| [`tests/test_moosedev_contract.py`](../tests/test_moosedev_contract.py) | 8-case canonical contract suite (no-ops, additions, supersession collapsing, rationale absorption, working set semantics, historical motivations) | 8 | 100% |
| [`tests/test_impact_engine.py`](../tests/test_impact_engine.py) | 1-hop & 2-hop traversal, custom propagation rules, retired target suppression, false-positive prevention | 5 | 100% |
| [`tests/test_diff_structural.py`](../tests/test_diff_structural.py) | Structural event taxonomy (add, remove, status change, modified properties, relation changes, supersessions) | 7 | 100% |
| [`tests/test_moosedev_adapter.py`](../tests/test_moosedev_adapter.py) | RDF N-Quads parsing, determinism, Git snapshot loading, status normalization | 4 | 100% |
| [`tests/test_console_report.py`](../tests/test_console_report.py) | Rich terminal formatting, card rendering, markup escaping, live Git commit diffing | 4 | 100% |
| [`tests/test_json_report.py`](../tests/test_json_report.py) | Structured JSON report serialization & CLI `--json` flag | 2 | 100% |
| [`tests/test_git.py`](../tests/test_git.py) | Ref resolution, revision range parsing, isolated `git show` snapshot loading without working tree checkout | 7 | 100% |
| [`tests/test_edge_cases.py`](../tests/test_edge_cases.py) | Unicode/emoji symbols, empty graph handling, whitespace ranges, predicate priority ordering | 5 | 100% |
| [`tests/test_cli.py`](../tests/test_cli.py) | `--help`, `--version`, subcommands, strict missing snapshot error exits | 5 | 100% |
| [`tests/test_domain.py`](../tests/test_domain.py) | Pydantic model serialization, working-set active record properties | 2 | 100% |
| **Total** | | **49** | **100%** |

---

## 3. Real-World Production Trial (`Trivyn/moosedev`)

We evaluated A Little Diff directly against the production knowledge graph of `Trivyn/moosedev` (`.moosedev/kg.nq`), comparing **Release 0.8.0 (`4f76c5bc`)** to **Latest (`2b7d733d`)**.

### Graph Scale & Composition
- **Total Quads:** 27,263 RDF quads in `.moosedev/kg.nq`
- **Total Unique Entities:** 3,334 subjects
- **Authoritative Active Set:** 3,209 records
- **Entity Breakdown:**
  - `CodeEntity`: 2,440 (73.2%)
  - `ProposedLink`: 189 (5.7%)
  - `ArchitecturalDecision`: 176 (5.3%)
  - `Lesson`: 148 (4.4%)
  - `Alternative`: 146 (4.4%)
  - `Consequence`: 112 (3.4%)
  - `Rationale`: 65 (1.9%)
  - `Requirement`: 18 (0.5%)
  - `Constraint`: 14 (0.4%)
  - `SystemComponent`: 12 (0.4%)
  - `CodeRole`: 6 (0.2%)
  - `Pattern`: 5 (0.2%)
  - `Criticality`: 3 (0.1%)

---

## 4. Empirical Breakdown of Changes & Impacts

### 71 Epistemic Changes by Entity Kind

| Entity Kind | Count | Percentage |
|---|---|---|
| `ArchitecturalDecision` | 30 | 42.3% |
| `Lesson` | 26 | 36.6% |
| `Consequence` | 5 | 7.0% |
| `Constraint` | 3 | 4.2% |
| `Requirement` | 3 | 4.2% |
| `Alternative` | 3 | 4.2% |
| `Rationale` | 1 | 1.4% |
| `CodeEntity` | **0** | **0.0%** |

> [!NOTE]
> **Substrate Isolation:** In this real commit range, low-level `CodeEntity` churn did not leak into the primary change set; 100% of reported changes were human-level architectural units (Decisions, Lessons, Consequences, Constraints, Requirements).

### 54 Downstream Impact Candidates by Target Kind & Policy Rule

The 54 impact candidates were generated along the corrected propagation policy rules ([`src/alittlediff/impact/policy.py`](../src/alittlediff/impact/policy.py)):

| Traversed Predicate | Policy Direction | Confidence | Target Record Kind | Count |
|---|---|---|---|---|
| `constrains` | Forward | **High** | `ArchitecturalDecision` | 1 |
| `resultsIn` | Forward | **Medium** | `Consequence` | 14 |
| `learnedFrom` | Reverse | **Medium** | `Lesson` | 2 |
| `concerns` | Both | **Low** | `SystemComponent` (35), `CodeEntity` (2) | 37 |
| **Total** | | | | **54** |

All 54 individual impact evaluations are cataloged in machine-readable format at [`evaluation/v0-moosedev.jsonl`](../evaluation/v0-moosedev.jsonl).

---

## 5. Actionability & Usefulness Evaluation

We manually evaluated all 54 impact candidates across the three confidence tiers:

### Tier 1: High-Confidence Impacts (1 candidate — `constrains` path)
- **Constraint $\rightarrow$ `constrains` $\rightarrow$ Architectural Decision:**
  - **Source:** Constraint *"Instance (A-box) dense retrieval is permitted only as a bounded SEED for get_relevant_context; walk planning remains the precision engine"*.
  - **Target:** Architectural Decision *"Two-tier granularity: substrate code index vs KG skeleton"*.
  - **Verdict:** **USEFUL / High Actionability.** When the core dense retrieval constraint changed, the foundational architectural decision restricting code index granularity vs KG skeleton required immediate re-verification.

### Tier 2: Medium-Confidence Impacts (16 candidates — `resultsIn` & `learnedFrom` paths)
- **14 Decisions $\rightarrow$ `resultsIn` $\rightarrow$ Consequences:**
  - *Examples:* AD *"Python substrate support"* $\rightarrow$ Consequence *"scip-python emits unspecified position_encoding..."*; AD *"Generation-proven session-pinned LSP coordinates"* $\rightarrow$ Consequence *"Every incoming LSP message costs one SubstrateMeta manifest read"*.
  - **Verdict:** **USEFUL (14/14).** When an architectural decision is superseded or revised, its documented operational consequences (e.g. latency costs, worker child orphan risks, reindex costs) must be re-evaluated to see if the consequence still holds or has been mitigated.
- **2 Decisions $\rightarrow$ `learnedFrom` $\rightarrow$ Lessons:**
  - *Examples:* AD *"LSP positions track unsaved buffers by exact line alignment"* $\rightarrow$ Lesson *"Correct disk ranges can still be wrong for the editor buffer"*.
  - **Verdict:** **USEFUL (2/2).** Directly flags empirical lessons drawn from the decision that was modified.

### Tier 3: Low-Confidence Impacts (37 candidates — `concerns` path)
- **Decisions / Lessons $\rightarrow$ `concerns` $\rightarrow$ `SystemComponent` (35) / `CodeEntity` (2):**
  - **Verdict:** **BROAD COMPONENT ASSOCIATIONS (37/37).** In MOOSEDev, decisions attach `concerns -> SystemComponent`. Alerting that a broad system component is related is topologically accurate but rarely individually actionable. Grouping or summarizing these in the console output appropriately declutters the report.

### Actionability Summary Table
| Category | Count | Percentage | Description |
|---|---|---|---|
| **Useful / High Actionability** | 16 | 29.6% | Directly actionable design constraints, consequences, and lessons |
| **Broad Component Associations** | 37 | 68.5% | Topologically accurate component context (properly labeled LOW) |
| **Correct Context / Informative** | 1 | 1.9% | Architectural invariant confirmation |
| **Total** | **54** | **100%** | |

---

## 6. End-to-End Deep-Dive Case Study

To trace the causal chain from commit to developer action:

1. **Changed Premise (Commit `4f76c5bc` $\rightarrow$ `2b7d733d`):**
   - Constraint `Instance (A-box) dense retrieval is permitted only as a bounded SEED...` was refined/superseded during retrieval pipeline updates.
2. **Graph Traversal:**
   - Propagated forward via `constrains` directly to Architectural Decision `Two-tier granularity: substrate code index vs KG skeleton`.
3. **Downstream Target Flagged:**
   - Architectural Decision `Two-tier granularity: substrate code index vs KG skeleton`.
4. **Human Judgment:**
   - **Yes.** When modifying how dense vector retrieval seeds context recall, the decision that divided responsibilities between the substrate code index and the KG skeleton must be verified to ensure its granularity boundary is not violated.

---

## 7. Conclusions & Next Steps

1. **V0 Status:** Technical compatibility across real MOOSEDev data is proven. Forward `constrains` and inverse `learnedFrom`/`isConstrainedBy` propagation rules operate with clean, verifiable causal semantics.
2. **Console UX:** Low-confidence `concerns` impacts are now compactly grouped by entity kind in standard console output, preventing terminal clutter.
3. **Subsequent Phase (Ollama Integration):**
   - With deterministic impact paths verified, local models (`qwen3:8b`/`14b`) can now be evaluated for semantic classification (`revision` vs `world_update`) and natural-language rationale summaries.
