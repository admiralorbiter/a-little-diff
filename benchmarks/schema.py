"""Strict Pydantic schema for alittlediff-bench manifests."""

from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class SemanticCategory(str, Enum):
    REFINEMENT = "refinement"
    REVISION = "revision"
    WORLD_UPDATE = "world_update"
    EXPANSION = "expansion"
    CONTRACTION = "contraction"
    CONTRADICTION = "contradiction"
    SEMANTIC_NOOP = "semantic_noop"
    UNCLEAR = "unclear"


class MetamorphicInvariant(str, Enum):
    LINE_ORDER_PERMUTATION = "line_order_permutation"
    WHITESPACE_NORMALIZATION = "whitespace_normalization"
    CRLF_VS_LF = "crlf_vs_lf"
    NAMED_GRAPH_EQUIVALENCE = "named_graph_equivalence"
    DIRECT_INVERSE_RELATION_EQUIVALENCE = "direct_inverse_relation_equivalence"
    IRRELEVANT_RECORD_INJECTION = "irrelevant_record_injection"
    IRRELEVANT_METADATA_INJECTION = "irrelevant_metadata_injection"
    DUPLICATE_TRIPLE_INJECTION = "duplicate_triple_injection"
    UNRELATED_RETIRED_NOISE = "unrelated_retired_noise"
    UNRELATED_SUBSTRATE_ISOLATION = "unrelated_substrate_isolation"
    INVERSE_RELATION_EQUIVALENCE = "inverse_relation_equivalence"


class CoreExpectedChange(BaseModel):
    """Deterministic structural change expected by Core Bench."""
    model_config = ConfigDict(extra="forbid")

    structural_type: str = Field(..., description="Lifecycle structural type: superseded, added, removed, modified, status_changed")
    before_id: Optional[str] = Field(default=None, description="Expected before record IRI/slug")
    after_id: Optional[str] = Field(default=None, description="Expected after record IRI/slug")
    semantic_type: Optional[str] = Field(default=None, description="Ground truth annotation for future Semantic Bench")
    note: Optional[str] = Field(default=None, description="Explanatory note")


class CoreExpectedImpact(BaseModel):
    """Deterministic causal impact expected by Core Bench."""
    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., description="Target record ID flagged for reconsideration")
    effect: str = Field(..., description="Categorical effect identifier (e.g. justification_may_have_changed)")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Expected confidence level")
    predicate: str = Field(..., description="Expected causal relationship traversed")


class FutureExpected(BaseModel):
    """Future V1 target behavior (e.g. truth maintenance support degradation)."""
    model_config = ConfigDict(extra="forbid")

    effect: str = Field(..., description="Target future effect (e.g. support_degraded)")
    detail: Optional[str] = Field(default=None, description="Target future detail description")


class BenchmarkManifest(BaseModel):
    """Complete specification for an alittlediff-bench scenario."""
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field(default="1.0", description="Manifest schema version")
    id: str = Field(..., pattern=r"^[0-9]{2}_[a-z0-9_]+$", description="Scenario identifier (e.g. 02_workflow_confirmation_refinement)")
    name: str = Field(..., description="Human-readable title")
    category: SemanticCategory = Field(..., description="Semantic category from SEMANTIC_GUIDE.md")
    description: str = Field(..., description="Description of the scenario and its causal dynamics")
    state_a_nquads: str = Field(..., description="N-Quads string for State A")
    state_b_nquads: str = Field(..., description="N-Quads string for State B")
    expected_changes: list[CoreExpectedChange] = Field(default_factory=list, description="List of expected structural changes")
    expected_impacts: list[CoreExpectedImpact] = Field(default_factory=list, description="List of expected causal impacts")
    expected_non_impacts: list[str] = Field(default_factory=list, description="List of record IDs that must NOT be impacted")
    metamorphic_invariants: list[MetamorphicInvariant] = Field(default_factory=list, description="List of applicable metamorphic invariants")
    future_target: Optional[FutureExpected] = Field(default=None, description="Future V1 target behavior specification")
