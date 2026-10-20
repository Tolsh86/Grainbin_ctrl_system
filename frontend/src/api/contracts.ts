import client from "./client";
import type { PaginatedResponse } from "./projects";

// ── 合同 ──

export interface Contract {
  id: string;
  project_id: string;
  seq: number;
  contract_no: string;
  supplier_name: string;
  contract_desc: string;
  sign_date: string | null;
  contract_amount: number | null; // 分
  contract_type: string;
  status: string;
  // V2.2 fields
  contract_group: string | null;
  review_mode: string | null;
  ledger_group: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContractGroup {
  contract_group: string;
  contracts: Contract[];
}

export interface ContractDetail extends Contract {
  payment_stages: PaymentStage[];
}

export async function getContracts(
  projectId: string,
  params?: { page?: number; page_size?: number; contract_type?: string; status?: string; keyword?: string }
): Promise<PaginatedResponse<Contract>> {
  const { data } = await client.get(`/projects/${projectId}/contracts`, { params });
  return data;
}

export async function createContract(
  projectId: string,
  body: Record<string, unknown>
): Promise<Contract> {
  const { data } = await client.post(`/projects/${projectId}/contracts`, body);
  return data;
}

export async function getContract(id: string): Promise<ContractDetail> {
  const { data } = await client.get(`/contracts/${id}`);
  return data;
}

export async function updateContract(id: string, body: Record<string, unknown>): Promise<Contract> {
  const { data } = await client.put(`/contracts/${id}`, body);
  return data;
}

export async function deleteContract(id: string): Promise<{ message: string }> {
  const { data } = await client.delete(`/contracts/${id}`);
  return data;
}

// ── 支付节点 ──

export interface PaymentStage {
  id: string;
  contract_id: string;
  contract_no: string;
  supplier_name?: string | null;
  contract_desc?: string | null;
  stage_order: number;
  stage_name: string;
  payment_terms: string | null;
  node_name: string | null;
  agreed_ratio: number | null;
  agreed_amount: number | null; // 分
  planned_pay_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  cumulative_paid: number | null;
  remaining_unpaid: number | null;
  paid_ratio: number | null;
  remaining_ratio: number | null;
  // V2.2 fields
  triggered_at: string | null;
  reported_amount: number | null;
  reviewed_amount: number | null;
  created_at: string;
}

export async function getProjectNodes(projectId: string): Promise<PaymentStage[]> {
  const { data } = await client.get(`/projects/${projectId}/nodes`);
  return data;
}

export async function getContractNodes(contractId: string): Promise<PaymentStage[]> {
  const { data } = await client.get(`/contracts/${contractId}/nodes`);
  return data;
}

export async function createContractNode(
  contractId: string,
  body: Record<string, unknown>
): Promise<PaymentStage> {
  const { data } = await client.post(`/contracts/${contractId}/nodes`, body);
  return data;
}

export async function updateContractNode(
  contractId: string,
  nodeId: string,
  body: Record<string, unknown>
): Promise<PaymentStage> {
  const { data } = await client.put(`/contracts/${contractId}/nodes/${nodeId}`, body);
  return data;
}

export async function deleteContractNode(
  contractId: string,
  nodeId: string
): Promise<{ message: string }> {
  const { data } = await client.delete(`/contracts/${contractId}/nodes/${nodeId}`);
  return data;
}

export async function completeContractNode(
  contractId: string,
  nodeId: string
): Promise<PaymentStage> {
  const { data } = await client.patch(`/contracts/${contractId}/nodes/${nodeId}/complete`);
  return data;
}

export async function generateNodesFromTemplate(
  contractId: string,
  body: { template_id: string; contract_amount: number; sign_date?: string }
): Promise<PaymentStage[]> {
  const { data } = await client.post(`/contracts/${contractId}/nodes/from-template`, body);
  return data;
}

// ── 节点模板 ──

export interface NodeTemplate {
  id: string;
  template_name: string;
  biz_type: string;
  description: string | null;
  is_preset: boolean;
  stages: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export async function getContractGroups(projectId: string): Promise<ContractGroup[]> {
  const { data } = await client.get(`/projects/${projectId}/contracts/groups`);
  return data;
}

export async function getNodeTemplates(params?: {
  biz_type?: string;
  is_preset?: boolean;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<NodeTemplate>> {
  const { data } = await client.get("/node-templates", { params });
  return data;
}

export async function createNodeTemplate(
  body: Record<string, unknown>,
): Promise<NodeTemplate> {
  const { data } = await client.post("/node-templates", body);
  return data;
}

// ── 审核模式 & 台账分组（字典）──

export interface ReviewMode {
  value: string;
  label: string;
  description: string;
}

export interface LedgerGroup {
  value: string;
  label: string;
}

export async function getReviewModes(): Promise<ReviewMode[]> {
  const { data } = await client.get("/contracts/review-modes");
  return data as ReviewMode[];
}

export async function getLedgerGroups(): Promise<LedgerGroup[]> {
  const { data } = await client.get("/contracts/ledger-groups");
  return data as LedgerGroup[];
}

// ── 已有合同编号（AutoComplete）──

export async function getContractNos(projectId: string): Promise<string[]> {
  const { data } = await client.get(`/projects/${projectId}/contracts/nos`);
  return data as string[];
}

// ── 费用分项（Phase2 新增）──

export interface ContractFeeItem {
  id: string;
  contract_id: string;
  item_name: string;
  contract_amount: number | null;
  current_ratio: number | null;
  sort_order: number;
  remark: string | null;
}

export async function getContractFeeItems(contractId: string): Promise<ContractFeeItem[]> {
  const { data } = await client.get(`/contracts/${contractId}/fee-items`);
  return data as ContractFeeItem[];
}

export async function createContractFeeItems(
  contractId: string,
  items: { item_name: string; contract_amount?: number; current_ratio?: number; sort_order?: number; remark?: string }[]
): Promise<ContractFeeItem[]> {
  const { data } = await client.post(`/contracts/${contractId}/fee-items`, items);
  return data as ContractFeeItem[];
}

export async function updateContractFeeItem(
  contractId: string,
  itemId: string,
  body: Record<string, unknown>
): Promise<ContractFeeItem> {
  const { data } = await client.put(`/contracts/${contractId}/fee-items/${itemId}`, body);
  return data as ContractFeeItem;
}

export async function deleteContractFeeItem(
  contractId: string,
  itemId: string
): Promise<{ message: string }> {
  const { data } = await client.delete(`/contracts/${contractId}/fee-items/${itemId}`);
  return data;
}
