'use client';

import React, { useState, useEffect } from 'react';
import Navigation from '@/components/Navigation';

interface ToolTrace {
  tool_name: string;
  input_params: Record<string, any>;
  output_summary: Record<string, any>;
  duration_ms: number;
  timestamp: string;
}

interface DisputeOption {
  id: string;
  razorpay_dispute_id: string;
  status: string;
  dispute_amount: number;
}

export default function AgentTraceVisualizer() {
  const [disputes, setDisputes] = useState<DisputeOption[]>([]);
  const [selectedDisputeId, setSelectedDisputeId] = useState<string>('');
  const [traces, setTraces] = useState<ToolTrace[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchDisputes = async () => {
      try {
        const res = await fetch(`/api/v1/disputes`);
        if (res.ok) {
          const data = await res.json();
          setDisputes(data);
          if (data.length > 0) {
            setSelectedDisputeId(data[0].id);
          }
        }
      } catch (e) {
        console.error('Failed to fetch disputes for trace selector', e);
      }
    };
    fetchDisputes();
  }, []);

  const fetchTrace = async (id: string) => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/disputes/${id}/trace`);
      if (res.ok) {
        const data = await res.json();
        setTraces(data.tool_traces || []);
      }
    } catch (e) {
      console.error('Failed to fetch trace log', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDisputeId) {
      fetchTrace(selectedDisputeId);
    }
  }, [selectedDisputeId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navigation />

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">AI Agent Tool Execution Trace</h1>
            <p className="text-xs text-slate-400 mt-1">Real-time visual timeline of sandboxed tool invocations during dispute investigation</p>
          </div>

          {/* Dispute Selector */}
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-slate-400">Select Dispute Case:</span>
            <select
              value={selectedDisputeId}
              onChange={(e) => setSelectedDisputeId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white text-xs rounded-lg px-3 py-2 font-mono font-bold focus:outline-none focus:border-indigo-500"
            >
              {disputes.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.razorpay_dispute_id} (₹{d.dispute_amount.toLocaleString('en-IN')})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Trace Visualizer List */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-2xl relative">
          {loading ? (
            <div className="py-12 text-center text-slate-500 text-xs animate-pulse">
              Tracing AI Tool Call Sequence...
            </div>
          ) : traces.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No tool execution trace records found for selected dispute.
            </div>
          ) : (
            <div className="relative border-l-2 border-indigo-500/40 ml-4 pl-8 space-y-8">
              {traces.map((trace, i) => (
                <div key={i} className="relative group">
                  {/* Timeline Bullet */}
                  <div className="absolute -left-[41px] top-1.5 w-5 h-5 rounded-full bg-indigo-600 border-4 border-slate-950 shadow-md shadow-indigo-500/50 flex items-center justify-center font-mono text-[9px] font-bold text-white">
                    {i + 1}
                  </div>

                  {/* Card Content */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800/80 bg-slate-900/60 hover:border-indigo-500/40 transition-all shadow-lg">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="font-mono text-sm font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-lg">
                          {trace.tool_name}()
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">
                          Latency: <strong className="text-slate-300">{trace.duration_ms}ms</strong>
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(trace.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                      <div>
                        <span className="text-[11px] font-semibold text-slate-400 block mb-1">INPUT PARAMS</span>
                        <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-emerald-400 overflow-x-auto text-[11px]">
                          {JSON.stringify(trace.input_params, null, 2)}
                        </pre>
                      </div>

                      <div>
                        <span className="text-[11px] font-semibold text-slate-400 block mb-1">RETRIEVED OUTPUT</span>
                        <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-indigo-300 overflow-x-auto text-[11px]">
                          {JSON.stringify(trace.output_summary, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
