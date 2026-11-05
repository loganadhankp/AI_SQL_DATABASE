import React from 'react';
import { Database, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Navbar({ activeConnection, connections, onSelectConnection }) {
  return (
    <header className="h-16 bg-slate-950/70 backdrop-blur-md border-b border-slate-800 px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Target Database
        </span>

        {connections.length > 0 ? (
          <div className="relative">
            <select
              value={activeConnection?.id || ''}
              onChange={(e) => {
                const selected = connections.find((c) => c.id === parseInt(e.target.value));
                if (selected) onSelectConnection(selected);
              }}
              className="bg-slate-900 border border-slate-700/80 rounded-lg text-xs font-medium text-slate-200 py-1.5 pl-3 pr-8 focus:outline-none focus:border-sky-500 transition-colors cursor-pointer"
            >
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.connection_name} ({c.database_name} @ {c.host})
                </option>
              ))}
            </select>
          </div>
        ) : (
          <span className="text-xs text-amber-400 font-medium flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" /> No database connected
          </span>
        )}
      </div>

      <div className="flex items-center space-x-3">
        {activeConnection ? (
          <div className="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-medium text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Connected: {activeConnection.database_name}</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 bg-slate-800/60 px-3 py-1 rounded-full text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-slate-500"></span>
            <span>Disconnected</span>
          </div>
        )}
      </div>
    </header>
  );
}
