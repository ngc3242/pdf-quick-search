import client from './client';
import type {
  TypoCheckRequest,
  TypoCheckResult,
  ProviderAvailability,
  TypoHistoryResponse,
  TypoCheckJobPollResult,
} from '@/types';

interface CheckTypoCachedResponse {
  cached: true;
  result: TypoCheckResult;
}

interface CheckTypoJobResponse {
  cached: false;
  job_id: number;
}

export type CheckTypoResponse = CheckTypoCachedResponse | CheckTypoJobResponse;

export const typoApi = {
  checkTypo: async (request: TypoCheckRequest): Promise<CheckTypoResponse> => {
    const response = await client.post('/typo-check', request, {
      validateStatus: (status) => status === 200 || status === 202,
    });

    if (response.status === 200 && response.data.cached) {
      return {
        cached: true,
        result: {
          original_text: request.text,
          corrected_text: response.data.corrected_text,
          issues: response.data.issues,
          provider: response.data.provider,
          processing_time_ms: 0,
          chunk_count: 0,
        },
      };
    }

    return { cached: false, job_id: response.data.job_id };
  },

  getJobStatus: async (jobId: number): Promise<TypoCheckJobPollResult> => {
    const response = await client.get<TypoCheckJobPollResult>(
      `/typo-check/jobs/${jobId}`
    );
    return response.data;
  },

  cancelJob: async (jobId: number): Promise<void> => {
    await client.post(`/typo-check/jobs/${jobId}/cancel`);
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
