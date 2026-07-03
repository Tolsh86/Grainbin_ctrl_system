import client from "./client";

export interface LoginParams {
  email: string;
  password: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export async function login(params: LoginParams): Promise<TokenResponse> {
  const { data } = await client.post("/auth/login", params);
  return data;
}

export async function register(params: {
  email: string;
  password: string;
  full_name: string;
  role: string;
}): Promise<UserResponse> {
  const { data } = await client.post("/auth/register", params);
  return data;
}

export async function getMe(): Promise<UserResponse> {
  const { data } = await client.get("/users/me");
  return data;
}
