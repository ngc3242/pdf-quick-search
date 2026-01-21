import client from './client';
import type { LoginRequest, LoginResponse, SignupRequest, SignupResponse, User } from '@/types';

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await client.post<LoginResponse>('/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await client.post('/auth/logout');
  },

  me: async (): Promise<User> => {
    const response = await client.get<{ user: User }>('/auth/me');
    return response.data.user;
  },

  signup: async (data: SignupRequest): Promise<SignupResponse> => {
    const response = await client.post<SignupResponse>('/auth/signup', data);
    return response.data;
  },
};
