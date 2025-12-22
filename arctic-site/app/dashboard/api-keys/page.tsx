'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  is_active: boolean;
  last_used_at: string | null;
}

interface NewAPIKey {
  id: string;
  key: string;
  key_prefix: string;
  name: string;
  created_at: string;
}

export default function APIKeysPage() {
  const router = useRouter();
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newKey, setNewKey] = useState<NewAPIKey | null>(null);
  const [keyName, setKeyName] = useState('');

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        router.push('/auth/login');
        return;
      }

      const response = await fetch('/api/api-keys', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        router.push('/auth/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch API keys');
      }

      const data = await response.json();
      setKeys(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!keyName.trim()) {
      setError('Key name is required');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('/api/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: keyName }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create API key');
      }

      const data = await response.json() as NewAPIKey;
      setNewKey(data);
      setKeyName('');
      
      // Refresh keys list
      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Revoke this API key? Any integrations using it will stop working.')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`/api/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to revoke API key');
      }

      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-spin text-blue-600">⏳ Loading API keys...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">API Keys</h1>
        <p className="text-slate-400">Manage programmatic access to your organization</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {newKey && (
        <Card className="p-6 bg-green-900/20 border-green-700 mb-8">
          <h2 className="text-lg font-bold text-green-300 mb-4">✓ API Key Created</h2>
          <p className="text-slate-300 mb-4">
            Save this key now. You won't be able to see it again!
          </p>
          
          <div className="bg-slate-900 p-4 rounded-lg mb-4 font-mono text-sm break-all">
            <code className="text-slate-300">{newKey.key}</code>
          </div>
          
          <div className="flex gap-2">
            <Button
              onClick={() => copyToClipboard(newKey.key)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Copy to Clipboard
            </Button>
            <Button
              onClick={() => setNewKey(null)}
              className="bg-slate-700 hover:bg-slate-600 text-white"
            >
              Done
            </Button>
          </div>
        </Card>
      )}

      <div className="mb-6">
        <Button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          {showCreateForm ? 'Cancel' : '+ Create API Key'}
        </Button>
      </div>

      {showCreateForm && (
        <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Create API Key</h2>
          
          <form onSubmit={handleCreateKey} className="flex gap-3">
            <Input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g., GitHub Actions, Production API"
              className="bg-slate-700 border-slate-600 text-white flex-1"
            />
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create
            </Button>
          </form>
          
          <p className="text-xs text-slate-500 mt-3">
            API keys can be used to access the ArcticCodex API programmatically.
            Treat them like passwords and keep them secret.
          </p>
        </Card>
      )}

      <Card className="bg-slate-800 border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700 border-b border-slate-600">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Name
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Key Prefix
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Created
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Last Used
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">
                Status
              </th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-slate-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {keys.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                  No API keys yet. Create one to get started.
                </td>
              </tr>
            ) : (
              keys.map(key => (
                <tr key={key.id} className="hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-sm text-slate-300 font-medium">
                    {key.name}
                  </td>
                  <td className="px-6 py-4 text-sm font-mono text-slate-400">
                    {key.key_prefix}***
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-400">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-400">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : 'Never'
                    }
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`${
                      key.is_active ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {key.is_active ? '✓ Active' : '✗ Revoked'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-right">
                    {key.is_active && (
                      <button
                        onClick={() => handleRevokeKey(key.id)}
                        className="text-red-400 hover:text-red-300 font-medium"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      <div className="mt-8 p-6 bg-blue-900/20 border border-blue-700 rounded-lg">
        <h3 className="font-semibold text-blue-200 mb-2">Usage Example</h3>
        <code className="text-sm text-blue-300 block bg-slate-900 p-4 rounded font-mono break-words">
          curl -H "Authorization: Bearer ac_your_key_here" \<br/>
          &nbsp;&nbsp;https://api.arcticcodex.com/agents/run \<br/>
          &nbsp;&nbsp;-d &#123;"query": "Analyze this"&#125;
        </code>
      </div>
    </div>
  );
}
