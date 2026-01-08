import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '@/components/common';
import { UserFormDialog, PasswordResetDialog } from '@/components/admin';
import { adminApi } from '@/api';
import { useAuthStore } from '@/store';
import type { UserWithDocuments, CreateUserRequest, UpdateUserRequest } from '@/types';

export function AdminPage() {
  const navigate = useNavigate();
  const { user: currentUser, logout } = useAuthStore();
  const [users, setUsers] = useState<UserWithDocuments[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

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
      setError(err instanceof Error ? err.message : 'Failed to load users');
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
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleResetPassword = async (newPassword: string) => {
    if (!passwordUser) return;
    await adminApi.resetPassword(passwordUser.id, newPassword);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      !searchQuery ||
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.phone && u.phone.includes(searchQuery));
    const matchesRole = !roleFilter || u.role === roleFilter;
    const matchesStatus =
      !statusFilter ||
      (statusFilter === 'active' && u.is_active) ||
      (statusFilter === 'inactive' && !u.is_active);
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            Admin
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            User
          </span>
        );
    }
  };

  return (
    <div className="bg-background-light font-display min-h-screen flex flex-row overflow-hidden">
      {/* Side Navigation */}
      <div className="hidden lg:flex w-72 flex-col border-r border-[#e5e7eb] bg-white sticky top-0 h-screen overflow-y-auto">
        <div className="flex flex-col gap-4 p-4 min-h-full justify-between">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 px-2">
              <div className="size-10 rounded-full bg-primary flex items-center justify-center text-white">
                <span className="material-symbols-outlined">picture_as_pdf</span>
              </div>
              <h1 className="text-text-primary text-xl font-bold leading-normal tracking-tight">PDF Admin</h1>
            </div>
            <div className="flex flex-col gap-2 mt-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-background-light transition-colors group"
              >
                <span className="material-symbols-outlined text-text-secondary group-hover:text-primary text-[24px]">
                  description
                </span>
                <p className="text-text-primary text-sm font-medium leading-normal">Documents</p>
              </button>
              <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-primary/10 text-primary">
                <span className="material-symbols-outlined text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  group
                </span>
                <p className="text-primary text-sm font-bold leading-normal">User Management</p>
              </button>
            </div>
          </div>
          <div className="flex flex-col gap-2 border-t border-[#e5e7eb] pt-4">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="size-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold">
                {currentUser?.name?.charAt(0).toUpperCase() || 'A'}
              </div>
              <div className="flex flex-col">
                <p className="text-text-primary text-sm font-medium leading-tight">{currentUser?.name || 'Admin'}</p>
                <p className="text-text-secondary text-xs font-normal leading-tight">{currentUser?.email}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-white">
        {/* Top Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-[#e5e7eb] bg-white">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-text-primary">menu</span>
            <h1 className="text-text-primary text-lg font-bold">PDF Admin</h1>
          </div>
          <button
            onClick={handleLogout}
            className="size-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold"
          >
            {currentUser?.name?.charAt(0).toUpperCase() || 'A'}
          </button>
        </div>

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:px-12 lg:py-10">
          <div className="max-w-7xl mx-auto flex flex-col gap-6">
            {/* Breadcrumbs */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/')}
                className="text-text-secondary hover:text-primary text-sm font-medium leading-normal transition-colors"
              >
                Dashboard
              </button>
              <span className="material-symbols-outlined text-text-secondary text-sm">chevron_right</span>
              <span className="text-text-primary text-sm font-medium leading-normal">User Management</span>
            </div>

            {/* Page Heading & Actions */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div className="flex flex-col gap-2">
                <h2 className="text-text-primary text-3xl md:text-4xl font-black leading-tight tracking-tight">
                  User Management
                </h2>
                <p className="text-text-secondary text-base font-normal">
                  Manage accounts, roles, and view document statistics.
                </p>
              </div>
              <button
                onClick={() => setIsCreateOpen(true)}
                className="flex items-center justify-center gap-2 bg-primary hover:bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-bold shadow-sm transition-all focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                <span className="material-symbols-outlined text-[20px]">add</span>
                <span>Create New User</span>
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Filters & Search Bar */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white p-1 rounded-xl">
              {/* Search */}
              <div className="w-full md:w-96">
                <label className="flex w-full items-center gap-2 rounded-lg bg-[#f0f2f4] px-3 py-2.5 border border-transparent focus-within:border-primary/50 focus-within:bg-white transition-all">
                  <span className="material-symbols-outlined text-text-secondary">search</span>
                  <input
                    className="w-full bg-transparent text-sm font-normal text-text-primary placeholder-text-secondary focus:outline-none"
                    placeholder="Search users by name, email or phone..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </label>
              </div>
              {/* Filters */}
              <div className="flex w-full md:w-auto gap-3 overflow-x-auto pb-2 md:pb-0 scrollbar-hide">
                <div className="relative group">
                  <select
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value)}
                    className="flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-lg border border-[#e5e7eb] bg-white px-4 hover:bg-[#f9fafb] transition-colors text-text-primary text-sm font-medium cursor-pointer appearance-none pr-8"
                  >
                    <option value="">Role: All</option>
                    <option value="admin">Admin</option>
                    <option value="user">User</option>
                  </select>
                </div>
                <div className="relative group">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-lg border border-[#e5e7eb] bg-white px-4 hover:bg-[#f9fafb] transition-colors text-text-primary text-sm font-medium cursor-pointer appearance-none pr-8"
                  >
                    <option value="">Status: All</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setRoleFilter('');
                    setStatusFilter('');
                  }}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[#e5e7eb] bg-white hover:bg-[#f9fafb] transition-colors text-text-secondary"
                  title="Reset Filters"
                >
                  <span className="material-symbols-outlined">filter_alt_off</span>
                </button>
              </div>
            </div>

            {/* Users Table */}
            <div className="border border-[#e5e7eb] rounded-xl overflow-hidden shadow-sm bg-white">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-[#f9fafb] border-b border-[#e5e7eb]">
                    <tr>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[30%]">
                        User
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider text-center">
                        Docs
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                        Phone
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider text-right">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#e5e7eb]">
                    {isLoading ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-12 text-center">
                          <span className="material-symbols-outlined text-4xl text-text-secondary animate-spin">
                            progress_activity
                          </span>
                          <p className="mt-2 text-text-secondary">Loading users...</p>
                        </td>
                      </tr>
                    ) : filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-12 text-center">
                          <span className="material-symbols-outlined text-4xl text-text-secondary">person_off</span>
                          <p className="mt-2 text-text-secondary">No users found</p>
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => (
                        <tr key={u.id} className="hover:bg-primary/5 transition-colors group">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-3">
                              <div className="h-10 w-10 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold shrink-0">
                                {u.name.charAt(0).toUpperCase()}
                              </div>
                              <div className="flex flex-col">
                                <span className="text-sm font-semibold text-text-primary">{u.name}</span>
                                <span className="text-xs text-text-secondary">{u.email}</span>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">{getRoleBadge(u.role)}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-2 h-2 rounded-full ${u.is_active ? 'bg-green-500' : 'bg-red-500'}`}
                              ></div>
                              <span className="text-sm text-text-primary">{u.is_active ? 'Active' : 'Inactive'}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center">
                            <span className="text-sm font-medium text-text-primary">{u.document_count}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-text-secondary">{u.phone || '-'}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <div className="flex items-center justify-end gap-2 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => setEditUser(u)}
                                className="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded-md transition-colors"
                                title="Edit User"
                              >
                                <span className="material-symbols-outlined text-[20px]">edit</span>
                              </button>
                              <button
                                onClick={() => setPasswordUser(u)}
                                className="p-1.5 text-text-secondary hover:text-orange-600 hover:bg-orange-50 rounded-md transition-colors"
                                title="Reset Password"
                              >
                                <span className="material-symbols-outlined text-[20px]">lock_reset</span>
                              </button>
                              <button
                                onClick={() => setDeleteUser(u)}
                                className="p-1.5 text-text-secondary hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                title="Delete User"
                              >
                                <span className="material-symbols-outlined text-[20px]">delete</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              {/* Pagination */}
              <div className="px-6 py-4 border-t border-[#e5e7eb] flex items-center justify-between bg-white">
                <p className="text-sm text-text-secondary">
                  Showing <span className="font-medium text-text-primary">{filteredUsers.length}</span> of{' '}
                  <span className="font-medium text-text-primary">{users.length}</span> users
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Create User Dialog */}
      <UserFormDialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} onSubmit={handleCreateUser} mode="create" />

      {/* Edit User Dialog */}
      <UserFormDialog
        isOpen={!!editUser}
        onClose={() => setEditUser(null)}
        onSubmit={handleUpdateUser}
        user={editUser}
        mode="edit"
      />

      {/* Delete Confirmation Dialog */}
      <Modal isOpen={!!deleteUser} onClose={() => setDeleteUser(null)} title="Delete User" size="sm">
        <div className="space-y-4">
          <p className="text-text-secondary">
            Are you sure you want to delete this user? All their documents will also be deleted.
            <br />
            <span className="font-medium text-text-primary">
              {deleteUser?.name} ({deleteUser?.email})
            </span>
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setDeleteUser(null)}
              className="px-4 py-2 rounded-lg border border-[#dbe0e6] text-text-primary font-medium text-sm hover:bg-[#f9fafb] transition-colors"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              onClick={handleDeleteUser}
              className="px-4 py-2 rounded-lg bg-red-600 text-white font-medium text-sm hover:bg-red-700 transition-colors disabled:opacity-50"
              disabled={isDeleting}
            >
              {isDeleting ? (
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                  Deleting...
                </span>
              ) : (
                'Delete'
              )}
            </button>
          </div>
        </div>
      </Modal>

      {/* Password Reset Dialog */}
      <PasswordResetDialog isOpen={!!passwordUser} onClose={() => setPasswordUser(null)} onSubmit={handleResetPassword} user={passwordUser} />
    </div>
  );
}
