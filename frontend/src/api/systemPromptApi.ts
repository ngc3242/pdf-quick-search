import client from './client';
import type {
  SystemPrompt,
  SystemPromptsResponse,
  UpdateSystemPromptRequest,
  ResetSystemPromptResponse,
  TypoProvider,
} from '@/types';

export const systemPromptApi = {
  /**
   * Get all system prompts for all providers.
   * Returns custom prompts if configured, otherwise defaults.
   */
  getSystemPrompts: async (): Promise<SystemPrompt[]> => {
    const response = await client.get<SystemPromptsResponse>('/admin/system-prompts');
    return response.data.prompts;
  },

  /**
   * Get system prompt for a specific provider.
   */
  getSystemPrompt: async (provider: TypoProvider): Promise<SystemPrompt> => {
    const response = await client.get<SystemPrompt>(`/admin/system-prompts/${provider}`);
    return response.data;
  },

  /**
   * Update or create a custom system prompt for a provider.
   */
  updateSystemPrompt: async (
    provider: TypoProvider,
    data: UpdateSystemPromptRequest
  ): Promise<SystemPrompt> => {
    const response = await client.put<SystemPrompt>(`/admin/system-prompts/${provider}`, data);
    return response.data;
  },

  /**
   * Reset a provider's prompt to the default.
   * Removes any custom configuration.
   */
  resetSystemPrompt: async (provider: TypoProvider): Promise<ResetSystemPromptResponse> => {
    const response = await client.post<ResetSystemPromptResponse>(
      `/admin/system-prompts/${provider}/reset`
    );
    return response.data;
  },
};
