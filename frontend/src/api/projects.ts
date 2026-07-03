import client from "./client";

export interface ProjectResponse {
  id: string;
  project_name: string;
  project_code: string;
  project_status: string;
  total_investment: number | null;
  owner_unit: string | null;
  constructor_unit: string | null;
  start_date: string | null;
  planned_end_date: string | null;
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
