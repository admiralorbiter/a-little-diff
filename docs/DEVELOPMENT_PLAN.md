# A Little Diff — Development Plan

## 1. Development strategy

The project should be developed as a sequence of **epistemic capability proofs**, not as a march toward a predetermined large architecture.

The first question is not:

> Can we build a beautiful project-knowledge platform?

It is:

> Does an epistemic diff produce information that changes what a developer notices or decides?

The plan therefore deliberately keeps the first release narrow.

---

# 2. V0 definition

## User story

Given a repository with MOOSEDev memory committed at two revisions:

```bash
alittlediff <A>..<B>
```

show:

1. what durable project knowledge changed;
2. what the project treated as true/active before and after;
3. explicit supersessions or retractions;
4. a small set of downstream records that may deserve reconsideration;
5. why each consequence was flagged;
6. evidence sufficient to audit the result.

The report must remain useful with:

```bash
--no-model
```

Models may enrich the interpretation but cannot be necessary for basic correctness.

---

# 3. Milestone 0 — Repository scaffold

## Deliverables

```text
pyproject.toml
src/alittlediff/
tests/
README.md
docs/
```

Dependencies:

```text
typer
pydantic
rdflib
rich
pytest
```

Optional dependency group:

```text
ollama
```

## CLI smoke test

```bash
alittlediff --help
alittlediff --version
```

## Acceptance

- package installs in a fresh virtual environment;
- tests run;
- CLI boots;
- no model or MOOSEDev process is required.

---

# 4. Milestone 1 — Git snapshot loader

## Goal

Read `.moosedev/kg.nq` at arbitrary Git refs without checking out the repository.

## Operations

```bash
git rev-parse <ref>
git show <ref>:.moosedev/kg.nq
```

## Implement

```text
git/refs.py
git/snapshots.py
```

Typed error conditions:

```text
NotGitRepository
UnknownRevision
MissingKnowledgeSnapshot
InvalidKnowledgeSnapshot
```

## Tests

Create tiny fixture repositories with:

- graph at both refs;
- missing graph at base;
- missing graph at head;
- malformed graph;
- branch/tag/SHA refs.

## Acceptance

This works:

```python
snapshot = load_text_at_ref(
    repo,
    "HEAD~1",
    ".moosedev/kg.nq",
)
```

without changing the working tree.

---

# 5. Milestone 2 — MOOSEDev normalization

## Goal

Convert raw N-Quads into `EpistemicState`.

## First pass

Identify:

- information-record instances;
- class/kind;
- title;
- description/claim;
- lifecycle status;
- known relationships;
- supersession;
- provenance included in the committed graph, if present.

Do not attempt complete ontology reasoning.

## Output

```python
EpistemicState(
    source="moosedev",
    revision=sha,
    records={...},
)
```

## Fixture design

Construct a deliberately tiny graph:

```text
Constraint C1
Decision D1 isMotivatedBy C1
Plan/Requirement R1 concerns ...
```

Then add a later state containing:

```text
Constraint C2 supersedes C1
```

## Acceptance

Snapshot normalization is deterministic and stable across runs.

---

# 6. Milestone 3 — Structural epistemic diff

## Goal

Generate a typed, deterministic delta.

Implement:

```text
added
removed
status_changed
superseded
relation_added
relation_removed
modified
```

## Important normalization

Prefer one high-level lifecycle event:

```text
C1 superseded by C2
```

over three noisy low-level events:

```text
C1 status changed
C2 added
supersedes relation added
```

The details can be nested beneath the primary event.

## JSON first

Before building terminal presentation, ensure:

```bash
alittlediff A..B --json
```

returns a stable report structure.

## Acceptance

Golden tests cover all structural change types.

No LLM is called.

---

# 7. Milestone 4 — Human-readable report

## Goal

Make the deterministic diff pleasant enough that the project can be tested on real work immediately.

Use Rich.

Initial layout:

```text
A LITTLE DIFF
A → B

2 meaningful knowledge changes
1 explicit supersession
1 downstream item worth inspecting

BELIEF SUPERSEDED
...

WHY IT MATTERS
...

EVIDENCE
...
```

## Design rule

Do not lead with graph trivia.

Lead with the human unit:

```text
belief
decision
constraint
requirement
question
```

## Acceptance

A developer can understand each reported change without opening the raw RDF.

---

# 8. Milestone 5 — Small impact engine

## Goal

Test the hypothesis that a changed premise can expose a downstream decision worth revisiting.

## Approach

