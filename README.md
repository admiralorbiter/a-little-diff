# A Little Diff

> **Technical operation:** an *epistemic diff*  
> **Core question:** *What did this project believe before, what does it believe now, and what should we reconsider because of that change?*

A Little Diff is an experimental developer tool for comparing **project understanding**, not merely source files.

A normal Git diff can tell us:

- 12 files changed
- 423 lines added
- 87 lines removed

A Little Diff should instead be able to tell us:

- a constraint we previously treated as true no longer applies;
- an architectural decision has lost its original justification;
- a previously rejected option may now be viable;
- a plan or TODO was based on an assumption that changed;
- a conclusion remains valid even though one of its supporting premises disappeared;
- the world changed versus our understanding of the world changed;
- documentation, code, and recorded decisions now disagree.

The first implementation should be intentionally small. It should prove that an epistemic diff can reveal **one meaningful consequence of a change that a developer would otherwise have missed**.

---

## Project thesis

Software projects accumulate a model of reality:

- requirements;
- constraints;
- assumptions;
- architectural decisions;
- rationales;
- lessons;
- plans;
- unresolved questions;
- rejected alternatives.

Those things change over time, but conventional developer tooling primarily versions the **artifacts** that express them.

A Little Diff treats the project's evolving understanding as a first-class object that can itself be compared.

The long-term conceptual pipeline is:

```text
project state A
      │
      ▼
epistemic model A
      │
      ├────────────┐
      │            │
      │      epistemic diff
      │            │
      └────────────┤
                   ▼
             changed premises
                   │
                   ▼
            support / impact
                   │
                   ▼
        "what should we revisit?"
```

The important product distinction is:

> **A Little Diff should not be an LLM that summarizes a Git diff.**  
> It should be a structured change-analysis engine that uses models only where interpretation is genuinely ambiguous.

---

## Initial direction

The recommended first integration is **MOOSEDev**.

MOOSEDev already supplies much of the hard substrate:

- typed project knowledge;
- decisions, requirements, constraints, lessons, rationales, etc.;
- lifecycle status;
- explicit supersession and retraction;
- provenance;
- temporal Git-history bootstrap;
- an RDF knowledge graph;
- a canonical, version-controlled project-memory representation.

A Little Diff should initially build **beside MOOSEDev**, not fork it.

The core seam is:

```text
git ref A ─► .moosedev/kg.nq at A ─┐
                                    ├─► A Little Diff
git ref B ─► .moosedev/kg.nq at B ─┘
```

This lets the experiment use MOOSEDev's knowledge model without coupling the project to the proprietary MOOSE reasoning engine or requiring a source build of MOOSEDev.

Later, A Little Diff can support other adapters:

```text
MOOSEDev
ADRs
Markdown knowledge bases
GitHub issues / PRs
requirements systems
ordinary repositories
other structured project-memory systems
```

Git is an important source and transport, but it should not become the conceptual boundary of the project.

---

## Core design principles

1. **Evidence before prose.** Every reported epistemic change or consequence should carry traceable evidence.
2. **Models interpret; code maintains truth.** Deterministic graph and lifecycle rules do the bookkeeping. LLMs classify ambiguity and communicate results.
3. **Local-first, model-optional.** The deterministic engine must work without an LLM. Ollama is the preferred first model integration.
4. **Preserve uncertainty.** Inferred or speculative claims must never silently become asserted project truth.
5. **Meaning over textual churn.** Many structural changes may produce no epistemic change; a tiny artifact change may produce a large epistemic change.
6. **Typed propagation.** A graph edge does not automatically imply impact. Relationship semantics determine whether and how a change propagates.
7. **Do not overbuild V0.** No autonomous agent, vector database, giant ontology extension, or general repository inference is needed to prove the core idea.
8. **Source-independent core.** The diff engine should operate on normalized epistemic states, not MOOSEDev-specific objects.

---

## Example target experience

```bash
alittlediff HEAD~12..HEAD
```

Possible output:

```text
A LITTLE DIFF
3f991c → a88102

BELIEF SUPERSEDED

BEFORE
  Constraint:
  Teacher attendance must be entered manually.

AFTER
  Constraint:
  Pathful provides teacher attendance through its import.

CHANGE TYPE
  World update — likely
  The external system appears to have gained a capability.

AFFECTED

  → Manual attendance workflow
      justified by the old constraint

  → Teacher dashboard
      depends on the workflow

RECOMMENDATION

  Re-evaluate whether the manual attendance workflow
  remains necessary.

WHY THIS WAS FLAGGED

  Old constraint ─isMotivatedBy⁻¹→ Manual workflow
                 ─concerns→ Teacher dashboard

EVIDENCE
  commit abc123
  .moosedev record <...>
```

The report may eventually be much richer, but the experience should stay understandable.

---

## Documentation map

- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — purpose, product model, terminology, scope, non-goals, and long-term vision.
- [`docs/RESEARCH_FOUNDATIONS.md`](docs/RESEARCH_FOUNDATIONS.md) — research synthesis and the specific features or design rules it suggests.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — proposed technical architecture, data model, MOOSEDev seam, Ollama integration, and package layout.
- [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) — staged implementation plan with acceptance criteria and guardrails against premature complexity.
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — evaluation strategy, golden cases, model benchmarking, and product-level success measures.

---

## Current product vocabulary

| Term | Meaning |
|---|---|
| **A Little Diff** | Project/tool name. |
| **Epistemic state** | A normalized representation of what a project treats as true, chosen, constrained, unresolved, or justified at a point in time. |
| **Epistemic diff** | The meaningful change between two epistemic states. |
| **Premise** | A proposition, requirement, constraint, assumption, observation, or other knowledge item that can support downstream conclusions. |
| **Support path** | A traceable chain showing why a decision, plan, or conclusion depends on one or more premises. |
| **Impact** | A downstream item whose validity, justification, priority, or status should be reconsidered because an upstream epistemic change occurred. |
| **Revision** | Our understanding of an otherwise unchanged world changed. |
| **World update** | The external world itself changed, requiring our project model to catch up. |
| **Reopened question** | A previously settled design question whose premises or criteria changed enough to merit reconsideration. |

---

## First proof

The first proof should answer one question:

> **Does an epistemic diff surface a useful consequence of my own recent work that I failed to notice?**

If the answer is yes, continue.

If the answer is no, improve the representation and evaluation before adding features.

That criterion should remain more important than how impressive the architecture looks.
