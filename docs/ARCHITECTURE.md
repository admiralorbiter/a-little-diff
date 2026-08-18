# A Little Diff — Proposed Architecture

## 1. Architecture objective

The architecture should make the smallest version easy while keeping the conceptual core independent of:

- MOOSEDev;
- RDF;
- Ollama;
- Git;
- any individual LLM provider.

The system should have a deterministic center with adapters on the outside.

```text
                    SOURCES
                      │
        ┌─────────────┼──────────────┐
        │             │              │
     MOOSEDev       future         future
      kg.nq           ADRs       GitHub/docs
        │             │              │
        └─────────────┼──────────────┘
                      ▼
               EpistemicAdapter
                      │
                      ▼
              Normalized State
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
 Structural Diff             Provenance
         │                         │
         └────────────┬────────────┘
                      ▼
              Epistemic Changes
                      │
                      ▼
               Impact Engine
                      │
              ┌───────┴───────┐
              │               │
        deterministic      ambiguous
              │               │
              │               ▼
              │        Model Provider
              │         (Ollama first)
              │               │
              └───────┬───────┘
                      ▼
                Report Model
                      │
            ┌─────────┼──────────┐
            ▼         ▼          ▼
          Rich       JSON      Markdown
          CLI
```

---

# 2. Recommended V0 technology stack

```text
Python 3.12+
Typer
RDFLib
Pydantic
Rich
pytest
subprocess → system git
Ollama Python client (optional)
```

### Why Python

V0 is primarily:

- Git plumbing;
- RDF parsing;
- graph normalization;
- comparison;
- typed data transformations;
- experiment iteration;
- model calls.

Python minimizes friction for all of these.

There is no current performance reason to put the core in Rust.

If graph scale eventually demands a faster engine, the normalized domain boundary makes later replacement possible.

### Why direct `git`

Use the installed Git binary through `subprocess`.

Do not introduce GitPython until a concrete use case justifies it.

The actual Git operations are small and auditable:

```bash
git rev-parse
git show
git diff
git log
```

### Why RDFLib

V0 needs to parse canonical N-Quads and extract a subset of MOOSEDev records.

RDFLib is sufficient and avoids requiring MOOSEDev's runtime.

---

# 3. Proposed package layout

```text
a-little-diff/
├── pyproject.toml
├── README.md
├── docs/
├── src/
│   └── alittlediff/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       │
│       ├── domain/
│       │   ├── state.py
│       │   ├── record.py
│       │   ├── relation.py
│       │   ├── change.py
│       │   ├── impact.py
│       │   └── evidence.py
│       │
│       ├── adapters/
│       │   ├── base.py
│       │   └── moosedev.py
│       │
│       ├── git/
│       │   ├── refs.py
│       │   └── snapshots.py
│       │
│       ├── diff/
│       │   ├── structural.py
│       │   ├── semantic.py
│       │   └── classify.py
│       │
│       ├── impact/
│       │   ├── traversal.py
│       │   ├── policy.py
│       │   └── support.py
│       │
│       ├── models/
│       │   ├── base.py
│       │   ├── ollama.py
│       │   └── none.py
│       │
│       └── report/
│           ├── console.py
│           ├── markdown.py
│           └── json.py
│
└── tests/
    ├── fixtures/
    ├── golden/
    └── ...
```

V0 does not need every file on day one. This is a sensible direction, not a scaffold requirement.

---

# 4. Normalized domain model

The core engine should not expose raw RDF triples.

## EpistemicRecord

```python
class EpistemicRecord(BaseModel):
    id: str
    kind: str

    title: str | None
    claim: str | None
    status: str | None

    relations: list["Relation"]
    evidence: list["Evidence"]

    source_metadata: dict[str, Any] = {}
```

`id` is adapter-scoped but stable between state A and state B whenever the source supports stable identity.

For MOOSEDev it can be the record IRI.

## Relation

```python
class Relation(BaseModel):
    predicate: str
    subject_id: str
    object_id: str
    evidence: list["Evidence"] = []
```

The domain layer should preserve the source predicate while optionally exposing a normalized semantic category.

## EpistemicState

```python
class EpistemicState(BaseModel):
    source: str
    revision: str
    records: dict[str, EpistemicRecord]
```

## Evidence

```python
class Evidence(BaseModel):
    source_type: str
    source_id: str | None
    revision: str | None
    path: str | None
    locator: str | None
    excerpt: str | None
```

The schema should support future evidence such as:

```text
git
MOOSEDev record
PR
issue
ADR
doc
test
runtime observation
external source
```

## EpistemicChange

```python
class EpistemicChange(BaseModel):
    change_id: str

    structural_type: Literal[
        "added",
        "removed",
        "status_changed",
        "superseded",
        "relation_added",
        "relation_removed",
        "modified",
    ]

    semantic_type: Literal[
        "expansion",
        "contraction",
        "revision",
        "world_update",
        "refinement",
        "contradiction",
        "semantic_noop",
        "unknown",
    ] | None

    before: EpistemicRecord | None
    after: EpistemicRecord | None

    evidence: list[Evidence]
    judgment_source: Literal[
        "deterministic",
        "model",
        "human",
    ]
```