Hard-code a conservative allowlist of semantically meaningful MOOSEDev relations after verifying their direction and intended ontology use.

Start with one-hop propagation.

Potential second hop only when the full explanation path remains obvious.

Every impact must include:

```text
source change
relation/path
target
effect label
```

Example:

```text
Constraint C1 superseded
  └─ isMotivatedBy⁻¹
     └─ Decision D1

Effect:
Decision D1's original justification changed.
```

## Important negative result

It is acceptable for V0 to produce:

```text
No downstream consequence confidently identified.
```

False positives will kill trust faster than sparse output.

## Acceptance

Golden tests include:

- valid impact;
- unrelated neighbor not flagged;
- relation with no propagation rule;
- multiple possible paths;
- retired target.

---

# 9. Milestone 6 — First real-project trial

Run A Little Diff against recent commit ranges in a project whose decisions and assumptions are already understood.

For each result, label manually:

```text
useful
correct but obvious
incorrect
unsupported
missing an important consequence
```

Record especially:

> Did this expose something I had not consciously reconsidered?

Do not change architecture before collecting these cases.

## Initial success gate

Continue investment if the tool repeatedly produces at least one of:

- a missed stale assumption;
- a decision worth reconsidering;
- a useful clarification of why a change mattered;
- a false "impact" that reveals a needed relation-semantics rule.

The experiment can succeed by teaching us what the representation lacks.

---

# 10. Milestone 7 — Optional Ollama semantic classifier

Only add this after deterministic reports exist.

## First model task

Classify a bounded before/after pair as:

```text
revision
world_update
refinement
contradiction
same
unknown
```

with evidence IDs.

## Requirements

- Pydantic schema;
- JSON-schema-constrained output;
- temperature 0;
- timeout;
- explicit model name in report;
- inference labeled `model`, never `deterministic`;
- graceful operation when Ollama is unavailable.

## Initial benchmark

Compare at least:

```text
qwen3:8b
qwen3:14b
```

Optionally:

```text
gpt-oss:20b
```

on a small manually labeled corpus.

Do not select the model by generic benchmark reputation.

Select it by **A Little Diff task performance**.

---

# 11. V0.1 — model-assisted explanations

Once classification is stable, allow a model to write a concise explanation from an already validated support path.

Input must contain:

```text
changed record
target record
typed path
evidence
deterministic effect
```

The model is not asked to invent the path.

Example:

```text
Deterministic:
C1 superseded; D1 isMotivatedBy C1.

Model task:
Explain in one or two sentences why D1 deserves reconsideration.
```

Every generated explanation remains secondary to the structured path.

---

# 12. V0 exit criteria

V0 is complete when:

- [x] arbitrary Git refs can be loaded;
- [x] MOOSEDev snapshots normalize deterministically;
- [x] structural changes are correctly classified;
- [x] explicit supersessions/retractions render cleanly;
- [x] conservative downstream impact works for a verified relation subset;
- [x] every reported consequence carries a support path/evidence;
- [x] CLI has console and JSON output;
- [x] model use is optional;
- [x] at least one real-project trial has been manually evaluated (see [`docs/V0_EVALUATION_REPORT.md`](V0_EVALUATION_REPORT.md));
- [x] a small golden corpus protects against regression (49 passing tests);
- [x] documentation states known limitations.

Do not declare V0 complete merely because the CLI runs.

---

# 13. V1 — Truth maintenance

V1 should begin only if V0 demonstrates that consequence analysis is useful.

## Main goal

Distinguish:

```text
changed upstream premise
```

from:

```text
downstream conclusion actually lost support
```

## Add

```text
Justification
SupportSet
support status
```

Potential statuses:

```text
fully_supported
support_degraded
unsupported
support_unknown
```

## New reports

```text
SUPPORT DEGRADED

Decision D previously had two known justifications.
One disappeared; one remains active.
```

```text
SUPPORT LOST

No known active justification remains for Decision D.
```

## Research question

Can MOOSEDev's current relationships be mapped reliably enough to support sets, or must A Little Diff introduce additional explicit support metadata?

Answer this empirically.

---

# 14. V1.5 — Semantic identity across independently expressed claims

Only here introduce embeddings if needed.

## Use case

Same premise expressed differently at two states/sources with no stable shared ID.

Pipeline:

```text
local embeddings
  ↓
candidate pairs
  ↓
semantic judge
  ↓
same / refine / related / distinct
```

Initial embedding candidate:

```text
qwen3-embedding:0.6b
```

## Evaluation requirement

Measure:

