'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Navigation from '@/components/Navigation';

interface DisputeDetail {
  id: string;
  razorpay_dispute_id: string;
  status: string;
  dispute_amount: number;
  reason_code: string;
  respond_by: string;
  created_at: string;
  transaction: {
    razorpay_payment_id: string;
    amount: number;
    payment_method: string;
    device_fingerprint: string;
    ip_country: string;
  };
  customer: {
    email: string;
    total_orders: number;
    historical_disputes: number;
  };
  order: {
    delivery_status: string;
    tracking_number: string;
    carrier_delivered_at: string;
  };
  risk_score: {
    score: number;
    level: string;
    feature_contributions: Record<string, number>;
  };
  decision: {
    recommendation: string;
    confidence: number;
    executive_summary: string;
    supporting_evidence: string[];
    contradicting_evidence: string[];
    human_approval_required: boolean;
  };
}

export default function DisputeHeroScreen() {
  const params = useParams();
  const disputeId = params.id as string;

  const [dispute, setDispute] = useState<DisputeDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionOutput, setActionOutput] = useState<any | null>(null);
  const [actionExecuting, setActionExecuting] = useState<boolean>(false);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/disputes/${disputeId}`);
      if (res.ok) {
        const data = await res.json();
        setDispute(data);
      }
    } catch (e) {
      console.error('Failed to fetch dispute detail', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (disputeId) {
      fetchDetail();
    }
  }, [disputeId]);

  const executeAction = async (actionType: 'DEFEND' | 'ACCEPT' | 'ESCALATE_FOR_REVIEW', isHuman: boolean = true) => {
    if (!dispute) return;
    setActionExecuting(true);
    setActionOutput(null);

    try {
      const payload = {
        dispute_id: dispute.id,
        action: actionType,
        actor_type: isHuman ? 'HUMAN_USER' : 'AI_AGENT',
        actor_id: isHuman ? 'merchant_admin_42' : 'ResolveAI_Investigator_v1',
        risk_score: dispute.risk_score.score,
        dispute_amount: dispute.dispute_amount,
        ai_confidence: dispute.decision.confidence,
        supporting_evidence: dispute.decision.supporting_evidence
      };

      const res = await fetch(`/api/v1/actions/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const result = await res.json();
        setActionOutput(result);
        fetchDetail();
      }
    } catch (e) {
      console.error('Action execution failed', e);
    } finally {
      setActionExecuting(false);
    }
  };

  if (loading || !dispute) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <Navigation />
        <div className="flex-1 flex items-center justify-center">
          <p className="text-slate-400 animate-pulse text-sm">Loading Dispute Investigation Details...</p>
        </div>
      </div>
    );
  }

  const riskPct = Math.round(dispute.risk_score.score * 100);
  const isHighRisk = dispute.risk_score.level === 'HIGH';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navigation />

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Top Header Banner */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-black text-white tracking-tight">DISPUTE #{dispute.razorpay_dispute_id}</h1>
              <span className={`px-3 py-0.5 rounded-full text-xs font-bold uppercase border ${
                dispute.status === 'DEFENDED'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}>
                {dispute.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Customer: <span className="text-slate-200 font-semibold">{dispute.customer.email}</span> | Reason: <span className="text-indigo-400 font-medium">{dispute.reason_code}</span>
            </p>
          </div>

          <div className="text-right">
            <div className="text-3xl font-black text-white">₹{dispute.dispute_amount.toLocaleString('en-IN')}</div>
            <div className="text-[11px] text-slate-400">Respond By: {new Date(dispute.respond_by).toLocaleDateString()}</div>
          </div>
        </div>

        {/* Hero Grid: Risk Gauge & AI Executive Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Radial ML Risk Gauge */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-center relative overflow-hidden">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">ML Risk Engine Score</div>
            
            <div className="relative w-40 h-40 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-slate-800"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={isHighRisk ? "text-rose-500" : "text-emerald-400"}
                  strokeDasharray={`${riskPct}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-4xl font-black text-white">{riskPct}%</span>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded mt-1 ${
                  isHighRisk ? "bg-rose-500/20 text-rose-300" : "bg-emerald-500/20 text-emerald-300"
                }`}>
                  {dispute.risk_score.level} RISK
                </span>
              </div>
            </div>

            <div className="w-full mt-6 space-y-2 border-t border-slate-800 pt-4 text-left text-xs">
              <span className="text-slate-400 font-semibold block text-[11px] uppercase">Top Feature Contributions:</span>
              {Object.entries(dispute.risk_score.feature_contributions).map(([k, v]) => (
                <div key={k} className="flex justify-between text-slate-300">
                  <span>{k}</span>
                  <span className={v > 0 ? "text-rose-400 font-semibold" : "text-emerald-400 font-semibold"}>
                    {v > 0 ? `+${v}` : v}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Executive Summary & Recommendation Box */}
          <div className="md:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping"></span>
                  <h3 className="font-bold text-white text-base">AI Investigator Recommendation</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">Confidence:</span>
                  <span className="text-xs font-extrabold text-indigo-400">{(dispute.decision.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="mt-4 flex items-center space-x-4">
                <span className="px-4 py-1.5 rounded-xl text-lg font-black bg-indigo-600 text-white shadow-lg shadow-indigo-600/30">
                  {dispute.decision.recommendation}
                </span>
                <p className="text-slate-300 text-xs leading-relaxed">
                  {dispute.decision.executive_summary}
                </p>
              </div>
            </div>

            {/* Evidence Matrix */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
              <div className="bg-emerald-500/5 border border-emerald-500/20 p-4 rounded-xl">
                <span className="text-xs font-bold text-emerald-400 block mb-2">Supporting Evidence (DEFEND)</span>
                <ul className="space-y-1 text-xs text-slate-300">
                  {dispute.decision.supporting_evidence.map((ev, i) => (
                    <li key={i} className="flex items-start space-x-2">
                      <span className="text-emerald-400">✓</span>
                      <span>{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-rose-500/5 border border-rose-500/20 p-4 rounded-xl">
                <span className="text-xs font-bold text-rose-400 block mb-2">Contradicting / Risk Flags</span>
                <ul className="space-y-1 text-xs text-slate-300">
                  {dispute.decision.contradicting_evidence.length === 0 ? (
                    <li className="text-slate-500 text-xs italic">No contradicting flags detected</li>
                  ) : (
                    dispute.decision.contradicting_evidence.map((ev, i) => (
                      <li key={i} className="flex items-start space-x-2">
                        <span className="text-rose-400">⚠</span>
                        <span>{ev}</span>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>

            {/* Action Controls */}
            <div className="border-t border-slate-800 pt-4 flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Policy State: <span className="text-white font-bold">{dispute.decision.human_approval_required ? 'REQUIRES_HUMAN_APPROVAL' : 'ALLOWED'}</span>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => executeAction('DEFEND', true)}
                  disabled={actionExecuting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-50"
                >
                  Approve AI Defense
                </button>
                <button
                  onClick={() => executeAction('ACCEPT', true)}
                  disabled={actionExecuting}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-rose-600/20 transition-all disabled:opacity-50"
                >
                  Accept Liability
                </button>
              </div>
            </div>

            {/* Policy Execution Alert Output */}
            {actionOutput && (
              <div className={`p-4 rounded-xl border text-xs font-medium ${
                actionOutput.outcome === 'ALLOWED'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : actionOutput.outcome === 'REQUIRES_HUMAN_APPROVAL'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              }`}>
                <div className="font-bold mb-1">
                  Policy Result: {actionOutput.outcome} ({actionOutput.rule_triggered})
                </div>
                <p>{actionOutput.reason}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
