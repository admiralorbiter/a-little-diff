"""JSON report formatter for epistemic diff results."""

import json
from alittlediff.report.diff_report import DiffReport


def render_json_report(report: DiffReport, indent: int = 2) -> str:
    """Serialize a DiffReport to a formatted JSON string.
    
    Args:
        report: The DiffReport instance.
        indent: JSON indentation spaces.
        
    Returns:
        JSON string representation.
    """
    return json.dumps(
        report.model_dump(mode="json"),
        indent=indent,
        ensure_ascii=False,
    )
