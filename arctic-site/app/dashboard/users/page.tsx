'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface Member {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export default function UsersPage() {
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [orgId, setOrgId] = useState('');
  
  const [inviteForm, setInviteForm] = useState({
    email: '',
    fullName: '',
    password: '',
    role: 'viewer',
  });

  useEffect(() => {
    fetchMembers();
  }, []);

  const fetchMembers = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('access_token');
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      
      if (!user.org_id || !token) {
        router.push('/auth/login');
        return;
      }

      setOrgId(user.org_id);

      const response = await fetch(`/api/orgs/${user.org_id}/members`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        router.push('/auth/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch members');
      }

      const data = await response.json();
      setMembers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInviteChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setInviteForm(prev => ({ ...prev, [name]: value }));
  };

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`/api/orgs/${orgId}/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: inviteForm.email,
          full_name: inviteForm.fullName,
          password: inviteForm.password,
          role: inviteForm.role,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to invite user');
      }

      setInviteForm({ email: '', fullName: '', password: '', role: 'viewer' });
      setShowInviteForm(false);
      
      // Refresh members list
      await fetchMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this member?')) return;

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`/api/orgs/${orgId}/members/${userId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to remove member');
      }

      await fetchMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-spin text-blue-600">⏳ Loading members...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Team Members</h1>
        <p className="text-slate-400">Manage your organization's users and permissions</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      <div className="mb-6">
        <Button
          onClick={() => setShowInviteForm(!showInviteForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          {showInviteForm ? 'Cancel' : '+ Invite Member'}
        </Button>
      </div>

      {showInviteForm && (
        <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Invite Team Member</h2>
          
          <form onSubmit={handleInviteSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email
              </label>
              <Input
                type="email"
                name="email"
                value={inviteForm.email}
                onChange={handleInviteChange}
                placeholder="user@example.com"
                required
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Full Name
              </label>
              <Input
                type="text"
                name="fullName"
                value={inviteForm.fullName}
                onChange={handleInviteChange}
                placeholder="John Doe"
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <Input
                type="password"
                name="password"
                value={inviteForm.password}
                onChange={handleInviteChange}
                placeholder="••••••••"
                required
                minLength={8}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Role
              </label>
              <select
                name="role"
                value={inviteForm.role}
                onChange={handleInviteChange}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
              >
                <option value="viewer">Viewer (read-only)</option>
                <option value="analyst">Analyst (can run agents)</option>
                <option value="admin">Admin (full access)</option>
              </select>
              <p className="text-xs text-slate-500 mt-2">
                • Viewer: View runs and audit logs only<br />
                • Analyst: Run agents, ingest data, view results<br />
                • Admin: Full org management, user invites, policies
              </p>
            </div>

            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              Send Invitation
            </Button>
          </form>
        </Card>
      )}

      <Card className="bg-slate-800 border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700 border-b border-slate-600">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Email
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Name
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Role
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Status
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Last Login
              </th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-slate-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {members.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                  No team members yet
                </td>
              </tr>
            ) : (
              members.map(member => (
                <tr key={member.id} className="hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-sm text-slate-300">{member.email}</td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {member.full_name || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      member.role === 'admin' ? 'bg-red-900/50 text-red-200' :
                      member.role === 'analyst' ? 'bg-blue-900/50 text-blue-200' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      {member.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`${
                      member.is_active ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {member.is_active ? '✓ Active' : '✗ Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-400">
                    {member.last_login_at
                      ? new Date(member.last_login_at).toLocaleDateString()
                      : 'Never'
                    }
                  </td>
                  <td className="px-6 py-4 text-sm text-right">
                    <button
                      onClick={() => handleRemoveMember(member.id)}
                      className="text-red-400 hover:text-red-300 font-medium"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
