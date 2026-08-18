# A Little Diff — Evaluation Strategy

## 1. Why evaluation matters unusually early

A Little Diff can produce outputs that *sound* insightful while being useless or wrong.

That makes ordinary software tests necessary but insufficient.

The project needs to evaluate at least four separate properties:

```text
structural correctness
semantic correctness
impact correctness
human usefulness
```

A model can generate excellent prose around a bad impact path.

A graph algorithm can generate a perfectly valid path that is cognitively useless.

Evaluation must therefore stay close to the actual product question:

> **Did this help the developer update their mental model correctly?**

---

# 2. Evaluation layers

## Layer A — Parser and structural correctness

Deterministic.

Examples:

- correct record identity;
- correct lifecycle status;
- correct supersession;
- correct relation delta;
- no accidental duplicate records.

These should be standard unit/golden tests.

## Layer B — Epistemic classification

Examples:

- revision vs world update;
- refinement vs contradiction;
- semantic no-op vs meaningful revision.

Some classifications can be deterministic; others will be model-assisted.

Use a manually labeled corpus.

## Layer C — Impact correctness

For each changed premise:

```text
Which downstream records genuinely deserve reconsideration?
```

This is the most important engine metric.

## Layer D — Human value

Ask:

```text
Did the report reveal something useful?
Did it change what I inspected?
Did it shorten re-entry?
Was the explanation trustworthy?
Was it noisy?
```

---

# 3. Golden corpus

Start tiny and curated.

A test case should contain:

```yaml
name: attendance-capability-change

base_state: ...
head_state: ...

expected_changes:
  - type: superseded
    before: constraint.manual_attendance
    after: constraint.pathful_attendance

expected_impacts:
  - target: decision.manual_attendance_workflow
    effect: reconsider

not_expected_impacts:
  - decision.unrelated_authentication

semantic_label:
  type: world_update
  evidence: ...
```

Every real-project failure can become a new golden case.

This matters more than collecting hundreds of synthetic cases early.

---

# 4. Structural metrics

Track:

```text
record delta precision
record delta recall
supersession precision
supersession recall
relation-delta precision
relation-delta recall
```

For MOOSEDev stable identities these should approach deterministic correctness.

Any errors here should be fixed before evaluating LLM quality.

---

# 5. Impact metrics

## Impact precision

Of everything A Little Diff says deserves attention, how much really does?

This should be favored over aggressive recall early.

A noisy metacognitive assistant is easy to ignore.

## Impact recall

Of the consequences a knowledgeable human identifies, how many does the system surface?

## Unsupported-impact rate

Especially important:

```text
reported impact with no defensible typed/evidence path
-------------------------------------------------------
all reported impacts
```

Target should be extremely low.

## Path validity

Does the relation sequence actually justify the claimed effect?

This is separate from merely checking that the edges exist.

---

# 6. Evidence metrics

## Evidence coverage

Percentage of reported conclusions containing source evidence.

For high-level impact claims the target should be 100%.

## Evidence sufficiency

Human rating:

```text
0 = does not support claim
1 = weak / indirect
2 = sufficient
3 = strong / direct
```

## Provenance completeness

Can the user get from a reported conclusion back to:

```text
record
commit
artifact/path
```

where available?

---

# 7. Semantic-classification benchmark

Create a hand-labeled set of before/after pairs.

Labels:

```text
same
expansion
contraction
revision
world_update
refinement
contradiction
unknown
```

For each model record:

```text
model
quantization/version
prompt version
schema version
accuracy
per-class precision/recall
unknown rate
evidence compliance
latency
```

Do not primarily optimize for raw accuracy if the model achieves it by refusing everything or overusing one class.

---

# 8. Local model experiment

Initial candidates:

```text
qwen3:8b
qwen3:14b
gpt-oss:20b
```

Questions:

1. Is 8B good enough for bounded classification?
2. Does the larger model reduce the *dangerous* errors?
3. Which classes are unstable?
4. Does adding commit evidence improve classification?
5. Does supplying only structured knowledge outperform supplying the raw code diff?
6. Does asking the model for evidence IDs reduce unsupported rationales?

### Do not trust model confidence at face value

A model saying:

```text
confidence: 0.94
```

does not mean its probabilities are calibrated.

Use empirical disagreement and error patterns for routing.

---

# 9. Possible escalation experiment

Compare:

