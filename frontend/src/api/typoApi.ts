import client from './client';
import type {
  TypoCheckRequest,
  TypoCheckResult,
  ProviderAvailability,
  TypoHistoryResponse,
} from '@/types';

export const typoApi = {
  checkTypo: async (request: TypoCheckRequest): Promise<TypoCheckResult> => {
    const response = await client.post<TypoCheckResult>('/typo-check', request);
    return response.data;
  },

  getProviderAvailability: async (): Promise<ProviderAvailability> => {
    const response = await client.get<ProviderAvailability>('/typo-check/providers');
    return response.data;
  },

  downloadReport: async (
    result: TypoCheckResult,
    format: 'html' | 'pdf'
  ): Promise<Blob> => {
    const response = await client.post<Blob>(
      `/typo-check/report/${format}`,
      result,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  getHistory: async (page = 1, perPage = 20): Promise<TypoHistoryResponse> => {
    const response = await client.get<TypoHistoryResponse>(
      `/typo-check/history?page=${page}&per_page=${perPage}`
    );
    return response.data;
  },

  deleteHistoryItem: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await client.delete<{ success: boolean; message: string }>(
      `/typo-check/${id}`
    );
    return response.data;
  },
};
