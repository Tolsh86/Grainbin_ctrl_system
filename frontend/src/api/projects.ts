import client from "./client";

export interface ProjectResponse {
  id: string;
  project_name: string;
  project_code: string;
  project_status: string;
  project_nature: string;
  invest_timing: string;
  invest_nature: string | null;
  invest_structure: string | null;
  invest_field: string | null;
  implement_body: string | null;
  business_class: string | null;
  region: string;
  importance: string | null;
  supervising_dept: string | null;
  project_level_remark: string | null;
  start_date: string | null;
  end_date: string | null;
  planned_total_invest: number;
  planned_invest_2026: number | null;
  owner_unit: string | null;
  responsible_unit: string | null;
  construction_content: string | null;
  construction_scale: string | null;
  construction_period: string | null;
  quality_target: string;
  safety_target: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export async function getProjects(params?: {
  page?: number;
  page_size?: number;
  status?: string;
}): Promise<PaginatedResponse<ProjectResponse>> {
  const { data } = await client.get("/projects", { params });
  return data;
}

export async function getProject(id: string): Promise<ProjectResponse> {
  const { data } = await client.get(`/projects/${id}`);
  return data;
}

export async function createProject(body: Record<string, unknown>): Promise<ProjectResponse> {
  const { data } = await client.post("/projects", body);
  return data;
}

export async function updateProject(
  id: string,
  body: Record<string, unknown>
): Promise<ProjectResponse> {
  const { data } = await client.put(`/projects/${id}`, body);
  return data;
}

export async function deleteProject(id: string): Promise<{ message: string }> {
  const { data } = await client.delete(`/projects/${id}`);
  return data;
}
