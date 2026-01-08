import client from './client';
import type { Document, DocumentsResponse } from '@/types';

export const documentApi = {
  list: async (page = 1, perPage = 20): Promise<DocumentsResponse> => {
    const response = await client.get<DocumentsResponse>('/documents', {
      params: { page, per_page: perPage },
    });
    return response.data;
  },

  get: async (id: number): Promise<Document> => {
    const response = await client.get<{ document: Document }>(`/documents/${id}`);
    return response.data.document;
  },

  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await client.post<{ document: Document; message: string }>(
      '/documents',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.document;
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/documents/${id}`);
  },

  getFileUrl: (id: number): string => {
    const token = localStorage.getItem('access_token');
    return `/api/documents/${id}/file?token=${token}`;
  },
};
