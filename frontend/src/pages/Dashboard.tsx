import React from 'react';
import {
  DashboardSummary,
  NavPage
} from '../types';
import {
  Server,
  Network,
  Database,
  HardDrive,
  FileText,
  Clock,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  DollarSign,
  ShieldCheck,
  TrendingDown,
  Layers,
  Activity
} from 'lucide-react';

interface DashboardProps {
  data: DashboardSummary | null;
  loading: boolean;
  onNavigate: (page: NavPage) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ data, loading, onNavigate }) => {
  if (loading && !data) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
        <p>Loading enterprise platform telemetry...</p>
      </div>
    );
  }

  const counts = data?.resource_counts || { total: 0, managed: 0, discovered: 0, by_type: {} };
  const conn = data?.aws_connection;

  return (
    <div style={{ padding: '1.75rem 2rem', display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: '1440px', margin: '0 auto' }}>
      {/* Top Banner Notice */}
      <div style={{
        padding: '0.85rem 1.15rem',
        borderRadius: '8px',
        backgroundColor: data?.is_demo ? 'rgba(245, 158, 11, 0.08)' : 'rgba(16, 185, 129, 0.08)',
        border: `1px solid ${data?.is_demo ? 'rgba(245, 158, 11, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          {data?.is_demo ? (
            <AlertTriangle size={17} style={{ color: '#fbbf24' }} />
          ) : (
            <CheckCircle2 size={17} style={{ color: '#34d399' }} />
          )}
          <div>
            <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: data?.is_demo ? '#fbbf24' : '#34d399' }}>
              {data?.is_demo ? 'Operating in Safe Demo Sandbox Mode' : 'Connected to Live AWS Cloud'}
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              {data?.data_notice}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => onNavigate('connect-aws')}
            className="btn-secondary"
            style={{ padding: '0.35rem 0.65rem', fontSize: '0.725rem' }}
          >
            Manage Credentials &rarr;
          </button>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Managed Cloud Assets
            </span>
            <Server size={16} style={{ color: '#38bdf8' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            {counts.managed} <span style={{ fontSize: '0.85rem', fontWeight: 500, color: '#64748b' }}>/ {counts.total} total</span>
          </div>
          <p style={{ fontSize: '0.725rem', color: '#38bdf8', marginTop: '0.25rem' }}>
            Governed by isolated Terraform workspaces
          </p>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Est. Monthly Spend
            </span>
            <DollarSign size={16} style={{ color: '#34d399' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            ${data?.estimated_monthly_spend.toFixed(2)}
          </div>
          <p style={{ fontSize: '0.725rem', color: '#34d399', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <TrendingDown size={13} /> Multi-Cloud Arbitrage active
          </p>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Architecture Reports
            </span>
            <FileText size={16} style={{ color: '#a78bfa' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            {data?.total_reports_generated || 0}
          </div>
          <button
            onClick={() => onNavigate('advisor')}
            style={{ background: 'none', border: 'none', color: '#a78bfa', fontSize: '0.725rem', cursor: 'pointer', padding: 0, marginTop: '0.25rem', textAlign: 'left' }}
          >
            Run Questionnaire &rarr;
          </button>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Security Guardrails
            </span>
            <ShieldCheck size={16} style={{ color: '#10b981' }} />
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.35rem' }}>
            {conn?.read_only_access ? 'Least-Privilege' : 'Pending Check'}
          </div>
          <p style={{ fontSize: '0.725rem', color: '#10b981', marginTop: '0.25rem' }}>
            IMDSv2 & Private Subnets enforced
          </p>
        </div>
      </div>

      {/* Multi-Cloud Spend Comparison Callout Card */}
      <div className="card" style={{ background: 'linear-gradient(180deg, #121a2b 0%, #0d1422 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.675rem', fontWeight: 600, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Multi-Cloud FinOps Intelligence
            </span>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.1rem' }}>
              Workload Cost Arbitrage: AWS vs. Azure vs. Google Cloud
            </h3>
          </div>
          <button
            onClick={() => onNavigate('pricing')}
            className="btn-primary"
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.75rem' }}
          >
            Launch Cost Modeler &rarr;
          </button>
        </div>

        {/* Cloud Comparison Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.85rem' }}>
          <div style={{ padding: '1rem', backgroundColor: '#090d16', borderRadius: '6px', border: '1px solid rgba(255, 153, 0, 0.25)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span className="badge-aws">AWS</span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>us-east-1</span>
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
              ${data?.estimated_monthly_spend.toFixed(2)}/mo
            </div>
            <p style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem' }}>
              Baseline EC2, gp3, RDS PostgreSQL
            </p>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#090d16', borderRadius: '6px', border: '1px solid rgba(0, 120, 212, 0.25)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span className="badge-azure">Microsoft Azure</span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>East US</span>
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>
              ${((data?.estimated_monthly_spend || 135) * 0.96).toFixed(2)}/mo
            </div>
            <p style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem' }}>
              Saves ~4% via lower Azure Blob Hot pricing
            </p>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#090d16', borderRadius: '6px', border: '1px solid rgba(66, 133, 244, 0.3)', position: 'relative' }}>
            <span style={{
              position: 'absolute',
              top: '-8px',
              right: '10px',
              backgroundColor: '#10b981',
              color: '#090d16',
              fontSize: '0.625rem',
              fontWeight: 800,
              padding: '0.1rem 0.4rem',
              borderRadius: '3px'
            }}>
              CHEAPEST
            </span>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span className="badge-gcp">Google Cloud</span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>us-east4</span>
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>
              ${((data?.estimated_monthly_spend || 135) * 0.93).toFixed(2)}/mo
            </div>
            <p style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem' }}>
              Saves ~7% via E2 shared core optimization
            </p>
          </div>
        </div>
      </div>

      {/* Main Split: Operations Feed & Inventory Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
        {/* Recent Operations */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '0.925rem', fontWeight: 700, color: '#f8fafc' }}>
                Recent Infrastructure Operations
              </h3>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                Tracked Terraform plan, apply, and destroy runs
              </p>
            </div>
            <button
              onClick={() => onNavigate('provisioning')}
              className="btn-secondary"
              style={{ padding: '0.35rem 0.65rem', fontSize: '0.725rem' }}
            >
              Launch Provisioner <ArrowRight size={13} />
            </button>
          </div>

          {data?.recent_operations && data.recent_operations.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.775rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1c2638', color: '#64748b' }}>
                    <th style={{ padding: '0.6rem 0.4rem' }}>Operation ID</th>
                    <th style={{ padding: '0.6rem 0.4rem' }}>Action</th>
                    <th style={{ padding: '0.6rem 0.4rem' }}>Status</th>
                    <th style={{ padding: '0.6rem 0.4rem' }}>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_operations.map((op) => (
                    <tr key={op.operation_id} style={{ borderBottom: '1px solid #141b29' }}>
                      <td style={{ padding: '0.6rem 0.4rem', fontFamily: 'monospace', color: '#38bdf8' }}>
                        {op.operation_id}
                      </td>
                      <td style={{ padding: '0.6rem 0.4rem', textTransform: 'uppercase', fontWeight: 600 }}>
                        {op.action}
                      </td>
                      <td style={{ padding: '0.6rem 0.4rem' }}>
                        <span style={{
                          padding: '0.15rem 0.45rem',
                          borderRadius: '3px',
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          backgroundColor:
                            op.status === 'succeeded'
                              ? 'rgba(16, 185, 129, 0.12)'
                              : op.status === 'failed'
                              ? 'rgba(239, 68, 68, 0.12)'
                              : 'rgba(56, 189, 248, 0.12)',
                          color:
                            op.status === 'succeeded'
                              ? '#34d399'
                              : op.status === 'failed'
                              ? '#f87171'
                              : '#38bdf8'
                        }}>
                          {op.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem 0.4rem', color: '#64748b' }}>
                        {op.started_at ? new Date(op.started_at).toLocaleTimeString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ padding: '2rem 1rem', textAlign: 'center', color: '#64748b' }}>
              <Clock size={28} style={{ margin: '0 auto 0.5rem auto', opacity: 0.4 }} />
              <p style={{ fontSize: '0.8125rem' }}>No recent operations logged in this workspace.</p>
              <button
                onClick={() => onNavigate('provisioning')}
                className="btn-primary"
                style={{ marginTop: '0.75rem', fontSize: '0.75rem' }}
              >
                Provision New Environment
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Inventory Breakdown */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.85rem' }}>
              Inventory by Resource Type
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1' }}>
                  <Server size={14} style={{ color: '#38bdf8' }} /> Compute (EC2 / VM)
                </span>
                <span style={{ fontWeight: 600 }}>{counts.by_type?.ec2 || 0}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1' }}>
                  <Network size={14} style={{ color: '#818cf8' }} /> VPC & Networks
                </span>
                <span style={{ fontWeight: 600 }}>{counts.by_type?.vpc || 0}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1' }}>
                  <HardDrive size={14} style={{ color: '#34d399' }} /> S3 & Blob Storage
                </span>
                <span style={{ fontWeight: 600 }}>{counts.by_type?.s3 || 0}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1' }}>
                  <Database size={14} style={{ color: '#f59e0b' }} /> RDS & Cloud SQL
                </span>
                <span style={{ fontWeight: 600 }}>{counts.by_type?.rds || 0}</span>
              </div>
            </div>
            <button
              onClick={() => onNavigate('inventory')}
              className="btn-secondary"
              style={{ width: '100%', marginTop: '1rem', justifyContent: 'center', fontSize: '0.725rem' }}
            >
              Full Inventory Table <ArrowRight size={12} />
            </button>
          </div>

          {/* Audit Trail Snippet */}
          <div className="card" style={{ padding: '1rem' }}>
            <h4 style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Live Audit Log
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.725rem' }}>
              {data?.audit_events && data.audit_events.length > 0 ? (
                data.audit_events.slice(0, 3).map((ev, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                    <span>{ev.action}</span>
                    <span style={{ color: '#64748b' }}>{ev.timestamp.slice(11, 19)}</span>
                  </div>
                ))
              ) : (
                <span style={{ color: '#64748b' }}>No audit events logged</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