- candidate recall;
- identity precision;
- false merge rate.

False identity merges are especially dangerous because they fabricate revision history.

---

# 15. V2 — Reopened decisions and minimal explanation

## QOC-inspired model

Add:

```text
Question
Option
Criterion
```

Connect accepted decisions to the question they answered and criteria that mattered.

## Feature: reopen

```text
Criterion changed
      ↓
Question may be unsettled again
      ↓
previous options re-evaluated
```

## Feature: minimal reconciliation

Given a changed decision:

```text
Which smallest set of changed project facts explains
why the new decision makes sense?
```

This should eventually power concise re-entry reports.

---

# 16. V2 — Contradiction diagnosis

Move beyond:

```text
"Docs and decision graph disagree."
```

Toward:

```text
Minimal conflicting set:
P17
P31
P42
```

Provide candidate repair operations without applying them.

Possible sources:

```text
recorded knowledge
docs
requirements
code-derived facts
```

All evidence must remain explicit.

---

# 17. V3 — Multi-artifact rationale adapter

Inspired by ARGUS.

## Inputs

```text
commit
PR
issue
review comments
docs
ADRs
code comments
```

## Pipeline

```text
retrieve related artifacts
        ↓
extract evidence-bearing rationale fragments
        ↓
classify:
goal / need / alternative / criterion / constraint / evidence
        ↓
normalize
        ↓
compare epistemic states
```

Do not concatenate all artifacts directly into one LLM call.

Keep extraction and reasoning separable and auditable.

---

# 18. V3 — Epistemic trajectories

Instead of only:

```text
A → B
```

support:

```text
A → B → C → D → E
```

Potential findings:

```text
RECURRENT REVERSAL
This architectural choice has flipped three times.

UNSTABLE ASSUMPTION
This external-system premise has changed four times in six months.

STABLE DECISION
Surrounding constraints changed repeatedly, but this decision
remained supported throughout.

REOPEN LOOP
The same design question has reopened after each dependency update.
```

This could be one of the strongest long-term uses of the accumulated graph.

---

# 19. Explicitly deferred work

Until evidence says otherwise, do **not** prioritize:

- web application;
- hosted SaaS;
- user accounts;
- real-time GitHub bot;
- automatic write-back to MOOSEDev;
- generalized ontology editor;
- custom vector database;
- custom model training;
- fine-tuning;
- agent swarm;
- background daemon;
- IDE extension;
- full theorem prover;
- enterprise policy layer.

Most can be added later if the epistemic primitive proves useful.

---

# 20. Risk register

## Risk: graph quality limits output

If source knowledge is sparse or wrong, A Little Diff cannot manufacture trustworthy consequences.

**Response:** expose evidence and uncertainty; measure graph coverage.

## Risk: too many false impacts

**Response:** conservative typed propagation; never use generic reachability as impact.

## Risk: model inference sounds more certain than evidence

**Response:** typed epistemic status; schema-constrained results; evidence IDs; inferred labels.

## Risk: tool repeats what the developer already knows

**Response:** evaluate "novel useful consequence" explicitly, not only correctness.

## Risk: RDF/MOOSEDev design leaks into core

**Response:** adapter contract and normalized domain model from the first implementation.

## Risk: overbuilding research ideas

**Response:** research sections are a design reservoir, not the V0 backlog.

---

# 21. Recommended first issue sequence

A coding agent could reasonably execute these in order:

1. Create Python package + Typer CLI.
2. Add Git-ref resolver.
3. Add file-at-ref loader.
4. Add MOOSEDev N-Quads fixture.
5. Define core Pydantic domain models.
6. Implement MOOSEDev state normalization.
7. Add state inspection command for debugging.
8. Implement structural record diff.
9. Implement lifecycle/supersession collapsing.
10. Add JSON report.
11. Add Rich console report.
12. Define verified propagation-policy schema.
13. Implement one-hop impact analysis.
14. Add golden impact tests.
15. Run first real-project comparison.
16. Write evaluation cases from observed failures.
17. Only then add optional Ollama provider.
18. Benchmark bounded semantic classifications.
19. Decide whether V0 needs semantic classification at all.
20. Revisit V1 architecture using actual evidence.

---

# 22. The development decision rule

Whenever a proposed feature appears, ask:

> **Does this help us discover, validate, explain, or act on a changed project belief?**

If not, it is probably outside the current project.

And whenever the system itself becomes elaborate, remember the name:

> **A Little Diff.**

The implementation should earn complexity rather than assume it.
