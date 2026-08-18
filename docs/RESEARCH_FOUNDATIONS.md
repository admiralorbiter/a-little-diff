# A Little Diff — Research Foundations

## Executive synthesis

A Little Diff sits at the intersection of several older and newer research traditions.

No one tradition directly yields the proposed developer tool. Together, however, they provide a strong intellectual architecture:

```text
belief revision
     │
     ├── how should a knowledge state change?
     │
truth maintenance
     │
     ├── what conclusions still have support?
     │
semantic differencing
     │
     ├── which representational changes alter meaning?
     │
change-impact analysis
     │
     ├── where should changed meaning propagate?
     │
design rationale
     │
     ├── what questions/options/criteria produced decisions?
     │
model reconciliation
     │
     ├── what is the smallest explanation of changed behavior?
     │
provenance
     │
     ├── why and where did a claim come from?
     │
multi-artifact rationale mining
     │
     └── where is the missing "why" actually recorded?
```

The strongest research-guided product decision is therefore:

> A Little Diff should be a structured truth/change-maintenance system with model-assisted interpretation, not a free-form LLM summarizer.

---

# 1. MOOSEDev: the immediate substrate

**James Adam, "Ontology-Grounded Project Memory for Coding Agents" (2026).**

MOOSEDev gives coding agents a structured, ontology-grounded project memory containing architectural decisions, lessons, constraints, rationales and related information records. The records carry lifecycle status, provenance and supersession links.

The system also includes a temporal Git-history bootstrap intended to reconstruct decision history with real chronology.

### Why it matters

A Little Diff needs two things that are expensive to invent well:

1. a normalized representation of project knowledge;
2. identity and lifecycle across time.

MOOSEDev already provides both.

### Feature/design implications

**Use now**

- Make MOOSEDev the first adapter.
- Treat `.moosedev/kg.nq` as a versioned epistemic snapshot.
- Reuse stable record identities and explicit lifecycle transitions.
- Preserve its evidence-first, symbolic-primary philosophy.

**Do not inherit unnecessarily**

- Do not make A Little Diff depend on the proprietary MOOSE engine.
- Do not couple the core diff representation to RDF.
- Do not assume all future sources will be MOOSEDev.

**Potential future upstream contribution**

If the experiment proves useful, a narrow MOOSEDev primitive such as:

```text
diff_knowledge_state(A, B)
```

could belong upstream, while A Little Diff remains the higher-level consequence/reconciliation product.

**Sources**

- Paper: https://arxiv.org/abs/2608.13662
- Repository: https://github.com/Trivyn/moosedev

---

# 2. AGM belief revision: a vocabulary for knowledge change

**Carlos E. Alchourrón, Peter Gärdenfors, David Makinson (1985), "On the Logic of Theory Change: Partial Meet Contraction and Revision Functions."**

The AGM tradition formalizes rational change to a knowledge/belief set, especially operations such as expansion, contraction, and revision.

### Why it matters

A project-state diff needs something richer than:

```text
added
removed
changed
```

The important distinction is how the project's epistemic commitment changed.

### Product translation

Potential semantic change classes:

```text
EXPANSION
new accepted knowledge

CONTRACTION
knowledge withdrawn

REVISION
old belief replaced after new information

REFINEMENT
old claim retained but narrowed or made more precise
```

Do not try to implement AGM postulates literally in V0.

The practical value is a better conceptual taxonomy and a reminder that knowledge revision should preserve as much justified existing structure as possible.

### Later question inspired by AGM

When a contradiction appears, which beliefs should be given up while disturbing the least well-supported project knowledge?

**Source**

- DOI: https://doi.org/10.2307/2274239
- Cambridge record: https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/on-the-logic-of-theory-change-partial-meet-contraction-and-revision-functions/7ED837BAD5FB6D9A7C77906D73527F9C

---

# 3. Katsuno–Mendelzon: world update vs belief revision

**Hirofumi Katsuno and Alberto O. Mendelzon, "On the Difference Between Updating a Knowledge Base and Revising It."**

Their central distinction is unusually valuable for A Little Diff:

- **update**: the represented world changed;
- **revision**: better information arrived about a world that was assumed not to have changed.

### Example

```text
BEFORE
"The vendor API cannot return teacher attendance."

AFTER
"The vendor API returns teacher attendance."
```

