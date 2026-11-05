import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  CheckCircle, 
  XCircle, 
  Trash2, 
  Code2, 
  Play, 
  Clock 
} from 'lucide-react';
import { historyAPI } from '../services/api';

export default function QueryHistoryPage({ setActiveTab, setPresetQuestion }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await historyAPI.list(100);
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this history record?')) return;
    try {
      await historyAPI.delete(id);
      setHistory(history.filter(h => h.id !== id));
      if (selectedItem?.id === id) setSelectedItem(null);
    } catch (err) {
      alert('Failed to delete history record.');
    }
  };

  const filtered = history.filter(h => 
    h.question.toLowerCase().includes(search.toLowerCase()) ||
    (h.generated_sql && h.generated_sql.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2.5">
            <History className="w-5 h-5 text-sky-400" />
            <span>Query Execution Audit History</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Track previous questions, generated SQL, execution metrics, and latency
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search questions or SQL..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Question</th>
                <th className="py-3 px-4 font-semibold">Generated SQL</th>
                <th className="py-3 px-4 font-semibold">Latency</th>
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filtered.map((item) => (
                <tr 
                  key={item.id} 
                  onClick={() => setSelectedItem(item)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4">
                    {item.execution_status === 'completed' || item.execution_status === 'success' ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-sans">
                        <CheckCircle className="w-3 h-3" /> Success
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 font-sans">
                        <XCircle className="w-3 h-3" /> {item.execution_status}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-sans text-slate-200 font-medium max-w-xs truncate">
                    {item.question}
                  </td>
                  <td className="py-3 px-4 text-sky-300 text-[11px] max-w-sm truncate">
                    {item.generated_sql || '—'}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {item.execution_time_ms ? `${item.execution_time_ms} ms` : '—'}
                  </td>
                  <td className="py-3 px-4 text-slate-500 text-[11px]">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      className="text-slate-500 hover:text-rose-400 p-1.5 rounded hover:bg-slate-800 transition-colors"
                      title="Delete Entry"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500 font-sans">
                    No history records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* SQL Detail Drawer / Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-100">Historical Query Details</h3>
                <p className="text-xs text-slate-400 mt-0.5">{selectedItem.question}</p>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                Generated SQL
              </span>
              <pre className="bg-slate-950 border border-slate-800 rounded-lg p-3.5 font-mono text-xs text-sky-300 overflow-x-auto">
                <code>{selectedItem.generated_sql || 'No SQL generated'}</code>
              </pre>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(selectedItem.generated_sql || '');
                  alert('SQL copied to clipboard!');
                }}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2 rounded-lg border border-slate-700"
              >
                Copy SQL
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
