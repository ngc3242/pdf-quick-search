import { useId, type ChangeEvent } from 'react';
import type { TypoProvider, ProviderAvailability } from '@/types';

interface ProviderSelectorProps {
  value: TypoProvider;
  onChange: (provider: TypoProvider) => void;
  availability: ProviderAvailability;
  disabled?: boolean;
  label?: string;
}

interface ProviderOption {
  value: TypoProvider;
  label: string;
  description: string;
}

const PROVIDER_OPTIONS: ProviderOption[] = [
  {
    value: 'claude',
    label: 'Claude',
    description: 'Anthropic Claude AI',
  },
  {
    value: 'openai',
    label: 'OpenAI',
    description: 'OpenAI GPT',
  },
  {
    value: 'gemini',
    label: 'Gemini',
    description: 'Google Gemini AI',
  },
];

export const ProviderSelector = ({
  value,
  onChange,
  availability,
  disabled = false,
  label,
}: ProviderSelectorProps) => {
  const id = useId();

  const handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const selectedProvider = e.target.value as TypoProvider;
    if (availability[selectedProvider]) {
      onChange(selectedProvider);
    }
  };

  const getOptionLabel = (option: ProviderOption): string => {
    const isAvailable = availability[option.value];
    if (isAvailable) {
      return option.label;
    }
    return `${option.label} (사용 불가)`;
  };

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          {label}
        </label>
      )}
      <select
        id={id}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className={`
          w-full px-4 py-2 border rounded-lg
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:bg-gray-100 disabled:cursor-not-allowed
          ${disabled ? 'text-gray-500' : 'text-gray-900'}
          border-gray-300 bg-white
        `}
      >
        {PROVIDER_OPTIONS.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={!availability[option.value]}
          >
            {getOptionLabel(option)}
          </option>
        ))}
      </select>
    </div>
  );
};
