export type ConceptTag =
  | "vlan"
  | "gateway"
  | "dhcp"
  | "dns"
  | "routing"
  | "acl"
  | "nat"
  | "wireless";

export type OsiLayer = "L1" | "L2" | "L3" | "L4" | "L5" | "L6" | "L7";
export type Severity = "low" | "medium" | "high" | "critical";

export interface Pagination {
  total: number;
  limit: number;
  offset: number;
}

export interface CaseSummary {
  id: number;
  case_code: string;
  title: string;
  osi_layer: OsiLayer;
  concept_tag: ConceptTag;
  severity: Severity;
  source: string;
  lifecycle_status: string;
  created_at: string;
  updated_at: string;
}

export interface RuleCheckResult {
  rule_name: string;
  status: "pass" | "fail";
  evidence: string[];
  explanation: string;
  devices: string[];
  severity: string | null;
}

export interface RuleEvaluateResponse {
  results: RuleCheckResult[];
  fail_count: number;
  pass_count: number;
  rule_run_id: number | null;
  case_id: number | null;
}

export interface CaseDetail extends CaseSummary {
  symptom: string;
  topology_note: string;
  show_outputs: string;
  expected_fault: string;
  latest_rule_run: RuleRunRead | null;
  latest_diagnosis: DiagnosisRead | null;
  latest_review: ReviewRead | null;
  latest_verification: VerificationRead | null;
}

export interface RuleRunRead {
  id: number;
  case_id: number;
  diagnosis_id: number | null;
  phase: string;
  findings_json: RuleCheckResult[];
  error_count: number;
  created_at: string;
}

export interface CaseCreate {
  case_code: string;
  title: string;
  symptom: string;
  topology_note: string;
  show_outputs: string;
  expected_fault: string;
  osi_layer: OsiLayer;
  concept_tag: ConceptTag;
  severity: Severity;
  source?: string;
}

export interface VerificationRead {
  id: number;
  case_id: number;
  review_id: number;
  verified_by: string;
  notes: string | null;
  created_at: string;
}

export interface VerificationCreate {
  verified_by?: string;
  notes?: string;
}

export interface CaseImportResult {
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}

export interface DiagnosisEvidence {
  quote: string;
  command: string;
  why: string;
}

export interface DiagnosisRead {
  id: number;
  case_id: number;
  model_name: string;
  root_cause: string;
  osi_layer: OsiLayer | string;
  concept_tag: ConceptTag | string;
  concept?: string;
  severity: Severity | string;
  verification_command: string;
  confidence: number;
  confidence_label: string;
  evidence_json: DiagnosisEvidence[];
  next_commands_json: string[];
  fix_steps_json: string[];
  grounded: boolean;
  expected_match: boolean | null;
  status: string;
  raw_response?: string | null;
  created_at: string;
}

export interface DiagnosisDetail extends DiagnosisRead {
  ungrounded_quotes: string[];
  next_command: string | null;
  raw_response?: string | null;
}

export type ReviewVerdict = "accepted" | "edited" | "rejected";

export type RaiFailureClass =
  | "hallucinated_evidence"
  | "wrong_layer"
  | "wrong_concept"
  | "missed_rule_finding"
  | "incomplete_fix"
  | "overconfident";

export interface ReviewRead {
  id: number;
  diagnosis_id: number;
  reviewer_id: number;
  verdict: ReviewVerdict | string;
  corrected_root_cause: string | null;
  corrected_osi_layer: string | null;
  corrected_concept_tag: string | null;
  corrected_fix_steps_json: string[] | null;
  correction_reason: string | null;
  override_ungrounded: boolean;
  fix_applied?: boolean;
  fix_applied_by?: string | null;
  fix_applied_at?: string | null;
  created_at: string;
}

export interface ReviewDetail extends ReviewRead {
  reviewer_name: string;
  diagnosis_status: string;
  rai_event_id: number | null;
  original_ai: Record<string, unknown>;
}

export interface ReviewCreate {
  verdict: ReviewVerdict;
  reviewer_name?: string;
  correction_reason?: string;
  corrected_root_cause?: string;
  corrected_osi_layer?: OsiLayer;
  corrected_concept_tag?: ConceptTag;
  corrected_fix_steps?: string[];
  override_ungrounded?: boolean;
  failure_class?: RaiFailureClass;
}

export interface CaseListResponse {
  items: CaseSummary[];
  pagination: Pagination;
}

export interface CoverageBucket {
  key: string;
  count: number;
}

export interface DatasetCoverage {
  case_count: number;
  required_minimum: number;
  concepts: CoverageBucket[];
  osi_layers: CoverageBucket[];
  severities: CoverageBucket[];
  missing_concepts: ConceptTag[];
  meets_coverage_gate: boolean;
}

export interface HealthResponse {
  status: string;
  database: string;
  case_count: number;
  app: string;
  llm_configured?: boolean;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface RateMetric {
  sample_size: number;
  value: number | null;
}

export interface AnalyticsSummary {
  case_count: number;
  diagnosed_count: number;
  pending_review_count: number;
  reviewed_count: number;
  accepted_count: number;
  edited_count: number;
  rejected_count: number;
  unresolved_count: number;
  verified_count: number;
  rai_event_count: number;
  rule_error_count: number;
  counts_by_concept: CoverageBucket[];
  counts_by_severity: CoverageBucket[];
  review_verdicts: CoverageBucket[];
  rai_failure_classes: CoverageBucket[];
  ai_human_agreement: RateMetric;
  ai_expected_match: RateMetric;
  verification_success: RateMetric;
}

export interface ReviewQueueItem {
  review_id: number | null;
  diagnosis_id: number;
  case_id: number;
  case_code: string;
  title: string;
  concept_tag: string;
  status: string;
  created_at: string;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
}

export interface RaiEventRead {
  id: number;
  review_id: number;
  case_id: number;
  case_code?: string | null;
  verdict?: string | null;
  failure_class: string;
  explanation: string;
  record_kind?: string;
  ai_snapshot_json?: Record<string, unknown>;
  human_correction_json?: Record<string, unknown>;
  created_at: string;
}

export interface RaiEventListResponse {
  items: RaiEventRead[];
  total: number;
}
