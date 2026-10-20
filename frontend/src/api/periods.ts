import client from "./client";
import type { PaginatedResponse } from "./projects";

// ── 期次类型 ──

export interface Period {
  id: string;
  project_id: string;
  period_no: number;
  period_month: string; // YYYY-MM
  status: string;       // draft / in_progress / reviewed / closed
  remark: string | null;
  contract_count?: number;
  review_count?: number;
  created_at: string;
  updated_at: string;
}

export interface PeriodDetail extends Period {
  contract_ids: string[];
}

// ── 费用分项值（快照）──

export interface ReviewFeeItem {
  id: string;
  review_id: string;
  fee_item_id: string | null;
  item_name: string;
  payment_ratio: number | null;
  reported_amount: number | null;
  reviewed_amount: number | null;
  remark: string | null;
}

// ── 审核记录（Phase2）──

export interface ReviewPhase2 {
  id: string;
  project_id: string;
  contract_id: string;
  period_id: string;
  review_type: string;
  applicant_unit: string;
  contract_amount: number;
  cumulative_reported_output: number;
  current_audited_output: number;
  cumulative_audited_output: number;
  cumulative_audited_payable: number;
  extra_fields: Record<string, unknown> | null;
  remark: string | null;
  tax_rate: number | null;
  audit_status: string; // draft / submitted / reviewed
  submit_date: string | null;
  audited_by: string | null;
  audited_at: string | null;
  created_at: string;
  updated_at: string;
  fee_items: ReviewFeeItem[];
}

// ── 创建期次（含 contract_ids）──

export interface PeriodCreate {
  period_month: string;
  period_no: number;
  contract_ids: string[];
  remark?: string;
}

export interface PeriodUpdate {
  period_month?: string;
  contract_ids?: string[];
  remark?: string;
}

// ── 期次 API ──

export async function getPeriods(
  projectId: string,
  params?: { page?: number; page_size?: number; status?: string }
): Promise<PaginatedResponse<Period>> {
  const { data } = await client.get(`/projects/${projectId}/periods`, { params });
  return data;
}

export async function createPeriod(
  projectId: string,
  body: PeriodCreate
): Promise<PeriodDetail> {
  const { data } = await client.post(`/projects/${projectId}/periods`, body);
  return data;
}

export async function getPeriod(id: string): Promise<PeriodDetail> {
  const { data } = await client.get(`/periods/${id}`);
  return data;
}

export async function updatePeriod(
  id: string,
  body: PeriodUpdate
): Promise<Period> {
  const { data } = await client.patch(`/periods/${id}`, body);
  return data;
}

export async function updatePeriodStatus(
  id: string,
  body: { status: string }
): Promise<Period> {
  const { data } = await client.patch(`/periods/${id}/status`, body);
  return data;
}

export async function deletePeriod(id: string): Promise<void> {
  await client.delete(`/periods/${id}`);
}

// ── 期次下的审核记录 ──

export async function getPeriodReviews(
  periodId: string,
  params?: {
    page?: number; page_size?: number;
    review_type?: string; audit_status?: string; keyword?: string;
  }
): Promise<PaginatedResponse<ReviewPhase2>> {
  const { data } = await client.get(`/periods/${periodId}/reviews`, { params });
  return data;
}

export async function createReviewInPeriod(
  periodId: string,
  body: Record<string, unknown>
): Promise<ReviewPhase2> {
  const { data } = await client.post(`/periods/${periodId}/reviews`, body);
  return data;
}

/** 获取期次审核汇总表导出 URL */
export function getPeriodExportUrl(periodId: string): string {
  return `/api/v1/periods/${periodId}/export`;
}