The distinction between structural and semantic change is intentional.

---

# 5. Adapter contract

```python
class EpistemicAdapter(Protocol):
    def can_load(
        self,
        repo: Path,
        revision: str,
    ) -> bool:
        ...

    def load_state(
        self,
        repo: Path,
        revision: str,
    ) -> EpistemicState:
        ...
```

The diff engine should receive:

```text
EpistemicState(A)
EpistemicState(B)
```

and know nothing about how they were produced.

---

# 6. MOOSEDev adapter

## Snapshot retrieval

V0:

```bash
git show <ref>:.moosedev/kg.nq
```

Failure states need explicit handling:

```text
file absent at A
file absent at B
invalid N-Quads
repository not initialized
ref does not exist
```

The adapter should not start MOOSEDev.

It should not modify `.moosedev`.

## Parsing

RDFLib:

```python
Graph().parse(data=nquads, format="nquads")
```

In practice N-Quads may use named graphs, so use an RDFLib dataset/conjunctive graph structure appropriate to preserving graph context.

## Normalization

The adapter needs a bounded set of mapping rules for MOOSEDev's public ontology.

Prefer:

```text
known classes
known lifecycle property
known title/description properties
known relation predicates
```

over trying to generically interpret every ontology construct.

Unknown records can be retained with:

```text
kind = original local class name
```

rather than silently discarded if doing so is cheap.

## Identity

Stable IRI identity is the easiest path:

```text
record exists at A and B → same record
```

Explicit lifecycle edges such as supersession should be interpreted before any semantic-model matching.

This is why embeddings are unnecessary in V0.

---

# 7. Structural diff engine

Given:

```text
records_A
records_B
```

calculate:

```text
added IDs
removed IDs
shared IDs
property changes on shared IDs
relation set delta
status delta
explicit supersession patterns
```

Order of precedence matters.

For example, if the old record remains in the graph with status `superseded` and a new record points to it through `supersedes`, emit:

```text
SUPERSEDED
```

rather than:

```text
old status changed
new record added
relation added
```

The lower-level changes may remain attached as details.

This keeps the primary report epistemically meaningful.

---

# 8. Impact engine

## V0 policy-driven traversal

Define a very small propagation table.

Example only:

```python
IMPACT_RULES = {
    "isMotivatedBy": {
        "direction": "reverse",
        "effect": "justification_may_have_changed",
        "strength": "high",
    },
    "constrains": {
        "direction": "reverse",
        "effect": "constraint_context_changed",
        "strength": "high",
    },
    "resultsIn": {
        "direction": "forward",
        "effect": "consequence_may_have_changed",
        "strength": "medium",
    },
    "concerns": {
        "direction": "both",
        "effect": "inspect",
        "strength": "low",
    },
}
```

These are hypotheses to validate against actual MOOSEDev ontology directionality and real examples.

Do not treat this example as final semantics.

## V0 traversal depth

Keep default propagation deliberately shallow:

```text
1–2 meaningful edges
```

and expose the full support path in output.

If the result cannot explain **why** the path implies reconsideration, do not escalate it merely because it is reachable.

---

# 9. Future support / truth-maintenance layer

V1 can introduce explicit support objects:

```python
class SupportSet(BaseModel):
    conclusion_id: str
    premise_ids: frozenset[str]
```

The important operation:

```python
def remains_supported(
    conclusion,
    active_premises,
    support_sets,
) -> bool:
    ...
```

Now a changed premise can produce:

```text
SUPPORT DEGRADED
one justification disappeared;
another valid support set remains.
```

versus:

```text
SUPPORT LOST
no known justification remains.
```

This is far more useful than graph reachability.

---

# 10. Model provider layer

## Interface

```python
class EpistemicReasoner(Protocol):
    def classify_change(
        self,
        before: EpistemicRecord,
        after: EpistemicRecord,
        evidence: list[Evidence],
    ) -> ChangeJudgment:
        ...

    def explain_impact(
        self,
        change: EpistemicChange,
        impact_path: list[Relation],
        evidence: list[Evidence],
    ) -> ImpactExplanation:
        ...
```

Future:

```python
align_claims(...)
reconcile_model(...)
extract_rationale(...)
```

## Providers

```text
NoneReasoner
OllamaReasoner
future OpenAICompatibleReasoner
future explicit cloud providers
```

No domain code should call `ollama.chat()` directly.

---

# 11. Ollama integration

## Initial use

Do not ask the model:

> Read this repo and decide what changed.

Give it a bounded evidence packet.

Example:

```json
{
  "before": {
    "kind": "Constraint",
    "claim": "..."
  },
  "after": {
    "kind": "Constraint",
    "claim": "..."
  },
  "git_context": [],
  "known_lifecycle": "superseded"
}
```

