import client from "./client";

// ── Payment Matrix types ──

export interface PaymentMatrixNode {
  node_name: string | null;
  stage_name: string;
  agreed_amount: number | null;  // 分
  agreed_ratio: number | null;
  planned_pay_date: string | null;  // "YYYY-MM-DD"
  is_completed: boolean;
}

export interface PaymentMatrixContract {
  contract_id: string;
  supplier_name: string;
  contract_desc: string;
  contract_amount: number | null;  // 分
  sign_date: string | null;
  review_mode: string | null;
  nodes: PaymentMatrixNode[];
}

export interface PaymentMatrixGroup {
  contract_no: string;
  total_amount: number;  // 分（组内合同金额之和）
  contracts: PaymentMatrixContract[];
}

export interface PaymentMatrixResponse {
  project_name: string;
  month_range: string[];  // ["2025-06", "2025-07", ...]
  monthly_totals: Record<string, number>;  // {"2025-06": 120000.00, ...}  元
  groups: PaymentMatrixGroup[];
}

// ── API functions ──

export async function getPaymentMatrix(
  projectId: string,
): Promise<PaymentMatrixResponse> {
  const { data } = await client.get(`/projects/${projectId}/payment-matrix`);
  return data;
}
