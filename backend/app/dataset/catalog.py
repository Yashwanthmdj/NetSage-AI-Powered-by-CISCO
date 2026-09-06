from __future__ import annotations

from collections import Counter

from app.dataset.acl import ACL_CASES
from app.dataset.dhcp import DHCP_CASES
from app.dataset.dns import DNS_CASES
from app.dataset.gateway import GATEWAY_CASES
from app.dataset.nat import NAT_CASES
from app.dataset.routing import ROUTING_CASES
from app.dataset.vlan import VLAN_CASES
from app.dataset.wireless import WIRELESS_CASES
from app.dataset._record import REQUIRED_FIELDS
from app.models.enums import ConceptTag

CASE_RECORDS: list[dict] = [
    *VLAN_CASES,
    *GATEWAY_CASES,
    *DHCP_CASES,
    *DNS_CASES,
    *ROUTING_CASES,
    *ACL_CASES,
    *NAT_CASES,
    *WIRELESS_CASES,
]

REQUIRED_CONCEPTS = {item.value for item in ConceptTag}
MINIMUM_CASES = 30


def required_fields_ok(row: dict) -> list[str]:
    return [name for name in REQUIRED_FIELDS if not str(row.get(name, "")).strip()]


def validate_catalog(rows: list[dict] | None = None) -> list[str]:
    catalog = rows if rows is not None else CASE_RECORDS
    errors: list[str] = []
    codes: list[str] = []
    concepts: set[str] = set()

    if len(catalog) < MINIMUM_CASES:
        errors.append(f"catalog has {len(catalog)} cases; minimum is {MINIMUM_CASES}")

    for row in catalog:
        code = str(row.get("case_code", "<missing>"))
        codes.append(code)
        missing = required_fields_ok(row)
        if missing:
            errors.append(f"{code}: missing {missing}")
        concept = row.get("concept_tag")
        if concept is not None:
            concepts.add(getattr(concept, "value", concept))

    duplicates = [code for code, count in Counter(codes).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate case_code values: {duplicates}")

    missing_concepts = sorted(REQUIRED_CONCEPTS - concepts)
    if missing_concepts:
        errors.append(f"missing concept coverage: {missing_concepts}")

    return errors
