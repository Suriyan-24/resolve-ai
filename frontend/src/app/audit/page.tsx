'use client';

import React, { useState, useEffect } from 'react';
import Navigation from '@/components/Navigation';

interface AuditLogEntry {
  id: string;
  dispute_id: string;
  actor_type: string;
  actor_id: string;
  action_taken: string;
  payload: Record<string, any>;
  timestamp: string;
}

export default function AuditTrailPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/audit`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (e) {
      console.error('Failed to fetch audit logs', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navigation />

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        <div className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Immutable Audit Log Trail</h1>
            <p className="text-xs text-slate-400 mt-1">Cryptographic compliance log tracking all system, AI agent, and human user decisions</p>
          </div>
          <button
            onClick={fetchAuditLogs}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg text-xs font-semibold border border-slate-800 transition-colors"
          >
            🔄 Refresh Trail
          </button>
        </div>

        {/* Audit Logs Table */}
        <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Actor</th>
                <th className="px-6 py-4">Action Taken</th>
                <th className="px-6 py-4">Dispute Target</th>
                <th className="px-6 py-4">Context Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    Loading audit trail entries...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    No audit records logged yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const actorColor =
                    log.actor_type === 'AI_AGENT'
                      ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      : log.actor_type === 'HUMAN_USER'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20';

                  return (
                    <tr key={log.id} className="hover:bg-slate-900/50 transition-colors">
                      <td className="px-6 py-4 text-slate-400 text-[11px]">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold border ${actorColor}`}>
                          {log.actor_type}: {log.actor_id}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-bold text-white">
                        {log.action_taken}
                      </td>
                      <td className="px-6 py-4 text-indigo-300">
                        {log.dispute_id ? log.dispute_id.substring(0, 13) : 'GLOBAL'}
                      </td>
                      <td className="px-6 py-4">
                        <pre className="text-[10px] text-slate-400 bg-slate-950 p-2 rounded border border-slate-800/60 overflow-x-auto max-w-xs">
                          {JSON.stringify(log.payload)}
                        </pre>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
