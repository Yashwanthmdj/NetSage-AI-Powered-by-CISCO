from app.models.enums import CaseSource, ConceptTag, OsiLayer, Severity

REQUIRED_FIELDS = (
    "case_code",
    "title",
    "symptom",
    "topology_note",
    "show_outputs",
    "expected_fault",
    "osi_layer",
    "concept_tag",
    "severity",
    "source",
)


def record(
    *,
    case_code: str,
    title: str,
    symptom: str,
    topology_note: str,
    show_outputs: str,
    expected_fault: str,
    osi_layer: OsiLayer,
    concept_tag: ConceptTag,
    severity: Severity,
    source: CaseSource = CaseSource.PACKET_TRACER,
) -> dict:
    payload = {
        "case_code": case_code.strip(),
        "title": title.strip(),
        "symptom": symptom.strip(),
        "topology_note": topology_note.strip(),
        "show_outputs": show_outputs.strip(),
        "expected_fault": expected_fault.strip(),
        "osi_layer": osi_layer,
        "concept_tag": concept_tag,
        "severity": severity,
        "source": source,
    }
    missing = [name for name in REQUIRED_FIELDS if not str(payload[name]).strip()]
    if missing:
        raise ValueError(f"{case_code}: missing required fields: {missing}")
    return payload
