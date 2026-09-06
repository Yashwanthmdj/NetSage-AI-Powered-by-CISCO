import { apiGet, apiPost } from "./client";
import type {
  CaseCreate,
  CaseDetail,
  CaseImportResult,
  CaseListResponse,
  DatasetCoverage,
  DiagnosisDetail,
  HealthResponse,
  RuleEvaluateResponse,
  VerificationCreate,
  VerificationRead,
} from "./types";

export function fetchHealth() {
  return apiGet<HealthResponse>("/health");
}

export function fetchCases(params: Record<string, string | undefined> = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return apiGet<CaseListResponse>(`/cases${suffix}`);
}

export function fetchCaseByCode(caseCode: string) {
  return apiGet<CaseDetail>(`/cases/by-code/${encodeURIComponent(caseCode)}`);
}

export function fetchCoverage() {
  return apiGet<DatasetCoverage>("/cases/coverage");
}

export function runCaseRules(caseId: number) {
  return apiPost<RuleEvaluateResponse, Record<string, never>>(`/cases/${caseId}/rules`, {});
}

export function runDiagnosis(caseId: number) {
  return apiPost<DiagnosisDetail, Record<string, never>>(`/cases/${caseId}/diagnoses`, {});
}

export function evaluateRules(show_outputs: string, topology_note = "") {
  return apiPost<RuleEvaluateResponse, { show_outputs: string; topology_note: string }>(
    "/rules/evaluate",
    { show_outputs, topology_note },
  );
}

export function createCase(payload: CaseCreate) {
  return apiPost<CaseDetail, CaseCreate>("/cases", payload);
}

export function seedCatalog() {
  return apiPost<CaseImportResult, Record<string, never>>("/cases/seed", {});
}

export function verifyCase(caseId: number, payload: VerificationCreate) {
  return apiPost<VerificationRead, VerificationCreate>(`/cases/${caseId}/verifications`, payload);
}
