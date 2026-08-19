# Semantic Annotation Guide for Epistemic Transitions

This guide defines the formal taxonomy and decision criteria for labeling epistemic transitions in **A Little Diff (`alittlediff-bench`)**.

---

## 1. Core Principle: Lifecycle vs. Semantic Meaning

Knowledge management substrates (such as MOOSEDev) track graph **lifecycle events** (`added`, `superseded`, `retracted`, `modified`).

The **Semantic Bench** measures how accurately models and reasoners classify the **epistemic meaning** of those transitions:

```text
  Graph Lifecycle Event (Structural)
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  structural_type: "superseded"  │
  └─────────────────────────────────┘
                 │
       [Semantic Classifier]
                 ▼
  ┌─────────────────────────────────┐
  │   semantic_type: "refinement"   │
  └─────────────────────────────────┘
```

---

## 2. Epistemic Taxonomy & Classification Rules

| Category | Canonical Definition | Decision Criterion | Archetypal Example |
|---|---|---|---|
| **`refinement`** | The previous proposition remains substantially true, but has been narrowed, qualified, constrained, or made more precise. | Core intent preserved; preconditions or scope tightened. | An automated workflow transition acquires a mandatory confirmation precondition. |
| **`revision`** | Internal belief was mistaken, suboptimal, or redesigned; the relevant external reality is assumed stable. | The team replaced one design or assumption with another to better solve the same stable problem. | Replacing a synchronous HTTP worker with an asynchronous Redis background queue. |
| **`world_update`** | The external environment or external systems changed, causing a previously correct belief to become outdated. | External facts or upstream provider changed outside the project boundary. | An external identity provider changes its token expiration TTL from 1 hour to 24 hours. |
| **`expansion`** | New compatible information or capability was introduced without invalidating existing claims. | No prior belief contradicted or superseded. | Adding a new caching layer or audit logging requirement to an existing subsystem. |
| **`contraction`** | A proposition or requirement is withdrawn without replacement. | Prior claim abandoned; no successor record created. | Deprecating and removing legacy XML export without replacement. |
| **`contradiction`** | The epistemic state contains conflicting assertions that cannot jointly hold. | Incompatible mutual claims detected within the same active scope. | Two active constraints asserting conflicting token encryption requirements. |
| **`semantic_noop`** | Syntactic or representation changes with zero semantic or architectural divergence. | Meaning byte-for-byte or logically identical. | Reordering N-Quads lines or adding unrelated low-level AST symbol nodes. |
| **`unclear`** | Evidence or context is insufficient to distinguish the above categories. | Ambiguous rationale or missing context. | Record text is a raw hash or placeholder without descriptive claim. |

---

## 3. Standard Annotation Workflow

When annotating a new benchmark transition pair:

1. **Check for Invalidation:** Did the previous premise stop being true?
   - If *No* $\rightarrow$ Is it more precise? $\rightarrow$ **`refinement`**.
   - If *Yes* $\rightarrow$ Did the external world change (**`world_update`**) or did our internal design/understanding change (**`revision`**)?
2. **Check for Succession:** Was a replacement record introduced?
   - If *No* $\rightarrow$ Was something dropped? $\rightarrow$ **`contraction`**; was something added? $\rightarrow$ **`expansion`**.
3. **Record Ground Truth:** Specify the label in the benchmark manifest under `semantic_type` alongside explanatory rationale.
