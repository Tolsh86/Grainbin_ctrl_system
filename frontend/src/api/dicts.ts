import client from "./client";
import type { PaginatedResponse } from "./projects";

// ── 字典缓存 ──

export interface DictCache {
  [key: string]: { code: string; name: string; is_active: boolean }[];
}

export async function getAllDicts(): Promise<DictCache> {
  const { data } = await client.get("/dicts");
  return data;
}

export async function getDict(name: string): Promise<{ code: string; name: string; is_active: boolean }[]> {
  const { data } = await client.get(`/dicts/${name}`);
  return data;
}

export async function refreshDicts(): Promise<{ message: string }> {
  const { data } = await client.post("/dicts/refresh");
  return data;
}

// ── 字典条目 ──

export interface DictItem {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  sort_order: number | null;
}

export async function getDictItems(
  name: string,
  params?: { page?: number; page_size?: number; is_active?: boolean }
): Promise<PaginatedResponse<DictItem>> {
  const { data } = await client.get(`/dicts/${name}/items`, { params });
  return data;
}

export async function getDictItem(name: string, itemId: string): Promise<DictItem> {
  const { data } = await client.get(`/dicts/${name}/items/${itemId}`);
  return data;
}

export async function createDictItem(
  name: string,
  body: Record<string, unknown>
): Promise<DictItem> {
  const { data } = await client.post(`/dicts/${name}/items`, body);
  return data;
}

export async function updateDictItem(
  name: string,
  itemId: string,
  body: Record<string, unknown>
): Promise<DictItem> {
  const { data } = await client.put(`/dicts/${name}/items/${itemId}`, body);
  return data;
}

export async function deleteDictItem(name: string, itemId: string): Promise<{ message: string }> {
  const { data } = await client.delete(`/dicts/${name}/items/${itemId}`);
  return data;
}

export async function toggleDictItem(name: string, itemId: string): Promise<DictItem> {
  const { data } = await client.patch(`/dicts/${name}/items/${itemId}/toggle-active`);
  return data;
}
