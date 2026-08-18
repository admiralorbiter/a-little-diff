# A Little Diff — V0 Evaluation & Real-World Validation Report

This report summarizes the verification of **A Little Diff (`alittlediff`) V0**, including both the **synthetic golden contract test suite** and the **live real-world evaluation** against the production knowledge graph of [Trivyn/moosedev](https://github.com/Trivyn/moosedev).

---

## 1. Executive Summary

- **Core Capability Proved:** A Little Diff successfully ingests versioned knowledge graphs directly from Git history, isolates meaningful epistemic changes from structural noise, collapses supersessions, and flags downstream consequences using typed propagation policy rules without model inference.
- **Real-World Scale:** Evaluated against **3,334 real knowledge records** in the `Trivyn/moosedev` production repository (`.moosedev/kg.nq`).
- **Test Suite Status:** **49/49 tests passing** in `pytest` with **95% overall code coverage**.
- **Model Independence:** The complete pipeline (diffing, collapsing, downstream impact propagation, Rich terminal reporting, and JSON generation) executes 100% deterministically with zero model dependency.

---

## 2. Test Architecture & Coverage

The test suite covers five distinct layers of validation:

| Test Suite | Purpose | Tests |
|---|---|---|
| [`tests/test_moosedev_contract.py`](../tests/test_moosedev_contract.py) | 8-case canonical contract evaluation (semantic no-ops, expansions, supersessions with absorbed rationales, working set filtering, historical edge preservation) | 8 |
| [`tests/test_impact_engine.py`](../tests/test_impact_engine.py) | 1-hop & 2-hop traversal, custom propagation rules, retired target suppression, false-positive prevention | 5 |
| [`tests/test_diff_structural.py`](../tests/test_diff_structural.py) | Record additions/removals, status changes, property modifications, relation additions/removals, supersession collapsing | 7 |
| [`tests/test_moosedev_adapter.py`](../tests/test_moosedev_adapter.py) | RDF parsing, determinism, Git snapshot loading, status normalization | 4 |
| [`tests/test_console_report.py`](../tests/test_console_report.py) | Rich terminal formatting, card rendering, markup escaping, live Git commit diffing | 4 |
| [`tests/test_json_report.py`](../tests/test_json_report.py) | Structured JSON report serialization & CLI `--json` flag | 2 |
| [`tests/test_git.py`](../tests/test_git.py) | Ref resolution, revision range parsing, isolated `git show` snapshot loading without working tree checkout | 7 |
| [`tests/test_edge_cases.py`](../tests/test_edge_cases.py) | Unicode/emoji symbols, empty graph handling, whitespace ranges, predicate priority ordering | 5 |
| [`tests/test_cli.py`](../tests/test_cli.py) | `--help`, `--version`, subcommands, strict missing snapshot error exits | 5 |
| [`tests/test_domain.py`](../tests/test_domain.py) | Pydantic model serialization, working-set active record properties | 2 |
| **Total** | | **49** |

---

## 3. Real-World MOOSEDev Production Trial

To test beyond synthetic fixtures, we fetched live, version-controlled knowledge graph snapshots from the official `Trivyn/moosedev` repository.

### Scale of Production Graph
- **Total Quads:** 27,263 RDF quads in `.moosedev/kg.nq`
- **Total Subjects:** 3,334 unique entities
- **Authoritative Active Set:** 3,209 records
- **Entity Breakdown:**
  - `CodeEntity`: 2,440
  - `ProposedLink`: 189
  - `ArchitecturalDecision`: 176
  - `Lesson`: 148
  - `Alternative`: 146
  - `Consequence`: 112
  - `Rationale`: 65
  - `Requirement`: 18
  - `Constraint`: 14
  - `SystemComponent`: 12
  - `CodeRole`: 6
  - `Pattern`: 5
  - `Criticality`: 3

### Technical Findings & System Fixes

1. **Named Graph Extraction in RDF N-Quads:**
   - *Discovery:* Real MOOSEDev serializes all asserted project quads inside the named graph `<https://moosedev.dev/kg/project>`. Standard RDFLib `Dataset.subjects()` queries only the default graph `urn:x-rdflib:default`, returning 0 records.
   - *Fix:* Re-implemented `MOOSEDevAdapter.parse_nquads` to group quads across all graphs via `dataset.quads((None, None, None))`.

2. **Deterministic Predicate Priority Ordering:**
   - *Discovery:* In real graphs where multiple labeling predicates co-exist (e.g. `rdfs:label` and `hasTitle`), iteration order in RDFLib is non-deterministic across Python runs.
   - *Fix:* Implemented priority-keyed dictionaries:
     - Titles: `hasTitle` > `dcterms:title` > `rdfs:label` > `skos:prefLabel`
     - Descriptions: `hasDescription` > `dcterms:description` > `rdfs:comment` > `skos:definition`
     - Status: `hasLifecycleStatus` > `hasStatus` > `status`

3. **Windows Terminal Stream Encoding:**
   - *Discovery:* Windows console default code page (`cp1252`) crashed when printing Unicode box characters (`═`, `──►`).
   - *Fix:* Added `sys.stdout.reconfigure(encoding="utf-8")` and `Console(legacy_windows=False)` to guarantee UTF-8 console output.

---

## 4. Live Diff Evaluation (`4f76c5bc` $\rightarrow$ `2b7d733d`)

Comparing commit `4f76c5bc` (Release 0.8.0) to commit `2b7d733d` (Latest) on `Trivyn/moosedev`:

- **Baseline (`4f76c5bc`):** 3,314 records (3,192 active)
- **Head (`2b7d733d`):** 3,334 records (3,209 active)
- **Detected Epistemic Changes:** 71 meaningful changes (55 explicit supersessions, 16 added records).
- **Downstream Consequences Flagged:** 54 impacts tracked along `constrains`, `learnedFrom`, `resultsFrom`, and `concerns`.

### Sample Terminal Card from Production Run

```text
════════════════════════════════════════════════════════════
 A LITTLE DIFF  (moosedev)
 4f76c5bc ──► 2b7d733d
════════════════════════════════════════════════════════════

71 meaningful knowledge changes  •  55 explicit supersessions  •  54 downstream items worth inspecting

▼ DOWNSTREAM ITEMS WORTH RECONSIDERING

╭──────────────────────── RECONSIDER (HIGH confidence) ────────────────────────╮
│ Target: Constraint: Normalize crate-version descriptor in SCIP symbols at KG │
│ minting                                                                      │
│ Effect: Constraint Context Changed                                           │
│ Path: (constrains)                                                           │
│ Why: A governing constraint for this decision or requirement changed.        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## 5. Answers to Core Evaluation Criteria

Referring to [`docs/EVALUATION.md`](EVALUATION.md):

1. **Does the tool invent changes when only code modified?**
   - **No.** Verified in Contract Case 2: Code changes without `.moosedev/kg.nq` updates produce 0 changes and 0 impacts.
2. **Does it collapse noisy RDF churn into coherent events?**
   - **Yes.** Supersessions with associated `hasRationale` nodes, `supersedes` links, `isSupersededBy` inverses, and status updates are collapsed into a single `superseded` event.
3. **Does it preserve historical motivations?**
   - **Yes.** Verified in Contract Case 8: When a premise changes, downstream decisions motivated by that premise in the baseline revision are flagged even if the link was dropped in the head revision.
4. **Does it suppress false positives on retired/deprecated items?**
   - **Yes.** Verified in Contract Case 7: Items with status `superseded`, `deprecated`, `retracted`, `proposed`, or `rejected` are suppressed from active impact notifications.

---

## 6. Conclusion & Recommendation

The deterministic core of **A Little Diff V0** is complete, stable, and verified against real production artifacts. The project is ready for ongoing use and evaluation on active development repositories.