Request a schema-constrained result.

## Schema

```python
class ChangeJudgment(BaseModel):
    semantic_type: Literal[
        "revision",
        "world_update",
        "refinement",
        "contradiction",
        "same",
        "unknown",
    ]

    rationale: str
    evidence_ids: list[str]

    # model confidence is useful metadata but should not
    # be treated as calibrated probability
    confidence: Literal["low", "medium", "high"]
```

Use:

```text
temperature = 0
```

for these bounded classification calls.

## Initial models

Recommended benchmark set rather than hard dependency:

```text
qwen3:8b
qwen3:14b
gpt-oss:20b
```

Choose the smallest model that meets task-specific quality.

## Escalation

Do not route merely because:

```text
model says confidence = .71
```

Prefer signals such as:

- deterministic and model classifications disagree;
- two local models disagree;
- required evidence is missing;
- multiple semantic classes remain plausible;
- contradiction is detected;
- high-impact downstream consequences are being proposed.

A future auto router:

```text
rules
  │
  ├─ sufficient → accept
  │
  └─ ambiguous
       │
       ▼
   qwen3:8b
       │
       ├─ stable + grounded → accept inference
       │
       └─ conflict / high-risk
             │
             ▼
       stronger local model
             │
             └─ optional explicit cloud escalation
```

---

# 12. Embeddings

Do not use embeddings in V0.

Stable MOOSEDev IRIs make identity matching deterministic.

Embeddings become useful when adapters need to align semantically equivalent but separately expressed claims:

```text
"External coordinators require local credentials."

"Non-PREP-KC users authenticate through username/password."
```

Future process:

```text
qwen3-embedding:0.6b
      │
      ▼
candidate pairs
      │
      ▼
reasoner judgment
      │
      ├─ same claim
      ├─ refinement
      ├─ related
      └─ distinct
```

Embedding similarity should produce candidates, not authoritative identity.

---

# 13. Report model

The report itself should also be typed.

```python
class DiffReport(BaseModel):
    base_revision: str
    head_revision: str

    changes: list[EpistemicChange]
    impacts: list[Impact]
    warnings: list[str]
```

Then renderers transform the same object into:

```text
console
JSON
Markdown
```

This makes testing far easier than testing formatted terminal strings.

---

# 14. CLI

Initial CLI:

```bash
alittlediff A..B
```

Useful flags:

```bash
alittlediff A..B --json
alittlediff A..B --markdown
alittlediff A..B --no-model
alittlediff A..B --model qwen3:8b
alittlediff A..B --verbose
```

Do not add dozens of knobs until usage reveals actual needs.

Future:

```bash
alittlediff explain A..B --decision <id-or-query>
alittlediff why <claim>
alittlediff diagnose
alittlediff trajectory <claim>
```

---

# 15. Configuration

Possible `.alittlediff.toml`:

```toml
[model]
provider = "ollama"
model = "qwen3:8b"
temperature = 0

[impact]
max_depth = 2

[output]
show_evidence = true
```

The application should have sensible defaults and work without a config file.

---

# 16. Caching and persistence

V0 likely needs none beyond normal process memory.

If model calls become repeated:

```text
SQLite
```

is sufficient for:

- prompt fingerprint;
- model identifier;
- schema version;
- response;
- evidence hash.

Do not add a vector database merely because the project involves knowledge.

---

# 17. Epistemic safety rules

These are not content-safety rules; they protect the integrity of the project's own reasoning.

## Asserted

Directly present in the source graph/artifact.

## Derived

Obtained through deterministic structural or rule-based reasoning.

## Inferred

Produced by a model from explicit evidence.

## Speculative

A possible interpretation proposed for human consideration.

Every report object should preserve which category applies.

A model-produced inference must not be written back as an asserted MOOSEDev record unless a separate, explicit human/ratification workflow is introduced.

---

# 18. Observability

Log enough to debug epistemic mistakes:

```text
input refs
adapter version
record counts
structural changes
propagation paths considered
propagation rules fired
model name
prompt/schema version
evidence IDs supplied
structured model judgment
```

Avoid making the only debugging artifact a giant transcript.

The goal is reproducibility.

---

# 19. Future architecture extensions

## Multi-artifact project state

```text
GitHub PRs / issues / reviews
          │
          ▼
 rationale extraction
          │
          ▼
 normalized premises / questions / options
```

## Query-level semantic diff

Define important project questions and compare answers across states.

## Truth maintenance

Support-set invalidation and remaining-justification analysis.

## QOC / decision reopening

Changed criteria trigger reconsideration of previously settled questions.

## Contradiction diagnosis

Minimal conflicting sets and repair candidates.

## Temporal trajectory analysis

```text
state 1 → state 2 → state 3 → ... → state N
```

Detect recurring reversals, unstable assumptions, and repeatedly reopened design issues.

None of these should complicate the first proof.