Those states alone do not tell us what happened.

#### World update

The vendor shipped a new capability.

Consequence:

> Architecture must adapt to a changed external dependency.

#### Belief revision

The capability existed, but the project misunderstood it.

Consequence:

> Decisions made under the old premise may have been unnecessarily constrained from the beginning.

That difference is extremely meaningful for retrospection.

### Feature implication

Add a semantic classification field:

```python
change_origin:
    world_update
    belief_revision
    unclear
```

This may initially be model-assisted and evidence-bound.

Never force the classification when evidence is insufficient.

**Source**

- https://doi.org/10.1017/CBO9780511526664.007
- https://www.cambridge.org/core/books/abs/belief-revision/on-the-difference-between-updating-a-knowledge-base-and-revising-it/8ADFFF65FA776C21E8646D6F4D2434AB

---

# 4. Assumption-Based Truth Maintenance Systems: the consequence engine

Work by **Johan de Kleer** and the broader Truth Maintenance System tradition is one of the most important conceptual foundations for the project.

An Assumption-Based Truth Maintenance System (ATMS) tracks the sets of assumptions under which conclusions hold, enabling derived results to be maintained as assumptions change.

### Why it matters

A naive blast-radius system would do:

```text
A changed
  ↓
A links to B
  ↓
B links to C
  ↓
flag B and C
```

That creates noise.

Truth maintenance encourages a stronger question:

> **Does the downstream conclusion still have a valid justification?**

Example:

```text
Premise A ─┐
           ├── supports Decision D
Premise B ─┘
```

If A is retracted but B remains sufficient, then:

```text
Decision D is still supported.
```

The useful report is not:

> Decision D affected.

It is:

> One supporting premise changed, but Decision D remains justified by Premise B.

If no sufficient support set remains:

> Decision D is now unsupported and should be reconsidered.

### Future domain model

```text
Assumption
Justification
SupportSet
DerivedClaim
```

### Future killer operations

```text
Why do we believe X?
What supports X?
What became unsupported?
What remains supported for another reason?
If X disappears, what loses all support?
```

### Scope warning

Do **not** build a complete ATMS in V0.

The near-term lesson is simply to preserve enough relationship semantics that V1 can distinguish:

```text
reachable
```

from:

```text
actually dependent
```

**Sources**

- de Kleer, "A General Labeling Algorithm for Assumption-Based Truth Maintenance": https://new.aaai.org/Library/AAAI/1988/aaai88-034.php
- Morris & Nado, "Representing Actions with an Assumption-Based Truth Maintenance System": https://vvvvw.aaai.org/Library/AAAI/1986/aaai86-003.php

---

# 5. Logical / semantic difference: meaning rather than representation

**Boris Konev, Michel Ludwig, Dirk Walther, Frank Wolter (2014), "The Logical Difference for the Lightweight Description Logic EL."**

A key ontology-versioning idea is that two knowledge bases can be compared not merely by their axioms but by the **queries for which their answers differ**.

### Why it matters

Consider:

```text
14 RDF triples changed.
```

That does not imply 14 meaningful changes.

A Little Diff should eventually distinguish:

```text
STRUCTURAL DIFF
what records/relations changed

EPISTEMIC DIFF
what accepted project claims changed

LOGICAL DIFF
what relevant conclusions or query answers changed
```

This creates the equivalent of "ignore whitespace" for project knowledge.

### Important future output

```text
SEMANTIC NO-OP

The representation changed, but none of the configured
project questions receive a different answer.
```

Or:

```text
ONE RECORD CHANGED

but 11 downstream project questions now receive
different answers.
```

### "Witnesses"

Semantic differencing also motivates concrete witnesses:

```text
Previously impossible:
  automated attendance → dashboard

Now possible:
  Pathful attendance → import → dashboard
```

These witnesses may be far more understandable than abstract graph output.

**Sources**

- https://arxiv.org/abs/1401.5850
- Related survey on ontology inseparability: https://arxiv.org/abs/1804.07805

---

# 6. Model reconciliation: explain the smallest necessary change

**Chakraborti, Sreedharan, Zhang, Kambhampati (IJCAI 2017), "Plan Explanations as Model Reconciliation: Moving Beyond Explanation as Soliloquy."**

The model-reconciliation view treats explanation as updating the human's model enough that the system's behavior makes sense.

