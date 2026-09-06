from enum import Enum


class UserRole(str, Enum):
    ANALYST = "analyst"
    REVIEWER = "reviewer"


class OsiLayer(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"
    L7 = "L7"


class ConceptTag(str, Enum):
    VLAN = "vlan"
    GATEWAY = "gateway"
    DHCP = "dhcp"
    DNS = "dns"
    ROUTING = "routing"
    ACL = "acl"
    NAT = "nat"
    WIRELESS = "wireless"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseSource(str, Enum):
    PACKET_TRACER = "packet_tracer"
    LAB = "lab"


class DiagnosisStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"
    FAILED = "failed"


class ReviewVerdict(str, Enum):
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class RulePhase(str, Enum):
    PRE_AI = "pre_ai"
    POST_AI = "post_ai"
    CLI = "cli"


class RaiFailureClass(str, Enum):
    HALLUCINATED_EVIDENCE = "hallucinated_evidence"
    WRONG_LAYER = "wrong_layer"
    WRONG_CONCEPT = "wrong_concept"
    MISSED_RULE_FINDING = "missed_rule_finding"
    INCOMPLETE_FIX = "incomplete_fix"
    OVERCONFIDENT = "overconfident"


class ConfidenceLabel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
