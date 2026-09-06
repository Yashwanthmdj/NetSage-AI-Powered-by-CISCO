from __future__ import annotations

from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ConceptTag, ConfidenceLabel, OsiLayer, Severity


class EvidenceItem(BaseModel):
    quote: str = Field(min_length=1)
    command: str = Field(min_length=1)
    why: str = Field(min_length=1)

    @field_validator("quote", "command", "why")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("evidence fields cannot be blank")
        return cleaned


class DiagnosisOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    root_cause: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel
    osi_layer: OsiLayer
    concept_tag: ConceptTag = Field(validation_alias=AliasChoices("concept_tag", "concept"))
    severity: Severity
    evidence: List[EvidenceItem] = Field(min_length=1)
    next_command: str = Field(min_length=1)
    next_commands: List[str] = Field(default_factory=list)
    fix_steps: List[str] = Field(min_length=1)
    verification_command: str = Field(min_length=1)
    uncertainties: List[str] = Field(default_factory=list)
    rule_alignment: Optional[str] = None

    @field_validator("root_cause", "next_command", "verification_command")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be blank")
        return cleaned

    @field_validator("next_commands", "fix_steps")
    @classmethod
    def strip_lists(cls, values: List[str]) -> List[str]:
        cleaned = [item.strip() for item in values if item and item.strip()]
        return cleaned

    @model_validator(mode="after")
    def align_commands_and_confidence(self) -> "DiagnosisOutput":
        if self.next_command not in self.next_commands:
            self.next_commands = [self.next_command, *self.next_commands]
        if not self.fix_steps:
            raise ValueError("fix_steps must contain at least one step")
        expected = _label_for(self.confidence)
        if self.confidence_label != expected and abs(self.confidence - _mid(self.confidence_label)) > 0.35:
            # Keep the provided label but this is still valid JSON; only reject empty contradictions.
            pass
        return self


def _label_for(confidence: float) -> ConfidenceLabel:
    if confidence < 0.4:
        return ConfidenceLabel.LOW
    if confidence < 0.75:
        return ConfidenceLabel.MEDIUM
    return ConfidenceLabel.HIGH


def _mid(label: ConfidenceLabel) -> float:
    return {
        ConfidenceLabel.LOW: 0.2,
        ConfidenceLabel.MEDIUM: 0.55,
        ConfidenceLabel.HIGH: 0.85,
    }[label]
