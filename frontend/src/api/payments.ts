/** 支付台账 API */

import client from "./client";

// ── 支付记录响应 ──

export interface PaymentResponse {
  id: string;
  contract_id: string;
  contract_no: string;
  stage_id: string | null;
  reported_amount: number;   // 分
  approved_amount: number;   // 分
  status: string;            // pending / confirmed / rejected
  reject_reason: string | null;
  confirmed_at: string | null;
  payment_voucher: string | null;
  remark: string | null;
  stage_name: string | null;
  supplier_name: string | null;
  created_at: string;
  updated_at: string;
}

// ── 支付台账按月分组 ──

export interface PaymentLedgerGroup {
  month: string;                           // "2026-01" | "未确认"
  items: PaymentResponse[];
  month_total_reported: number;            // 分
  month_total_approved: number;            // 分
}

// ── 请求体 ──

export interface PaymentCreateRequest {
  stage_id: string;
  reported_amount: number;                 // 分
}

export interface PaymentRejectRequest {
  reject_reason: string;
}

// ── API 函数 ──

/** 获取合同支付台账（按月分组） */
export async function getContractPayments(
  contractId: string,
  year?: number,
): Promise<PaymentLedgerGroup[]> {
  const params: Record<string, unknown> = {};
  if (year !== undefined) params.year = year;
  const { data } = await client.get(`/contracts/${contractId}/payments`, { params });
  return data;
}

/** 创建支付记录（报送） */
export async function createPayment(
  contractId: string,
  body: PaymentCreateRequest,
): Promise<PaymentResponse> {
  const { data } = await client.post(`/contracts/${contractId}/payments`, body);
  return data;
}

/** 确认批准支付 */
export async function confirmPayment(
  contractId: string,
  paymentId: string,
): Promise<PaymentResponse> {
  const { data } = await client.post(`/contracts/${contractId}/payments/${paymentId}/confirm`);
  return data;
}

/** 驳回支付 */
export async function rejectPayment(
  contractId: string,
  paymentId: string,
  body: PaymentRejectRequest,
): Promise<PaymentResponse> {
  const { data } = await client.post(`/contracts/${contractId}/payments/${paymentId}/reject`, body);
  return data;
}
