from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ConceptTag


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: object | None = None


class HealthResponse(BaseModel):
    status: str
    database: str
    case_count: int
    app: str
    llm_configured: bool = False


class CoverageBucket(BaseModel):
    key: str
    count: int = Field(ge=0)


class DatasetCoverage(BaseModel):
    case_count: int
    required_minimum: int = 30
    concepts: list[CoverageBucket]
    osi_layers: list[CoverageBucket]
    severities: list[CoverageBucket]
    missing_concepts: list[ConceptTag]
    meets_coverage_gate: bool


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int