### Why it matters

A Little Diff should not dump every changed node.

Instead it can eventually answer:

> What is the **smallest epistemic patch** needed to understand why the plan changed?

Example:

```text
WHY DID WE REMOVE MANUAL ATTENDANCE ENTRY?

Only two changed premises are required:

1. Pathful now supplies attendance.
2. The data arrives before dashboard refresh.

Together these invalidate the original need for manual entry.
```

That is cognitively much better than displaying 37 graph changes.

### Future feature

```bash
alittlediff explain A..B --decision "manual attendance"
```

Output:

```text
Minimal reconciliation:
  + premise 17
  ~ premise 22

These changes are sufficient to explain the new decision.
```

### Product lesson

Optimize explanations for **minimal sufficient understanding**, not exhaustiveness.

**Source**

- https://www.ijcai.org/proceedings/2017/23

---

# 7. QOC design rationale: changed premises should reopen questions

**MacLean, Young, Bellotti, Moran (1991), "Questions, Options, and Criteria: Elements of Design Space Analysis."**

QOC represents design rationale using:

- **Questions** — the design issues;
- **Options** — candidate answers;
- **Criteria** — dimensions used to assess the options.

### Why it matters

A changed premise does not always mean:

> Decision X is now wrong.

Sometimes the more appropriate output is:

> **Question X should be reopened.**

Example:

```text
QUESTION
How should external coordinators authenticate?

OPTIONS
A. local credentials
B. Google SSO

CRITERIA
C1. external domains supported
C2. low support burden
C3. no Workspace dependency
```

If C1 changes, a previously rejected option may become viable.

### Future feature

```text
REOPENED QUESTION

How should external coordinators authenticate?

Reason:
Criterion C1 changed.

Previously rejected option B may now be viable.
```

### Architecture implication

Reserve room in the normalized model for:

```text
Question
Option
Criterion
```

but do not require them in V0.

**Source**

- https://doi.org/10.1080/07370024.1991.9667168

---

# 8. Requirements change-impact analysis: relations need propagation semantics

Research on requirements change-impact analysis demonstrates a practical danger:

> If every relation simply propagates "affected," impact analysis explodes into false positives.

Work by Göknil and colleagues formalizes relation meanings and change types so propagation can be more selective.

### Why it matters

A Little Diff should not implement:

```python
for node in graph.neighbors(changed):
    mark_affected(node)
```

Instead relation types need semantics.

Possible future policy:

```yaml
isMotivatedBy:
  target_retracted: support_lost
  target_revised: reconsider
  propagation: high

constrains:
  target_retracted: constraint_relaxed
  target_revised: reconsider
  propagation: high

concerns:
  source_changed: inspect
  propagation: medium

similarTo:
  propagation: none
```

### V0 implication

Whitelist a very small number of relations.

Prefer missed impacts to a noisy "everything is affected" report while learning the correct semantics.

**Sources**

- "Change impact analysis for requirements: A metamodeling approach": https://doi.org/10.1016/j.infsof.2014.03.002
- "A Rule-Based Change Impact Analysis Approach in Software Architecture for Requirements Changes": https://arxiv.org/abs/1608.02757

---

# 9. Provenance: every conclusion needs both "why" and "where"

**Buneman, Khanna, Tan (2001), "Why and Where: A Characterization of Data Provenance."**

The work distinguishes:

- **why-provenance** — source information that influenced why a result exists;
- **where-provenance** — where the contributing information came from.

### Why it matters

A Little Diff should answer both.

```text
WHY IS THIS DECISION FLAGGED?

Constraint C changed.
Decision D is motivated by C.
Plan P depends on D.
```

And:

```text
WHERE DID C COME FROM?

commit abc123
PR #217
docs/pathful.md
MOOSEDev record <IRI>
```

### Design rule

A prose explanation without a structured support/evidence record should be considered incomplete.

Suggested internal shape:

```json
{
  "claim": "Manual attendance should be reconsidered.",
  "support_path": ["constraint:c17", "decision:d4"],
  "evidence": [
    {
      "source_type": "git",
      "commit": "abc123",
      "path": "..."
    }
  ]
}
```

**Source**

- https://doi.org/10.1007/3-540-44503-X_20
- University of Edinburgh record: https://www.research.ed.ac.uk/en/publications/why-and-where-a-characterization-of-data-provenance

