import { apiGet, apiPost } from "./client";
import type {
  AnalyticsSummary,
  RaiEventListResponse,
  ReviewCreate,
  ReviewDetail,
  ReviewQueueResponse,
} from "./types";

export function fetchAnalytics() {
  return apiGet<AnalyticsSummary>("/analytics/summary");
}

export function fetchReviewQueue() {
  return apiGet<ReviewQueueResponse>("/reviews/queue");
}

export function fetchRaiEvents() {
  return apiGet<RaiEventListResponse>("/rai-events");
}

export function submitReview(diagnosisId: number, body: ReviewCreate) {
  return apiPost<ReviewDetail, ReviewCreate>(`/diagnoses/${diagnosisId}/reviews`, body);
}

export function applyReviewFix(reviewId: number, applied_by = "Lab Reviewer") {
  return apiPost<ReviewDetail, { applied_by: string }>(`/reviews/${reviewId}/apply-fix`, { applied_by });
}
