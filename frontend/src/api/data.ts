import client from "./client";
import type { PaginatedResponse } from "./projects";

// ── 上传 ──

export interface UploadResult {
  file_path: string;
  file_name: string;
  file_size: number;
  format: string;
  message: string;
}

export async function uploadFile(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/upload/file", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function uploadFiles(fileList: File[]): Promise<UploadResult[]> {
  const form = new FormData();
  fileList.forEach((f) => form.append("files", f));
  const { data } = await client.post("/upload/files", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ── 批次管理 (新的 /import/batch 路由) ──

export interface Batch {
  id: string;
  project_id: string;
  source_doc: string;
  source_path: string;
  source_type: string;
  file_format: string;
  period_start: string | null;
  period_end: string | null;
  mapping_id: string | null;
  total_rows: number;
  parsed_rows: number;
  valid_rows: number;
  error_rows: number;
  quality_score: number | null;
  status: string;
  committed_at: string | null;
  rolled_back_at: string | null;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
}

export async function getBatch(batchId: string): Promise<Batch> {
  const { data } = await client.get(`/import/batch/${batchId}`);
  return data;
}

export async function parseBatch(batchId: string): Promise<Batch> {
  const { data } = await client.post(`/import/batch/${batchId}/parse`);
  return data;
}

export async function getBatchRows(
  batchId: string,
  params?: { page?: number; page_size?: number; is_valid?: boolean }
): Promise<PaginatedResponse<Record<string, unknown>>> {
  const { data } = await client.get(`/import/batch/${batchId}/rows`, { params });
  return data;
}

export interface BatchError {
  id: string;
  batch_id: string;
  row_id: string | null;
  error_stage: string;
  error_code: string;
  error_message: string;
  error_field: string | null;
  error_value: string | null;
  severity: string;
  resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export async function getBatchErrors(
  batchId: string,
  params?: { page?: number; page_size?: number; severity?: string }
): Promise<PaginatedResponse<BatchError>> {
  const { data } = await client.get(`/import/batch/${batchId}/errors`, { params });
  return data;
}

// ── 字段映射 ──

export interface FieldMapping {
  id: string;
  mapping_name: string;
  project_id: string | null;
  file_format: string;
  header_row: number;
  sheet_index: number;
  rules: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function getFieldMappings(params?: {
  page?: number;
  page_size?: number;
  biz_type?: string;
  keyword?: string;
}): Promise<PaginatedResponse<FieldMapping>> {
  const { data } = await client.get("/import/mapping", { params });
  return data;
}

export async function getFieldMapping(id: string): Promise<FieldMapping> {
  const { data } = await client.get(`/import/mapping/${id}`);
  return data;
}

export async function createFieldMapping(body: Record<string, unknown>): Promise<FieldMapping> {
  const { data } = await client.post("/import/mapping", body);
  return data;
}

export async function updateFieldMapping(
  id: string,
  body: Record<string, unknown>
): Promise<FieldMapping> {
  const { data } = await client.put(`/import/mapping/${id}`, body);
  return data;
}

export async function deleteFieldMapping(id: string): Promise<void> {
  await client.delete(`/import/mapping/${id}`);
}

export async function seedPresets(): Promise<{ message: string }> {
  const { data } = await client.post("/import/mapping/presets");
  return data;
}

export async function previewMapping(
  mappingId: string,
  file: File
): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post(`/import/mapping/preview`, form, {
    params: { mapping_id: mappingId },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ── 原 /ingest 路由 (旧批次管理) ──

export async function uploadAndCreateBatch(
  projectId: string,
  file: File,
  params?: { mapping_id?: string }
): Promise<Batch> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/ingest/upload", form, {
    params: { project_id: projectId, ...params },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getIngestBatches(
  params?: { project_id?: string; page?: number; page_size?: number }
): Promise<PaginatedResponse<Batch>> {
  const { data } = await client.get("/ingest/batches", { params });
  return data;
}

export async function getIngestBatchRows(
  batchId: string,
  params?: { page?: number; page_size?: number; is_valid?: boolean }
): Promise<PaginatedResponse<Record<string, unknown>>> {
  const { data } = await client.get(`/ingest/batches/${batchId}/rows`, { params });
  return data;
}

export async function commitBatch(batchId: string): Promise<{ message: string }> {
  const { data } = await client.post(`/ingest/batches/${batchId}/commit`);
  return data;
}

export async function rollbackBatch(batchId: string): Promise<{ message: string }> {
  const { data } = await client.post(`/ingest/batches/${batchId}/rollback`);
  return data;
}

// ── 数据行列表 (t_data_rows) ──

export interface DataRow {
  id: string;
  project_id: string;
  batch_id: string | null;
  data_date: string | null;
  category: string | null;
  item_name: string | null;
  planned_quantity: number | null;
  actual_quantity: number | null;
  unit: string | null;
  unit_price: number | null;
  amount: number | null;
  cost_type: string | null;
  created_at: string;
}

export async function getDataRows(
  projectId: string,
  params?: { page?: number; page_size?: number; category?: string; keyword?: string }
): Promise<PaginatedResponse<DataRow>> {
  const { data } = await client.get(`/projects/${projectId}/data-rows`, { params });
  return data;
}
