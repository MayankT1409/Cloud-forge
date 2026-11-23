import React, { useState, useEffect } from 'react';
import {
  KeyRound,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Copy,
  ExternalLink,
  Lock,
  Radio,
  FileCode,
  ShieldAlert,
  Server
} from 'lucide-react';
import { api } from '../services/api';
import { AWSConnectionStatus, LeastPrivilegePolicyGuide } from '../types';

export const ConnectAWS: React.FC = () => {
  const [status, setStatus] = useState<AWSConnectionStatus | null>(null);
  const [policyGuide, setPolicyGuide] = useState<LeastPrivilegePolicyGuide | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form inputs
  const [accountId, setAccountId] = useState('');
  const [roleArn, setRoleArn] = useState('');
  const [externalId, setExternalId] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusRes, policyRes] = await Promise.all([
        api.getAWSStatus(),
        api.getLeastPrivilegePolicy(),
      ]);
      setStatus(statusRes);
      setPolicyGuide(policyRes);
      if (policyRes.external_id) {
        setExternalId(policyRes.external_id);
      }
      if (statusRes.account_id && !statusRes.is_demo) {
        setAccountId(statusRes.account_id);
      }
      if (statusRes.role_arn) {
        setRoleArn(statusRes.role_arn);
      }
      if (statusRes.region) {
        setRegion(statusRes.region);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch AWS connection status');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      const res = await api.connectAWS(roleArn, externalId, accountId, region);
      setStatus(res);
      setSuccessMsg('Successfully assumed IAM role and verified identity via STS GetCallerIdentity!');
    } catch (err: any) {
      setErrorMsg(err.message || 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.disconnectAWS();
      setStatus(res);
      setSuccessMsg('AWS credentials flushed. Operating in disconnected mode.');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleDemoMode = async (enabled: boolean) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.toggleDemoMode(enabled);
      setStatus(res);
      setSuccessMsg(
        enabled
          ? 'Demo sandbox activated. Realistic state simulation enabled without AWS billing.'
          : 'Demo sandbox deactivated.'
      );
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <KeyRound className="h-6 w-6 text-brand-primary" />
            AWS Account Connection & IAM Security
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Zero-secret cross-account IAM role assumption via STS with cryptographically unique External IDs.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="btn-secondary flex items-center gap-2 text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Verify Connection
        </button>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-red-200">Security / Connection Alert</div>
            <div>{errorMsg}</div>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-sm flex items-start gap-3">
          <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-emerald-200">Operation Successful</div>
            <div>{successMsg}</div>
          </div>
        </div>
      )}

      {/* Security Architecture Principle Alert */}
      <div className="p-4 rounded-lg bg-surface-muted border border-surface-border flex items-start gap-3">
        <Lock className="h-5 w-5 text-brand-primary flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <span className="font-semibold text-white">Security Guarantee: </span>
          CloudForge never requests or stores AWS root credentials, static access keys (<code className="text-amber-400">AKIA*</code>),
          or SSH private key <code className="text-amber-400">.pem</code> files. All provisioning and inventory calls execute
          via short-lived AWS STS temporary security tokens (<code className="text-emerald-400">ASIA*</code>) valid for 1 hour.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Connection Form & Mode Toggle */}
        <div className="lg:col-span-5 space-y-5">
          {/* Active Status Card */}
          <div className="panel p-5">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4 flex items-center justify-between">
              <span>Account Status</span>
              {status?.is_demo ? (
                <span className="badge-warning">Demo Mode</span>
              ) : status?.connected ? (
                <span className="badge-green">Connected (STS)</span>
              ) : (
                <span className="badge-gray">Disconnected</span>
              )}
            </h2>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-surface-border">
                <span className="text-slate-400">Target Region</span>
                <span className="font-mono text-white">{status?.region || 'us-east-1'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-surface-border">
                <span className="text-slate-400">Account ID</span>
                <span className="font-mono text-white">{status?.account_id || 'Not configured'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-surface-border">
                <span className="text-slate-400">Read-Only Permission</span>
                <span className={status?.read_only_access ? 'text-emerald-400 font-medium' : 'text-slate-500'}>
                  {status?.read_only_access ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-surface-border">
                <span className="text-slate-400">Provisioning Permission</span>
                <span className={status?.provisioning_access ? 'text-emerald-400 font-medium' : 'text-slate-500'}>
                  {status?.provisioning_access ? 'Active' : 'Inactive'}
                </span>
              </div>
              {status?.verified_at && (
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Verified Identity</span>
                  <span className="font-mono text-[11px] text-slate-300 truncate max-w-[200px]" title={status.arn}>
                    {status.arn || 'sts:AssumeRole'}
                  </span>
                </div>
              )}
            </div>

            {/* Sandbox Toggle */}
            <div className="mt-5 pt-4 border-t border-surface-border flex items-center justify-between">
              <div>
                <div className="text-xs font-medium text-white">Demo Sandbox Mode</div>
                <div className="text-[11px] text-slate-400">Simulate actions safely without AWS credentials</div>
              </div>
              <button
                onClick={() => handleToggleDemoMode(!status?.is_demo)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  status?.is_demo
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30'
                    : 'bg-surface-muted text-slate-400 hover:text-white'
                }`}
              >
                {status?.is_demo ? 'Exit Demo' : 'Enable Demo'}
              </button>
            </div>
          </div>

          {/* Connect Account Form */}
          <div className="panel p-5">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              Cross-Account STS AssumeRole
            </h2>

            <form onSubmit={handleConnect} className="space-y-3.5">
              <div>
                <label className="text-xs text-slate-400 block mb-1">AWS Account ID (12 digits)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 123456789012"
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  className="input-text text-xs font-mono"
                  pattern="\d{12}"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">IAM Role ARN</label>
                <input
                  type="text"
                  required
                  placeholder="arn:aws:iam::123456789012:role/CloudForgeProvisionerRole"
                  value={roleArn}
                  onChange={(e) => setRoleArn(e.target.value)}
                  className="input-text text-xs font-mono"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">External ID (Anti-Confused-Deputy)</label>
                <input
                  type="text"
                  readOnly
                  value={externalId}
                  className="input-text text-xs font-mono bg-surface-dark text-slate-400"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  Generated securely by CloudForge. Must match your role trust policy.
                </span>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">Target Region</label>
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="input-select text-xs"
                >
                  <option value="us-east-1">us-east-1 (N. Virginia)</option>
                  <option value="us-west-2">us-west-2 (Oregon)</option>
                  <option value="eu-west-1">eu-west-1 (Ireland)</option>
                  <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
                </select>
              </div>

              <div className="pt-2 flex items-center gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary flex-1 text-xs py-2 flex items-center justify-center gap-2"
                >
                  {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                  Verify & Connect Role
                </button>
                {status?.connected && !status?.is_demo && (
                  <button
                    type="button"
                    onClick={handleDisconnect}
                    className="btn-secondary text-xs text-red-400 hover:text-red-300"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Right: Least-Privilege Setup Guide */}
        <div className="lg:col-span-7 space-y-5">
          <div className="panel p-5">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-brand-primary" />
              Least-Privilege Policy Guide
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              To grant CloudForge secure access, create an IAM role in your AWS account using the following scoped policies:
            </p>

            {/* Setup Steps */}
            <div className="space-y-2 mb-6">
              {policyGuide?.setup_steps.map((step, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                  <div className="h-4 w-4 rounded-full bg-brand-primary/20 text-brand-primary flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div>{step}</div>
                </div>
              ))}
            </div>

            {/* Policy JSON Blocks */}
            <div className="space-y-4">
              {/* Trust Policy */}
              <div>
                <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
                  <span className="font-semibold text-white">1. Role Trust Policy (AssumeRole with ExternalID)</span>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        JSON.stringify(policyGuide?.trust_policy, null, 2),
                        'trust'
                      )
                    }
                    className="text-brand-primary hover:underline flex items-center gap-1 text-[11px]"
                  >
                    <Copy className="h-3 w-3" />
                    {copiedKey === 'trust' ? 'Copied!' : 'Copy Policy'}
                  </button>
                </div>
                <pre className="p-3 rounded bg-surface-dark border border-surface-border text-slate-300 font-mono text-[11px] overflow-auto max-h-36">
                  {JSON.stringify(policyGuide?.trust_policy, null, 2)}
                </pre>
              </div>

              {/* Read Only Policy */}
              <div>
                <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
                  <span className="font-semibold text-white">2. Read-Only Discovery Policy (Inventory & CloudWatch)</span>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        JSON.stringify(policyGuide?.read_only_policy, null, 2),
                        'readonly'
                      )
                    }
                    className="text-brand-primary hover:underline flex items-center gap-1 text-[11px]"
                  >
                    <Copy className="h-3 w-3" />
                    {copiedKey === 'readonly' ? 'Copied!' : 'Copy Policy'}
                  </button>
                </div>
                <pre className="p-3 rounded bg-surface-dark border border-surface-border text-slate-300 font-mono text-[11px] overflow-auto max-h-36">
                  {JSON.stringify(policyGuide?.read_only_policy, null, 2)}
                </pre>
              </div>

              {/* Provisioning Policy */}
              <div>
                <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
                  <span className="font-semibold text-white">3. Provisioning Policy (Scoped to Approved Templates)</span>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        JSON.stringify(policyGuide?.provisioning_policy, null, 2),
                        'prov'
                      )
                    }
                    className="text-brand-primary hover:underline flex items-center gap-1 text-[11px]"
                  >
                    <Copy className="h-3 w-3" />
                    {copiedKey === 'prov' ? 'Copied!' : 'Copy Policy'}
                  </button>
                </div>
                <pre className="p-3 rounded bg-surface-dark border border-surface-border text-slate-300 font-mono text-[11px] overflow-auto max-h-36">
                  {JSON.stringify(policyGuide?.provisioning_policy, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
