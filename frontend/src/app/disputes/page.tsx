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
}

export default function DisputesQueuePage() {
  const [disputes, setDisputes] = useState<DisputeSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchDisputes = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/disputes`);
        if (res.ok) {
          const data = await res.json();
          setDisputes(data);
        }
      } catch (e) {
        console.error('Failed to fetch dispute cases', e);
      } finally {
        setLoading(false);
      }
    };
    fetchDisputes();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navigation />

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        <div className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Active Dispute Case Queue</h1>
            <p className="text-xs text-slate-400 mt-1">Full list of open, defended, and under-review chargebacks</p>
          </div>
        </div>

        <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Dispute ID</th>
                <th className="px-6 py-4">Customer</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">Risk Level</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">AI Rec</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    Loading dispute queue...
                  </td>
                </tr>
              ) : (
                disputes.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="px-6 py-4 font-bold text-white">{d.razorpay_dispute_id}</td>
                    <td className="px-6 py-4 font-sans text-slate-300">{d.customer_email}</td>
                    <td className="px-6 py-4 font-bold text-white">₹{d.dispute_amount.toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        d.risk_level === 'HIGH' ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                      }`}>
                        {(d.risk_score * 100).toFixed(0)}% ({d.risk_level})
                      </span>
                    </td>
                    <td className="px-6 py-4 font-bold uppercase text-amber-400">{d.status}</td>
                    <td className="px-6 py-4 font-bold text-indigo-400">{d.recommendation}</td>
                    <td className="px-6 py-4 text-right font-sans">
                      <Link
                        href={`/disputes/${d.id}`}
                        className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
                      >
                        Investigate →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
