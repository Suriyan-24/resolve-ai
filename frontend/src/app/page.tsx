'use client';

import React, { useState, useEffect } from 'react';

interface HealthData {
  status: string;
  app_name: string;
  environment: str;
  database_connected: boolean;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/health`);
      if (!res.ok) {
        throw new Error(`HTTP Error ${res.status}`);
      }
      const data: HealthData = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="min-h-screen flex flex-col justify-between p-8 max-w-6xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-xl shadow-lg shadow-indigo-500/30">
            R
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">ResolveAI</h1>
            <p className="text-xs text-slate-400">Razorpay Buildathon — AI Risk Manager</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Phase 1 Bootstrapped
          </span>
        </div>
      </header>

      {/* Main Shell Content */}
      <main className="my-12 space-y-8">
        <div className="glass-panel rounded-2xl p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute -top-24 -right-24 w-72 h-72 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>

          <h2 className="text-2xl font-bold text-white mb-2">ResolveAI Application Shell</h2>
          <p className="text-slate-300 text-sm max-w-2xl leading-relaxed mb-6">
            The foundation for AI dispute triage, machine learning risk scoring, policy guardrails, and automated chargeback defense is online.
          </p>

          <div className="border-t border-slate-800 pt-6">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Backend Connectivity Test
            </h3>

            <div className="flex items-center space-x-4">
              <button
                onClick={checkHealth}
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm transition-all duration-200 shadow-lg shadow-indigo-600/25 disabled:opacity-50"
              >
                {loading ? 'Checking Gateway...' : 'Ping FastAPI Gateway'}
              </button>

              {health && (
                <div className="flex items-center space-x-3 text-xs bg-slate-900/80 px-4 py-2 rounded-lg border border-slate-800">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="text-slate-300 font-medium">{health.app_name}</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400">DB: {health.database_connected ? 'Connected' : 'Disconnected'}</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-emerald-400 font-semibold uppercase">{health.status}</span>
                </div>
              )}

              {error && (
                <div className="flex items-center space-x-2 text-xs bg-rose-500/10 text-rose-400 px-4 py-2 rounded-lg border border-rose-500/20">
                  <span>⚠️ Connection Error: {error}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Phase Breakdown Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-xl">
            <div className="text-indigo-400 font-mono text-xs mb-2">PHASE 1 (COMPLETE)</div>
            <h4 className="font-bold text-white text-base mb-1">Architecture & Skeleton</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              FastAPI gateway, SQLite/Postgres connection layer, ML risk engine interface, next.js UI shell, pytest suite.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-xl opacity-60">
            <div className="text-slate-500 font-mono text-xs mb-2">PHASE 2 (NEXT)</div>
            <h4 className="font-bold text-slate-300 text-base mb-1">Persistence & Schema</h4>
            <p className="text-slate-500 text-xs leading-relaxed">
              PostgreSQL relational tables, Alembic migrations, database models, and synthetic seed generator.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-xl opacity-60">
            <div className="text-slate-500 font-mono text-xs mb-2">PHASE 3</div>
            <h4 className="font-bold text-slate-300 text-base mb-1">ML Risk Engine</h4>
            <p className="text-slate-500 text-xs leading-relaxed">
              Synthetic dataset generator, model training pipeline, precision/recall held-out evaluation report.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 pt-6 text-center text-xs text-slate-500">
        ResolveAI Prototype — Designed for Razorpay Buildathon 2026
      </footer>
    </div>
  );
}
