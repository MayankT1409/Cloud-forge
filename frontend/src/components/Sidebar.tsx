import React from 'react';
import {
  LayoutDashboard,
  Hammer,
  Compass,
  Calculator,
  ShieldCheck,
  Server,
  Activity,
  Terminal,
  ChevronDown,
  Layers
} from 'lucide-react';
import { NavPage, AWSConnectionStatus } from '../types';

interface SidebarProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  awsStatus: AWSConnectionStatus | null;
  onToggleDemo: (enabled: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  awsStatus,
  onToggleDemo
}) => {
  const sections: Array<{
    title: string;
    items: Array<{ id: NavPage; label: string; icon: React.ReactNode; badge?: string }>;
  }> = [
    {
      title: 'Core Platform',
      items: [
        { id: 'dashboard', label: 'Overview', icon: <LayoutDashboard size={16} /> },
        { id: 'provisioning', label: 'Provisioning', icon: <Hammer size={16} />, badge: 'Terraform' },
        { id: 'advisor', label: 'Architecture Advisor', icon: <Compass size={16} /> },
      ],
    },
    {
      title: 'Multi-Cloud Intelligence',
      items: [
        { id: 'pricing', label: 'Cost & Arbitrage', icon: <Calculator size={16} />, badge: 'Multi-Cloud' },
        { id: 'inventory', label: 'Resource Inventory', icon: <Server size={16} /> },
        { id: 'monitoring', label: 'Observability', icon: <Activity size={16} /> },
      ],
    },
    {
      title: 'Identity & Access',
      items: [
        { id: 'connect-aws', label: 'Cloud Credentials', icon: <ShieldCheck size={16} /> },
      ],
    },
  ];

  return (
    <aside style={{
      width: '260px',
      flexShrink: 0,
      backgroundColor: '#0a0e17',
      borderRight: '1px solid rgba(255, 255, 255, 0.08)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'sticky',
      top: 0
    }}>
      {/* Workspace / Org Switcher */}
      <div style={{
        padding: '1.15rem 1.25rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #2563eb, #0ea5e9)',
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 700,
            fontSize: '0.8125rem'
          }}>
            CF
          </div>
          <div>
            <h1 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#f8fafc', lineHeight: 1.2 }}>
              CloudForge
            </h1>
            <p style={{ fontSize: '0.7rem', color: '#64748b' }}>
              Internal Developer Platform
            </p>
          </div>
        </div>
        <span style={{
          fontSize: '0.65rem',
          padding: '0.15rem 0.4rem',
          borderRadius: '4px',
          backgroundColor: '#161f30',
          color: '#38bdf8',
          border: '1px solid rgba(56, 189, 248, 0.2)'
        }}>
          v1.2
        </span>
      </div>

      {/* Navigation Sections */}
      <nav style={{ padding: '1rem 0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem', overflowY: 'auto' }}>
        {sections.map((section, sIdx) => (
          <div key={sIdx}>
            <div style={{
              fontSize: '0.675rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: '#475569',
              padding: '0 0.6rem 0.35rem 0.6rem'
            }}>
              {section.title}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
              {section.items.map((item) => {
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.65rem',
                      padding: '0.5rem 0.65rem',
                      borderRadius: '6px',
                      border: 'none',
                      backgroundColor: isActive ? '#151e2f' : 'transparent',
                      color: isActive ? '#f8fafc' : '#94a3b8',
                      fontWeight: isActive ? 600 : 500,
                      fontSize: '0.8125rem',
                      cursor: 'pointer',
                      textAlign: 'left',
                      width: '100%',
                      transition: 'all 0.1s ease'
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) e.currentTarget.style.backgroundColor = '#0f1726';
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <span style={{ color: isActive ? '#38bdf8' : '#64748b' }}>{item.icon}</span>
                    <span style={{ flex: 1 }}>{item.label}</span>
                    {item.badge && (
                      <span style={{
                        fontSize: '0.625rem',
                        padding: '0.1rem 0.35rem',
                        borderRadius: '3px',
                        backgroundColor: isActive ? 'rgba(56, 189, 248, 0.15)' : '#162033',
                        color: isActive ? '#38bdf8' : '#64748b'
                      }}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Cloud Providers Status Box */}
      <div style={{
        padding: '0.85rem',
        margin: '0.75rem',
        backgroundColor: '#0f1726',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
            Multi-Cloud Status
          </span>
          {awsStatus?.is_demo ? (
            <span className="badge-demo" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>SANDBOX</span>
          ) : (
            <span className="badge-live" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>LIVE</span>
          )}
        </div>

        {/* Cloud Badges */}
        <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '0.75rem' }}>
          <span className="badge-aws" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>AWS</span>
          <span className="badge-azure" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>Azure</span>
          <span className="badge-gcp" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>GCP</span>
        </div>

        <button
          onClick={() => onToggleDemo(!awsStatus?.is_demo)}
          style={{
            width: '100%',
            padding: '0.35rem 0.5rem',
            fontSize: '0.725rem',
            borderRadius: '5px',
            border: '1px solid #243147',
            backgroundColor: '#161f30',
            color: '#cbd5e1',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.35rem'
          }}
        >
          <Terminal size={12} />
          {awsStatus?.is_demo ? 'Switch to Live Credentials' : 'Use Demo Sandbox'}
        </button>
      </div>
    </aside>
  );
};
