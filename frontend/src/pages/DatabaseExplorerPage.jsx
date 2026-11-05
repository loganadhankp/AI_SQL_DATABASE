import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Table, 
  Key, 
  Link2, 
  Eye, 
  RefreshCw, 
  AlertCircle 
} from 'lucide-react';
import { connectionsAPI } from '../services/api';

export default function DatabaseExplorerPage({ activeConnection }) {
  const [schema, setSchema] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSchema = async () => {
    if (!activeConnection) return;
    setLoading(true);
    setError(null);
    try {
      const res = await connectionsAPI.getSchema(activeConnection.id);
      setSchema(res.data);
      if (res.data?.tables?.length > 0) {
        setSelectedTable(res.data.tables[0]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load database schema.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchema();
  }, [activeConnection]);

  useEffect(() => {
    const fetchPreview = async () => {
      if (!activeConnection || !selectedTable) return;
      setPreviewLoading(true);
      try {
        const res = await connectionsAPI.getTablePreview(activeConnection.id, selectedTable.name);
        setPreview(res.data);
      } catch (err) {
        console.error('Failed to preview table data:', err);
      } finally {
        setPreviewLoading(false);
      }
    };
    fetchPreview();
  }, [selectedTable, activeConnection]);

  if (!activeConnection) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center py-24 space-y-3">
        <Database className="w-12 h-12 text-slate-600 mx-auto" />
        <h2 className="text-lg font-bold text-slate-200">No Target Database Connected</h2>
        <p className="text-sm text-slate-500">
          Go to the Connections tab to configure and connect your MySQL database.
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2.5">
            <Database className="w-5 h-5 text-sky-400" />
            <span>Database Explorer: {schema?.database_name || activeConnection.database_name}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Dynamic schema discovery, relationship mapping, and sample record preview
          </p>
        </div>

        <button
          onClick={fetchSchema}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3.5 py-2 rounded-lg border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Schema</span>
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-xs text-rose-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Dual-Pane Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
        {/* Left Pane: Table List */}
        <div className="md:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl space-y-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block px-2 pb-1">
            Tables ({schema?.tables?.length || 0})
          </span>

          <div className="space-y-1">
            {schema?.tables?.map((table) => {
              const isSelected = selectedTable?.name === table.name;
              return (
                <button
                  key={table.name}
                  onClick={() => setSelectedTable(table)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isSelected
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                      : 'text-slate-300 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <Table className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{table.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 shrink-0">
                    {table.estimated_row_count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Pane: Table Details & Sample Preview */}
        <div className="md:col-span-3 space-y-6">
          {selectedTable ? (
            <>
              {/* Columns & Metadata Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-200">
                      Table: <code className="text-sky-400">{selectedTable.name}</code>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Approx {selectedTable.estimated_row_count} records • {selectedTable.columns.length} columns
                    </p>
                  </div>

                  {selectedTable.primary_keys?.length > 0 && (
                    <span className="text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20 px-2.5 py-1 rounded-md flex items-center gap-1.5">
                      <Key className="w-3 h-3" />
                      <span>PK: {selectedTable.primary_keys.join(', ')}</span>
                    </span>
                  )}
                </div>

                {/* Column Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2 px-3 font-semibold">Column Name</th>
                        <th className="py-2 px-3 font-semibold">Data Type</th>
                        <th className="py-2 px-3 font-semibold">Nullable</th>
                        <th className="py-2 px-3 font-semibold">Attributes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {selectedTable.columns.map((col, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-bold text-slate-200 flex items-center gap-1.5">
                            {col.primary_key && <Key className="w-3 h-3 text-amber-400" />}
                            <span>{col.name}</span>
                          </td>
                          <td className="py-2.5 px-3 text-sky-300">{col.data_type}</td>
                          <td className="py-2.5 px-3 text-slate-400">
                            {col.nullable ? 'YES' : <span className="text-rose-400 font-semibold">NO</span>}
                          </td>
                          <td className="py-2.5 px-3 text-slate-400">
                            {col.primary_key ? (
                              <span className="text-amber-400 font-bold">PRIMARY KEY</span>
                            ) : (
                              '—'
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Foreign Key Relations */}
                {selectedTable.foreign_keys?.length > 0 && (
                  <div className="pt-3 border-t border-slate-800/80">
                    <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mb-2">
                      <Link2 className="w-3.5 h-3.5 text-sky-400" />
                      Foreign Key References (JOIN Paths):
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {selectedTable.foreign_keys.map((fk, fIdx) => (
                        <span
                          key={fIdx}
                          className="text-xs bg-slate-950 border border-slate-800 text-slate-300 px-3 py-1 rounded-lg font-mono"
                        >
                          {selectedTable.name}.{fk.constrained_columns.join(', ')} ➔ {fk.referred_table}.{fk.referred_columns.join(', ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Sample 5-Row Data Preview */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                    <Eye className="w-4 h-4 text-sky-400" />
                    <span>Sample Records Preview (Bounded to 5 Rows)</span>
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    Safe non-blocking read
                  </span>
                </div>

                {previewLoading ? (
                  <div className="py-12 flex justify-center">
                    <div className="w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : preview?.rows?.length > 0 ? (
                  <div className="overflow-x-auto rounded-lg border border-slate-800">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                        <tr>
                          {preview.columns.map((c, i) => (
                            <th key={i} className="py-2.5 px-3 font-semibold text-slate-300">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {preview.rows.map((r, rI) => (
                          <tr key={rI} className="hover:bg-slate-800/40">
                            {preview.columns.map((c, cI) => (
                              <td key={cI} className="py-2 px-3 text-slate-300 truncate max-w-xs">
                                {r[c] !== null && r[c] !== undefined ? String(r[c]) : <span className="text-slate-600">NULL</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 py-6 text-center">No preview data returned.</p>
                )}
              </div>
            </>
          ) : (
            <p className="text-xs text-slate-500 text-center py-20">Select a table on the left to inspect.</p>
          )}
        </div>
      </div>
    </div>
  );
}
