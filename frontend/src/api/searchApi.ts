import client from './client';
import type { SearchResponse } from '@/types';

export const searchApi = {
  search: async (query: string, limit = 50, offset = 0): Promise<SearchResponse> => {
    const response = await client.get<SearchResponse>('/search', {
      params: { q: query, limit, offset },
    });
    return response.data;
  },
};
