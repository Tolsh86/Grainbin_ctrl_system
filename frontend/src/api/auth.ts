import client from "./client";

export interface LoginParams {
  username: string;
  password: string;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string | null;
  real_name: string;
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
  username: string;
  password: string;
  real_name: string;
  email?: string;
  role: string;
}): Promise<UserResponse> {
  const { data } = await client.post("/auth/register", params);
  return data;
}

export async function getMe(): Promise<UserResponse> {
  const { data } = await client.get("/users/me");
  return data;
}
