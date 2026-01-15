import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSystemPromptStore } from './systemPromptStore';
import { systemPromptApi } from '@/api';
import type { SystemPrompt } from '@/types';

// Mock the API
vi.mock('@/api', () => ({
  systemPromptApi: {
    getSystemPrompts: vi.fn(),
    updateSystemPrompt: vi.fn(),
    resetSystemPrompt: vi.fn(),
  },
}));

const mockPrompts: SystemPrompt[] = [
  {
    provider: 'claude',
    prompt: 'Claude default prompt',
    is_active: true,
    is_custom: false,
    updated_at: null,
  },
  {
    provider: 'gemini',
    prompt: 'Gemini default prompt',
    is_active: true,
    is_custom: false,
    updated_at: null,
  },
  {
    provider: 'openai',
    prompt: 'OpenAI default prompt',
    is_active: true,
    is_custom: false,
    updated_at: null,
  },
];

describe('systemPromptStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useSystemPromptStore.setState({
      prompts: [],
      isLoading: false,
      error: null,
      editingProvider: null,
      isSaving: false,
      isResetting: false,
    });
    vi.clearAllMocks();
  });

  describe('loadPrompts', () => {
    it('should load prompts successfully', async () => {
      vi.mocked(systemPromptApi.getSystemPrompts).mockResolvedValue(mockPrompts);

      await useSystemPromptStore.getState().loadPrompts();

      const state = useSystemPromptStore.getState();
      expect(state.prompts).toEqual(mockPrompts);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle error when loading prompts fails', async () => {
      vi.mocked(systemPromptApi.getSystemPrompts).mockRejectedValue(
        new Error('Network error')
      );

      await useSystemPromptStore.getState().loadPrompts();

      const state = useSystemPromptStore.getState();
      expect(state.prompts).toEqual([]);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Network error');
    });

    it('should set isLoading while loading', async () => {
      let resolvePromise: (value: SystemPrompt[]) => void;
      const promise = new Promise<SystemPrompt[]>((resolve) => {
        resolvePromise = resolve;
      });
      vi.mocked(systemPromptApi.getSystemPrompts).mockReturnValue(promise);

      const loadPromise = useSystemPromptStore.getState().loadPrompts();

      expect(useSystemPromptStore.getState().isLoading).toBe(true);

      resolvePromise!(mockPrompts);
      await loadPromise;

      expect(useSystemPromptStore.getState().isLoading).toBe(false);
    });
  });

  describe('updatePrompt', () => {
    it('should update prompt successfully', async () => {
      useSystemPromptStore.setState({ prompts: mockPrompts });

      const updatedPrompt: SystemPrompt = {
        provider: 'claude',
        prompt: 'Updated Claude prompt',
        is_active: true,
        is_custom: true,
        updated_at: '2024-01-15T10:00:00Z',
      };
      vi.mocked(systemPromptApi.updateSystemPrompt).mockResolvedValue(updatedPrompt);

      await useSystemPromptStore.getState().updatePrompt('claude', 'Updated Claude prompt');

      const state = useSystemPromptStore.getState();
      expect(state.prompts.find((p) => p.provider === 'claude')?.prompt).toBe(
        'Updated Claude prompt'
      );
      expect(state.isSaving).toBe(false);
      expect(state.editingProvider).toBe(null);
    });

    it('should handle error when updating prompt fails', async () => {
      useSystemPromptStore.setState({ prompts: mockPrompts });

      vi.mocked(systemPromptApi.updateSystemPrompt).mockRejectedValue(
        new Error('Update failed')
      );

      await useSystemPromptStore.getState().updatePrompt('claude', 'New prompt');

      const state = useSystemPromptStore.getState();
      expect(state.error).toBe('Update failed');
      expect(state.isSaving).toBe(false);
    });
  });

  describe('resetPrompt', () => {
    it('should reset prompt to default successfully', async () => {
      const customPrompts = mockPrompts.map((p) =>
        p.provider === 'claude'
          ? { ...p, prompt: 'Custom prompt', is_custom: true }
          : p
      );
      useSystemPromptStore.setState({ prompts: customPrompts });

      vi.mocked(systemPromptApi.resetSystemPrompt).mockResolvedValue({
        message: 'Prompt reset to default',
        default_prompt: 'Claude default prompt',
      });

      await useSystemPromptStore.getState().resetPrompt('claude');

      const state = useSystemPromptStore.getState();
      const claudePrompt = state.prompts.find((p) => p.provider === 'claude');
      expect(claudePrompt?.prompt).toBe('Claude default prompt');
      expect(claudePrompt?.is_custom).toBe(false);
      expect(state.isResetting).toBe(false);
    });

    it('should handle error when resetting prompt fails', async () => {
      useSystemPromptStore.setState({ prompts: mockPrompts });

      vi.mocked(systemPromptApi.resetSystemPrompt).mockRejectedValue(
        new Error('Reset failed')
      );

      await useSystemPromptStore.getState().resetPrompt('claude');

      const state = useSystemPromptStore.getState();
      expect(state.error).toBe('Reset failed');
      expect(state.isResetting).toBe(false);
    });
  });

  describe('setEditingProvider', () => {
    it('should set editing provider', () => {
      useSystemPromptStore.getState().setEditingProvider('gemini');

      expect(useSystemPromptStore.getState().editingProvider).toBe('gemini');
    });

    it('should clear error when setting editing provider', () => {
      useSystemPromptStore.setState({ error: 'Some error' });

      useSystemPromptStore.getState().setEditingProvider('claude');

      expect(useSystemPromptStore.getState().error).toBe(null);
    });

    it('should allow setting to null', () => {
      useSystemPromptStore.setState({ editingProvider: 'claude' });

      useSystemPromptStore.getState().setEditingProvider(null);

      expect(useSystemPromptStore.getState().editingProvider).toBe(null);
    });
  });

  describe('clearError', () => {
    it('should clear the error', () => {
      useSystemPromptStore.setState({ error: 'Some error' });

      useSystemPromptStore.getState().clearError();

      expect(useSystemPromptStore.getState().error).toBe(null);
    });
  });
});
