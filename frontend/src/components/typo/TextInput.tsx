import { useId, type ChangeEvent } from 'react';

interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
  label?: string;
}

const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

const getCharacterCountClass = (current: number, max: number): string => {
  const percentage = (current / max) * 100;

  if (percentage >= 100) {
    return 'text-red-600';
  }
  if (percentage >= 95) {
    return 'text-yellow-600';
  }
  return 'text-gray-500';
};

export const TextInput = ({
  value,
  onChange,
  placeholder = '맞춤법을 검사할 텍스트를 입력하세요...',
  maxLength = 100000,
  disabled = false,
  label,
}: TextInputProps) => {
  const id = useId();
  const charCountId = `${id}-char-count`;
  const characterCount = value.length;

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
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
      <div className="relative">
        <textarea
          id={id}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          maxLength={maxLength}
          disabled={disabled}
          aria-describedby={charCountId}
          className={`
            w-full min-h-[200px] p-4 border rounded-lg resize-y
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:bg-gray-100 disabled:cursor-not-allowed
            ${disabled ? 'text-gray-500' : 'text-gray-900'}
            border-gray-300
          `}
        />
      </div>
      <div
        id={charCountId}
        className={`mt-2 text-sm text-right ${getCharacterCountClass(characterCount, maxLength)}`}
      >
        <span>{formatNumber(characterCount)}</span>
        <span className="text-gray-400"> / </span>
        <span>{formatNumber(maxLength)}</span>
        <span className="text-gray-400 ml-1">자</span>
      </div>
    </div>
  );
};
