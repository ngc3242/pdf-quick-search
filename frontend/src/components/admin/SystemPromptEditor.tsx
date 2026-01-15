import { useEffect, useState } from 'react';
import { useSystemPromptStore } from '@/store';
import type { TypoProvider } from '@/types';

const PROVIDER_LABELS: Record<TypoProvider, string> = {
  claude: 'Claude (Anthropic)',
  gemini: 'Gemini (Google)',
  openai: 'OpenAI (GPT)',
};

const PROVIDER_DESCRIPTIONS: Record<TypoProvider, string> = {
  claude: 'Anthropic Claude AI model for Korean typo checking',
  gemini: 'Google Gemini AI model for Korean typo checking',
  openai: 'OpenAI GPT model for Korean typo checking',
};

export function SystemPromptEditor() {
  const {
    prompts,
    isLoading,
    error,
    editingProvider,
    isSaving,
    isResetting,
    loadPrompts,
    updatePrompt,
    resetPrompt,
    setEditingProvider,
    clearError,
  } = useSystemPromptStore();

  const [editedPrompt, setEditedPrompt] = useState('');

  useEffect(() => {
    loadPrompts();
  }, [loadPrompts]);

  useEffect(() => {
    if (editingProvider) {
      const prompt = prompts.find((p) => p.provider === editingProvider);
      setEditedPrompt(prompt?.prompt || '');
    }
  }, [editingProvider, prompts]);

  const handleEdit = (provider: TypoProvider) => {
    setEditingProvider(provider);
  };

  const handleCancel = () => {
    setEditingProvider(null);
    setEditedPrompt('');
  };

  const handleSave = async () => {
    if (editingProvider && editedPrompt.trim()) {
      await updatePrompt(editingProvider, editedPrompt.trim());
    }
  };

  const handleReset = async (provider: TypoProvider) => {
    if (window.confirm('Are you sure you want to reset this prompt to the default?')) {
      await resetPrompt(provider);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="material-symbols-outlined text-4xl text-text-secondary animate-spin">
          progress_activity
        </span>
        <p className="ml-3 text-text-secondary">Loading system prompts...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xl font-bold text-text-primary">System Prompts</h3>
        <p className="text-sm text-text-secondary">
          Customize the system prompts used by AI providers for typo checking.
          Changes will take effect immediately for new checks.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <p className="text-sm text-red-600">{error}</p>
          <button
            onClick={clearError}
            className="text-red-600 hover:text-red-800"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      )}

      {/* Prompt Cards */}
      <div className="space-y-4">
        {prompts.map((promptConfig) => (
          <div
            key={promptConfig.provider}
            className="border border-[#e5e7eb] rounded-xl bg-white overflow-hidden"
          >
            {/* Card Header */}
            <div className="flex items-center justify-between px-6 py-4 bg-[#f9fafb] border-b border-[#e5e7eb]">
              <div className="flex items-center gap-3">
                <div className="flex flex-col">
                  <h4 className="text-base font-semibold text-text-primary">
                    {PROVIDER_LABELS[promptConfig.provider]}
                  </h4>
                  <p className="text-xs text-text-secondary">
                    {PROVIDER_DESCRIPTIONS[promptConfig.provider]}
                  </p>
                </div>
                {promptConfig.is_custom && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    Custom
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {editingProvider !== promptConfig.provider && (
                  <>
                    <button
                      onClick={() => handleEdit(promptConfig.provider)}
                      className="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded-md transition-colors"
                      title="Edit Prompt"
                    >
                      <span className="material-symbols-outlined text-[20px]">edit</span>
                    </button>
                    {promptConfig.is_custom && (
                      <button
                        onClick={() => handleReset(promptConfig.provider)}
                        disabled={isResetting}
                        className="p-1.5 text-text-secondary hover:text-orange-600 hover:bg-orange-50 rounded-md transition-colors disabled:opacity-50"
                        title="Reset to Default"
                      >
                        <span className="material-symbols-outlined text-[20px]">restart_alt</span>
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Card Content */}
            <div className="p-6">
              {editingProvider === promptConfig.provider ? (
                /* Edit Mode */
                <div className="space-y-4">
                  <textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    className="w-full h-64 px-4 py-3 text-sm font-mono text-text-primary bg-[#f9fafb] border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none"
                    placeholder="Enter the system prompt..."
                  />
                  <div className="flex items-center justify-end gap-3">
                    <button
                      onClick={handleCancel}
                      disabled={isSaving}
                      className="px-4 py-2 text-sm font-medium text-text-primary border border-[#e5e7eb] rounded-lg hover:bg-[#f9fafb] transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={isSaving || !editedPrompt.trim()}
                      className="px-4 py-2 text-sm font-bold text-white bg-primary hover:bg-blue-600 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      {isSaving ? (
                        <>
                          <span className="material-symbols-outlined text-[18px] animate-spin">
                            progress_activity
                          </span>
                          Saving...
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-[18px]">save</span>
                          Save Changes
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                /* View Mode */
                <div className="space-y-3">
                  <pre className="w-full max-h-48 overflow-auto p-4 text-sm font-mono text-text-primary bg-[#f9fafb] border border-[#e5e7eb] rounded-lg whitespace-pre-wrap">
                    {promptConfig.prompt}
                  </pre>
                  {promptConfig.updated_at && (
                    <p className="text-xs text-text-secondary">
                      Last updated: {new Date(promptConfig.updated_at).toLocaleString()}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {prompts.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <span className="material-symbols-outlined text-4xl text-text-secondary">
            description
          </span>
          <p className="mt-2 text-text-secondary">No system prompts configured.</p>
        </div>
      )}
    </div>
  );
}
