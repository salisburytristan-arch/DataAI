'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface ModelPolicy {
  id: string;
  provider: string;
  model_name: string;
  max_rpm: number | null;
  max_tpm: number | null;
  max_daily_cost: number | null;
}

interface OrgSettings {
  display_name: string;
  settings: Record<string, any>;
}

export default function SettingsPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<OrgSettings | null>(null);
  const [modelPolicies, setModelPolicies] = useState<ModelPolicy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'general' | 'models'>('general');
  const [showNewModelForm, setShowNewModelForm] = useState(false);

  const [orgForm, setOrgForm] = useState({
    display_name: '',
  });

  const [newModel, setNewModel] = useState({
    provider: 'openai',
    model_name: 'gpt-4',
    max_rpm: 60,
    max_tpm: null,
    max_daily_cost: null,
  });

  useEffect(() => {
    fetchSettings();
    fetchModelPolicies();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('access_token');

      if (!token) {
        router.push('/auth/login');
        return;
      }

      const response = await fetch('/api/orgs', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        router.push('/auth/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch settings');
      }

      const data = await response.json();
      setSettings(data);
      setOrgForm({ display_name: data.display_name });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchModelPolicies = async () => {
    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/model-policies', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setModelPolicies(data);
      }
    } catch (err) {
      // Silently fail
    }
  };

  const handleUpdateSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const user = JSON.parse(localStorage.getItem('user') || '{}');

      const response = await fetch(`/api/orgs/${user.org_id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(orgForm),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update settings');
      }

      await fetchSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleAddModelPolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/model-policies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newModel),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create policy');
      }

      setNewModel({
        provider: 'openai',
        model_name: 'gpt-4',
        max_rpm: 60,
        max_tpm: null,
        max_daily_cost: null,
      });
      setShowNewModelForm(false);

      await fetchModelPolicies();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-spin text-blue-600">⏳ Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-slate-400">Manage your organization configuration</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('general')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'general'
              ? 'text-white border-b-2 border-blue-600'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          General
        </button>
        <button
          onClick={() => setActiveTab('models')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'models'
              ? 'text-white border-b-2 border-blue-600'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          LLM Models
        </button>
      </div>

      {activeTab === 'general' && settings && (
        <Card className="p-8 bg-slate-800 border-slate-700 max-w-2xl">
          <h2 className="text-xl font-bold text-white mb-6">Organization Settings</h2>

          <form onSubmit={handleUpdateSettings} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Organization Display Name
              </label>
              <Input
                type="text"
                value={orgForm.display_name}
                onChange={(e) =>
                  setOrgForm({ ...orgForm, display_name: e.target.value })
                }
                className="bg-slate-700 border-slate-600 text-white"
              />
              <p className="text-xs text-slate-500 mt-2">
                This is the display name shown throughout the application.
              </p>
            </div>

            <div className="pt-4 border-t border-slate-700">
              <h3 className="font-semibold text-white mb-4">Vault Configuration</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Evidence Chunk Limit
                  </label>
                  <Input
                    type="number"
                    defaultValue="5"
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Maximum number of evidence chunks returned per query
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Retrieval Strategy
                  </label>
                  <select className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm">
                    <option>Semantic (vector similarity)</option>
                    <option>Keyword (BM25)</option>
                    <option>Hybrid (semantic + keyword)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Save Changes
              </Button>
              <Button
                type="button"
                onClick={() => fetchSettings()}
                className="bg-slate-700 hover:bg-slate-600 text-white"
              >
                Reset
              </Button>
            </div>
          </form>

          <div className="mt-8 pt-8 border-t border-slate-700">
            <h3 className="font-semibold text-white mb-4">Danger Zone</h3>
            <Button className="bg-red-900/50 hover:bg-red-900 text-red-200 border border-red-700">
              Delete Organization
            </Button>
            <p className="text-xs text-slate-500 mt-2">
              This action cannot be undone. All data will be permanently deleted.
            </p>
          </div>
        </Card>
      )}

      {activeTab === 'models' && (
        <>
          <div className="mb-6">
            <Button
              onClick={() => setShowNewModelForm(!showNewModelForm)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {showNewModelForm ? 'Cancel' : '+ Add Model'}
            </Button>
          </div>

          {showNewModelForm && (
            <Card className="p-6 bg-slate-800 border-slate-700 mb-8 max-w-2xl">
              <h2 className="text-xl font-bold text-white mb-4">Add LLM Model</h2>

              <form onSubmit={handleAddModelPolicy} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Provider
                  </label>
                  <select
                    value={newModel.provider}
                    onChange={(e) =>
                      setNewModel({ ...newModel, provider: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="local">Local (llama.cpp)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Model Name
                  </label>
                  <Input
                    type="text"
                    value={newModel.model_name}
                    onChange={(e) =>
                      setNewModel({ ...newModel, model_name: e.target.value })
                    }
                    placeholder="gpt-4, claude-3-opus-20240229, etc."
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Max Requests/Min
                    </label>
                    <Input
                      type="number"
                      value={newModel.max_rpm || ''}
                      onChange={(e) =>
                        setNewModel({
                          ...newModel,
                          max_rpm: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Max Tokens/Min
                    </label>
                    <Input
                      type="number"
                      value={newModel.max_tpm || ''}
                      onChange={(e) =>
                        setNewModel({
                          ...newModel,
                          max_tpm: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Max Daily Cost ($)
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newModel.max_daily_cost || ''}
                    onChange={(e) =>
                      setNewModel({
                        ...newModel,
                        max_daily_cost: e.target.value
                          ? parseFloat(e.target.value)
                          : null,
                      })
                    }
                    placeholder="Leave blank for unlimited"
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Add Model
                </Button>
              </form>
            </Card>
          )}

          <div className="space-y-4 max-w-4xl">
            {modelPolicies.length === 0 ? (
              <Card className="p-8 bg-slate-800 border-slate-700 text-center">
                <p className="text-slate-400">
                  No models configured yet. Add your first model to get started.
                </p>
              </Card>
            ) : (
              modelPolicies.map(policy => (
                <Card key={policy.id} className="p-6 bg-slate-800 border-slate-700">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white">
                        {policy.provider}
                      </h3>
                      <p className="text-sm text-slate-400">{policy.model_name}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400">Rate Limit</p>
                      <p className="text-white">
                        {policy.max_rpm ? `${policy.max_rpm} req/min` : 'Unlimited'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400">Token Limit</p>
                      <p className="text-white">
                        {policy.max_tpm ? `${policy.max_tpm} tok/min` : 'Unlimited'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400">Daily Budget</p>
                      <p className="text-white">
                        {policy.max_daily_cost
                          ? `$${policy.max_daily_cost.toFixed(2)}`
                          : 'Unlimited'}
                      </p>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
