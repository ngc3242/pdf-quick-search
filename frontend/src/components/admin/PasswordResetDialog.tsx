import { useState, type FormEvent } from 'react';
import { Modal, Button, Input } from '@/components/common';
import type { UserWithDocuments } from '@/types';

interface PasswordResetDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (newPassword: string) => Promise<void>;
  user: UserWithDocuments | null;
}

export function PasswordResetDialog({
  isOpen,
  onClose,
  onSubmit,
  user,
}: PasswordResetDialogProps) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!password || password.length < 6) {
      setError('비밀번호는 6자 이상이어야 합니다');
      return;
    }

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다');
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(password);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '비밀번호 변경에 실패했습니다');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setPassword('');
    setConfirmPassword('');
    setError('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="비밀번호 변경"
      size="sm"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-gray-600">
          <span className="font-medium">{user?.name}</span> 사용자의 비밀번호를 변경합니다.
        </p>

        <Input
          label="새 비밀번호"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="새 비밀번호를 입력하세요"
          disabled={isSubmitting}
        />

        <Input
          label="비밀번호 확인"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="비밀번호를 다시 입력하세요"
          disabled={isSubmitting}
        />

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            취소
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            변경
          </Button>
        </div>
      </form>
    </Modal>
  );
}
