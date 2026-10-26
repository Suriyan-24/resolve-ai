'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';

interface DisputeSummary {
  id: string;
  razorpay_dispute_id: string;
  dispute_amount: number;
  status: string;
  reason_code: string;
  customer_email: string;
  payment_method: string;
  risk_score: number;
  risk_level: string;
  recommendation: string;
  created_at: string;
}

interface Metrics {
  total_disputes: number;
  high_risk_count: number;
  under_review_count: number;
  protected_funds_inr: number;
}

export default function CommandCenter() {
  const [disputes, setDisputes] = useState<DisputeSummary[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>('ALL');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dispRes, metricRes] = await Promise.all([
        fetch(`/api/v1/disputes`),
        fetch(`/api/v1/disputes/metrics/summary`)
      ]);

      if (dispRes.ok) {
        const data = await dispRes.json();
        setDisputes(data);
      }

      if (metricRes.ok) {
        const mData = await metricRes.json();
        setMetrics(mData);
      }
    } catch (e) {
      console.error('Failed to fetch command center data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredDisputes = disputes.filter((d) => {
    if (filter === 'HIGH_RISK') return d.risk_level === 'HIGH';
    if (filter === 'REVIEW') return d.status === 'UNDER_REVIEW' || d.status === 'OPEN';
    if (filter === 'DEFENDED') return d.status === 'DEFENDED';
    return true;
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navigation />

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Title */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Dispute Command Center</h1>
            <p className="text-xs text-slate-400 mt-1">Real-time AI chargeback triage, risk scoring, and policy enforcement</p>
          </div>
          <button
            onClick={fetchData}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg text-xs font-semibold border border-slate-800 transition-colors"
          >
            🔄 Refresh Queue
          </button>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 shadow-lg">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Disputes Ingested</span>
            <div className="text-3xl font-extrabold text-white mt-2">
              {metrics ? metrics.total_disputes : '--'}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Razorpay Test Mode Ingestion</span>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-rose-500/20 bg-rose-500/5 shadow-lg">
            <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">High Risk Cases</span>
            <div className="text-3xl font-extrabold text-rose-400 mt-2">
              {metrics ? metrics.high_risk_count : '--'}
            </div>
            <span className="text-[11px] text-rose-300/60 mt-1 block">Risk Score ≥ 70%</span>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-amber-500/20 bg-amber-500/5 shadow-lg">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Under Human Review</span>
            <div className="text-3xl font-extrabold text-amber-400 mt-2">
              {metrics ? metrics.under_review_count : '--'}
            </div>
            <span className="text-[11px] text-amber-300/60 mt-1 block">Escalated by Policy Engine</span>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 shadow-lg">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Protected Funds</span>
            <div className="text-3xl font-extrabold text-emerald-400 mt-2">
              ₹{metrics ? metrics.protected_funds_inr.toLocaleString('en-IN') : '--'}
            </div>
            <span className="text-[11px] text-emerald-300/60 mt-1 block">Successfully Defended</span>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-4">
          {[
            { id: 'ALL', label: 'All Cases' },
            { id: 'HIGH_RISK', label: 'High Risk (≥ 70%)' },
            { id: 'REVIEW', label: 'Under Review' },
            { id: 'DEFENDED', label: 'Defended' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === tab.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Disputes Table */}
        <div className="glass-panel rounded-xl overflow-hidden border border-slate-800 shadow-xl">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Dispute ID</th>
                <th className="px-6 py-4">Customer</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">ML Risk Score</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">AI Recommendation</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    Loading dispute queue...
                  </td>
                </tr>
              ) : filteredDisputes.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    No disputes match current filter criteria.
                  </td>
                </tr>
              ) : (
                filteredDisputes.map((d) => {
                  const riskColor =
                    d.risk_level === 'HIGH'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      : d.risk_level === 'MEDIUM'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';

                  const statusColor =
                    d.status === 'DEFENDED'
                      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                      : d.status === 'ACCEPTED'
                      ? 'text-slate-400 bg-slate-800 border-slate-700'
                      : 'text-amber-400 bg-amber-500/10 border-amber-500/20';

                  return (
                    <tr key={d.id} className="hover:bg-slate-900/50 transition-colors">
                      <td className="px-6 py-4 font-mono font-bold text-white">
                        {d.razorpay_dispute_id}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {d.customer_email}
                      </td>
                      <td className="px-6 py-4 font-semibold text-white">
                        ₹{d.dispute_amount.toLocaleString('en-IN')}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold border ${riskColor}`}>
                          {(d.risk_score * 100).toFixed(0)}% ({d.risk_level})
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusColor}`}>
                          {d.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-bold text-indigo-400">
                        {d.recommendation}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          href={`/disputes/${d.id}`}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-xs shadow-sm transition-all"
                        >
                          Investigate →
                        </Link>
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