---

# 10. Contradiction diagnosis: do not merely say "these disagree"

Constraint diagnosis and **Minimal Correction Subset (MCS)** research studies minimal groups of constraints whose removal can restore consistency.

### Why it matters

Suppose:

```text
P17: External coordinators cannot use SSO.
P31: All coordinators authenticate through SSO.
P42: External coordinators are coordinators.
```

A generic model could say:

> There seems to be a contradiction.

A better system says:

```text
MINIMAL CONFLICTING SET
{P17, P31, P42}

Potential repairs:
- retract P17
- refine P31
- refine P42
```

### Future feature

```bash
alittlediff diagnose
```

This belongs well after V0, but the underlying principle should influence data design now:

> Preserve precise identities, types and provenance so future inconsistency diagnosis is possible.

**Source**

- "Premise Set Caching for Enumerating Minimal Correction Subsets": https://ojs.aaai.org/index.php/AAAI/article/view/12213

---

# 11. Argumentation: not every disagreement has one immediate truth

**Phan Minh Dung (1995), "On the Acceptability of Arguments and its Fundamental Role in Nonmonotonic Reasoning, Logic Programming and n-Person Games."**

Abstract argumentation represents arguments and attack relationships, then reasons about which sets of arguments can be accepted.

### Why it matters

Real software architecture often contains genuine unresolved disagreement:

```text
Argument A:
local-first improves privacy and resilience

Argument B:
cloud-first reduces operational burden

Argument C attacks A:
local models do not meet quality threshold

Argument D attacks C:
quality threshold only matters for high-risk classifications
```

A Little Diff should eventually be capable of preserving contested reasoning rather than using an LLM to prematurely synthesize it into one fake consensus.

### Future use

- contested architectural choices;
- unresolved hypotheses;
- conflicting evidence;
- alternate support chains.

**Source**

- https://doi.org/10.1016/0004-3702(94)00041-X

---

# 12. ARGUS: rationale is fragmented across development artifacts

**Sun, Saha, De Silva, Mastropaolo, Chaparro (2026), "Fine-grained Multi-Document Extraction and Generation of Code Change Rationale."**

The study examines rationale across commits, issues, pull requests, reviews and code documentation.

Its important finding for A Little Diff is that **no single artifact consistently contains the complete rationale**. Goals are often captured differently from needs and alternatives.

ARGUS therefore uses a multi-document process:

1. retrieve related artifacts;
2. identify rationale-bearing sentences;
3. synthesize structured rationale components.

### Why it matters

The future generic adapter cannot assume:

```text
commit message == why
```

Nor should it concatenate an entire issue/PR/repository into one giant model prompt.

The ARGUS architecture supports a better staged pattern:

```text
retrieve
   ↓
filter rationale-bearing evidence
   ↓
classify / normalize
   ↓
reason over compact evidence
```

That approach fits local models particularly well.

### Future adapter implications

Potential evidence sources:

```text
commit message
diff
linked PR
linked issue
review comments
ADR
Javadoc / docstring
code comments
project docs
```

Every extracted rationale statement should retain a backlink to its source artifact.

**Source**

- https://arxiv.org/abs/2604.10345

---

# 13. Code review as decision-making: the human task is model construction

**Heander, Söderberg, Rydenfält (2026), "Code review as decision-making - building a cognitive model from the questions asked during code review."**

The study uses think-aloud code review sessions and models review as an iterative decision-making process involving understanding the implementation, assessing the change, assessing the implementation, and deciding what to do next.

### Why it matters

This reinforces the product premise that a reviewer is not merely scanning lines.

The reviewer is maintaining and updating a mental model of the system.

A Little Diff can reduce the cost of the transition:

```text
old mental model
      ↓
      ?   ← today's cognitive burden
      ↓
new mental model
```

by explicitly presenting the small number of model changes and consequences that deserve attention.

### UX implication

Optimize for:

- orientation;
- reconsideration;
- re-entry;
- prioritized questions.

Do not optimize the main report for maximum information density.

**Source**

- https://link.springer.com/article/10.1007/s10664-025-10791-2

---

# 14. Ollama and local models: a useful interpretation layer

Ollama currently supports:

- JSON-schema-constrained structured outputs;
- Pydantic-compatible schemas;
- embeddings;
- tool/function calling;
- OpenAI-compatible APIs.

