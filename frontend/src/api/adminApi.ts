import client from './client';
import type { User, UserWithDocuments, CreateUserRequest, UpdateUserRequest, Document } from '@/types';

export const adminApi = {
  listUsers: async (): Promise<UserWithDocuments[]> => {
    const response = await client.get<{ users: UserWithDocuments[] }>('/admin/users');
    return response.data.users;
  },

  createUser: async (data: CreateUserRequest): Promise<User> => {
    const response = await client.post<{ user: User }>('/admin/users', data);
    return response.data.user;
  },

  updateUser: async (userId: string, data: UpdateUserRequest): Promise<User> => {
    const response = await client.patch<{ user: User }>(`/admin/users/${userId}`, data);
    return response.data.user;
  },

  resetPassword: async (userId: string, newPassword: string): Promise<void> => {
    await client.post(`/admin/users/${userId}/password`, { new_password: newPassword });
  },

  deleteUser: async (userId: string): Promise<void> => {
    await client.delete(`/admin/users/${userId}`);
  },

  getUserDocuments: async (userId: string): Promise<Document[]> => {
    const response = await client.get<{ documents: Document[] }>(`/admin/users/${userId}/documents`);
    return response.data.documents;
  },
};
