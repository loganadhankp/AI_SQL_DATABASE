import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardOverview from './pages/DashboardOverview';
import AIAnalystPage from './pages/AIAnalystPage';
import DatabaseExplorerPage from './pages/DatabaseExplorerPage';
import SavedConnectionsPage from './pages/SavedConnectionsPage';
import QueryHistoryPage from './pages/QueryHistoryPage';
import AuthPage from './pages/AuthPage';
import { connectionsAPI } from './services/api';

export default function App() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [connections, setConnections] = useState([]);
  const [activeConnection, setActiveConnection] = useState(null);

  const fetchConnections = async () => {
    try {
      const res = await connectionsAPI.list();
      setConnections(res.data);
      if (res.data.length > 0 && !activeConnection) {
        setActiveConnection(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch connections:', err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
  }, [user]);

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans antialiased text-slate-100 selection:bg-sky-500 selection:text-white">
      {/* Fixed Left Navigation Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          activeConnection={activeConnection}
          connections={connections}
          onSelectConnection={setActiveConnection}
        />

        <main className="flex-1 overflow-y-auto">
          {activeTab === 'dashboard' && (
            <DashboardOverview 
              setActiveTab={setActiveTab} 
              activeConnection={activeConnection} 
            />
          )}

          {activeTab === 'analyst' && (
            <AIAnalystPage 
              activeConnection={activeConnection} 
            />
          )}

          {activeTab === 'explorer' && (
            <DatabaseExplorerPage 
              activeConnection={activeConnection} 
            />
          )}

          {activeTab === 'connections' && (
            <SavedConnectionsPage
              connections={connections}
              activeConnection={activeConnection}
              setActiveConnection={setActiveConnection}
              fetchConnections={fetchConnections}
            />
          )}

          {activeTab === 'history' && (
            <QueryHistoryPage 
              setActiveTab={setActiveTab} 
            />
          )}
        </main>
      </div>
    </div>
  );
}
