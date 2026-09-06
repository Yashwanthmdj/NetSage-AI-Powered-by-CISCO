from __future__ import annotations

from app.services.rules.checks import RULES
from app.services.rules.parser import parse_inventory
from app.services.rules.result import RuleEngineReport, RuleResult


def evaluate(show_outputs: str, topology_note: str = "") -> RuleEngineReport:
    """Run every deterministic rule. No I/O and no AI imports."""
    inventory = parse_inventory(show_outputs, topology_note)
    results = [rule(inventory) for rule in RULES]
    return RuleEngineReport.from_results(results)


def evaluate_results(show_outputs: str, topology_note: str = "") -> list[RuleResult]:
    return evaluate(show_outputs, topology_note).results
