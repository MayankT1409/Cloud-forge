import React, { useState, useEffect } from 'react';
import { NavPage, DashboardSummary, AWSConnectionStatus } from './types';
import { api } from './services/api';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { Provisioning } from './pages/Provisioning';
import { Advisor } from './pages/Advisor';
import { CostEstimation } from './pages/CostEstimation';
import { ConnectAWS } from './pages/ConnectAWS';
import { Inventory } from './pages/Inventory';
import { Monitoring } from './pages/Monitoring';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<NavPage>('dashboard');
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [awsStatus, setAwsStatus] = useState<AWSConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchGlobalState = async () => {
    setLoading(true);
    try {
      const [dash, status] = await Promise.all([
        api.getDashboardSummary(),
        api.getAWSStatus(),
      ]);
      setDashboardData(dash);
      setAwsStatus(status);
    } catch (err) {
      console.error('Failed to load platform data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobalState();
  }, []);

  const handleToggleDemo = async (enabled: boolean) => {
    try {
      const res = await api.toggleDemoMode(enabled);
      setAwsStatus(res);
      await fetchGlobalState();
    } catch (err) {
      console.error('Failed to toggle demo sandbox:', err);
    }
  };

  const renderActivePage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard data={dashboardData} loading={loading} onNavigate={setCurrentPage} />;
      case 'provisioning':
        return <Provisioning />;
      case 'advisor':
        return <Advisor />;
      case 'pricing':
        return <CostEstimation />;
      case 'connect-aws':
        return <ConnectAWS />;
      case 'inventory':
        return <Inventory />;
      case 'monitoring':
        return <Monitoring />;
      default:
        return <Dashboard data={dashboardData} loading={loading} onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-darker text-slate-100 font-sans selection:bg-brand-primary/30 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        awsStatus={awsStatus}
        onToggleDemo={handleToggleDemo}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          currentPage={currentPage}
          awsStatus={awsStatus}
          onRefresh={fetchGlobalState}
          loading={loading}
        />

        {/* Dynamic Page Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            {renderActivePage()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