```text
single small model
```

against:

```text
small model
  ↓ only on disagreement/ambiguity
strong local model
```

Measure:

```text
quality
total model calls
runtime
resource use
dangerous-error rate
```

The routing criterion should be grounded in observable uncertainty:

- conflicting evidence;
- classifier disagreement;
- missing required evidence;
- high-impact proposed consequence.

---

# 10. Semantic-no-op experiment

Create pairs where the graph representation changes but relevant answers do not.

Examples:

- title wording changes;
- rationale formatting changes;
- equivalent relation organization;
- metadata-only changes.

Ask:

> Can A Little Diff suppress these from the primary report while retaining them in verbose output?

This tests whether the project is actually a semantic diff rather than a prettier RDF diff.

---

# 11. Truth-maintenance experiment for V1

Construct:

```text
A ─┐
   ├─► Decision D
B ─┘
```

Retract A.

Correct output:

```text
D remains supported by B.
```

Then retract B.

Correct output:

```text
D lost all known support.
```

This simple case should become a foundational regression test before building a complex support engine.

---

# 12. Reopened-question experiment for V2

Represent:

```text
Question Q
Options O1 / O2
Criteria C1 / C2
Decision chooses O1
```

Change C1.

Human expected judgment:

```text
Q should reopen
```

or:

```text
Q remains settled
```

Measure whether the engine can explain which changed criterion crossed the decision boundary.

---

# 13. Minimal-reconciliation evaluation

Given a changed decision and many changed premises, manually identify the smallest sufficient explanatory subset.

Compare system output on:

```text
correctness
minimality
human comprehensibility
```

A complete explanation containing 20 irrelevant facts should score worse than a 2-premise explanation that is sufficient.

---

# 14. Human usefulness log

For personal real-project trials, keep a lightweight CSV/JSONL record.

Suggested fields:

```text
date
repo
range
reported_change_count
reported_impact_count

novel_useful_findings
correct_but_obvious
false_impacts
missed_impacts

did_reconsider_decision: bool
did_change_plan: bool
did_open_file_or_issue: bool

notes
```

The project's strongest early metric may simply be:

```text
Useful surprises per run
```

where a useful surprise means:

> The system surfaced a consequence the developer had not already consciously accounted for.

---

# 15. Trust failure taxonomy

Label failures rather than treating all mistakes equally.

## T1 — structural hallucination

Claims a record/relation changed when it did not.

Highest severity.

## T2 — unsupported causal path

Edges exist but do not justify the claimed consequence.

High severity.

## T3 — semantic misclassification

Example: revision labeled world update.

Medium/high depending on consequence.

## T4 — over-propagation

Valid change, irrelevant downstream items flagged.

Primary annoyance risk.

## T5 — under-propagation

Misses a useful consequence.

Important but less trust-destroying early than T1/T2.

## T6 — poor explanation

Underlying result correct but prose unclear.

Lower severity.

## T7 — provenance failure

Correct claim cannot be audited back to evidence.

High severity for this product.

---

# 16. Definition of a trustworthy result

A reported finding should ideally have:

```text
WHAT changed
  ↓
typed source records

HOW it changed
  ↓
deterministic lifecycle or bounded semantic judgment

WHY target is affected
  ↓
typed propagation/support path

WHERE evidence came from
  ↓
provenance

EPISTEMIC STATUS
  ↓
asserted / derived / inferred / speculative
```

If one layer is missing, the UI should show the limitation rather than paper over it.

---

# 17. First evaluation gates

Before moving from V0 toward V1:

- deterministic structural diff must be reliable;
- impact false positives must be low enough that reports are not ignored;
- evidence coverage must be near-complete;
- at least a handful of real runs should generate useful reconsideration;
- model-assisted classification must outperform a simpler heuristic enough to justify its complexity.

Before V2:

- explicit support/justification modeling must demonstrably outperform simple graph traversal;
- users must care about "remains supported" versus "lost support."

Before multi-artifact ingestion:

- prove that missing rationale in the current source is a major quality bottleneck.

---

# 18. Success definition

The strongest outcome is not:

> A Little Diff accurately summarizes 95% of commits.

It is:

> **A Little Diff reliably points to the small number of project assumptions, decisions, or questions that a developer should reconsider after meaningful change—and can show exactly why.**

Everything in the evaluation system should eventually point back to that.
