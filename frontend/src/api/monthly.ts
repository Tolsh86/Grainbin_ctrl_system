import client from "./client";

// ── Monthly ledger types ──

export interface MonthlyFeeItem {
  fee_item_id: string;
  name: string;
  output: number;
  payable: number;
}

export interface MonthlyContractItem {
  detail_id: string | null;
  contract_id: string;
  contract_no: string;
  supplier_name: string;
  review_mode: string | null;
  ledger_group: string | null;
  contract_group: string | null;
  contract_amount: number | null;
  monthly_output: number;
  monthly_payable: number;
  cumulative_output: number;
  cumulative_payable: number;
  completed_ratio: number | null;
  fee_items: MonthlyFeeItem[];
  source: string;
  status: string;
}

export interface MonthlyListGroup {
  month: string;
  contracts: MonthlyContractItem[];
  group_monthly_output: number;
  group_monthly_payable: number;
  group_cumulative_output: number;
  group_cumulative_payable: number;
}

export interface MonthlyListResponse {
  project_id: string;
  groups: MonthlyListGroup[];
}

// ── API functions ──

export async function getMonthlyList(
  projectId: string,
  month?: string,
): Promise<MonthlyListResponse> {
  const { data } = await client.get(`/projects/${projectId}/monthly`, {
    params: month ? { month } : undefined,
  });
  return data;
}

export async function revokeMonthlyDetail(
  detailId: string,
): Promise<{ message: string; detail: string }> {
  const { data } = await client.patch(`/monthly/${detailId}/revoke`);
  return data;
}

export function getMonthlyExportUrl(projectId: string): string {
  return `/api/v1/projects/${projectId}/monthly/export`;
}
