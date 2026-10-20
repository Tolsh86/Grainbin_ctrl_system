import client from "./client";
import type { PaginatedResponse } from "./projects";

// ── Phase2 费用分项 ──

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

// ── Phase2 审核记录（新版，无硬编码费用字段）──

export interface Review {
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
  audit_status: string;
  submit_date: string | null;
  audited_by: string | null;
  audited_at: string | null;
  created_at: string;
  updated_at: string;
  fee_items: ReviewFeeItem[];
}

// ── 操作接口 ──

// 项目维度查询
export async function getProjectReviews(
  projectId: string,
  params?: {
    page?: number; page_size?: number;
    review_type?: string; audit_status?: string; keyword?: string;
  }
): Promise<PaginatedResponse<Review>> {
  const { data } = await client.get(`/projects/${projectId}/reviews`, { params });
  return data;
}

// 期次维度查询
export async function getPeriodReviews(
  periodId: string,
  params?: {
    page?: number; page_size?: number;
    review_type?: string; audit_status?: string; keyword?: string;
  }
): Promise<PaginatedResponse<Review>> {
  const { data } = await client.get(`/periods/${periodId}/reviews`, { params });
  return data;
}

// 创建审核（期次下）
export async function createReview(
  periodId: string,
  body: Record<string, unknown>
): Promise<Review> {
  const { data } = await client.post(`/periods/${periodId}/reviews`, body);
  return data;
}

// 获取单条审核
export async function getReview(id: string): Promise<Review> {
  const { data } = await client.get(`/reviews/${id}`);
  return data;
}

// 更新审核（含 fee_items）
export async function updateReview(id: string, body: Record<string, unknown>): Promise<Review> {
  const { data } = await client.put(`/reviews/${id}`, body);
  return data;
}

// 更新审核状态
export async function updateReviewStatus(
  id: string,
  body: { audit_status: string }
): Promise<Review> {
  const { data } = await client.patch(`/reviews/${id}/status`, body);
  return data;
}

// 建安费用：从日报自动汇总
export async function aggregateDaily(
  reviewId: string
): Promise<Review> {
  const { data } = await client.put(`/reviews/${reviewId}/aggregate-daily`);
  return data;
}
