import { create } from 'zustand';
import type { SystemPrompt, TypoProvider } from '@/types';
import { systemPromptApi } from '@/api';

interface SystemPromptState {
  // State
  prompts: SystemPrompt[];
  isLoading: boolean;
  error: string | null;
  editingProvider: TypoProvider | null;
  isSaving: boolean;
  isResetting: boolean;

  // Actions
  loadPrompts: () => Promise<void>;
  updatePrompt: (provider: TypoProvider, prompt: string) => Promise<void>;
  resetPrompt: (provider: TypoProvider) => Promise<void>;
  setEditingProvider: (provider: TypoProvider | null) => void;
  clearError: () => void;
}

const initialState = {
  prompts: [] as SystemPrompt[],
  isLoading: false,
  error: null as string | null,
  editingProvider: null as TypoProvider | null,
  isSaving: false,
  isResetting: false,
};

export const useSystemPromptStore = create<SystemPromptState>((set, get) => ({
  ...initialState,

  loadPrompts: async () => {
    set({ isLoading: true, error: null });

    try {
      const prompts = await systemPromptApi.getSystemPrompts();
      set({ prompts, isLoading: false });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'Failed to load system prompts';
      set({ error: errorMessage, isLoading: false });
    }
  },

  updatePrompt: async (provider: TypoProvider, prompt: string) => {
    set({ isSaving: true, error: null });

    try {
      const updatedPrompt = await systemPromptApi.updateSystemPrompt(provider, { prompt });

      // Update the prompts array with the new prompt
      const { prompts } = get();
      const updatedPrompts = prompts.map((p) =>
        p.provider === provider ? updatedPrompt : p
      );

      set({
        prompts: updatedPrompts,
        isSaving: false,
        editingProvider: null,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'Failed to update system prompt';
      set({ error: errorMessage, isSaving: false });
    }
  },

  resetPrompt: async (provider: TypoProvider) => {
    set({ isResetting: true, error: null });

    try {
      const response = await systemPromptApi.resetSystemPrompt(provider);

      // Update the prompts array with the default prompt
      const { prompts } = get();
      const updatedPrompts = prompts.map((p) =>
        p.provider === provider
          ? {
              ...p,
              prompt: response.default_prompt,
              is_custom: false,
              updated_at: null,
            }
          : p
      );

      set({
        prompts: updatedPrompts,
        isResetting: false,
        editingProvider: null,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'Failed to reset system prompt';
      set({ error: errorMessage, isResetting: false });
    }
  },

  setEditingProvider: (provider: TypoProvider | null) => {
    set({ editingProvider: provider, error: null });
  },

  clearError: () => {
    set({ error: null });
  },
}));
