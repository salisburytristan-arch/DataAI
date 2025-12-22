'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface AuditEvent {
  id: string;
  event_type: string;
  timestamp: string;
  actor: string;
  payload: Record<string, any>;
  event_hash: string;
  prev_hash: string;
  run_id: string | null;
}

export default function AuditPage() {
  const router = useRouter();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Filter state
  const [filters, setFilters] = useState({
    eventType: '',
    actor: '',
    startDate: '',
    endDate: '',
    runId: '',
  });

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async (query = '') => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('access_token');

      if (!token) {
        router.push('/auth/login');
        return;
      }

      let url = '/api/audit/events';
      const params = new URLSearchParams();

      if (filters.eventType) params.append('event_type', filters.eventType);
      if (filters.actor) params.append('actor', filters.actor);
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.runId) params.append('run_id', filters.runId);

      if (params.toString()) {
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

      if (!response.ok) {
        throw new Error('Failed to fetch audit events');
      }

      const data = await response.json();
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleApplyFilters = () => {
    fetchEvents();
  };

  const handleClearFilters = () => {
    setFilters({
      eventType: '',
      actor: '',
      startDate: '',
      endDate: '',
      runId: '',
    });
    setTimeout(() => fetchEvents(), 0);
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/audit/export', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(filters),
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Download ZIP file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-export-${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'request':
        return 'bg-blue-900/20 border-blue-700';
      case 'response':
        return 'bg-green-900/20 border-green-700';
      case 'error':
        return 'bg-red-900/20 border-red-700';
      case 'auth':
        return 'bg-purple-900/20 border-purple-700';
      case 'tool':
        return 'bg-yellow-900/20 border-yellow-700';
      case 'phi':
        return 'bg-orange-900/20 border-orange-700';
      default:
        return 'bg-slate-900/20 border-slate-700';
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'request':
        return '📥';
      case 'response':
        return '📤';
      case 'error':
        return '⚠️';
      case 'auth':
        return '🔐';
      case 'tool':
        return '🔧';
      case 'phi':
        return '❓';
      default:
        return '📋';
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Audit Trail</h1>
        <p className="text-slate-400">Immutable, tamper-proof event log with hash-chain verification</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Filters */}
      <Card className="p-6 bg-slate-800 border-slate-700 mb-8">
        <h2 className="text-lg font-bold text-white mb-4">Filters</h2>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Event Type
            </label>
            <select
              name="eventType"
              value={filters.eventType}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
            >
              <option value="">All Events</option>
              <option value="request">Request</option>
              <option value="response">Response</option>
              <option value="error">Error</option>
              <option value="auth">Authentication</option>
              <option value="tool">Tool Execution</option>
              <option value="phi">PHI Detection</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Actor (Email)
            </label>
            <Input
              type="text"
              name="actor"
              value={filters.actor}
              onChange={handleFilterChange}
              placeholder="user@example.com"
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Start Date
            </label>
            <Input
              type="date"
              name="startDate"
              value={filters.startDate}
              onChange={handleFilterChange}
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              End Date
            </label>
            <Input
              type="date"
              name="endDate"
              value={filters.endDate}
              onChange={handleFilterChange}
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Run ID
            </label>
            <Input
              type="text"
              name="runId"
              value={filters.runId}
              onChange={handleFilterChange}
              placeholder="UUID or partial"
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            onClick={handleApplyFilters}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Apply Filters
          </Button>
          <Button
            onClick={handleClearFilters}
            className="bg-slate-700 hover:bg-slate-600 text-white"
          >
            Clear
          </Button>
          <Button
            onClick={handleExport}
            disabled={isExporting}
            className="bg-green-600 hover:bg-green-700 text-white ml-auto"
          >
            {isExporting ? 'Exporting...' : '⬇️ Export as ZIP'}
          </Button>
        </div>
      </Card>

      {/* Events List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-slate-400">⏳ Loading events...</div>
        ) : events.length === 0 ? (
          <Card className="p-8 bg-slate-800 border-slate-700 text-center">
            <p className="text-slate-400">No events found matching filters</p>
          </Card>
        ) : (
          <>
            <div className="text-sm text-slate-400 mb-4">
              Showing {events.length} event{events.length !== 1 ? 's' : ''}
            </div>

            {events.map((event, index) => (
              <Card
                key={event.id}
                className={`p-6 border cursor-pointer hover:shadow-lg transition-shadow ${getEventColor(event.event_type)}`}
              >
                <div className="flex items-start gap-4">
                  <div className="text-2xl">{getEventIcon(event.event_type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-mono text-xs bg-slate-900/50 px-2 py-1 rounded text-slate-300">
                        {event.event_type}
                      </span>
                      {event.run_id && (
                        <span className="text-xs text-slate-400">
                          Run: {event.run_id.slice(0, 8)}...
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-slate-300 mb-2">
                      <strong>Actor:</strong> {event.actor}
                    </p>

                    <p className="text-xs text-slate-400 mb-3">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>

                    {/* Payload preview */}
                    <div className="bg-slate-900/50 p-3 rounded text-xs text-slate-300 font-mono mb-3 max-h-24 overflow-y-auto">
                      <pre>{JSON.stringify(event.payload, null, 2)}</pre>
                    </div>

                    {/* Hash information */}
                    <div className="text-xs text-slate-500 space-y-1 border-t border-slate-700 pt-3">
                      <div>
                        <strong>Event Hash:</strong>
                        <code className="block font-mono text-slate-400 break-all">
                          {event.event_hash}
                        </code>
                      </div>
                      <div>
                        <strong>Previous Hash:</strong>
                        <code className="block font-mono text-slate-400 break-all">
                          {event.prev_hash === '0'.repeat(64) ? '(genesis)' : event.prev_hash}
                        </code>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </>
        )}
      </div>

      {/* Info Box */}
      <Card className="mt-8 p-6 bg-blue-900/20 border-blue-700">
        <h3 className="font-semibold text-blue-300 mb-2">🔐 Hash-Chain Security</h3>
        <p className="text-sm text-blue-200 mb-3">
          Every audit event is cryptographically linked to the previous event via SHA256 hashing.
          Tampering with any event will break the chain, immediately visible in verification.
        </p>
        <p className="text-xs text-blue-300">
          Export the audit trail with the hash manifest to verify integrity offline.
        </p>
      </Card>
    </div>
  );
}
