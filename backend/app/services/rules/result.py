from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

RuleStatus = Literal["pass", "fail"]


class RuleResult(BaseModel):
    rule_name: str
    status: RuleStatus
    evidence: List[str] = Field(default_factory=list)
    explanation: str
    devices: List[str] = Field(default_factory=list)
    severity: Optional[str] = None

    @classmethod
    def passed(cls, rule_name: str, explanation: str, evidence: Optional[List[str]] = None) -> "RuleResult":
        return cls(
            rule_name=rule_name,
            status="pass",
            explanation=explanation,
            evidence=evidence or [],
        )

    @classmethod
    def failed(
        cls,
        rule_name: str,
        explanation: str,
        evidence: List[str],
        devices: Optional[List[str]] = None,
        severity: str = "high",
    ) -> "RuleResult":
        return cls(
            rule_name=rule_name,
            status="fail",
            explanation=explanation,
            evidence=evidence,
            devices=devices or [],
            severity=severity,
        )


class RuleEngineReport(BaseModel):
    results: List[RuleResult]
    fail_count: int
    pass_count: int

    @classmethod
    def from_results(cls, results: List[RuleResult]) -> "RuleEngineReport":
        fails = sum(1 for item in results if item.status == "fail")
        return cls(results=results, fail_count=fails, pass_count=len(results) - fails)