### Why it matters

A Little Diff can keep inference local while demanding typed model outputs.

Example:

```python
class ChangeJudgment(BaseModel):
    transition: Literal[
        "same",
        "expansion",
        "contraction",
        "revision",
        "world_update",
        "refinement",
        "contradiction",
        "uncertain",
    ]
    rationale: str
    evidence_ids: list[str]
```

The model fills a constrained judgment. It does not control graph state.

### Initial recommendation

```text
qwen3:8b
```

for bounded semantic classification.

Evaluate a stronger local tier such as:

```text
qwen3:14b
gpt-oss:20b
```

rather than assuming larger is always needed.

Embeddings should wait until semantic identity/alignment is required across sources without stable IDs.

At that point:

```text
qwen3-embedding:0.6b
```

is an attractive initial candidate for local candidate generation.

**Sources**

- Structured outputs: https://docs.ollama.com/capabilities/structured-outputs
- Embeddings: https://docs.ollama.com/capabilities/embeddings
- OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
- Qwen3: https://ollama.com/library/qwen3
- Qwen3 Embedding: https://ollama.com/library/qwen3-embedding

---

# 15. Research-to-roadmap matrix

| Research area | Product lesson | Earliest sensible stage |
|---|---|---|
| MOOSEDev | Reuse typed, versioned knowledge instead of inferring everything | V0 |
| Belief revision | Give semantic names to knowledge changes | V0/V1 |
| Update vs revision | Distinguish "world changed" from "we learned we were wrong" | V0 optional model layer |
| Provenance | Every result must carry evidence | V0 |
| Requirements impact | Typed edges need typed propagation | V0 simple rules |
| Truth maintenance | Reachability is not justification; ask what remains supported | V1 |
| Semantic/logical difference | Ignore representational churn that changes no answers | V1/V2 |
| Model reconciliation | Explain the smallest sufficient epistemic patch | V2 |
| QOC | Changed criteria can reopen settled design questions | V2 |
| Contradiction diagnosis | Return minimal conflicts / repair candidates | V2/V3 |
| Argumentation | Preserve genuinely contested reasoning | V3 |
| ARGUS | Rationale lives across multiple artifacts | V3 adapters |
| Code-review cognition | Reports should support human model rebuilding | Every stage |

---

# 16. Research-derived invariants

The following should be treated as architectural principles unless experiments disprove them.

## R1 — Evidence or silence

A Little Diff should prefer:

> "Unable to determine whether this was revision or world update."

over an unsupported confident interpretation.

## R2 — Reachability is not dependency

A graph path is not sufficient evidence that a downstream item is invalidated.

## R3 — Current truth and historical truth are different queries

Retired knowledge should remain queryable for explanation and lineage without polluting the authoritative working set.

## R4 — Changed representation does not imply changed meaning

A structural graph diff is input to the epistemic diff, not the epistemic diff itself.

## R5 — Meaningful impact can be small in structure and large in consequence

Prioritize consequence over file/node counts.

## R6 — Explanation should be minimal but auditable

Show the smallest useful change set, with the ability to drill down to complete evidence.

## R7 — Models are sensors

Model output is typed, validated and labeled as inferred; it never silently mutates authoritative state.

## R8 — Questions deserve first-class status

The system should eventually know not only what decision was made, but what question that decision answered.

---

# 17. Open research questions for this project

These are more valuable than adding features prematurely.

1. **Can useful epistemic changes be recovered from the MOOSEDev graph alone, or is Git/code context usually required?**
2. **Which relation types have sufficiently reliable impact semantics to propagate automatically?**
3. **Can small local models reliably distinguish refinement, revision, contradiction and world update with grounded evidence?**
4. **What is the false-positive tolerance for "you should reconsider this" before the tool becomes annoying?**
5. **How often does a changed premise leave a downstream decision fully supported by another justification?**
6. **What evidence is required for users to trust a reported consequence?**
7. **Is the best human unit a changed belief, a changed question, or a changed decision?**
8. **Can we define a useful "epistemic semantic no-op" for ordinary software projects?**
9. **Does a minimal-reconciliation explanation improve re-entry compared with a complete change report?**
10. **How should confidence be calibrated when the evidence itself is incomplete or contradictory?**

These questions should become experiments before they become architecture.
