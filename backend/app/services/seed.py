from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dataset.catalog import CASE_RECORDS, validate_catalog
from app.schemas.case import CaseCreate
from app.services.cases import CaseService

CSV_FIELDS = [
    "case_id",
    "title",
    "symptom",
    "topology_note",
    "show_outputs",
    "expected_fault",
    "osi_layer",
    "concept_tag",
    "severity",
    "source",
]


def catalog_payloads() -> list[CaseCreate]:
    errors = validate_catalog()
    if errors:
        raise ValueError("Dataset catalog failed validation: " + "; ".join(errors))
    payloads: list[CaseCreate] = []
    for row in CASE_RECORDS:
        try:
            payloads.append(CaseCreate(**row))
        except ValidationError as exc:
            raise ValueError(f"{row.get('case_code')}: {exc}") from exc
    return payloads


def write_cases_csv(path: Path, payloads: list[CaseCreate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in payloads:
            writer.writerow(
                {
                    "case_id": item.case_code,
                    "title": item.title,
                    "symptom": item.symptom,
                    "topology_note": item.topology_note,
                    "show_outputs": item.show_outputs,
                    "expected_fault": item.expected_fault,
                    "osi_layer": item.osi_layer.value,
                    "concept_tag": item.concept_tag.value,
                    "severity": item.severity.value,
                    "source": item.source.value,
                }
            )


def seed_catalog(db: Session, *, write_csv: bool = True) -> dict[str, int | bool]:
    payloads = catalog_payloads()
    result = CaseService(db).import_records(payloads)
    if write_csv:
        write_cases_csv(get_settings().cases_csv_path, payloads)
    return {
        "created": result.created,
        "updated": result.updated,
        "total": len(payloads),
        "csv_written": write_csv,
    }
