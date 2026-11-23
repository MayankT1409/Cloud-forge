import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { MultiCloudCostComparison } from '../types';
import {
  Server,
  Database,
  Network,
  Info,
  TrendingDown,
  Layers,
  ArrowRight
} from 'lucide-react';

export const CostEstimation: React.FC = () => {
  const [region, setRegion] = useState('us-east-1');
  const [computeType, setComputeType] = useState('t3.medium');
  const [computeCount, setComputeCount] = useState(2);
  const [storageGb, setStorageGb] = useState(50);
  const [dbEnabled, setDbEnabled] = useState(true);
  const [dbClass, setDbClass] = useState('db.t3.micro');
  const [dbStorageGb, setDbStorageGb] = useState(20);
  const [dbMultiAz, setDbMultiAz] = useState(false);
  const [natCount, setNatCount] = useState(1);
  const [bandwidthGb, setBandwidthGb] = useState(150);
  const [s3StorageGb, setS3StorageGb] = useState(50);

  const [activeTab, setActiveTab] = useState<'comparison' | 'aws' | 'azure' | 'gcp'>('comparison');
  const [loading, setLoading] = useState(false);
  const [multiCloud, setMultiCloud] = useState<MultiCloudCostComparison | null>(null);

  useEffect(() => {
    fetchEstimate();
  }, [
    region,
    computeType,
    computeCount,
    storageGb,
    dbEnabled,
    dbClass,
    dbStorageGb,
    dbMultiAz,
    natCount,
    bandwidthGb,
    s3StorageGb
  ]);

  const fetchEstimate = async () => {
    setLoading(true);
    try {
      const res = await api.calculateMultiCloudCosts({
        region,
        compute_instance_type: computeType,
        compute_count: computeCount,
        storage_gb: storageGb,
        db_enabled: dbEnabled,
        db_instance_class: dbClass,
        db_storage_gb: dbStorageGb,
        db_multi_az: dbMultiAz,
        nat_gateway_count: natCount,
        bandwidth_gb: bandwidthGb,
        s3_storage_gb: s3StorageGb,
      });
      setMultiCloud(res);
    } catch (e) {
      console.error('Failed to calculate multi-cloud estimate:', e);
    } finally {
      setLoading(false);
    }
  };

  const awsData = multiCloud?.providers?.aws;
  const azData = multiCloud?.providers?.azure;
  const gcpData = multiCloud?.providers?.gcp;

  return (
    <div style={{ padding: '1.75rem 2rem', display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: '1440px', margin: '0 auto' }}>
      {/* Workload Sizing Controls */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
              Multi-Cloud Workload Sizing & Cost Modeling
            </h3>
            <p style={{ fontSize: '0.775rem', color: '#94a3b8' }}>
              Configure infrastructure parameters once to benchmark expenditures across AWS, Azure, and Google Cloud in real time.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Region:</span>
            <select value={region} onChange={(e) => setRegion(e.target.value)} style={{ width: '150px' }}>
              <option value="us-east-1">us-east-1 (N. Virginia)</option>
              <option value="us-west-2">us-west-2 (Oregon)</option>
              <option value="eu-west-1">eu-west-1 (Ireland)</option>
            </select>
          </div>
        </div>

        {/* Inputs Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {/* Compute Controls */}
          <div className="card-subtle">
            <span style={{ fontSize: '0.775rem', fontWeight: 600, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
              <Server size={14} /> Compute Workload
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div>
                <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Instance Specification</label>
                <select value={computeType} onChange={(e) => setComputeType(e.target.value)}>
                  <option value="t3.nano">t3.nano (2 vCPU, 0.5 GB)</option>
                  <option value="t3.micro">t3.micro (2 vCPU, 1 GB)</option>
                  <option value="t3.small">t3.small (2 vCPU, 2 GB)</option>
                  <option value="t3.medium">t3.medium (2 vCPU, 4 GB)</option>
                  <option value="t3.large">t3.large (2 vCPU, 8 GB)</option>
                  <option value="m6i.large">m6i.large (2 vCPU, 8 GB dedicated)</option>
                  <option value="c6i.large">c6i.large (2 vCPU, 4 GB compute opt)</option>
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div>
                  <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Count: {computeCount}</label>
                  <input type="range" min="1" max="10" value={computeCount} onChange={(e) => setComputeCount(Number(e.target.value))} />
                </div>
                <div>
                  <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Disk: {storageGb} GB</label>
                  <input type="range" min="20" max="500" step="10" value={storageGb} onChange={(e) => setStorageGb(Number(e.target.value))} />
                </div>
              </div>
            </div>
          </div>

          {/* Database Controls */}
          <div className="card-subtle">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.775rem', fontWeight: 600, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <Database size={14} /> Relational Database
              </span>
              <input type="checkbox" checked={dbEnabled} onChange={(e) => setDbEnabled(e.target.checked)} />
            </div>
            {dbEnabled && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div>
                  <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Database Tier</label>
                  <select value={dbClass} onChange={(e) => setDbClass(e.target.value)}>
                    <option value="db.t3.micro">Burstable Micro (2 vCPU, 1 GB)</option>
                    <option value="db.t3.small">Burstable Small (2 vCPU, 2 GB)</option>
                    <option value="db.t3.medium">Burstable Medium (2 vCPU, 4 GB)</option>
                    <option value="db.m6g.large">General Purpose (4 vCPU, 8 GB)</option>
                  </select>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Storage: {dbStorageGb} GB</label>
                  <input type="range" min="20" max="500" step="10" value={dbStorageGb} onChange={(e) => setDbStorageGb(Number(e.target.value))} style={{ width: '110px' }} />
                </div>
                <label style={{ fontSize: '0.725rem', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <input type="checkbox" checked={dbMultiAz} onChange={(e) => setDbMultiAz(e.target.checked)} />
                  Multi-AZ High Availability Standby
                </label>
              </div>
            )}
          </div>

          {/* Storage & Network Controls */}
          <div className="card-subtle">
            <span style={{ fontSize: '0.775rem', fontWeight: 600, color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
              <Network size={14} /> Networking & Object Storage
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div>
                <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>NAT Gateways: {natCount}</label>
                <input type="range" min="0" max="3" value={natCount} onChange={(e) => setNatCount(Number(e.target.value))} />
              </div>
              <div>
                <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Egress Bandwidth: {bandwidthGb} GB/mo</label>
                <input type="range" min="50" max="2000" step="50" value={bandwidthGb} onChange={(e) => setBandwidthGb(Number(e.target.value))} />
              </div>
              <div>
                <label style={{ fontSize: '0.725rem', color: '#94a3b8' }}>Object Storage (S3 / Blob / GCS): {s3StorageGb} GB</label>
                <input type="range" min="0" max="1000" step="50" value={s3StorageGb} onChange={(e) => setS3StorageGb(Number(e.target.value))} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Arbitrage Highlight Banner */}
      {multiCloud && (
        <div style={{
          padding: '1.25rem 1.5rem',
          backgroundColor: '#0c1626',
          border: '1px solid #1e3a5f',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.675rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '3px', backgroundColor: '#10b981', color: '#090d16' }}>
                OPTIMAL SELECTION
              </span>
              <span style={{ fontSize: '0.8125rem', color: '#94a3b8' }}>
                Most Cost-Effective Cloud: <b style={{ color: '#f8fafc' }}>{multiCloud.cheapest_provider}</b>
              </span>
            </div>
            <h3 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#34d399' }}>
              Save ${multiCloud.monthly_arbitrage_savings_usd.toFixed(2)}/month (${multiCloud.annual_arbitrage_savings_usd.toFixed(2)}/year)
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.15rem' }}>
              Compared to {multiCloud.most_expensive_provider} for the exact same compute, storage, and database specifications.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <div style={{ textAlign: 'center', padding: '0.5rem 0.85rem', backgroundColor: '#080d17', borderRadius: '6px', border: '1px solid #1c2638' }}>
              <span style={{ fontSize: '0.675rem', color: '#94a3b8' }}>AWS</span>
              <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>${awsData?.total_monthly_usd.toFixed(2)}</p>
            </div>
            <div style={{ textAlign: 'center', padding: '0.5rem 0.85rem', backgroundColor: '#080d17', borderRadius: '6px', border: '1px solid #1c2638' }}>
              <span style={{ fontSize: '0.675rem', color: '#94a3b8' }}>Azure</span>
              <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8' }}>${azData?.total_monthly_usd.toFixed(2)}</p>
            </div>
            <div style={{ textAlign: 'center', padding: '0.5rem 0.85rem', backgroundColor: '#080d17', borderRadius: '6px', border: '1px solid #1c2638' }}>
              <span style={{ fontSize: '0.675rem', color: '#94a3b8' }}>GCP</span>
              <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#34d399' }}>${gcpData?.total_monthly_usd.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs: Multi-Cloud Side-by-Side vs Provider Breakdown */}
      <div className="card">
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #1c2638', paddingBottom: '0.65rem', marginBottom: '1.25rem' }}>
          <button
            onClick={() => setActiveTab('comparison')}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '4px',
              border: 'none',
              backgroundColor: activeTab === 'comparison' ? '#2563eb' : 'transparent',
              color: activeTab === 'comparison' ? '#ffffff' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            Side-by-Side Multi-Cloud Comparison
          </button>
          <button
            onClick={() => setActiveTab('aws')}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '4px',
              border: 'none',
              backgroundColor: activeTab === 'aws' ? '#161f30' : 'transparent',
              color: activeTab === 'aws' ? '#ff9900' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            AWS Line Items
          </button>
          <button
            onClick={() => setActiveTab('azure')}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '4px',
              border: 'none',
              backgroundColor: activeTab === 'azure' ? '#161f30' : 'transparent',
              color: activeTab === 'azure' ? '#38bdf8' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            Azure Line Items
          </button>
          <button
            onClick={() => setActiveTab('gcp')}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '4px',
              border: 'none',
              backgroundColor: activeTab === 'gcp' ? '#161f30' : 'transparent',
              color: activeTab === 'gcp' ? '#60a5fa' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            GCP Line Items
          </button>
        </div>

        {/* TAB 1: SIDE BY SIDE COMPARISON */}
        {activeTab === 'comparison' && multiCloud && (
          <div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #243147', color: '#64748b' }}>
                    <th style={{ padding: '0.65rem 0.75rem' }}>Expense Category</th>
                    <th style={{ padding: '0.65rem 0.75rem' }}><span className="badge-aws">AWS</span></th>
                    <th style={{ padding: '0.65rem 0.75rem' }}><span className="badge-azure">Microsoft Azure</span></th>
                    <th style={{ padding: '0.65rem 0.75rem' }}><span className="badge-gcp">Google Cloud (GCP)</span></th>
                    <th style={{ padding: '0.65rem 0.75rem' }}>FinOps Notes</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid #161f30' }}>
                    <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600, color: '#f8fafc' }}>Compute Fleet</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#f8fafc' }}>${awsData?.monthly_compute_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#38bdf8' }}>${azData?.monthly_compute_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#34d399' }}>${gcpData?.monthly_compute_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#64748b' }}>GCP E2 shared cores offer lower entry barrier; AWS t3 provides burstable credit banking.</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #161f30' }}>
                    <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600, color: '#f8fafc' }}>Storage (Block + Object)</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#f8fafc' }}>${awsData?.monthly_storage_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#34d399' }}>${azData?.monthly_storage_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#f8fafc' }}>${gcpData?.monthly_storage_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#64748b' }}>Azure Blob Storage Hot is ~21% cheaper per GB than Amazon S3 Standard.</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #161f30' }}>
                    <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600, color: '#f8fafc' }}>Relational Database</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#f8fafc' }}>${awsData?.monthly_database_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#38bdf8' }}>${azData?.monthly_database_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#34d399' }}>${gcpData?.monthly_database_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#64748b' }}>Cloud SQL micro tier is competitive; RDS and Azure Flexible Server scale identically on gp3.</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #161f30' }}>
                    <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600, color: '#f8fafc' }}>Networking & NAT</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#f8fafc' }}>${awsData?.monthly_networking_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#38bdf8' }}>${azData?.monthly_networking_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#34d399' }}>${gcpData?.monthly_networking_usd.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#64748b' }}>All 3 providers include 100 GB/mo free internet egress before applying tiered bandwidth fees.</td>
                  </tr>
                  <tr style={{ backgroundColor: '#090d16', borderTop: '2px solid #243147' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: '#f8fafc', fontSize: '0.9rem' }}>Total Monthly Spend</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: '#f8fafc', fontSize: '0.9rem' }}>${awsData?.total_monthly_usd.toFixed(2)}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: '#38bdf8', fontSize: '0.9rem' }}>${azData?.total_monthly_usd.toFixed(2)}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: '#34d399', fontSize: '0.9rem' }}>${gcpData?.total_monthly_usd.toFixed(2)}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: '#34d399' }}>
                      Lowest: {multiCloud.cheapest_provider}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Arbitrage Insights Bullet Points */}
            <div style={{ marginTop: '1.25rem', padding: '1rem', backgroundColor: '#090d16', borderRadius: '6px', border: '1px solid #1c2638' }}>
              <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                <Info size={14} /> Multi-Cloud FinOps Key Findings
              </h4>
              <ul style={{ fontSize: '0.75rem', color: '#cbd5e1', paddingLeft: '1.25rem', lineHeight: '1.6' }}>
                {multiCloud.arbitrage_insights.map((insight, idx) => (
                  <li key={idx} dangerouslySetInnerHTML={{ __html: insight.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') }} />
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* TAB 2, 3, 4: SINGLE PROVIDER LINE ITEMS */}
        {activeTab !== 'comparison' && multiCloud && (
          <div>
            {(() => {
              const currentProvider = activeTab === 'aws' ? awsData : activeTab === 'azure' ? azData : gcpData;
              if (!currentProvider) return null;
              return (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #243147', color: '#64748b' }}>
                        <th style={{ padding: '0.65rem 0.75rem' }}>Resource Component</th>
                        <th style={{ padding: '0.65rem 0.75rem' }}>Category</th>
                        <th style={{ padding: '0.65rem 0.75rem' }}>Unit Rate</th>
                        <th style={{ padding: '0.65rem 0.75rem' }}>Monthly Cost</th>
                        <th style={{ padding: '0.65rem 0.75rem' }}>Engineering Assumptions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentProvider.items.map((item, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #161f30' }}>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600, color: '#f8fafc' }}>{item.resource_name}</td>
                          <td style={{ padding: '0.65rem 0.75rem', textTransform: 'capitalize', color: '#38bdf8' }}>{item.category}</td>
                          <td style={{ padding: '0.65rem 0.75rem', color: '#cbd5e1' }}>${item.unit_price_usd.toFixed(4)} / {item.unit}</td>
                          <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: '#34d399' }}>${item.monthly_cost_usd.toFixed(2)}</td>
                          <td style={{ padding: '0.65rem 0.75rem', color: '#64748b' }}>{item.assumptions}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
};
