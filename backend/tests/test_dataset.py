from collections import Counter

from app.dataset.catalog import CASE_RECORDS, MINIMUM_CASES, REQUIRED_CONCEPTS, validate_catalog
from app.dataset._record import REQUIRED_FIELDS


def test_catalog_meets_coverage_gate() -> None:
    assert validate_catalog() == []
    assert len(CASE_RECORDS) >= MINIMUM_CASES


def test_every_case_has_required_evidence_fields() -> None:
    for row in CASE_RECORDS:
        for field in REQUIRED_FIELDS:
            assert str(row[field]).strip(), f"{row['case_code']} missing {field}"
        assert "show " in row["show_outputs"].lower() or "#" in row["show_outputs"]


def test_all_eight_concepts_are_present() -> None:
    present = {row["concept_tag"].value for row in CASE_RECORDS}
    assert present == REQUIRED_CONCEPTS


def test_case_codes_are_unique() -> None:
    codes = [row["case_code"] for row in CASE_RECORDS]
    dupes = [code for code, count in Counter(codes).items() if count > 1]
    assert dupes == []
