from __future__ import annotations

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.exceptions import AppError
from app.models.enums import ConceptTag, OsiLayer, Severity
from app.schemas.case import (
    CaseCreate,
    CaseDetail,
    CaseImportResult,
    CaseListResponse,
    CaseUpdate,
)
from app.schemas.common import DatasetCoverage
from app.services.cases import CaseService
from app.services.seed import CSV_FIELDS, catalog_payloads, write_cases_csv

router = APIRouter(prefix="/cases", tags=["cases"])


def _service(db: Session = Depends(get_db)) -> CaseService:
    return CaseService(db)


@router.get("", response_model=CaseListResponse)
def list_cases(
    service: Annotated[CaseService, Depends(_service)],
    concept_tag: ConceptTag | None = None,
    severity: Severity | None = None,
    osi_layer: OsiLayer | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CaseListResponse:
    return service.list_cases(
        concept_tag=concept_tag.value if concept_tag else None,
        severity=severity.value if severity else None,
        osi_layer=osi_layer.value if osi_layer else None,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/coverage", response_model=DatasetCoverage)
def case_coverage(service: Annotated[CaseService, Depends(_service)]) -> DatasetCoverage:
    return service.coverage()


@router.get("/export.csv")
def export_cases_csv(service: Annotated[CaseService, Depends(_service)]) -> StreamingResponse:
    result = service.list_cases(limit=200, offset=0)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for item in result.items:
        detail = service.get_case(item.id)
        writer.writerow(
            {
                "case_id": detail.case_code,
                "title": detail.title,
                "symptom": detail.symptom,
                "topology_note": detail.topology_note,
                "show_outputs": detail.show_outputs,
                "expected_fault": detail.expected_fault,
                "osi_layer": detail.osi_layer.value,
                "concept_tag": detail.concept_tag.value,
                "severity": detail.severity.value,
                "source": detail.source.value,
            }
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cases.csv"},
    )


@router.post("", response_model=CaseDetail, status_code=201)
def create_case(
    payload: CaseCreate, service: Annotated[CaseService, Depends(_service)]
) -> CaseDetail:
    return service.create_case(payload)


@router.post("/import", response_model=CaseImportResult)
async def import_cases_csv(
    service: Annotated[CaseService, Depends(_service)],
    file: UploadFile = File(...),
) -> CaseImportResult:
    raw_bytes = await file.read()
    if len(raw_bytes) > 2_000_000:
        raise AppError("validation_error", "CSV is larger than 2 MB", 422)
    raw = raw_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None:
        raise AppError("validation_error", "CSV has no header row", 422)
    records: list[CaseCreate] = []
    errors: list[str] = []
    for index, row in enumerate(reader, start=2):
        mapped = {
            "case_code": row.get("case_id") or row.get("case_code"),
            "title": row.get("title"),
            "symptom": row.get("symptom"),
            "topology_note": row.get("topology_note"),
            "show_outputs": row.get("show_outputs"),
            "expected_fault": row.get("expected_fault"),
            "osi_layer": row.get("osi_layer"),
            "concept_tag": row.get("concept_tag"),
            "severity": row.get("severity"),
            "source": row.get("source") or "packet_tracer",
        }
        try:
            records.append(CaseCreate.model_validate(mapped))
        except ValidationError as exc:
            errors.append(f"row {index}: {exc.errors()[0]['msg']}")
    result = service.import_records(records)
    result.errors.extend(errors)
    result.skipped += len(errors)
    return result


@router.post("/seed", response_model=CaseImportResult)
def seed_from_catalog(service: Annotated[CaseService, Depends(_service)]) -> CaseImportResult:
    payloads = catalog_payloads()
    result = service.import_records(payloads)
    write_cases_csv(get_settings().cases_csv_path, payloads)
    return result


@router.get("/by-code/{case_code}", response_model=CaseDetail)
def get_case_by_code(
    case_code: str, service: Annotated[CaseService, Depends(_service)]
) -> CaseDetail:
    return service.get_case_by_code(case_code)


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, service: Annotated[CaseService, Depends(_service)]) -> CaseDetail:
    return service.get_case(case_id)


@router.patch("/{case_id}", response_model=CaseDetail)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    service: Annotated[CaseService, Depends(_service)],
) -> CaseDetail:
    return service.update_case(case_id, payload)
