import React, { useState } from 'react';
import { 
  Send, 
  Sparkles, 
  Code2, 
  Copy, 
  Check, 
  BarChart3, 
  Table as TableIcon, 
  Download, 
  Printer, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { analystAPI } from '../services/api';
import ChartRenderer from '../components/ChartRenderer';

const SAMPLE_PROMPTS = [
  "Show the top 10 customers by total purchase amount",
  "Which products generated the highest revenue?",
  "What was the total revenue last month?",
  "Which products have stock below 10?",
  "Find customers who have never placed an order",
  "Compare total orders between cities",
];

export default function AIAnalystPage({ activeConnection }) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('chart'); // 'chart' or 'table'

  const handleQuerySubmit = async (queryText) => {
    const q = queryText || question;
    if (!q.trim()) return;

    if (!activeConnection) {
      setError('Please select an active database connection before submitting questions.');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await analystAPI.query({
        connection_id: activeConnection.id,
        question: q.trim(),
      });
      setResponse(res.data);
      if (res.data.workflow_status === 'failed') {
        setError(res.data.error_message || res.data.final_explanation || 'Query execution could not be completed.');
      } else if (!res.data.suggested_chart || res.data.suggested_chart.chart_type === 'none') {
        setViewMode('table');
      } else {
        setViewMode('chart');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during query execution.');
    } finally {
      setLoading(false);
    }
  };

  const copySQL = () => {
    if (response?.generated_sql) {
      navigator.clipboard.writeText(response.generated_sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadCSV = () => {
    if (!response?.rows || response.rows.length === 0) return;
    const headers = response.columns.join(',');
    const rowsCSV = response.rows.map(row => 
      response.columns.map(col => {
        const val = row[col] === null || row[col] === undefined ? '' : String(row[col]);
        return `"${val.replace(/"/g, '""')}"`;
      }).join(',')
    );
    const csvContent = "data:text/csv;charset=utf-8," + [headers, ...rowsCSV].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `sql_query_result_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const printReport = () => {
    window.print();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Search Input Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-slate-100">Ask Any Question in Plain English</h2>
          </div>
          {activeConnection && (
            <span className="text-xs text-slate-400 font-medium">
              Target DB: <strong className="text-sky-400">{activeConnection.database_name}</strong>
            </span>
          )}
        </div>

        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleQuerySubmit();
          }}
          className="flex gap-3"
        >
          <div className="relative flex-1">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Show top 10 customers by total purchase amount or Which products have stock below 10?"
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="inline-flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-slate-950 font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-sky-500/20 transition-all text-sm shrink-0"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></div>
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>Generate & Execute</span>
                <Send className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Quick Example Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mr-1">Examples:</span>
          {SAMPLE_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuestion(p);
                handleQuerySubmit(p);
              }}
              className="text-xs bg-slate-800/70 hover:bg-slate-800 text-slate-300 hover:text-sky-300 border border-slate-700/60 rounded-lg px-2.5 py-1 transition-all"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start space-x-3 text-rose-400">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Query Failed</p>
            <p className="text-xs mt-0.5 text-rose-300/90">{error}</p>
          </div>
        </div>
      )}

      {/* Clarification Needed Banner */}
      {response?.needs_clarification && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start space-x-3 text-amber-300">
          <Sparkles className="w-5 h-5 shrink-0 mt-0.5 text-amber-400" />
          <div className="text-sm">
            <p className="font-semibold text-amber-200">Clarification Needed</p>
            <p className="text-xs mt-0.5 text-amber-300/90">
              {response.clarification_message || 'Could you please specify which table or metric you are looking for?'}
            </p>
          </div>
        </div>
      )}

      {/* Agent Workflow Execution Timeline Steps */}
      {response?.execution_steps?.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Agentic LangGraph Workflow Execution
            </h3>
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> Total execution: {response.execution_time_ms} ms
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5 pt-1">
            {response.execution_steps.map((step, i) => {
              const isError = step.status === 'failed' || step.status === 'rejected';
              return (
                <div 
                  key={i} 
                  className={`border rounded-lg p-2.5 flex items-start space-x-2 text-xs ${
                    isError 
                      ? 'bg-rose-950/40 border-rose-800/80' 
                      : 'bg-slate-950/70 border-slate-800/80'
                  }`}
                >
                  {isError ? (
                    <AlertCircle className="w-3.5 h-3.5 text-rose-400 mt-0.5 shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                  )}
                  <div className="truncate">
                    <p className="font-semibold text-slate-200 capitalize truncate">
                      {step.node.replace(/_/g, ' ')}
                    </p>
                    <p className="text-[10px] text-slate-500 truncate">{step.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Generated SQL & Insights Panel */}
      {response && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Generated SQL Code Block */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Code2 className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Validated SQL (MySQL 8 Dialect)
                  </span>
                </div>
                <button
                  onClick={copySQL}
                  className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-100 bg-slate-800/80 hover:bg-slate-700/80 px-2.5 py-1 rounded-md transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied!' : 'Copy SQL'}</span>
                </button>
              </div>

              <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-sky-300 overflow-x-auto leading-relaxed">
                <code>{response.generated_sql || '—'}</code>
              </pre>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span>Security: <strong className="text-emerald-400 font-medium">AST-Verified Read-Only SELECT</strong></span>
              <span>Rows Returned: <strong className="text-slate-200">{response.row_count}</strong></span>
            </div>
          </div>

          {/* Right: AI Insights Summary */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between space-y-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Executive Insights
              </span>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {response.final_explanation}
              </p>

              {response.observations?.length > 0 && (
                <ul className="mt-3 space-y-2">
                  {response.observations.map((obs, idx) => (
                    <li key={idx} className="text-xs text-slate-400 flex items-start gap-2">
                      <ChevronRight className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
                      <span>{obs}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800/60 flex items-center gap-2">
              <button
                onClick={downloadCSV}
                disabled={!response.rows || response.rows.length === 0}
                className="flex-1 inline-flex items-center justify-center gap-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 rounded-lg transition-colors disabled:opacity-40"
              >
                <Download className="w-3.5 h-3.5 text-sky-400" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={printReport}
                className="inline-flex items-center justify-center gap-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 p-2 rounded-lg transition-colors"
                title="Print Report"
              >
                <Printer className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Visualizations or Table View */}
      {response?.rows?.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Query Results ({response.row_count} Records)
            </h3>

            {/* View Switcher */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1 space-x-1">
              <button
                onClick={() => setViewMode('chart')}
                disabled={!response.suggested_chart || response.suggested_chart.chart_type === 'none'}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === 'chart'
                    ? 'bg-sky-500 text-slate-950 font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200 disabled:opacity-40'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Chart View</span>
              </button>

              <button
                onClick={() => setViewMode('table')}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-sky-500 text-slate-950 font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <TableIcon className="w-3.5 h-3.5" />
                <span>Table View</span>
              </button>
            </div>
          </div>

          {/* Render Active View */}
          {viewMode === 'chart' && response.suggested_chart && response.suggested_chart.chart_type !== 'none' ? (
            <ChartRenderer chartConfig={response.suggested_chart} data={response.rows} />
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4 font-semibold text-slate-500 w-12">#</th>
                      {response.columns.map((col, idx) => (
                        <th key={idx} className="py-3 px-4 font-semibold uppercase tracking-wider text-slate-300">
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {response.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-2.5 px-4 text-slate-500">{rIdx + 1}</td>
                        {response.columns.map((col, cIdx) => (
                          <td key={cIdx} className="py-2.5 px-4 text-slate-200 truncate max-w-xs">
                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-slate-600">NULL</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
