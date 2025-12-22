'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface ToolPolicy {
  id: string;
  tool_name: string;
  mode: string;
  constraints: Record<string, any>;
  allowed_roles: string[];
  created_at: string;
  created_by: string;
}

interface ToolApproval {
  id: string;
  tool_name: string;
  tool_args: Record<string, any>;
  requested_by: string;
  requested_at: string;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

const DEFAULT_CONSTRAINTS = {
  max_file_size_mb: 100,
  allowed_paths: ['/data'],
  network_enabled: false,
  timeout_seconds: 300,
};

export default function PoliciesPage() {
  const router = useRouter();
  const [policies, setPolicies] = useState<ToolPolicy[]>([]);
  const [approvals, setApprovals] = useState<ToolApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'policies' | 'approvals'>('policies');
  const [showCreateForm, setShowCreateForm] = useState(false);

  const [newPolicy, setNewPolicy] = useState({
    tool_name: '',
    mode: 'approve',
    constraints: DEFAULT_CONSTRAINTS,
    allowed_roles: ['admin', 'analyst'],
  });

  useEffect(() => {
    fetchPolicies();
    fetchApprovals();
  }, []);

  const fetchPolicies = async () => {
    try {
      const token = localStorage.getItem('access_token');

      if (!token) {
        router.push('/auth/login');
        return;
      }

      const response = await fetch('/api/tool-policies', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        router.push('/auth/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch policies');
      }

      const data = await response.json();
      setPolicies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchApprovals = async () => {
    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/tools/approvals', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setApprovals(data);
      }
    } catch (err) {
      // Silently fail if endpoint doesn't exist yet
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!newPolicy.tool_name.trim()) {
      setError('Tool name is required');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/tool-policies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newPolicy),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create policy');
      }

      setNewPolicy({
        tool_name: '',
        mode: 'approve',
        constraints: DEFAULT_CONSTRAINTS,
        allowed_roles: ['admin', 'analyst'],
      });
      setShowCreateForm(false);

      await fetchPolicies();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleApproveRequest = async (approvalId: string, approve: boolean) => {
    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch(`/api/tools/approvals/${approvalId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: approve ? 'approved' : 'denied',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update approval');
      }

      await fetchApprovals();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'auto':
        return 'bg-green-900/50 text-green-200';
      case 'approve':
        return 'bg-yellow-900/50 text-yellow-200';
      case 'deny':
        return 'bg-red-900/50 text-red-200';
      default:
        return 'bg-slate-900/50 text-slate-200';
    }
  };

  const getModeDescription = (mode: string) => {
    switch (mode) {
      case 'auto':
        return '✓ Execute automatically';
      case 'approve':
        return '⚠️ Require approval';
      case 'deny':
        return '✗ Block execution';
      default:
        return 'Unknown mode';
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Tool Policies</h1>
        <p className="text-slate-400">Control tool execution and approval workflows</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('policies')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'policies'
              ? 'text-white border-b-2 border-blue-600'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          Policies ({policies.length})
        </button>
        <button
          onClick={() => setActiveTab('approvals')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'approvals'
              ? 'text-white border-b-2 border-blue-600'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          Approvals ({approvals.filter(a => a.status === 'pending').length})
        </button>
      </div>

      {activeTab === 'policies' && (
        <>
          <div className="mb-6">
            <Button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {showCreateForm ? 'Cancel' : '+ Create Policy'}
            </Button>
          </div>

          {showCreateForm && (
            <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
              <h2 className="text-xl font-bold text-white mb-4">Create Tool Policy</h2>

              <form onSubmit={handleCreatePolicy} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Tool Name
                  </label>
                  <Input
                    type="text"
                    value={newPolicy.tool_name}
                    onChange={(e) =>
                      setNewPolicy({ ...newPolicy, tool_name: e.target.value })
                    }
                    placeholder="e.g., file_write, web_fetch, sql_query"
                    required
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Execution Mode
                  </label>
                  <select
                    value={newPolicy.mode}
                    onChange={(e) =>
                      setNewPolicy({ ...newPolicy, mode: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
                  >
                    <option value="auto">✓ Auto (execute immediately)</option>
                    <option value="approve">⚠️ Approve (require human review)</option>
                    <option value="deny">✗ Deny (block execution)</option>
                  </select>
                  <p className="text-xs text-slate-500 mt-2">
                    • Auto: Tool always executes (safest for harmless tools)<br />
                    • Approve: Requires admin review before execution<br />
                    • Deny: Tool never executes (for dangerous operations)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Constraints
                  </label>
                  <div className="space-y-2 text-sm">
                    <div>
                      <label className="text-slate-400">Max File Size (MB)</label>
                      <Input
                        type="number"
                        value={newPolicy.constraints.max_file_size_mb}
                        onChange={(e) =>
                          setNewPolicy({
                            ...newPolicy,
                            constraints: {
                              ...newPolicy.constraints,
                              max_file_size_mb: parseInt(e.target.value),
                            },
                          })
                        }
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>

                    <div>
                      <label className="text-slate-400">Timeout (seconds)</label>
                      <Input
                        type="number"
                        value={newPolicy.constraints.timeout_seconds}
                        onChange={(e) =>
                          setNewPolicy({
                            ...newPolicy,
                            constraints: {
                              ...newPolicy.constraints,
                              timeout_seconds: parseInt(e.target.value),
                            },
                          })
                        }
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="network"
                        checked={newPolicy.constraints.network_enabled}
                        onChange={(e) =>
                          setNewPolicy({
                            ...newPolicy,
                            constraints: {
                              ...newPolicy.constraints,
                              network_enabled: e.target.checked,
                            },
                          })
                        }
                        className="rounded"
                      />
                      <label htmlFor="network" className="text-slate-400">
                        Network access enabled
                      </label>
                    </div>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Create Policy
                </Button>
              </form>
            </Card>
          )}

          <div className="space-y-4">
            {isLoading ? (
              <div className="text-slate-400">⏳ Loading policies...</div>
            ) : policies.length === 0 ? (
              <Card className="p-8 bg-slate-800 border-slate-700 text-center">
                <p className="text-slate-400">No policies yet. Create one to start controlling tool execution.</p>
              </Card>
            ) : (
              policies.map(policy => (
                <Card key={policy.id} className="p-6 bg-slate-800 border-slate-700">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white">{policy.tool_name}</h3>
                      <p className="text-sm text-slate-400">Created {new Date(policy.created_at).toLocaleDateString()}</p>
                    </div>
                    <span className={`px-3 py-1 rounded text-sm font-medium ${getModeColor(policy.mode)}`}>
                      {getModeDescription(policy.mode)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400">Max File Size</p>
                      <p className="text-white">{policy.constraints.max_file_size_mb} MB</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Timeout</p>
                      <p className="text-white">{policy.constraints.timeout_seconds}s</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Network Access</p>
                      <p className="text-white">
                        {policy.constraints.network_enabled ? '✓ Enabled' : '✗ Disabled'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400">Allowed Roles</p>
                      <p className="text-white">{policy.allowed_roles.join(', ')}</p>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </>
      )}

      {activeTab === 'approvals' && (
        <div className="space-y-4">
          {approvals.length === 0 ? (
            <Card className="p-8 bg-slate-800 border-slate-700 text-center">
              <p className="text-slate-400">No pending approvals</p>
            </Card>
          ) : (
            approvals.map(approval => (
              <Card
                key={approval.id}
                className={`p-6 border ${
                  approval.status === 'pending'
                    ? 'bg-yellow-900/20 border-yellow-700'
                    : approval.status === 'approved'
                    ? 'bg-green-900/20 border-green-700'
                    : 'bg-red-900/20 border-red-700'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">{approval.tool_name}</h3>
                    <p className="text-sm text-slate-400">
                      Requested by {approval.requested_by} on{' '}
                      {new Date(approval.requested_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${
                    approval.status === 'pending' ? 'bg-yellow-900/50 text-yellow-200' :
                    approval.status === 'approved' ? 'bg-green-900/50 text-green-200' :
                    'bg-red-900/50 text-red-200'
                  }`}>
                    {approval.status.charAt(0).toUpperCase() + approval.status.slice(1)}
                  </span>
                </div>

                <div className="bg-slate-900/50 p-3 rounded text-xs text-slate-300 font-mono mb-4 max-h-24 overflow-y-auto">
                  <pre>{JSON.stringify(approval.tool_args, null, 2)}</pre>
                </div>

                {approval.status === 'pending' && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleApproveRequest(approval.id, true)}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      ✓ Approve
                    </Button>
                    <Button
                      onClick={() => handleApproveRequest(approval.id, false)}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      ✗ Deny
                    </Button>
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
