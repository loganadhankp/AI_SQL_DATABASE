import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Table, 
  MessageSquare, 
  CheckCircle, 
  XCircle, 
  ArrowRight,
  TrendingUp,
  Activity
} from 'lucide-react';
import { dashboardAPI } from '../services/api';

export default function DashboardOverview({ setActiveTab, activeConnection }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const res = await dashboardAPI.getOverview();
        setMetrics(res.data);
      } catch (err) {
        console.error('Failed to load dashboard overview:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchOverview();
  }, [activeConnection]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-sky-950/40 border border-slate-800 rounded-2xl p-8 relative overflow-hidden shadow-2xl">
        <div className="relative z-10 max-w-2xl">
          <span className="text-xs font-semibold text-sky-400 uppercase tracking-widest bg-sky-500/10 border border-sky-500/20 px-2.5 py-1 rounded-full">
            Autonomous SQL Agent
          </span>
          <h1 className="text-2xl font-bold text-white mt-3 tracking-tight">
            Conversational Relational Database Analytics
          </h1>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed">
            Interact with your databases using plain English. Our LangGraph agent automatically inspects live schemas, produces validated read-only SQL, self-heals from syntax errors, and plots interactive visual insights.
          </p>
          <div className="mt-5 flex gap-3">
            <button
              onClick={() => setActiveTab('analyst')}
              className="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs px-4 py-2.5 rounded-lg shadow-lg shadow-sky-500/25 transition-all"
            >
              <span>Launch AI Analyst</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('explorer')}
              className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs px-4 py-2.5 rounded-lg border border-slate-700 transition-colors"
            >
              <span>Explore Schema</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Target Database</span>
            <Database className="w-4 h-4 text-sky-400" />
          </div>
          <p className="text-xl font-bold text-slate-100 mt-2 truncate">
            {metrics?.active_connection?.database_name || 'None'}
          </p>
          <span className="text-xs text-slate-500 mt-1 block truncate">
            {metrics?.active_connection ? `${metrics.active_connection.host}:${metrics.active_connection.port}` : 'Connect in Connections tab'}
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Accessible Tables</span>
            <Table className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-xl font-bold text-slate-100 mt-2">
            {metrics?.accessible_tables_count || 0}
          </p>
          <span className="text-xs text-emerald-400 mt-1 block">Live introspection active</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Total AI Queries</span>
            <MessageSquare className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-xl font-bold text-slate-100 mt-2">
            {metrics?.total_queries || 0}
          </p>
          <span className="text-xs text-slate-500 mt-1 block">Audit log recorded</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Execution Success</span>
            <TrendingUp className="w-4 h-4 text-sky-400" />
          </div>
          <div className="flex items-baseline space-x-2 mt-2">
            <span className="text-xl font-bold text-slate-100">{metrics?.successful_queries || 0}</span>
            <span className="text-xs text-emerald-400 font-medium">passed</span>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-rose-400 font-medium">{metrics?.failed_queries || 0} failed</span>
          </div>
          <span className="text-xs text-slate-500 mt-1 block">AST protected read-only</span>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Activity className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Recent Analytical Inquiries
            </h2>
          </div>
          <button
            onClick={() => setActiveTab('history')}
            className="text-xs text-sky-400 hover:text-sky-300 font-medium"
          >
            View Full History →
          </button>
        </div>

        {metrics?.recent_history?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Question</th>
                  <th className="py-2.5 px-4 font-semibold">Generated SQL</th>
                  <th className="py-2.5 px-4 font-semibold">Status</th>
                  <th className="py-2.5 px-4 font-semibold">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {metrics.recent_history.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-slate-200 font-medium max-w-xs truncate">
                      {h.question}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-sky-300 max-w-sm truncate">
                      {h.generated_sql || '—'}
                    </td>
                    <td className="py-3 px-4">
                      {h.execution_status === 'completed' || h.execution_status === 'success' ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          <CheckCircle className="w-3 h-3" /> Success
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                          <XCircle className="w-3 h-3" /> {h.execution_status}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono">
                      {h.execution_time_ms ? `${h.execution_time_ms} ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-slate-500 py-6 text-center">
            No queries recorded yet. Launch the AI Analyst to ask your first question!
          </p>
        )}
      </div>
    </div>
  );
}
