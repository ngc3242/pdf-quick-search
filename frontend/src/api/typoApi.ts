import client from './client';
import type {
  TypoCheckRequest,
  TypoCheckResult,
  ProviderAvailability,
} from '@/types';

export const typoApi = {
  checkTypo: async (request: TypoCheckRequest): Promise<TypoCheckResult> => {
    const response = await client.post<TypoCheckResult>('/typo/check', request);
    return response.data;
  },

  getProviderAvailability: async (): Promise<ProviderAvailability> => {
    const response = await client.get<ProviderAvailability>('/typo/providers');
    return response.data;
  },

  downloadReport: async (
    result: TypoCheckResult,
    format: 'html' | 'pdf'
  ): Promise<Blob> => {
    const response = await client.post<Blob>(
      `/typo/report/${format}`,
      result,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },
};
