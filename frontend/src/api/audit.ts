import client from "./client";

// ── Audit summary ──

export interface AuditSummary {
  total_contracts: number;
  pending_count: number;
  confirmed_count: number;
}

// ── Construction audit ──

export interface ConstructionAggItem {
  category: string | null;
  cost_sub_type: string | null;
  item_name: string | null;
  unit: string | null;
  unit_price: number | null;
  total_quantity: number;
  total_amount: number;
  row_count: number;
}

export interface ConstructionAudit {
  contract_id: string;
  contract_no: string;
  review_mode: string | null;
  contract_amount: number | null;
  detail_month: string;
  items: ConstructionAggItem[];
  total_output: number;
  total_payable: number;
}

// ── Consulting audit ──

export interface ConsultingFeeNode {
  node_name: string | null;
  stage_order: number;
  stage_name: string | null;
  agreed_ratio: number | null;
  agreed_amount: number | null;
  reported_amount: number | null;
  reviewed_amount: number | null;
  is_completed: boolean;
  triggered_at: string | null;
}

export interface ConsultingFeeItemDetail {
  fee_item_id: string;
  name: string;
  contract_amount: number | null;
  agreed_ratio: number | null;
  nodes: ConsultingFeeNode[];
  cumulative_reported: number;
  cumulative_reviewed: number;
}

export interface ConsultingAudit {
  contract_id: string;
  contract_no: string;
  review_mode: string | null;
  contract_amount: number | null;
  detail_month: string;
  fee_items: ConsultingFeeItemDetail[];
  total_reported: number;
  total_reviewed: number;
}

// ── Confirm ──

export interface AuditConfirmItem {
  fee_item_id: string;
  name: string;
  output: number;
  ratio: number;
  payable: number;
}

export interface AuditConfirmRequest {
  contract_id: string;
  detail_month: string;
  items: AuditConfirmItem[];
  status: string;
}

// ── API functions ──

export async function getAuditSummary(projectId: string, month: string): Promise<AuditSummary> {
  const { data } = await client.get(`/projects/${projectId}/audit/summary`, { params: { month } });
  return data;
}

export async function getAuditContractDetail(
  projectId: string,
  contractId: string,
  month: string,
): Promise<ConstructionAudit | ConsultingAudit> {
  const { data } = await client.get(
    `/projects/${projectId}/audit/contract/${contractId}`,
    { params: { month } },
  );
  return data;
}

export async function confirmAudit(projectId: string, body: AuditConfirmRequest) {
  const { data } = await client.post(`/projects/${projectId}/audit/confirm`, body);
  return data;
}
