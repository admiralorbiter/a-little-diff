# A Little Diff — Project Brief

## 1. Purpose

A Little Diff exists to help a developer understand **how a project's model of reality changed**.

The project begins with a simple dissatisfaction:

```text
git diff
```

is excellent at answering:

> What artifacts changed?

but much weaker at answering:

> What did we used to believe?  
> What do we believe now?  
> Why did that change?  
> Which decisions depended on the old belief?  
> Which plans, TODOs, or design questions should now be reconsidered?

A Little Diff is an attempt to make that second class of question computationally tractable.

---

## 2. Product statement

**A Little Diff computes epistemic diffs over evolving projects.**

An epistemic diff is a structured report of:

1. the propositions, constraints, decisions, assumptions, or other knowledge that changed;
2. the character of each change;
3. the evidence supporting the interpretation;
4. downstream decisions or plans whose justification may have changed;
5. conclusions that remain supported despite an upstream change;
6. unresolved or previously settled questions that should reopen.

The central product value is not exhaustive historical documentation.

It is **re-entry and reconsideration**:

> Tell me the few things I now need to think differently about.

---

## 3. Problem

Fast software development creates a mismatch between **artifact velocity** and **human model maintenance**.

A project can change substantially while the developer still carries an obsolete internal model:

- an API gained a capability;
- an earlier workaround is no longer necessary;
- a constraint disappeared;
- an architectural tradeoff changed;
- a requirement became obsolete;
- a plan remains on the roadmap after the premise that created it vanished;
- a rejected option became viable;
- documentation and code no longer agree;
- a decision remains correct, but for a different reason than before.

Traditional diffs expose the raw changes but require the human to reconstruct those consequences.

AI-generated PR summaries improve compression, but they generally still summarize **the change itself**.

A Little Diff focuses on **change in understanding and consequences of changed understanding**.

---

## 4. Working definition of an epistemic state

An epistemic state is not intended to mean "everything that can possibly be inferred from the repository."

For this project it means a bounded set of project knowledge such as:

```text
Premises
├── assumptions
├── observations
├── requirements
├── constraints
└── external facts

Reasoning / rationale
├── support relations
├── motivations
├── tradeoffs
├── consequences
└── evidence

Commitments
├── decisions
├── plans
├── accepted patterns
└── rejected alternatives

Open design state
├── questions
├── options
├── criteria
└── hypotheses
```

V0 does not need all of these types.

MOOSEDev's existing information records are sufficient to begin.

---

## 5. Change taxonomy

The initial structural taxonomy can stay small:

- **added**
- **retracted**
- **superseded**
- **status changed**
- **relation added**
- **relation removed**

The semantic taxonomy should eventually include:

### Expansion

Something new became part of the project's accepted knowledge without displacing an old belief.

### Contraction

A belief or commitment was withdrawn without necessarily being replaced.

### Revision

New evidence changed our understanding of a world that did not itself change.

Example:

```text
Before: "The API cannot provide X."
After:  "The API has always provided X; we had overlooked it."
```

### World update

The world itself changed and the project model was updated accordingly.

Example:

```text
Before: "The API cannot provide X."
After:  "Version 4 of the API now provides X."
```

### Refinement

The old statement was directionally correct but underspecified or too broad.

### Contradiction

Two simultaneously active statements cannot both be true under the relevant interpretation.

### Semantic no-op

The representation changed while the relevant project conclusions did not.

This taxonomy should be allowed to contain **uncertain** classifications. A Little Diff should prefer honest ambiguity over false certainty.

---

## 6. Consequences are the product

Detecting a changed premise is necessary but not sufficient.

The distinctive operation is:

```text
changed premise
     │
     ▼
what depended on it?
     │
     ▼
does that item still have support?
     │
     ├── yes ─► remain valid; explain why
     │
     └── no ──► reconsider / reopen
```

This implies a future distinction between a generic graph edge and a **justification relation**.

A relationship such as:

```text
Decision D isMotivatedBy Constraint C
```

should have different propagation semantics from:

```text
Decision D concerns Component X
```

The engine should never blindly mark every reachable graph node as affected.

---

## 7. The future killer questions

A Little Diff should eventually make the following questions easy:

```text
What changed in our understanding between these two refs?

What became unsupported?

What remains true for a different reason?

Which plans assume something that is no longer true?

Which old decisions deserve another look?

Which rejected options became viable?

What is the smallest set of changed premises needed
to explain why the plan changed?

Why do we still believe X?

What would become suspect if X were withdrawn?

Where did this belief come from?

Are the code, docs, and recorded decisions telling
different stories?

Which assumptions have repeatedly flipped over the
history of this project?
```

V0 should not implement all of these. They define the direction.

---

## 8. Relationship to MOOSEDev

### Why MOOSEDev is the right first substrate

MOOSEDev is unusually close to the representation A Little Diff needs:

