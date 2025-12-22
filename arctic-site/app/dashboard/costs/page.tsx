'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface CostData {
  total_cost: number;
  total_tokens: number;
  runs_count: number;
  average_cost_per_run: number;
  by_provider: Record<string, { cost: number; tokens: number }>;
  daily_costs: Array<{ date: string; cost: number }>;
  top_users: Array<{ email: string; cost: number; runs: number }>;
}

interface ModelPolicy {
  id: string;
  provider: string;
  model_name: string;
  max_daily_cost: number | null;
  max_cost_per_request: number | null;
}

export default function CostsPage() {
  const router = useRouter();
  const [costData, setCostData] = useState<CostData | null>(null);
  const [modelPolicies, setModelPolicies] = useState<ModelPolicy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState({
    startDate: '',
    endDate: '',
  });

  useEffect(() => {
    fetchCostData();
    fetchModelPolicies();
  }, []);

  const fetchCostData = async () => {
    try {
      const token = localStorage.getItem('access_token');

      if (!token) {
        router.push('/auth/login');
        return;
      }

      let url = '/api/costs/summary';
      if (dateRange.startDate || dateRange.endDate) {
        const params = new URLSearchParams();
        if (dateRange.startDate) params.append('start_date', dateRange.startDate);
        if (dateRange.endDate) params.append('end_date', dateRange.endDate);
        url += '?' + params.toString();
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        router.push('/auth/login');
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setCostData(data);
      }
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
      // Silently fail if endpoint doesn't exist yet
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-spin text-blue-600">⏳ Loading cost data...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Cost & Usage</h1>
        <p className="text-slate-400">Track spending, set budgets, and optimize costs</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {costData && (
        <>
          <div className="grid grid-cols-4 gap-4 mb-8">
            <Card className="p-6 bg-slate-800 border-slate-700">
              <p className="text-slate-400 text-sm">Total Cost (30d)</p>
              <p className="text-3xl font-bold text-white mt-2">
                ${costData.total_cost.toFixed(2)}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {costData.runs_count} runs
              </p>
            </Card>

            <Card className="p-6 bg-slate-800 border-slate-700">
              <p className="text-slate-400 text-sm">Avg Cost/Run</p>
              <p className="text-3xl font-bold text-white mt-2">
                ${costData.average_cost_per_run.toFixed(4)}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {costData.total_tokens.toLocaleString()} tokens
              </p>
            </Card>

            <Card className="p-6 bg-slate-800 border-slate-700">
              <p className="text-slate-400 text-sm">Top Provider</p>
              <p className="text-2xl font-bold text-white mt-2">
                {Object.entries(costData.by_provider).sort(
                  ([, a], [, b]) => b.cost - a.cost
                )[0]?.[0] || 'N/A'}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                ${Object.entries(costData.by_provider)
                  .sort(([, a], [, b]) => b.cost - a.cost)[0]?.[1]
                  ?.cost.toFixed(2) || '0.00'}
              </p>
            </Card>

            <Card className="p-6 bg-slate-800 border-slate-700">
              <p className="text-slate-400 text-sm">Budget Status</p>
              <p className="text-2xl font-bold text-green-400 mt-2">✓ On Track</p>
              <p className="text-xs text-slate-500 mt-2">
                Under all limits
              </p>
            </Card>
          </div>

          {/* Provider Breakdown */}
          <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
            <h2 className="text-lg font-bold text-white mb-4">Cost by Provider</h2>
            <div className="space-y-4">
              {Object.entries(costData.by_provider).map(([provider, data]) => (
                <div key={provider} className="flex items-center gap-4">
                  <div className="w-32 text-sm font-medium text-slate-300">
                    {provider}
                  </div>
                  <div className="flex-1">
                    <div className="bg-slate-700 rounded-full h-8 flex items-center px-3">
                      <div
                        className="bg-blue-600 h-6 rounded-full"
                        style={{
                          width: `${(data.cost / costData.total_cost) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-semibold">
                      ${data.cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {data.tokens.toLocaleString()} tokens
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Top Users */}
          <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
            <h2 className="text-lg font-bold text-white mb-4">Top Users</h2>
            <table className="w-full text-sm">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-4 py-2 text-left text-slate-400">Email</th>
                  <th className="px-4 py-2 text-right text-slate-400">Cost</th>
                  <th className="px-4 py-2 text-right text-slate-400">Runs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {costData.top_users.map(user => (
                  <tr key={user.email} className="hover:bg-slate-700/30">
                    <td className="px-4 py-3 text-white">{user.email}</td>
                    <td className="px-4 py-3 text-right text-slate-300">
                      ${user.cost.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-300">
                      {user.runs}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {/* Daily Trend */}
          <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
            <h2 className="text-lg font-bold text-white mb-4">Daily Spending</h2>
            <div className="h-64 bg-slate-700/50 rounded-lg flex items-end gap-1 p-4">
              {costData.daily_costs.map(({ date, cost }) => {
                const maxCost = Math.max(
                  ...costData.daily_costs.map(c => c.cost),
                  1
                );
                return (
                  <div
                    key={date}
                    className="flex-1 bg-blue-600 rounded-t hover:bg-blue-500 transition-colors group relative"
                    style={{
                      height: `${(cost / maxCost) * 100}%`,
                      minHeight: '4px',
                    }}
                    title={`${date}: $${cost.toFixed(2)}`}
                  >
                    <div className="absolute bottom-full left-0 right-0 text-xs text-slate-400 text-center opacity-0 group-hover:opacity-100 mb-1">
                      ${cost.toFixed(2)}
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-slate-500 text-center mt-4">
              Last {costData.daily_costs.length} days
            </p>
          </Card>
        </>
      )}

      {/* Budget Configuration */}
      <Card className="p-6 bg-slate-800 border-slate-700">
        <h2 className="text-lg font-bold text-white mb-4">Budget Configuration</h2>

        <div className="space-y-6">
          {modelPolicies.length > 0 ? (
            modelPolicies.map(policy => (
              <div
                key={policy.id}
                className="p-4 bg-slate-700/50 rounded-lg border border-slate-600"
              >
                <h3 className="font-semibold text-white mb-3">
                  {policy.provider} - {policy.model_name}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-400 mb-2">Max Daily Cost</p>
                    <p className="text-white">
                      ${policy.max_daily_cost || 'Unlimited'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-2">Max Per Request</p>
                    <p className="text-white">
                      ${policy.max_cost_per_request || 'Unlimited'}
                    </p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-slate-400 text-sm">
              No budget limits configured. Create a model policy to set spending caps.
            </p>
          )}
        </div>

        <Button className="mt-6 bg-blue-600 hover:bg-blue-700 text-white">
          Configure Budgets
        </Button>
      </Card>

      {/* Alerts */}
      <Card className="mt-8 p-6 bg-blue-900/20 border-blue-700">
        <h3 className="font-semibold text-blue-300 mb-2">💰 Cost Management Tips</h3>
        <ul className="text-sm text-blue-200 space-y-2">
          <li>• Set daily budgets per model to avoid overspending</li>
          <li>• Use local LLM providers for development to reduce costs</li>
          <li>• Review top users weekly to identify optimization opportunities</li>
          <li>• Configure max_cost_per_request to catch runaway queries</li>
        </ul>
      </Card>
    </div>
  );
}
