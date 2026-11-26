import React, { useState, useEffect } from 'react';
import {
  KeyRound,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Copy,
  Lock,
  Eye,
  EyeOff,
  Cloud
} from 'lucide-react';
import { api } from '../services/api';
import { AWSConnectionStatus, CloudProvider, LeastPrivilegePolicyGuide } from '../types';

export const ConnectAWS: React.FC = () => {
  const [activeProvider, setActiveProvider] = useState<CloudProvider>('aws');
  const [status, setStatus] = useState<AWSConnectionStatus | null>(null);
  const [policyGuide, setPolicyGuide] = useState<LeastPrivilegePolicyGuide | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // AWS Access Key inputs
  const [accessKeyId, setAccessKeyId] = useState('');
  const [secretAccessKey, setSecretAccessKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [awsRegion, setAwsRegion] = useState('us-east-1');

  // Azure Service Principal inputs
  const [azureSubId, setAzureSubId] = useState('');
  const [azureTenantId, setAzureTenantId] = useState('');
  const [azureClientId, setAzureClientId] = useState('');
  const [azureClientSecret, setAzureClientSecret] = useState('');
  const [azureRegion, setAzureRegion] = useState('eastus');

  // GCP Service Account inputs
  const [gcpProjectId, setGcpProjectId] = useState('');
  const [gcpSaEmail, setGcpSaEmail] = useState('');
  const [gcpCredsJson, setGcpCredsJson] = useState('');
  const [gcpRegion, setGcpRegion] = useState('us-central1');

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
      if (statusRes.region) setAwsRegion(statusRes.region);
      if (statusRes.azure?.region) setAzureRegion(statusRes.azure.region);
      if (statusRes.gcp?.region) setGcpRegion(statusRes.gcp.region);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch cloud connection status');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectAWS = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await api.connectAWS(accessKeyId, secretAccessKey, awsRegion, sessionToken);
      setStatus(res);
      if (res.connected) {
        setSuccessMsg(`Connected to AWS account ${res.account_id} using Access Key (${res.access_key_id_masked}).`);
        setSecretAccessKey('');
        setSessionToken('');
      } else {
        setErrorMsg(res.message || 'AWS Access Key verification failed.');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'AWS connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnectAWS = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.disconnectAWS();
      setStatus(res);
      setAccessKeyId('');
      setSecretAccessKey('');
      setSuccessMsg('AWS Access Key credentials flushed from memory.');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectAzure = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await api.connectAzure(azureSubId, azureTenantId, azureClientId, azureClientSecret, azureRegion);
      if (res.connected) {
        setSuccessMsg(`Connected to Azure Subscription ${res.identifier} (${res.region}).`);
        setAzureClientSecret('');
      } else {
        setErrorMsg(res.message || 'Azure authentication failed.');
      }
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Azure connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnectAzure = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      await api.disconnectAzure();
      await loadData();
      setSuccessMsg('Azure Service Principal credentials flushed.');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectGCP = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await api.connectGCP(gcpProjectId, gcpCredsJson, gcpRegion, gcpSaEmail);
      if (res.connected) {
        setSuccessMsg(`Connected to GCP Project ${res.identifier} (${res.region}).`);
        setGcpCredsJson('');
      } else {
        setErrorMsg(res.message || 'GCP connection failed.');
      }
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || 'GCP connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnectGCP = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      await api.disconnectGCP();
      await loadData();
      setSuccessMsg('GCP Service Account credentials flushed.');
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
          ? 'Demo sandbox activated across AWS, Azure, and GCP.'
          : 'Demo sandbox deactivated. Enter live cloud credentials below.'
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

  const azureStatus = status?.azure;
  const gcpStatus = status?.gcp;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <KeyRound className="h-6 w-6 text-brand-primary" />
            Multi-Cloud Credentials & Access Keys
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Connect AWS via IAM Access Key & Secret Key, Microsoft Azure via Service Principal, and GCP via Service Account.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="btn-secondary flex items-center gap-2 text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Verify Connections
        </button>
      </div>

      {/* Multi-Cloud Provider Switcher */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          type="button"
          onClick={() => { setActiveProvider('aws'); setErrorMsg(null); setSuccessMsg(null); }}
          className={`panel p-4 text-left transition-all border ${
            activeProvider === 'aws' ? 'border-amber-500/60 bg-surface-muted' : 'border-surface-border hover:border-brand-primary/40'
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="badge-aws">AWS</span>
            {status?.is_demo ? (
              <span className="badge-warning">Demo</span>
            ) : status?.connected ? (
              <span className="badge-green">Connected</span>
            ) : (
              <span className="badge-gray">Disconnected</span>
            )}
          </div>
          <div className="text-xs font-semibold text-white">Amazon Web Services</div>
          <div className="text-[11px] text-slate-400 font-mono mt-0.5 truncate">
            {status?.access_key_id_masked || 'Access Key & Secret'}
          </div>
        </button>

        <button
          type="button"
          onClick={() => { setActiveProvider('azure'); setErrorMsg(null); setSuccessMsg(null); }}
          className={`panel p-4 text-left transition-all border ${
            activeProvider === 'azure' ? 'border-blue-500/60 bg-surface-muted' : 'border-surface-border hover:border-brand-primary/40'
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="badge-azure">Azure</span>
            {azureStatus?.is_demo ? (
              <span className="badge-warning">Demo</span>
            ) : azureStatus?.connected ? (
              <span className="badge-green">Connected</span>
            ) : (
              <span className="badge-gray">Disconnected</span>
            )}
          </div>
          <div className="text-xs font-semibold text-white">Microsoft Azure</div>
          <div className="text-[11px] text-slate-400 font-mono mt-0.5 truncate">
            {azureStatus?.identifier || 'Service Principal'}
          </div>
        </button>

        <button
          type="button"
          onClick={() => { setActiveProvider('gcp'); setErrorMsg(null); setSuccessMsg(null); }}
          className={`panel p-4 text-left transition-all border ${
            activeProvider === 'gcp' ? 'border-cyan-500/60 bg-surface-muted' : 'border-surface-border hover:border-brand-primary/40'
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="badge-gcp">GCP</span>
            {gcpStatus?.is_demo ? (
              <span className="badge-warning">Demo</span>
            ) : gcpStatus?.connected ? (
              <span className="badge-green">Connected</span>
            ) : (
              <span className="badge-gray">Disconnected</span>
            )}
          </div>
          <div className="text-xs font-semibold text-white">Google Cloud Platform</div>
          <div className="text-[11px] text-slate-400 font-mono mt-0.5 truncate">
            {gcpStatus?.identifier || 'Service Account JSON'}
          </div>
        </button>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-red-200">Connection Alert</div>
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
          <span className="font-semibold text-white">In-Memory Credential Isolation: </span>
          Credentials are kept strictly in server memory for active API &amp; Terraform operations, never written into generated{' '}
          <code className="text-amber-400">.tf</code> files, and automatically redacted from all logs and error responses.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Status + Provider Credential Form */}
        <div className="lg:col-span-5 space-y-5">
          {/* Active Status Card */}
          <div className="panel p-5">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4 flex items-center justify-between">
              <span>{activeProvider.toUpperCase()} Status</span>
              {status?.is_demo ? (
                <span className="badge-warning">Demo Mode</span>
              ) : (activeProvider === 'aws' ? status?.connected : activeProvider === 'azure' ? azureStatus?.connected : gcpStatus?.connected) ? (
                <span className="badge-green">Connected</span>
              ) : (
                <span className="badge-gray">Disconnected</span>
              )}
            </h2>

            {activeProvider === 'aws' && (
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Auth Method</span>
                  <span className="font-mono text-white">Access Key &amp; Secret Key</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Access Key ID</span>
                  <span className="font-mono text-white">{status?.access_key_id_masked || 'Not configured'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Account ID</span>
                  <span className="font-mono text-white">{status?.account_id || 'Not configured'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Default Region</span>
                  <span className="font-mono text-white">{status?.region || 'us-east-1'}</span>
                </div>
                {status?.arn && (
                  <div className="flex justify-between py-1.5 border-b border-surface-border">
                    <span className="text-slate-400">Caller Identity</span>
                    <span className="font-mono text-[11px] text-slate-300 truncate max-w-[200px]" title={status.arn}>
                      {status.arn}
                    </span>
                  </div>
                )}
              </div>
            )}

            {activeProvider === 'azure' && (
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Auth Method</span>
                  <span className="font-mono text-white">Service Principal (OAuth2)</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Subscription ID</span>
                  <span className="font-mono text-white truncate max-w-[200px]">{azureStatus?.identifier || 'Not configured'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Default Location</span>
                  <span className="font-mono text-white">{azureStatus?.region || 'eastus'}</span>
                </div>
              </div>
            )}

            {activeProvider === 'gcp' && (
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Auth Method</span>
                  <span className="font-mono text-white">Service Account JSON</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Project ID</span>
                  <span className="font-mono text-white">{gcpStatus?.identifier || 'Not configured'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-surface-border">
                  <span className="text-slate-400">Default Region</span>
                  <span className="font-mono text-white">{gcpStatus?.region || 'us-central1'}</span>
                </div>
              </div>
            )}

            {/* Sandbox Toggle */}
            <div className="mt-5 pt-4 border-t border-surface-border flex items-center justify-between">
              <div>
                <div className="text-xs font-medium text-white">Demo Sandbox Mode</div>
                <div className="text-[11px] text-slate-400">Simulate AWS, Azure &amp; GCP safely without billing</div>
              </div>
              <button
                onClick={() => handleToggleDemoMode(!status?.is_demo)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  status?.is_demo
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30'
                    : 'bg-surface-muted text-slate-400 hover:text-white border border-surface-border'
                }`}
              >
                {status?.is_demo ? 'Exit Demo' : 'Enable Demo'}
              </button>
            </div>
          </div>

          {/* AWS Form */}
          {activeProvider === 'aws' && (
            <div className="panel p-5">
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                Connect AWS with Access Key
              </h2>

              <form onSubmit={handleConnectAWS} className="space-y-3.5">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">AWS Access Key ID</label>
                  <input
                    type="text"
                    required
                    placeholder="AKIAIOSFODNN7EXAMPLE"
                    value={accessKeyId}
                    onChange={(e) => setAccessKeyId(e.target.value.trim())}
                    className="input-text text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1">AWS Secret Access Key</label>
                  <div className="relative">
                    <input
                      type={showSecret ? 'text' : 'password'}
                      required
                      placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                      value={secretAccessKey}
                      onChange={(e) => setSecretAccessKey(e.target.value)}
                      className="input-text text-xs font-mono pr-9"
                    />
                    <button
                      type="button"
                      onClick={() => setShowSecret(!showSecret)}
                      className="absolute right-2.5 top-2 text-slate-400 hover:text-white"
                      title={showSecret ? 'Hide secret' : 'Show secret'}
                    >
                      {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1">Session Token (Optional, for temporary STS keys)</label>
                  <input
                    type="password"
                    placeholder="Optional"
                    value={sessionToken}
                    onChange={(e) => setSessionToken(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1">Target AWS Region</label>
                  <select
                    value={awsRegion}
                    onChange={(e) => setAwsRegion(e.target.value)}
                    className="input-select text-xs"
                  >
                    <option value="us-east-1">us-east-1 (N. Virginia)</option>
                    <option value="us-west-2">us-west-2 (Oregon)</option>
                    <option value="eu-west-1">eu-west-1 (Ireland)</option>
                    <option value="ap-south-1">ap-south-1 (Mumbai)</option>
                    <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
                  </select>
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary flex-1 text-xs py-2 flex items-center justify-center gap-2"
                  >
                    {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <KeyRound className="h-3.5 w-3.5" />}
                    Verify &amp; Connect AWS
                  </button>
                  {status?.connected && !status?.is_demo && (
                    <button
                      type="button"
                      onClick={handleDisconnectAWS}
                      className="btn-secondary text-xs text-red-400 hover:text-red-300"
                    >
                      Disconnect
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}

          {/* Azure Form */}
          {activeProvider === 'azure' && (
            <div className="panel p-5">
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                Connect Microsoft Azure
              </h2>

              <form onSubmit={handleConnectAzure} className="space-y-3.5">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Subscription ID</label>
                  <input
                    type="text"
                    required
                    placeholder="00000000-0000-0000-0000-000000000000"
                    value={azureSubId}
                    onChange={(e) => setAzureSubId(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Directory (Tenant) ID</label>
                  <input
                    type="text"
                    required
                    placeholder="00000000-0000-0000-0000-000000000000"
                    value={azureTenantId}
                    onChange={(e) => setAzureTenantId(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Application (Client) ID</label>
                  <input
                    type="text"
                    required
                    placeholder="00000000-0000-0000-0000-000000000000"
                    value={azureClientId}
                    onChange={(e) => setAzureClientId(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Client Secret</label>
                  <input
                    type="password"
                    required
                    placeholder="Service Principal secret value"
                    value={azureClientSecret}
                    onChange={(e) => setAzureClientSecret(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Default Azure Location</label>
                  <select
                    value={azureRegion}
                    onChange={(e) => setAzureRegion(e.target.value)}
                    className="input-select text-xs"
                  >
                    <option value="eastus">eastus (East US)</option>
                    <option value="westus2">westus2 (West US 2)</option>
                    <option value="westeurope">westeurope (West Europe)</option>
                    <option value="centralindia">centralindia (Central India)</option>
                    <option value="southeastasia">southeastasia (Southeast Asia)</option>
                  </select>
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary flex-1 text-xs py-2 flex items-center justify-center gap-2"
                  >
                    {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Cloud className="h-3.5 w-3.5" />}
                    Verify &amp; Connect Azure
                  </button>
                  {azureStatus?.connected && !azureStatus?.is_demo && (
                    <button
                      type="button"
                      onClick={handleDisconnectAzure}
                      className="btn-secondary text-xs text-red-400 hover:text-red-300"
                    >
                      Disconnect
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}

          {/* GCP Form */}
          {activeProvider === 'gcp' && (
            <div className="panel p-5">
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                Connect Google Cloud (GCP)
              </h2>

              <form onSubmit={handleConnectGCP} className="space-y-3.5">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">GCP Project ID</label>
                  <input
                    type="text"
                    required
                    placeholder="my-cloudforge-project-123"
                    value={gcpProjectId}
                    onChange={(e) => setGcpProjectId(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Service Account Email (Optional if in JSON)</label>
                  <input
                    type="text"
                    placeholder="cloudforge@my-project.iam.gserviceaccount.com"
                    value={gcpSaEmail}
                    onChange={(e) => setGcpSaEmail(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Service Account JSON Key</label>
                  <textarea
                    required
                    rows={4}
                    placeholder='{"type": "service_account", "project_id": "...", "private_key": "...", "client_email": "..."}'
                    value={gcpCredsJson}
                    onChange={(e) => setGcpCredsJson(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Default GCP Region</label>
                  <select
                    value={gcpRegion}
                    onChange={(e) => setGcpRegion(e.target.value)}
                    className="input-select text-xs"
                  >
                    <option value="us-central1">us-central1 (Iowa)</option>
                    <option value="us-east1">us-east1 (South Carolina)</option>
                    <option value="europe-west1">europe-west1 (Belgium)</option>
                    <option value="asia-south1">asia-south1 (Mumbai)</option>
                    <option value="asia-southeast1">asia-southeast1 (Singapore)</option>
                  </select>
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary flex-1 text-xs py-2 flex items-center justify-center gap-2"
                  >
                    {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Cloud className="h-3.5 w-3.5" />}
                    Connect GCP Project
                  </button>
                  {gcpStatus?.connected && !gcpStatus?.is_demo && (
                    <button
                      type="button"
                      onClick={handleDisconnectGCP}
                      className="btn-secondary text-xs text-red-400 hover:text-red-300"
                    >
                      Disconnect
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}
        </div>

        {/* Right: Setup Guide */}
        <div className="lg:col-span-7 space-y-5">
          <div className="panel p-5">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-brand-primary" />
              {activeProvider === 'aws'
                ? 'AWS Access Key Setup & Scoped Policy'
                : activeProvider === 'azure'
                ? 'Azure Service Principal Setup Guide'
                : 'GCP Service Account Setup Guide'}
            </h2>

            {activeProvider === 'aws' && (
              <>
                <p className="text-xs text-slate-400 mb-4">
                  Create an IAM user access key in AWS and attach these scoped discovery &amp; provisioning permissions:
                </p>

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

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
                      <span className="font-semibold text-white">1. Read-Only Discovery Policy (Inventory &amp; CloudWatch)</span>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(policyGuide?.read_only_policy, null, 2), 'readonly')}
                        className="text-brand-primary hover:underline flex items-center gap-1 text-[11px]"
                      >
                        <Copy className="h-3 w-3" />
                        {copiedKey === 'readonly' ? 'Copied!' : 'Copy Policy'}
                      </button>
                    </div>
                    <pre className="p-3 rounded bg-surface-dark border border-surface-border text-slate-300 font-mono text-[11px] overflow-auto max-h-44">
                      {JSON.stringify(policyGuide?.read_only_policy, null, 2)}
                    </pre>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
                      <span className="font-semibold text-white">2. Provisioning Policy (EC2, VPC, S3, RDS)</span>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(policyGuide?.provisioning_policy, null, 2), 'prov')}
                        className="text-brand-primary hover:underline flex items-center gap-1 text-[11px]"
                      >
                        <Copy className="h-3 w-3" />
                        {copiedKey === 'prov' ? 'Copied!' : 'Copy Policy'}
                      </button>
                    </div>
                    <pre className="p-3 rounded bg-surface-dark border border-surface-border text-slate-300 font-mono text-[11px] overflow-auto max-h-44">
                      {JSON.stringify(policyGuide?.provisioning_policy, null, 2)}
                    </pre>
                  </div>
                </div>
              </>
            )}

            {activeProvider === 'azure' && (
              <div className="space-y-4 text-xs text-slate-300">
                <p className="text-slate-400">
                  Run the Azure CLI command below to create a Service Principal scoped to your target subscription:
                </p>
                <pre className="p-3 rounded bg-surface-dark border border-surface-border text-cyan-300 font-mono text-[11px] overflow-auto">
{`az ad sp create-for-rbac \\
  --name "cloudforge-provisioner" \\
  --role Contributor \\
  --scopes /subscriptions/<SUBSCRIPTION_ID>`}
                </pre>
                <ul className="space-y-2 list-disc list-inside text-slate-300">
                  <li>Copy <code className="text-amber-300">appId</code> into Application (Client) ID.</li>
                  <li>Copy <code className="text-amber-300">password</code> into Client Secret.</li>
                  <li>Copy <code className="text-amber-300">tenant</code> into Directory (Tenant) ID.</li>
                </ul>
              </div>
            )}

            {activeProvider === 'gcp' && (
              <div className="space-y-4 text-xs text-slate-300">
                <p className="text-slate-400">
                  Create a GCP Service Account with Compute, Storage, and Cloud SQL permissions and download its JSON key:
                </p>
                <pre className="p-3 rounded bg-surface-dark border border-surface-border text-cyan-300 font-mono text-[11px] overflow-auto">
{`gcloud iam service-accounts create cloudforge-provisioner \\
  --display-name="CloudForge Provisioner"

gcloud projects add-iam-policy-binding <PROJECT_ID> \\
  --member="serviceAccount:cloudforge-provisioner@<PROJECT_ID>.iam.gserviceaccount.com" \\
  --role="roles/editor"

gcloud iam service-accounts keys create key.json \\
  --iam-account=cloudforge-provisioner@<PROJECT_ID>.iam.gserviceaccount.com`}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
