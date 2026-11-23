import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { QuestionnaireState, RecommendationResponse } from '../types';
import {
  Compass,
  ArrowRight,
  ArrowLeft,
  Download,
  CheckCircle2,
  ShieldAlert,
  Layers,
  Server,
  Database,
  ExternalLink
} from 'lucide-react';

export const Advisor: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5;

  const [formData, setFormData] = useState<QuestionnaireState>({
    app_type: 'web_application',
    runtime: 'Python / FastAPI',
    environment: 'production',
    daily_users: 5000,
    concurrent_users: 250,
    traffic_pattern: 'steady',
    scaling_required: true,
    cpu_cores: 2,
    ram_gb: 4,
    storage_gb: 50,
    bandwidth_gb_month: 150,
    db_required: true,
    db_engine: 'postgres',
    db_size_gb: 30,
    db_connections: 50,
    file_storage_required: true,
    file_storage_gb: 100,
    network_access: 'public_facing',
    encryption_at_rest: true,
    encryption_in_transit: true,
    waf_required: false,
    multi_az: true,
    sla_target: '99.9',
    backup_retention_days: 7,
    monthly_budget_usd: 250,
    preferred_region: 'us-east-1',
    existing_constraints: '',
  });

  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [reportsList, setReportsList] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const reps = await api.listReports();
      setReportsList(reps);
    } catch (e) {
      console.error('Failed to load past reports:', e);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.submitQuestionnaire(formData);
      setRecommendation(res);
      loadReports();
    } catch (err: any) {
      setError(err.message || 'Failed to generate recommendations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '1.75rem 2rem', display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: '1440px', margin: '0 auto' }}>
      {!recommendation ? (
        <div className="card">
          {error && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '6px',
              color: '#f87171',
              marginBottom: '1rem',
              fontSize: '0.8125rem'
            }}>
              {error}
            </div>
          )}

          {/* Stepper Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <div>
              <span style={{ fontSize: '0.675rem', fontWeight: 600, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Architecture Planning Engine
              </span>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.1rem' }}>
                Step {currentStep} of {totalSteps}: {
                  currentStep === 1 ? 'Application Profile & Runtime' :
                  currentStep === 2 ? 'Traffic & Concurrency' :
                  currentStep === 3 ? 'Compute & Resource Sizing' :
                  currentStep === 4 ? 'Database & Storage Requirements' :
                  'Security, Compliance & Target Budget'
                }
              </h3>
            </div>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              {[1, 2, 3, 4, 5].map((s) => (
                <div
                  key={s}
                  style={{
                    width: '28px',
                    height: '4px',
                    borderRadius: '2px',
                    backgroundColor: s === currentStep ? '#38bdf8' : s < currentStep ? '#10b981' : '#1c2638'
                  }}
                />
              ))}
            </div>
          </div>

          {/* STEP 1: Application Profile */}
          {currentStep === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Application Architecture Pattern
                  </label>
                  <select
                    value={formData.app_type}
                    onChange={(e) => setFormData({ ...formData, app_type: e.target.value })}
                  >
                    <option value="web_application">Web Application (Full Stack)</option>
                    <option value="api_backend">REST / GraphQL API Backend</option>
                    <option value="microservices">Microservices Architecture</option>
                    <option value="static_website">Static Website (SPA)</option>
                    <option value="background_worker">Background Worker / Asynchronous Queue</option>
                    <option value="data_processing">Data Processing / ETL Pipeline</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Language & Framework Runtime
                  </label>
                  <input
                    type="text"
                    value={formData.runtime}
                    onChange={(e) => setFormData({ ...formData, runtime: e.target.value })}
                    placeholder="e.g. Python / FastAPI, Node.js, Go"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Deployment Environment
                  </label>
                  <select
                    value={formData.environment}
                    onChange={(e: any) => setFormData({ ...formData, environment: e.target.value })}
                  >
                    <option value="development">Development</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Traffic & Concurrency */}
          {currentStep === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Peak Concurrent Users
                  </label>
                  <input
                    type="number"
                    value={formData.concurrent_users}
                    onChange={(e) => setFormData({ ...formData, concurrent_users: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Daily Active Users (DAU)
                  </label>
                  <input
                    type="number"
                    value={formData.daily_users}
                    onChange={(e) => setFormData({ ...formData, daily_users: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Traffic Distribution Profile
                  </label>
                  <select
                    value={formData.traffic_pattern}
                    onChange={(e: any) => setFormData({ ...formData, traffic_pattern: e.target.value })}
                  >
                    <option value="steady">Steady & Predictable</option>
                    <option value="spiky">Spiky & Volatile</option>
                    <option value="predictable_peaks">Scheduled Business Hour Peaks</option>
                  </select>
                </div>
              </div>
              <label style={{ fontSize: '0.8rem', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.45rem', marginTop: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={formData.scaling_required}
                  onChange={(e) => setFormData({ ...formData, scaling_required: e.target.checked })}
                />
                Configure Automated Horizontal Auto-Scaling
              </label>
            </div>
          )}

          {/* STEP 3: Compute & Sizing */}
          {currentStep === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Target CPU Cores
                  </label>
                  <input
                    type="number"
                    value={formData.cpu_cores}
                    onChange={(e) => setFormData({ ...formData, cpu_cores: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Estimated RAM (GB)
                  </label>
                  <input
                    type="number"
                    value={formData.ram_gb}
                    onChange={(e) => setFormData({ ...formData, ram_gb: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Root Disk Storage (GB)
                  </label>
                  <input
                    type="number"
                    value={formData.storage_gb}
                    onChange={(e) => setFormData({ ...formData, storage_gb: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Monthly Egress Bandwidth (GB)
                  </label>
                  <input
                    type="number"
                    value={formData.bandwidth_gb_month}
                    onChange={(e) => setFormData({ ...formData, bandwidth_gb_month: Number(e.target.value) })}
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Database & Storage */}
          {currentStep === 4 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <label style={{ fontSize: '0.8125rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 600 }}>
                <input
                  type="checkbox"
                  checked={formData.db_required}
                  onChange={(e) => setFormData({ ...formData, db_required: e.target.checked })}
                />
                Requires managed relational or document database tier
              </label>

              {formData.db_required && (
                <div className="card-subtle" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                      Database Engine
                    </label>
                    <select
                      value={formData.db_engine}
                      onChange={(e) => setFormData({ ...formData, db_engine: e.target.value })}
                    >
                      <option value="postgres">PostgreSQL</option>
                      <option value="mysql">MySQL</option>
                      <option value="aurora_postgres">Amazon Aurora PostgreSQL</option>
                      <option value="aurora_mysql">Amazon Aurora MySQL</option>
                      <option value="dynamodb">Amazon DynamoDB (NoSQL)</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                      Allocated Storage (GB)
                    </label>
                    <input
                      type="number"
                      value={formData.db_size_gb}
                      onChange={(e) => setFormData({ ...formData, db_size_gb: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                      Concurrent Database Connections
                    </label>
                    <input
                      type="number"
                      value={formData.db_connections}
                      onChange={(e) => setFormData({ ...formData, db_connections: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                      Backup Retention (Days)
                    </label>
                    <input
                      type="number"
                      value={formData.backup_retention_days}
                      onChange={(e) => setFormData({ ...formData, backup_retention_days: Number(e.target.value) })}
                    />
                  </div>
                </div>
              )}

              <div>
                <label style={{ fontSize: '0.8125rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 600 }}>
                  <input
                    type="checkbox"
                    checked={formData.file_storage_required}
                    onChange={(e) => setFormData({ ...formData, file_storage_required: e.target.checked })}
                  />
                  Requires cloud object storage for assets & uploads (S3 / Blob / GCS)
                </label>
                {formData.file_storage_required && (
                  <div style={{ marginTop: '0.75rem', width: '220px' }}>
                    <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                      Object Storage Capacity (GB)
                    </label>
                    <input
                      type="number"
                      value={formData.file_storage_gb}
                      onChange={(e) => setFormData({ ...formData, file_storage_gb: Number(e.target.value) })}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 5: Security & Budget */}
          {currentStep === 5 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Network Exposure
                  </label>
                  <select
                    value={formData.network_access}
                    onChange={(e) => setFormData({ ...formData, network_access: e.target.value })}
                  >
                    <option value="public_facing">Public-Facing via Application Load Balancer</option>
                    <option value="private_vpc">Private VPC Internal Only</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Target Monthly Budget (USD)
                  </label>
                  <input
                    type="number"
                    value={formData.monthly_budget_usd}
                    onChange={(e) => setFormData({ ...formData, monthly_budget_usd: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.775rem', color: '#94a3b8', display: 'block', marginBottom: '0.35rem' }}>
                    Primary Deployment Region
                  </label>
                  <select
                    value={formData.preferred_region}
                    onChange={(e) => setFormData({ ...formData, preferred_region: e.target.value })}
                  >
                    <option value="us-east-1">us-east-1 (N. Virginia)</option>
                    <option value="us-west-2">us-west-2 (Oregon)</option>
                    <option value="eu-west-1">eu-west-1 (Ireland)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginTop: '0.5rem' }}>
                <label style={{ fontSize: '0.775rem', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                  <input
                    type="checkbox"
                    checked={formData.multi_az}
                    onChange={(e) => setFormData({ ...formData, multi_az: e.target.checked })}
                  />
                  Enforce Multi-AZ High Availability (Automatic Failover)
                </label>
                <label style={{ fontSize: '0.775rem', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                  <input
                    type="checkbox"
                    checked={formData.waf_required}
                    onChange={(e) => setFormData({ ...formData, waf_required: e.target.checked })}
                  />
                  Attach AWS WAF (Web Application Firewall) for Layer 7 OWASP Protection
                </label>
                <label style={{ fontSize: '0.775rem', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                  <input
                    type="checkbox"
                    checked={formData.encryption_at_rest}
                    onChange={(e) => setFormData({ ...formData, encryption_at_rest: e.target.checked })}
                  />
                  Enforce AWS KMS Encryption at Rest
                </label>
              </div>
            </div>
          )}

          {/* Stepper Footer Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem', borderTop: '1px solid #1c2638', paddingTop: '1rem' }}>
            <button
              onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
              disabled={currentStep === 1}
              className="btn-secondary"
            >
              <ArrowLeft size={14} /> Back
            </button>

            {currentStep < totalSteps ? (
              <button
                onClick={() => setCurrentStep(currentStep + 1)}
                className="btn-primary"
              >
                Continue <ArrowRight size={14} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="btn-primary"
                style={{ backgroundColor: '#10b981' }}
              >
                <Compass size={14} />
                {loading ? 'Evaluating Rules & Generating Report...' : 'Generate Architecture Specification'}
              </button>
            )}
          </div>
        </div>
      ) : (
        /* RECOMMENDATION RESULTS VIEW */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Header Action Bar */}
          <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.2rem' }}>
                <span className="badge-live">DETERMINISTIC EVALUATION READY</span>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Report ID: {recommendation.report_id}</span>
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Architecture Tier: {recommendation.recommended_tier}
              </h3>
            </div>
            <div style={{ display: 'flex', gap: '0.65rem' }}>
              <button
                onClick={() => setRecommendation(null)}
                className="btn-secondary"
              >
                Adjust Parameters
              </button>
              <a
                href={api.getReportPdfUrl(recommendation.report_id)}
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{ textDecoration: 'none' }}
              >
                <Download size={14} /> Download PDF Report
              </a>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="card">
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.35rem' }}>
              Executive Summary
            </h4>
            <p style={{ fontSize: '0.8125rem', color: '#cbd5e1', lineHeight: '1.6' }}>
              {recommendation.executive_summary}
            </p>
          </div>

          {/* MULTI-CLOUD EQUIVALENTS MATRIX (CENTERPIECE) */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                  Multi-Cloud Architecture Equivalents Matrix
                </h4>
                <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  Standardized workload mappings across AWS, Microsoft Azure, and Google Cloud Platform.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <span className="badge-aws">AWS</span>
                <span className="badge-azure">Azure</span>
                <span className="badge-gcp">GCP</span>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.775rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #243147', color: '#64748b' }}>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Component</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>AWS Service</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Azure Equivalent</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>GCP Equivalent</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Portability Strategy</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendation.multi_cloud_mapping.map((m, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #161f30' }}>
                      <td style={{ padding: '0.65rem 0.5rem', fontWeight: 600, color: '#f8fafc' }}>{m.tier_component}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#ff9900' }}>{m.aws_service}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#38bdf8' }}>{m.azure_service}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#60a5fa' }}>{m.gcp_service}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#94a3b8' }}>{m.portability_guidance}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sizing & Primary AWS Services */}
          <div className="card">
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.85rem' }}>
              Resource Breakdown (AWS Baseline)
            </h4>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.775rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #243147', color: '#64748b' }}>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Service</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Category</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Configuration Details</th>
                    <th style={{ padding: '0.65rem 0.5rem' }}>Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendation.recommended_services.map((s, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #161f30' }}>
                      <td style={{ padding: '0.65rem 0.5rem', fontWeight: 600, color: '#f8fafc' }}>{s.service_name}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#38bdf8' }}>{s.category}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#cbd5e1' }}>{s.configuration_details}</td>
                      <td style={{ padding: '0.65rem 0.5rem', color: '#64748b' }}>{s.rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Implementation Roadmap */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <div className="card">
              <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
                <ShieldAlert size={16} /> Operational Risks & Bottlenecks
              </h4>
              <ul style={{ fontSize: '0.775rem', color: '#cbd5e1', paddingLeft: '1.25rem', lineHeight: '1.6' }}>
                {recommendation.risks_and_bottlenecks.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>

            <div className="card">
              <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
                <CheckCircle2 size={16} /> Step-by-Step Implementation Plan
              </h4>
              <ul style={{ fontSize: '0.775rem', color: '#cbd5e1', paddingLeft: '1.25rem', lineHeight: '1.6' }}>
                {recommendation.step_by_step_implementation_plan.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Archived Reports */}
      {reportsList.length > 0 && (
        <div className="card">
          <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.75rem' }}>
            Archived PDF Reports ({reportsList.length})
          </h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.775rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1c2638', color: '#64748b' }}>
                  <th style={{ padding: '0.5rem' }}>Report ID</th>
                  <th style={{ padding: '0.5rem' }}>Tier</th>
                  <th style={{ padding: '0.5rem' }}>Est. Spend</th>
                  <th style={{ padding: '0.5rem' }}>Generated</th>
                  <th style={{ padding: '0.5rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {reportsList.map((r) => (
                  <tr key={r.report_id} style={{ borderBottom: '1px solid #141b29' }}>
                    <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#38bdf8' }}>{r.report_id}</td>
                    <td style={{ padding: '0.5rem', color: '#f8fafc' }}>{r.recommended_tier}</td>
                    <td style={{ padding: '0.5rem', color: '#34d399' }}>${r.estimated_monthly_cost?.toFixed(2)}/mo</td>
                    <td style={{ padding: '0.5rem', color: '#64748b' }}>{r.created_at?.slice(0, 10)}</td>
                    <td style={{ padding: '0.5rem' }}>
                      <a
                        href={api.getReportPdfUrl(r.report_id)}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: '#38bdf8', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                      >
                        <Download size={12} /> Download
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
