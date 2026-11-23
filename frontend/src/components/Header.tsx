import React from 'react';
import { NavPage, AWSConnectionStatus } from '../types';
import { Globe, RefreshCw, UserCheck } from 'lucide-react';

interface HeaderProps {
  currentPage: NavPage;
  awsStatus: AWSConnectionStatus | null;
  onRefresh: () => void;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  awsStatus,
  onRefresh,
  loading
}) => {
  const titles: Record<NavPage, { name: string; section: string }> = {
    dashboard: { name: 'Infrastructure Overview', section: 'Core Platform' },
    provisioning: { name: 'Terraform Provisioner', section: 'Infrastructure as Code' },
    advisor: { name: 'Architecture Advisor & Sizing', section: 'Planning & Governance' },
    pricing: { name: 'Multi-Cloud Cost & Arbitrage', section: 'Financial Operations (FinOps)' },
    'connect-aws': { name: 'Cloud Credentials & IAM', section: 'Security & Access' },
    inventory: { name: 'Resource Inventory', section: 'Discovery & Telemetry' },
    monitoring: { name: 'Observability & Metrics', section: 'Operations' }
  };

  const meta = titles[currentPage] || { name: 'Dashboard', section: 'Overview' };

  return (
    <header style={{
      padding: '0.875rem 2rem',
      backgroundColor: '#0a0e17',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 20
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.725rem', color: '#64748b' }}>
          <span>{meta.section}</span>
          <span>/</span>
          <span style={{ color: '#cbd5e1' }}>{meta.name}</span>
        </div>
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em', marginTop: '0.1rem' }}>
          {meta.name}
        </h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Active Cloud Region Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          backgroundColor: '#0f1726',
          border: '1px solid #243147',
          padding: '0.3rem 0.65rem',
          borderRadius: '5px',
          fontSize: '0.75rem',
          color: '#cbd5e1'
        }}>
          <Globe size={13} style={{ color: '#38bdf8' }} />
          <span>{awsStatus?.region || 'us-east-1'}</span>
          <span style={{ color: '#334155' }}>|</span>
          <span style={{ color: awsStatus?.is_demo ? '#fbbf24' : '#34d399', fontWeight: 600 }}>
            {awsStatus?.is_demo ? 'Sandbox' : (awsStatus?.account_id || 'Connected')}
          </span>
        </div>

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          disabled={loading}
          style={{
            background: '#161f30',
            border: '1px solid #243147',
            color: '#cbd5e1',
            borderRadius: '6px',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s ease'
          }}
          title="Refresh platform telemetry"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>

        {/* User Identity Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          backgroundColor: '#0f1726',
          border: '1px solid #243147',
          padding: '0.3rem 0.65rem',
          borderRadius: '5px',
          fontSize: '0.75rem',
          color: '#cbd5e1'
        }}>
          <div style={{
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            backgroundColor: '#2563eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.625rem',
            color: 'white',
            fontWeight: 700
          }}>
            M
          </div>
          <span style={{ color: '#94a3b8' }}>devops-lead</span>
        </div>
      </div>
    </header>
  );
};
