import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { Button, Modal } from '@/components/common';
import { UserTable, UserFormDialog, PasswordResetDialog } from '@/components/admin';
import { adminApi } from '@/api';
import type { UserWithDocuments, CreateUserRequest, UpdateUserRequest } from '@/types';

export function AdminPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserWithDocuments[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<UserWithDocuments | null>(null);
  const [deleteUser, setDeleteUser] = useState<UserWithDocuments | null>(null);
  const [passwordUser, setPasswordUser] = useState<UserWithDocuments | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await adminApi.listUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '사용자 목록을 불러오는데 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (data: CreateUserRequest | UpdateUserRequest) => {
    await adminApi.createUser(data as CreateUserRequest);
    await fetchUsers();
  };

  const handleUpdateUser = async (data: CreateUserRequest | UpdateUserRequest) => {
    if (!editUser) return;
    await adminApi.updateUser(editUser.id, data as UpdateUserRequest);
    await fetchUsers();
  };

  const handleDeleteUser = async () => {
    if (!deleteUser) return;

    setIsDeleting(true);
    try {
      await adminApi.deleteUser(deleteUser.id);
      await fetchUsers();
      setDeleteUser(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '삭제에 실패했습니다');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleResetPassword = async (newPassword: string) => {
    if (!passwordUser) return;
    await adminApi.resetPassword(passwordUser.id, newPassword);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/')}
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </button>
              <h1 className="text-xl font-bold text-gray-900">사용자 관리</h1>
            </div>
            <Button onClick={() => setIsCreateOpen(true)}>
              <PlusIcon className="h-5 w-5 mr-1" />
              새 사용자 추가
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <UserTable
          users={users}
          isLoading={isLoading}
          onEdit={setEditUser}
          onDelete={setDeleteUser}
          onResetPassword={setPasswordUser}
        />
      </main>

      {/* Create User Dialog */}
      <UserFormDialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateUser}
        mode="create"
      />

      {/* Edit User Dialog */}
      <UserFormDialog
        isOpen={!!editUser}
        onClose={() => setEditUser(null)}
        onSubmit={handleUpdateUser}
        user={editUser}
        mode="edit"
      />

      {/* Delete Confirmation Dialog */}
      <Modal
        isOpen={!!deleteUser}
        onClose={() => setDeleteUser(null)}
        title="사용자 삭제"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            이 사용자를 삭제하시겠습니까? 사용자의 모든 문서도 함께 삭제됩니다.
            <br />
            <span className="font-medium text-gray-900">
              {deleteUser?.name} ({deleteUser?.email})
            </span>
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => setDeleteUser(null)}
              disabled={isDeleting}
            >
              취소
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteUser}
              isLoading={isDeleting}
            >
              삭제
            </Button>
          </div>
        </div>
      </Modal>

      {/* Password Reset Dialog */}
      <PasswordResetDialog
        isOpen={!!passwordUser}
        onClose={() => setPasswordUser(null)}
        onSubmit={handleResetPassword}
        user={passwordUser}
      />
    </div>
  );
}
