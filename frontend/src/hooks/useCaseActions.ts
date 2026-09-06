import { useState } from "react";
import { runCaseRules, runDiagnosis } from "../api/cases";
import { ApiRequestError } from "../api/client";
import type { DiagnosisDetail, RuleEvaluateResponse } from "../api/types";

export function diagnosisErrorMessage(err: unknown): string {
  if (err instanceof ApiRequestError) {
    if (err.status === 503) {
      return err.message || "The AI service is unavailable. No diagnosis was invented.";
    }
    if (err.status === 422) return "The AI returned an invalid diagnosis. Nothing was saved.";
    if (err.status === 409) return "This case already has a diagnosis pending review.";
    return err.message;
  }
  return err instanceof Error ? err.message : "Diagnosis failed";
}

export function useCaseActions() {
  const [report, setReport] = useState<RuleEvaluateResponse | null>(null);
  const [diagnosis, setDiagnosis] = useState<DiagnosisDetail | null>(null);
  const [ruleError, setRuleError] = useState<string | null>(null);
  const [diagnoseError, setDiagnoseError] = useState<string | null>(null);
  const [ruleSuccess, setRuleSuccess] = useState<string | null>(null);
  const [diagnoseSuccess, setDiagnoseSuccess] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [diagnosing, setDiagnosing] = useState(false);

  async function onRunRules(caseId: number) {
    setRunning(true);
    setRuleError(null);
    setRuleSuccess(null);
    try {
      const result = await runCaseRules(caseId);
      setReport(result);
      setRuleSuccess(
        `Rule engine finished: ${result.fail_count} failed, ${result.pass_count} passed.`,
      );
    } catch (err) {
      setRuleError(err instanceof Error ? err.message : "Rule engine failed");
    } finally {
      setRunning(false);
    }
  }

  async function onDiagnose(caseId: number) {
    setDiagnosing(true);
    setDiagnoseError(null);
    setDiagnoseSuccess(null);
    try {
      const result = await runDiagnosis(caseId);
      setDiagnosis(result);
      setDiagnoseSuccess("Diagnosis saved as pending review. A human must accept, edit, or reject it.");
    } catch (err) {
      setDiagnoseError(diagnosisErrorMessage(err));
    } finally {
      setDiagnosing(false);
    }
  }

  return {
    report,
    setReport,
    diagnosis,
    setDiagnosis,
    ruleError,
    diagnoseError,
    ruleSuccess,
    diagnoseSuccess,
    running,
    diagnosing,
    onRunRules,
    onDiagnose,
  };
}
