import { useState, useEffect, type FormEvent } from 'react';
import { Modal, Button, Input } from '@/components/common';
import type { UserWithDocuments, CreateUserRequest, UpdateUserRequest } from '@/types';

interface UserFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => Promise<void>;
  user?: UserWithDocuments | null;
  mode: 'create' | 'edit';
}

export function UserFormDialog({
  isOpen,
  onClose,
  onSubmit,
  user,
  mode,
}: UserFormDialogProps) {
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: '',
    phone: '',
    role: 'user' as 'admin' | 'user',
    is_active: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user && mode === 'edit') {
      setFormData({
        email: user.email,
        name: user.name,
        password: '',
        phone: user.phone || '',
        role: user.role,
        is_active: user.is_active,
      });
    } else {
      setFormData({
        email: '',
        name: '',
        password: '',
        phone: '',
        role: 'user',
        is_active: true,
      });
    }
    setError('');
  }, [user, mode, isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (mode === 'create') {
      if (!formData.email || !formData.name || !formData.password) {
        setError('이메일, 이름, 비밀번호는 필수입니다');
        return;
      }
    } else {
      if (!formData.name) {
        setError('이름은 필수입니다');
        return;
      }
    }

    setIsSubmitting(true);

    try {
      if (mode === 'create') {
        await onSubmit({
          email: formData.email,
          name: formData.name,
          password: formData.password,
          phone: formData.phone || undefined,
          role: formData.role,
        });
      } else {
        await onSubmit({
          name: formData.name,
          phone: formData.phone || undefined,
          role: formData.role,
          is_active: formData.is_active,
        });
      }
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '저장에 실패했습니다');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({
      email: '',
      name: '',
      password: '',
      phone: '',
      role: 'user',
      is_active: true,
    });
    setError('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={mode === 'create' ? '새 사용자 추가' : '사용자 수정'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'create' && (
          <Input
            label="이메일"
            type="email"
            value={formData.email}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, email: e.target.value }))
            }
            placeholder="이메일을 입력하세요"
            disabled={isSubmitting}
          />
        )}

        <Input
          label="이름"
          type="text"
          value={formData.name}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, name: e.target.value }))
          }
          placeholder="이름을 입력하세요"
          disabled={isSubmitting}
        />

        {mode === 'create' && (
          <Input
            label="비밀번호"
            type="password"
            value={formData.password}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, password: e.target.value }))
            }
            placeholder="비밀번호를 입력하세요"
            disabled={isSubmitting}
          />
        )}

        <Input
          label="전화번호"
          type="tel"
          value={formData.phone}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, phone: e.target.value }))
          }
          placeholder="전화번호를 입력하세요 (선택)"
          disabled={isSubmitting}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            역할
          </label>
          <select
            value={formData.role}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                role: e.target.value as 'admin' | 'user',
              }))
            }
            disabled={isSubmitting}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="user">사용자</option>
            <option value="admin">관리자</option>
          </select>
        </div>

        {mode === 'edit' && (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, is_active: e.target.checked }))
              }
              disabled={isSubmitting}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              활성 상태
            </label>
          </div>
        )}

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
            {mode === 'create' ? '추가' : '저장'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