- ontology-grounded information records;
- decisions, constraints, requirements, lessons, rationales, patterns and anti-patterns;
- explicit `supersedes` lifecycle behavior;
- retraction without deleting history;
- provenance;
- typed relationships;
- temporal bootstrap over Git history;
- canonical RDF project memory.

Its 2026 paper explicitly frames the project as structured, ontology-grounded long-term project memory for coding agents.

### Why not fork it first

MOOSEDev itself is open source, but its MOOSE neurosymbolic engine is proprietary. The public MOOSEDev repository states that building from source requires access to that engine, while releases are the supported route for outside users.

More importantly, A Little Diff's conceptual boundary should eventually be broader than MOOSEDev.

Therefore the preferred approach is:

```text
A Little Diff
    │
    ├── MOOSEDev adapter
    ├── future ADR adapter
    ├── future GitHub rationale adapter
    └── future generic project-state adapter
```

### Best initial seam

MOOSEDev version-controls a canonical project graph at:

```text
.moosedev/kg.nq
```

So V0 can reconstruct two epistemic snapshots directly through Git:

```bash
git show <A>:.moosedev/kg.nq
git show <B>:.moosedev/kg.nq
```

A Little Diff can parse those snapshots independently of the MOOSE runtime.

This is the smallest, cleanest experiment.

---

## 9. AI/model philosophy

A Little Diff should not place an LLM in charge of truth maintenance.

Preferred separation:

```text
DETERMINISTIC
- Git snapshot access
- RDF parsing
- stable identity
- lifecycle changes
- known relation semantics
- support traversal
- provenance
- validation

MODEL-ASSISTED
- semantic alignment
- refinement vs contradiction
- revision vs world update
- ambiguity classification
- concise explanations
- eventual rationale extraction
```

The rule is:

> **Models interpret uncertainty. Code maintains state and evidence.**

Every model-produced claim should be labeled by epistemic status, such as:

- asserted;
- structurally derived;
- model-inferred;
- speculative.

Model output must never silently become authoritative project memory.

---

## 10. Local-first model strategy

Ollama is the preferred first model integration.

Reasons:

- runs locally;
- supports structured JSON-schema outputs;
- supports Pydantic-friendly schemas;
- supports embeddings;
- provides OpenAI-compatible endpoints;
- allows easy model swapping;
- keeps experiments inexpensive;
- makes benchmarking small and large local models straightforward.

Initial recommendation:

```text
qwen3:8b     default semantic judge
qwen3:14b    optional stronger local judge
```

Later:

```text
qwen3-embedding:0.6b   candidate semantic alignment
gpt-oss:20b            stronger local reasoning tier
optional cloud provider  explicit escalation only
```

The provider must be abstracted so these recommendations can change without touching the diff engine.

---

## 11. V0 scope

V0 should support only repositories where two Git revisions contain MOOSEDev knowledge snapshots.

Input:

```bash
alittlediff <A>..<B>
```

V0 should:

1. retrieve both `.moosedev/kg.nq` files;
2. parse them;
3. normalize relevant information records;
4. identify structural lifecycle and relation changes;
5. render a human-readable report;
6. include evidence/provenance available from the graph and Git;
7. follow only a very small set of explicitly allowed relationships for downstream impact;
8. optionally use a local model to classify genuinely ambiguous semantic changes.

### V0 should not

- infer a full knowledge graph from arbitrary source code;
- use embeddings;
- run autonomous agents;
- alter MOOSEDev's graph;
- build a web UI;
- maintain a vector database;
- attempt general theorem proving;
- ingest every GitHub artifact;
- implement full AGM belief revision;
- implement a complete ATMS.

---

## 12. Long-term feature families

### Truth maintenance

Track support sets and identify whether a conclusion still has a valid justification after a premise changes.

### Reopened design questions

Represent Questions, Options, and Criteria so changed conditions can reopen choices previously considered settled.

### Semantic diff

Distinguish syntactic graph changes from changes in query answers or downstream entailments.

### Model reconciliation

Produce the smallest set of changed premises required to explain a changed decision or plan.

### Multi-artifact rationale

Combine commits, PRs, issues, reviews, ADRs, documentation, and code comments when rationale is fragmented.

### Contradiction diagnosis

Return a minimal conflicting set instead of merely announcing that "something disagrees."

### Epistemic trajectories

Analyze how beliefs and decisions move over time rather than only comparing two snapshots.

---

## 13. Product personality

The name **A Little Diff** is deliberate.

The project should not sound like an enterprise "AI knowledge intelligence platform."

It is a small, somewhat funny developer tool whose output can occasionally reveal something surprisingly important.

That tone can appear in the UI without sacrificing rigor:

```text
A LITTLE DIFF

One small thing changed.

Unfortunately, three decisions were standing on it.
```

The technical foundations can be formal; the experience should remain human.
