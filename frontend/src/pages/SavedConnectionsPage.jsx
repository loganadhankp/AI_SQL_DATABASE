import React, { useState } from 'react';
import { 
  Network, 
  Plus, 
  CheckCircle, 
  Trash2, 
  Check, 
  AlertCircle, 
  Database,
  Radio
} from 'lucide-react';
import { connectionsAPI } from '../services/api';

export default function SavedConnectionsPage({ 
  connections, 
  activeConnection, 
  setActiveConnection, 
  fetchConnections 
}) {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    connection_name: 'Local E-Commerce DB',
    dialect: 'mysql',
    host: '127.0.0.1',
    port: 3307,
    database_name: 'ecommerce_db',
    username: 'root',
    password: '',
  });

  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);
    try {
      const res = await connectionsAPI.test({
        dialect: formData.dialect,
        host: formData.host,
        port: parseInt(formData.port),
        database_name: formData.database_name,
        username: formData.username,
        password: formData.password,
      });
      setTestResult({ success: true, message: res.data.message || 'Connected successfully!' });
    } catch (err) {
      setTestResult({ 
        success: false, 
        message: err.response?.data?.detail || err.message || 'Connection test failed.' 
      });
    } finally {
      setTesting(false);
    }
  };

  const handleCreateConnection = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const res = await connectionsAPI.create({
        ...formData,
        port: parseInt(formData.port),
      });
      await fetchConnections();
      setActiveConnection(res.data);
      setShowModal(false);
      setTestResult(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save database connection.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConnection = async (id) => {
    if (!window.confirm('Are you sure you want to delete this connection?')) return;
    try {
      await connectionsAPI.delete(id);
      await fetchConnections();
      if (activeConnection?.id === id) {
        setActiveConnection(null);
      }
    } catch (err) {
      alert('Failed to delete connection.');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2.5">
            <Network className="w-5 h-5 text-sky-400" />
            <span>Database Connection Profiles</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage your secure MySQL connections. Credentials are encrypted at rest with AES-128.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-sky-500/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Connection</span>
        </button>
      </div>

      {/* Connection Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {connections.map((c) => {
          const isActive = activeConnection?.id === c.id;
          return (
            <div
              key={c.id}
              className={`bg-slate-900 border rounded-2xl p-5 shadow-xl relative transition-all ${
                isActive ? 'border-sky-500/70 shadow-sky-500/10' : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-sky-400">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-200 text-sm truncate max-w-[150px]">
                      {c.connection_name}
                    </h3>
                    <span className="text-[11px] text-sky-400 font-medium">
                      {c.dialect.toUpperCase()}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteConnection(c.id)}
                  className="text-slate-500 hover:text-rose-400 p-1.5 rounded-md hover:bg-slate-800 transition-colors"
                  title="Delete Connection"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-400 font-mono">
                <p>Database: <span className="text-slate-200">{c.database_name}</span></p>
                <p>Host: <span className="text-slate-200">{c.host}:{c.port}</span></p>
                <p>User: <span className="text-slate-200">{c.username}</span></p>
              </div>

              <div className="mt-5">
                {isActive ? (
                  <span className="w-full inline-flex items-center justify-center gap-1.5 bg-sky-500/15 border border-sky-500/30 text-sky-400 text-xs font-semibold py-2 rounded-lg">
                    <CheckCircle className="w-4 h-4" />
                    <span>Active Target</span>
                  </span>
                ) : (
                  <button
                    onClick={() => setActiveConnection(c)}
                    className="w-full inline-flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 rounded-lg transition-colors border border-slate-700"
                  >
                    <span>Set as Active</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {connections.length === 0 && (
          <div className="col-span-full py-16 text-center text-slate-500 space-y-3">
            <Network className="w-10 h-10 mx-auto text-slate-600" />
            <p className="text-sm font-medium">No database connections saved yet.</p>
            <p className="text-xs">Click "New Connection" above to connect your MySQL database.</p>
          </div>
        )}
      </div>

      {/* Add Connection Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">Connect Relational Database</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateConnection} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Connection Label</label>
                <input
                  type="text"
                  required
                  value={formData.connection_name}
                  onChange={(e) => setFormData({ ...formData, connection_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-slate-400 font-semibold mb-1">Host</label>
                  <input
                    type="text"
                    required
                    value={formData.host}
                    onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Port</label>
                  <input
                    type="number"
                    required
                    value={formData.port}
                    onChange={(e) => setFormData({ ...formData, port: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Database Name</label>
                <input
                  type="text"
                  required
                  value={formData.database_name}
                  onChange={(e) => setFormData({ ...formData, database_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Username</label>
                  <input
                    type="text"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Password</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Leave blank if none"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              {/* Live Test Feedback */}
              {testResult && (
                <div
                  className={`p-3 rounded-lg flex items-start gap-2 ${
                    testResult.success
                      ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                      : 'bg-rose-500/10 border border-rose-500/30 text-rose-400'
                  }`}
                >
                  {testResult.success ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                  <span className="text-xs">{testResult.message}</span>
                </div>
              )}

              {error && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs">
                  {error}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testing}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-2.5 rounded-lg border border-slate-700 transition-colors"
                >
                  {testing ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold py-2.5 rounded-lg transition-colors"
                >
                  {saving ? 'Saving...' : 'Save & Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
