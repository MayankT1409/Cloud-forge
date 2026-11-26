import React, { useState, useEffect, useRef } from 'react';
import {
  Layers,
  Server,
  Database,
  KeyRound,
  HardDrive,
  Terminal,
  Play,
  Trash2,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Eye,
  FileCode,
  Info
} from 'lucide-react';
import { api } from '../services/api';
import { AWSConnectionStatus, CloudProvider, PlanResponse, OperationRecord } from '../types';

const PROVIDER_REGIONS: Record<CloudProvider, Array<{ value: string; label: string }>> = {
  aws: [
    { value: 'us-east-1', label: 'us-east-1 (N. Virginia)' },
    { value: 'us-west-2', label: 'us-west-2 (Oregon)' },
    { value: 'eu-west-1', label: 'eu-west-1 (Ireland)' },
    { value: 'ap-south-1', label: 'ap-south-1 (Mumbai)' },
    { value: 'ap-southeast-1', label: 'ap-southeast-1 (Singapore)' },
  ],
  azure: [
    { value: 'eastus', label: 'eastus (East US)' },
    { value: 'westus2', label: 'westus2 (West US 2)' },
    { value: 'westeurope', label: 'westeurope (West Europe)' },
    { value: 'centralindia', label: 'centralindia (Central India)' },
    { value: 'southeastasia', label: 'southeastasia (Southeast Asia)' },
  ],
  gcp: [
    { value: 'us-central1', label: 'us-central1 (Iowa)' },
    { value: 'us-east1', label: 'us-east1 (South Carolina)' },
    { value: 'europe-west1', label: 'europe-west1 (Belgium)' },
    { value: 'asia-south1', label: 'asia-south1 (Mumbai)' },
    { value: 'asia-southeast1', label: 'asia-southeast1 (Singapore)' },
  ],
};

const INSTANCE_OPTIONS: Record<CloudProvider, Array<{ value: string; label: string }>> = {
  aws: [
    { value: 't3.micro', label: 't3.micro (2 vCPU, 1 GB)' },
    { value: 't3.small', label: 't3.small (2 vCPU, 2 GB)' },
    { value: 't3.medium', label: 't3.medium (2 vCPU, 4 GB)' },
    { value: 'm6i.large', label: 'm6i.large (2 vCPU, 8 GB)' },
    { value: 'c6i.xlarge', label: 'c6i.xlarge (4 vCPU, 8 GB)' },
  ],
  azure: [
    { value: 'Standard_B1s', label: 'Standard_B1s (1 vCPU, 1 GB)' },
    { value: 'Standard_B1ms', label: 'Standard_B1ms (1 vCPU, 2 GB)' },
    { value: 'Standard_B2s', label: 'Standard_B2s (2 vCPU, 4 GB)' },
    { value: 'Standard_D2s_v5', label: 'Standard_D2s_v5 (2 vCPU, 8 GB)' },
    { value: 'Standard_F4s_v2', label: 'Standard_F4s_v2 (4 vCPU, 8 GB)' },
  ],
  gcp: [
    { value: 'e2-micro', label: 'e2-micro (2 vCPU, 1 GB)' },
    { value: 'e2-small', label: 'e2-small (2 vCPU, 2 GB)' },
    { value: 'e2-medium', label: 'e2-medium (2 vCPU, 4 GB)' },
    { value: 'n2-standard-2', label: 'n2-standard-2 (2 vCPU, 8 GB)' },
    { value: 'c2-standard-4', label: 'c2-standard-4 (4 vCPU, 16 GB)' },
  ],
};

export const Provisioning: React.FC = () => {
  // Provider & Global State
  const [provider, setProvider] = useState<CloudProvider>('aws');
  const [environment, setEnvironment] = useState<'dev' | 'staging' | 'prod'>('dev');
  const [region, setRegion] = useState('us-east-1');
  const [cloudStatus, setCloudStatus] = useState<AWSConnectionStatus | null>(null);

  // Inline Credentials (Access Key & Secret for AWS, Service Principal for Azure, SA JSON for GCP)
  const [awsAccessKey, setAwsAccessKey] = useState('');
  const [awsSecretKey, setAwsSecretKey] = useState('');
  const [azureResourceGroup, setAzureResourceGroup] = useState('rg-cloudforge-dev');
  const [azureSubId, setAzureSubId] = useState('');
  const [azureTenantId, setAzureTenantId] = useState('');
  const [azureClientId, setAzureClientId] = useState('');
  const [azureClientSecret, setAzureClientSecret] = useState('');
  const [gcpProjectId, setGcpProjectId] = useState('');
  const [gcpCredsJson, setGcpCredsJson] = useState('');
  const [connectingCreds, setConnectingCreds] = useState(false);
  const [credNotice, setCredNotice] = useState<string | null>(null);

  // Network Config
  const [vpcEnabled, setVpcEnabled] = useState(true);
  const [vpcName, setVpcName] = useState('cloudforge-vpc');
  const [cidrBlock, setCidrBlock] = useState('10.0.0.0/16');
  const [enableNat, setEnableNat] = useState(true);

  // Compute Config
  const [ec2Enabled, setEc2Enabled] = useState(true);
  const [ec2Name, setEc2Name] = useState('cloudforge-app-server');
  const [instanceType, setInstanceType] = useState('t3.medium');
  const [amiId] = useState('ami-0c7217cdde317cfec');
  const [rootVolumeSize, setRootVolumeSize] = useState(30);
  const [enableImdsV2, setEnableImdsV2] = useState(true);

  // Object Storage Config
  const [s3Enabled, setS3Enabled] = useState(true);
  const [bucketPrefix, setBucketPrefix] = useState('cloudforge-storage');
  const [versioning, setVersioning] = useState(true);
  const [blockPublicAccess, setBlockPublicAccess] = useState(true);

  // Database Config
  const [rdsEnabled, setRdsEnabled] = useState(false);
  const [dbIdentifier, setDbIdentifier] = useState('cloudforge-db');
  const [dbEngine, setDbEngine] = useState<'postgres' | 'mysql'>('postgres');
  const [dbInstanceClass, setDbInstanceClass] = useState('db.t3.micro');
  const [allocatedStorage] = useState(20);
  const [multiAz, setMultiAz] = useState(false);
  const [backupRetention] = useState(7);
  const [deletionProtection, setDeletionProtection] = useState(true);

  // Workflow State
  const [isPlanning, setIsPlanning] = useState(false);
  const [planResult, setPlanResult] = useState<PlanResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'plan_summary' | 'terraform_hcl' | 'live_terminal'>('plan_summary');

  // Confirmation Modals
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applyConfirmPhrase, setApplyConfirmPhrase] = useState('');
  const [isApplying, setIsApplying] = useState(false);

  const [showDestroyModal, setShowDestroyModal] = useState(false);
  const [destroyConfirmPhrase, setDestroyConfirmPhrase] = useState('');
  const [isDestroying, setIsDestroying] = useState(false);

  // Active Operation Polling
  const [currentOperationId, setCurrentOperationId] = useState<string | null>(null);
  const [currentOperation, setCurrentOperation] = useState<OperationRecord | null>(null);
  const [recentOperations, setRecentOperations] = useState<OperationRecord[]>([]);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (!currentOperationId) return;

    const interval = setInterval(async () => {
      try {
        const op = await api.getOperationStatus(currentOperationId);
        setCurrentOperation(op);
        if (op.status === 'succeeded' || op.status === 'failed') {
          clearInterval(interval);
          loadRecentOperations();
        }
      } catch (e) {
        console.error('Failed to poll operation', e);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [currentOperationId]);

  useEffect(() => {
    if (activeTab === 'live_terminal' && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentOperation?.raw_logs, activeTab]);

  const loadInitialData = async () => {
    await Promise.all([loadRecentOperations(), loadCloudStatus()]);
  };

  const loadCloudStatus = async () => {
    try {
      const status = await api.getAWSStatus();
      setCloudStatus(status);
    } catch {
      // ignore
    }
  };

  const loadRecentOperations = async () => {
    try {
      const ops = await api.listOperations();
      setRecentOperations(ops);
    } catch {
      // ignore
    }
  };

  const handleProviderChange = (next: CloudProvider) => {
    setProvider(next);
    setRegion(PROVIDER_REGIONS[next][0].value);
    setInstanceType(INSTANCE_OPTIONS[next][2].value);
    setPlanResult(null);
    setErrorMsg(null);
    setCredNotice(null);
  };

  const handleConnectInlineCredentials = async (): Promise<boolean> => {
    setConnectingCreds(true);
    setErrorMsg(null);
    setCredNotice(null);
    try {
      if (provider === 'aws') {
        const res = await api.connectAWS(awsAccessKey, awsSecretKey, region);
        setCloudStatus(res);
        if (!res.connected) {
          setErrorMsg(res.message || 'AWS Access Key authentication failed.');
          return false;
        }
        setCredNotice(`Connected AWS (${res.account_id}) via Access Key ${res.access_key_id_masked}`);
        setAwsSecretKey('');
        return true;
      }
      if (provider === 'azure') {
        const res = await api.connectAzure(azureSubId, azureTenantId, azureClientId, azureClientSecret, region);
        await loadCloudStatus();
        if (!res.connected) {
          setErrorMsg(res.message || 'Azure Service Principal authentication failed.');
          return false;
        }
        setCredNotice(`Connected Azure Subscription ${res.identifier}`);
        setAzureClientSecret('');
        return true;
      }
      const res = await api.connectGCP(gcpProjectId, gcpCredsJson, region);
      await loadCloudStatus();
      if (!res.connected) {
        setErrorMsg(res.message || 'GCP Service Account connection failed.');
        return false;
      }
      setCredNotice(`Connected GCP Project ${res.identifier}`);
      setGcpCredsJson('');
      return true;
    } catch (err: any) {
      setErrorMsg(err.message || 'Credential connection failed');
      return false;
    } finally {
      setConnectingCreds(false);
    }
  };

  const handleGeneratePlan = async () => {
    setIsPlanning(true);
    setErrorMsg(null);
    try {
      // If user filled inline credentials on the Provisioning page, connect them before planning
      if (provider === 'aws' && awsAccessKey && awsSecretKey) {
        const ok = await handleConnectInlineCredentials();
        if (!ok) {
          setIsPlanning(false);
          return;
        }
      } else if (provider === 'azure' && azureSubId && azureTenantId && azureClientId && azureClientSecret) {
        const ok = await handleConnectInlineCredentials();
        if (!ok) {
          setIsPlanning(false);
          return;
        }
      } else if (provider === 'gcp' && gcpProjectId && gcpCredsJson) {
        const ok = await handleConnectInlineCredentials();
        if (!ok) {
          setIsPlanning(false);
          return;
        }
      }

      const payload = {
        provider,
        environment,
        region,
        azure_resource_group: azureResourceGroup,
        gcp_project_id: gcpProjectId || cloudStatus?.gcp?.identifier || undefined,
        tags: { Project: 'CloudForge', Environment: environment },
        vpc: {
          enabled: vpcEnabled,
          name: vpcName,
          cidr_block: cidrBlock,
          enable_nat_gateway: enableNat,
          single_nat_gateway: true,
        },
        ec2: {
          enabled: ec2Enabled,
          name: ec2Name,
          instance_type: instanceType,
          ami_id: amiId,
          root_volume_size_gb: rootVolumeSize,
          root_volume_type: 'gp3',
          associate_public_ip: false,
          enable_imds_v2: enableImdsV2,
        },
        s3: {
          enabled: s3Enabled,
          bucket_name_prefix: bucketPrefix,
          versioning_enabled: versioning,
          block_public_access: blockPublicAccess,
          server_side_encryption: 'AES256',
        },
        rds: {
          enabled: rdsEnabled,
          db_identifier: dbIdentifier,
          engine: dbEngine,
          engine_version: dbEngine === 'postgres' ? '15.4' : '8.0',
          instance_class: dbInstanceClass,
          allocated_storage_gb: allocatedStorage,
          storage_type: 'gp3',
          multi_az: multiAz,
          publicly_accessible: false,
          backup_retention_period: backupRetention,
          deletion_protection: deletionProtection,
        },
        iam: {
          enabled: false,
          role_name: 'unused',
          attach_ssm_policy: false,
          attach_s3_readonly: false,
        },
      };

      const res = await api.generatePlan(payload);
      setPlanResult(res);
      setActiveTab('plan_summary');
    } catch (err: any) {
      setErrorMsg(err.message || 'Plan generation failed');
    } finally {
      setIsPlanning(false);
    }
  };

  const handleApply = async () => {
    if (!planResult) return;
    setIsApplying(true);
    setErrorMsg(null);
    try {
      const res = await api.executeApply(planResult.plan_id, applyConfirmPhrase);
      setShowApplyModal(false);
      setApplyConfirmPhrase('');
      setCurrentOperationId(res.operation_id);
      setActiveTab('live_terminal');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to trigger apply');
    } finally {
      setIsApplying(false);
    }
  };

  const handleDestroy = async () => {
    if (!planResult) return;
    setIsDestroying(true);
    setErrorMsg(null);
    try {
      const res = await api.executeDestroy(planResult.plan_id, destroyConfirmPhrase);
      setShowDestroyModal(false);
      setDestroyConfirmPhrase('');
      setCurrentOperationId(res.operation_id);
      setActiveTab('live_terminal');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to trigger destroy');
    } finally {
      setIsDestroying(false);
    }
  };

  const isSelectedProviderConnected =
    cloudStatus?.is_demo ||
    (provider === 'aws' && cloudStatus?.connected) ||
    (provider === 'azure' && cloudStatus?.azure?.connected) ||
    (provider === 'gcp' && cloudStatus?.gcp?.connected);

  const networkTitle =
    provider === 'aws'
      ? 'VPC & Networking'
      : provider === 'azure'
      ? 'Azure Virtual Network (VNet)'
      : 'GCP VPC Network';

  const computeTitle =
    provider === 'aws'
      ? 'EC2 Virtual Machine'
      : provider === 'azure'
      ? 'Azure Linux Virtual Machine'
      : 'Compute Engine VM';

  const storageTitle =
    provider === 'aws'
      ? 'S3 Object Storage'
      : provider === 'azure'
      ? 'Azure Blob Storage Account'
      : 'Google Cloud Storage (GCS)';

  const dbTitle =
    provider === 'aws'
      ? 'RDS Managed Database'
      : provider === 'azure'
      ? 'Azure Flexible DB Server'
      : 'Google Cloud SQL';

  return (
    <div className="space-y-6">
      {/* Page Title & Cloud Selector */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Layers className="h-6 w-6 text-brand-primary" />
            Multi-Cloud Infrastructure Provisioning
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Provision AWS (via Access Key &amp; Secret), Microsoft Azure, and Google Cloud Platform resources with Terraform HCL.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={environment}
            onChange={(e) => setEnvironment(e.target.value as any)}
            className="input-select w-32 text-sm"
          >
            <option value="dev">dev</option>
            <option value="staging">staging</option>
            <option value="prod">prod</option>
          </select>

          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="input-select w-48 text-sm"
          >
            {PROVIDER_REGIONS[provider].map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>

          <button
            onClick={handleGeneratePlan}
            disabled={isPlanning || connectingCreds}
            className="btn-primary flex items-center gap-2"
          >
            {isPlanning ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Planning...
              </>
            ) : (
              <>
                <Terminal className="h-4 w-4" />
                Validate &amp; Plan
              </>
            )}
          </button>
        </div>
      </div>

      {/* Multi-Cloud Target Tabs */}
      <div className="panel p-2 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleProviderChange('aws')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${
              provider === 'aws'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            AWS (Access Key)
          </button>

          <button
            type="button"
            onClick={() => handleProviderChange('azure')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${
              provider === 'azure'
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-blue-400" />
            Microsoft Azure
          </button>

          <button
            type="button"
            onClick={() => handleProviderChange('gcp')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${
              provider === 'gcp'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            Google Cloud (GCP)
          </button>
        </div>

        <div className="flex items-center gap-2 text-xs pr-2">
          {cloudStatus?.is_demo ? (
            <span className="badge-warning">Demo Sandbox Mode</span>
          ) : isSelectedProviderConnected ? (
            <span className="badge-green">
              {provider.toUpperCase()} Live Credentials Ready
            </span>
          ) : (
            <span className="badge-gray">{provider.toUpperCase()} Not Connected</span>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-red-200">Execution Error</div>
            <div>{errorMsg}</div>
          </div>
        </div>
      )}

      {credNotice && (
        <div className="p-3.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
          <CheckCircle className="h-4 w-4 text-emerald-400 flex-shrink-0" />
          <span>{credNotice}</span>
        </div>
      )}

      {/* Main Grid: Resource Configuration (Left) & Plan/Logs (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Credentials + Resource Form */}
        <div className="lg:col-span-5 space-y-4">
          {/* Access Key & Cloud Credentials Card (Replaced IAM Role) */}
          <div className="panel p-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-cyan-400" />
                <span className="font-medium text-white text-sm">
                  {provider === 'aws'
                    ? 'AWS Access Key & Secret Key'
                    : provider === 'azure'
                    ? 'Azure Service Principal'
                    : 'GCP Service Account'}
                </span>
              </div>
              {isSelectedProviderConnected ? (
                <span className="badge-green text-[10px]">
                  {cloudStatus?.is_demo ? 'Sandbox' : 'Authenticated'}
                </span>
              ) : (
                <span className="badge-warning text-[10px]">Required for Live</span>
              )}
            </div>

            {provider === 'aws' && (
              <div className="mt-3 space-y-2.5 text-xs">
                {cloudStatus?.connected && !cloudStatus?.is_demo && (
                  <div className="p-2 rounded bg-emerald-950/30 border border-emerald-500/20 text-emerald-300 font-mono text-[11px]">
                    Active Key: {cloudStatus.access_key_id_masked} ({cloudStatus.account_id})
                  </div>
                )}
                <div>
                  <label className="text-slate-400 block mb-1">AWS Access Key ID</label>
                  <input
                    type="text"
                    placeholder="AKIAIOSFODNN7EXAMPLE"
                    value={awsAccessKey}
                    onChange={(e) => setAwsAccessKey(e.target.value.trim())}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">AWS Secret Access Key</label>
                  <input
                    type="password"
                    placeholder="Enter Secret Access Key"
                    value={awsSecretKey}
                    onChange={(e) => setAwsSecretKey(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleConnectInlineCredentials}
                  disabled={connectingCreds || !awsAccessKey || !awsSecretKey}
                  className="btn-secondary w-full justify-center text-xs py-1.5"
                >
                  {connectingCreds ? 'Verifying Keys...' : 'Connect & Use AWS Access Keys'}
                </button>
              </div>
            )}

            {provider === 'azure' && (
              <div className="mt-3 space-y-2.5 text-xs">
                {cloudStatus?.azure?.connected && !cloudStatus?.is_demo && (
                  <div className="p-2 rounded bg-emerald-950/30 border border-emerald-500/20 text-emerald-300 font-mono text-[11px]">
                    Active Subscription: {cloudStatus.azure.identifier}
                  </div>
                )}
                <div>
                  <label className="text-slate-400 block mb-1">Resource Group Name</label>
                  <input
                    type="text"
                    value={azureResourceGroup}
                    onChange={(e) => setAzureResourceGroup(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-400 block mb-1">Subscription ID</label>
                    <input
                      type="text"
                      placeholder="Subscription UUID"
                      value={azureSubId}
                      onChange={(e) => setAzureSubId(e.target.value)}
                      className="input-text text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Tenant ID</label>
                    <input
                      type="text"
                      placeholder="Tenant UUID"
                      value={azureTenantId}
                      onChange={(e) => setAzureTenantId(e.target.value)}
                      className="input-text text-xs font-mono"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-400 block mb-1">Client ID</label>
                    <input
                      type="text"
                      placeholder="App Client ID"
                      value={azureClientId}
                      onChange={(e) => setAzureClientId(e.target.value)}
                      className="input-text text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Client Secret</label>
                    <input
                      type="password"
                      placeholder="Client Secret"
                      value={azureClientSecret}
                      onChange={(e) => setAzureClientSecret(e.target.value)}
                      className="input-text text-xs font-mono"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleConnectInlineCredentials}
                  disabled={connectingCreds || !azureSubId || !azureTenantId || !azureClientId || !azureClientSecret}
                  className="btn-secondary w-full justify-center text-xs py-1.5"
                >
                  {connectingCreds ? 'Verifying Azure...' : 'Connect Azure Credentials'}
                </button>
              </div>
            )}

            {provider === 'gcp' && (
              <div className="mt-3 space-y-2.5 text-xs">
                {cloudStatus?.gcp?.connected && !cloudStatus?.is_demo && (
                  <div className="p-2 rounded bg-emerald-950/30 border border-emerald-500/20 text-emerald-300 font-mono text-[11px]">
                    Active Project: {cloudStatus.gcp.identifier}
                  </div>
                )}
                <div>
                  <label className="text-slate-400 block mb-1">GCP Project ID</label>
                  <input
                    type="text"
                    placeholder="my-gcp-project-id"
                    value={gcpProjectId}
                    onChange={(e) => setGcpProjectId(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Service Account JSON Key</label>
                  <textarea
                    rows={2}
                    placeholder='{"type": "service_account", ...}'
                    value={gcpCredsJson}
                    onChange={(e) => setGcpCredsJson(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleConnectInlineCredentials}
                  disabled={connectingCreds || !gcpProjectId || !gcpCredsJson}
                  className="btn-secondary w-full justify-center text-xs py-1.5"
                >
                  {connectingCreds ? 'Connecting GCP...' : 'Connect GCP Credentials'}
                </button>
              </div>
            )}
          </div>

          {/* Networking Card */}
          <div className="panel p-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <HardDrive className="h-4 w-4 text-brand-primary" />
                <span className="font-medium text-white text-sm">{networkTitle}</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={vpcEnabled}
                  onChange={(e) => setVpcEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-surface-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            {vpcEnabled && (
              <div className="mt-3 space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Network Name</label>
                  <input
                    type="text"
                    value={vpcName}
                    onChange={(e) => setVpcName(e.target.value)}
                    className="input-text text-xs"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">CIDR Block / Address Space</label>
                  <input
                    type="text"
                    value={cidrBlock}
                    onChange={(e) => setCidrBlock(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-slate-300">Outbound NAT Gateway</span>
                  <input
                    type="checkbox"
                    checked={enableNat}
                    onChange={(e) => setEnableNat(e.target.checked)}
                    className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Compute Card */}
          <div className="panel p-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-emerald-400" />
                <span className="font-medium text-white text-sm">{computeTitle}</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={ec2Enabled}
                  onChange={(e) => setEc2Enabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-surface-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            {ec2Enabled && (
              <div className="mt-3 space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Instance Name</label>
                  <input
                    type="text"
                    value={ec2Name}
                    onChange={(e) => setEc2Name(e.target.value)}
                    className="input-text text-xs"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-400 block mb-1">Machine / VM Size</label>
                    <select
                      value={instanceType}
                      onChange={(e) => setInstanceType(e.target.value)}
                      className="input-select text-xs"
                    >
                      {INSTANCE_OPTIONS[provider].map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Root Storage (GB)</label>
                    <input
                      type="number"
                      value={rootVolumeSize}
                      onChange={(e) => setRootVolumeSize(parseInt(e.target.value) || 30)}
                      className="input-text text-xs"
                      min={10}
                      max={500}
                    />
                  </div>
                </div>

                {provider === 'aws' && (
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-slate-300">Enforce IMDSv2 (Session Tokens)</span>
                    <input
                      type="checkbox"
                      checked={enableImdsV2}
                      onChange={(e) => setEnableImdsV2(e.target.checked)}
                      className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Storage Card */}
          <div className="panel p-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <HardDrive className="h-4 w-4 text-amber-400" />
                <span className="font-medium text-white text-sm">{storageTitle}</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={s3Enabled}
                  onChange={(e) => setS3Enabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-surface-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            {s3Enabled && (
              <div className="mt-3 space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Bucket / Account Prefix</label>
                  <input
                    type="text"
                    value={bucketPrefix}
                    onChange={(e) => setBucketPrefix(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-slate-300">Block Public Access</span>
                  <input
                    type="checkbox"
                    checked={blockPublicAccess}
                    onChange={(e) => setBlockPublicAccess(e.target.checked)}
                    className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">Object Versioning</span>
                  <input
                    type="checkbox"
                    checked={versioning}
                    onChange={(e) => setVersioning(e.target.checked)}
                    className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Database Card */}
          <div className="panel p-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-purple-400" />
                <span className="font-medium text-white text-sm">{dbTitle}</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={rdsEnabled}
                  onChange={(e) => setRdsEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-surface-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            {rdsEnabled && (
              <div className="mt-3 space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">DB Identifier</label>
                  <input
                    type="text"
                    value={dbIdentifier}
                    onChange={(e) => setDbIdentifier(e.target.value)}
                    className="input-text text-xs font-mono"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-400 block mb-1">Engine</label>
                    <select
                      value={dbEngine}
                      onChange={(e) => setDbEngine(e.target.value as any)}
                      className="input-select text-xs"
                    >
                      <option value="postgres">PostgreSQL 15</option>
                      <option value="mysql">MySQL 8.0</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Instance Tier</label>
                    <select
                      value={dbInstanceClass}
                      onChange={(e) => setDbInstanceClass(e.target.value)}
                      className="input-select text-xs"
                    >
                      <option value="db.t3.micro">Burstable Micro</option>
                      <option value="db.t3.small">Burstable Small</option>
                      <option value="db.m6g.large">General Purpose Large</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-slate-300">Multi-AZ High Availability</span>
                  <input
                    type="checkbox"
                    checked={multiAz}
                    onChange={(e) => setMultiAz(e.target.checked)}
                    className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">Deletion Protection</span>
                  <input
                    type="checkbox"
                    checked={deletionProtection}
                    onChange={(e) => setDeletionProtection(e.target.checked)}
                    className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Execution Viewport (Plan / HCL / Terminal) */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          <div className="panel p-2 flex items-center justify-between">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab('plan_summary')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${
                  activeTab === 'plan_summary'
                    ? 'bg-surface-muted text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Eye className="h-3.5 w-3.5" />
                Plan Review
                {planResult && (
                  <span className="badge-blue text-[10px] ml-1">
                    +{planResult.resources_to_add} ~{planResult.resources_to_change} -{planResult.resources_to_destroy}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('terraform_hcl')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${
                  activeTab === 'terraform_hcl'
                    ? 'bg-surface-muted text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <FileCode className="h-3.5 w-3.5" />
                Generated HCL
              </button>

              <button
                onClick={() => setActiveTab('live_terminal')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${
                  activeTab === 'live_terminal'
                    ? 'bg-surface-muted text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Terminal className="h-3.5 w-3.5" />
                Live Execution Logs
                {currentOperation && (
                  <span
                    className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-mono ${
                      currentOperation.status === 'running'
                        ? 'bg-blue-900/60 text-blue-300 animate-pulse'
                        : currentOperation.status === 'succeeded'
                        ? 'bg-emerald-900/60 text-emerald-300'
                        : 'bg-red-900/60 text-red-300'
                    }`}
                  >
                    {currentOperation.status}
                  </span>
                )}
              </button>
            </div>

            {planResult && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowApplyModal(true)}
                  className="px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1 transition-colors"
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  Apply Plan
                </button>
                <button
                  onClick={() => setShowDestroyModal(true)}
                  className="px-2.5 py-1.5 rounded-md bg-red-950/60 hover:bg-red-900 border border-red-500/30 text-red-300 text-xs font-medium flex items-center gap-1 transition-colors"
                  title="Safe Teardown"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Destroy
                </button>
              </div>
            )}
          </div>

          {activeTab === 'plan_summary' && (
            <div className="panel p-5 flex-1 min-h-[500px] flex flex-col justify-between">
              {planResult ? (
                <div className="space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                    <div>
                      <div className="text-xs text-slate-400">
                        Plan Workspace ({(planResult.provider || provider).toUpperCase()})
                      </div>
                      <div className="text-sm font-semibold text-white font-mono">{planResult.workspace_name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-slate-400">Monthly Est.</div>
                      <div className="text-base font-bold text-emerald-400 font-mono">
                        ${planResult.estimated_monthly_cost.toFixed(2)}/mo
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-center">
                      <div className="text-2xl font-bold text-emerald-400">+{planResult.resources_to_add}</div>
                      <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">To Create</div>
                    </div>
                    <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/20 text-center">
                      <div className="text-2xl font-bold text-amber-400">~{planResult.resources_to_change}</div>
                      <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">To Modify</div>
                    </div>
                    <div className="p-3 rounded-lg bg-red-950/20 border border-red-500/20 text-center">
                      <div className="text-2xl font-bold text-red-400">-{planResult.resources_to_destroy}</div>
                      <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">To Destroy</div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Planned Resource Creations
                    </h3>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {planResult.resource_changes.map((rc, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 rounded bg-surface-dark border border-surface-border text-xs font-mono"
                        >
                          <span className="text-slate-200">{rc.resource}</span>
                          <span className="text-emerald-400 font-medium">action: {rc.action}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Security &amp; Cost Guardrails
                    </h3>
                    <div className="space-y-1.5">
                      {planResult.risks_identified.length > 0 ? (
                        planResult.risks_identified.map((risk, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded bg-surface-muted border border-surface-border text-xs text-slate-300 flex items-start gap-2"
                          >
                            <Info className="h-4 w-4 text-brand-primary flex-shrink-0 mt-0.5" />
                            <span>{risk}</span>
                          </div>
                        ))
                      ) : (
                        <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                          <span>All security and cost guardrails passed. Ready to Apply.</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-3">
                  <Terminal className="h-10 w-10 text-slate-600" />
                  <div>
                    <div className="text-white font-medium">No Active Plan Generated</div>
                    <p className="text-xs text-slate-500 max-w-sm mt-1">
                      Select AWS, Azure, or GCP, configure your credentials &amp; resources on the left, and click
                      &quot;Validate &amp; Plan&quot;.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'terraform_hcl' && (
            <div className="panel p-4 flex-1 flex flex-col min-h-[500px]">
              <div className="flex items-center justify-between pb-2 border-b border-surface-border text-xs text-slate-400">
                <span>main.tf ({provider.toUpperCase()} Sanitized HCL Configuration)</span>
                <button
                  onClick={() => {
                    if (planResult?.generated_terraform_code) {
                      navigator.clipboard.writeText(planResult.generated_terraform_code);
                    }
                  }}
                  className="text-brand-primary hover:underline"
                >
                  Copy HCL
                </button>
              </div>
              <pre className="mt-3 flex-1 p-3 rounded bg-surface-dark text-slate-300 font-mono text-xs overflow-auto max-h-[460px] border border-surface-border leading-relaxed">
                {planResult?.generated_terraform_code || '# Configure resources and click "Validate & Plan" to review HCL'}
              </pre>
            </div>
          )}

          {activeTab === 'live_terminal' && (
            <div className="panel p-4 flex-1 flex flex-col min-h-[500px]">
              <div className="flex items-center justify-between pb-2 border-b border-surface-border text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="font-mono text-slate-300">
                    Operation: {currentOperation?.operation_id || 'Idle'}
                  </span>
                </div>
                <div className="text-slate-400 text-xs">
                  Secrets automatically redacted (AKIA*, ASIA*, passwords)
                </div>
              </div>

              <div className="mt-3 flex-1 p-4 rounded bg-black/90 text-slate-300 font-mono text-xs overflow-auto max-h-[460px] border border-surface-border leading-relaxed space-y-1">
                {currentOperation?.raw_logs ? (
                  currentOperation.raw_logs.split('\n').map((line, i) => (
                    <div
                      key={i}
                      className={
                        line.includes('ERROR') || line.includes('Error')
                          ? 'text-red-400'
                          : line.includes('complete') || line.includes('success') || line.includes('Created') || line.includes('Launched')
                          ? 'text-emerald-400'
                          : line.includes('Creating') || line.includes('Destroying')
                          ? 'text-amber-300'
                          : 'text-slate-300'
                      }
                    >
                      {line}
                    </div>
                  ))
                ) : (
                  <div className="text-slate-500 italic">No active background operations running. Logs will stream here.</div>
                )}
                <div ref={terminalEndRef} />
              </div>
            </div>
          )}

          <div className="panel p-4">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Recent Executions</span>
              <button onClick={loadRecentOperations} className="text-brand-primary hover:underline text-[11px] font-normal">
                Refresh
              </button>
            </h3>
            <div className="space-y-1.5 max-h-36 overflow-y-auto">
              {recentOperations.slice(0, 5).map((op) => (
                <div
                  key={op.operation_id}
                  onClick={() => {
                    setCurrentOperationId(op.operation_id);
                    setCurrentOperation(op);
                    setActiveTab('live_terminal');
                  }}
                  className="flex items-center justify-between p-2 rounded bg-surface-dark border border-surface-border text-xs hover:border-brand-primary/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-mono ${
                        op.action === 'apply' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30' : 'bg-red-950 text-red-300 border border-red-500/30'
                      }`}
                    >
                      {op.action}
                    </span>
                    <span className="font-mono text-slate-200">{op.operation_id}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-400">
                      {new Date(op.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span
                      className={`h-2 w-2 rounded-full ${
                        op.status === 'succeeded'
                          ? 'bg-emerald-400'
                          : op.status === 'running'
                          ? 'bg-blue-400 animate-pulse'
                          : 'bg-red-400'
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal: Apply */}
      {showApplyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="panel p-6 max-w-md w-full space-y-4 border-emerald-500/30">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
                <Play className="h-6 w-6 fill-current" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Confirm Infrastructure Apply</h3>
                <p className="text-xs text-slate-400">Isolated background execution ({provider.toUpperCase()})</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              This will provision resources for <span className="font-mono text-white">{planResult?.workspace_name}</span>.
              Type <strong className="text-white">CONFIRM</strong> below to verify authorization.
            </p>

            <div>
              <input
                type="text"
                placeholder="Type CONFIRM"
                value={applyConfirmPhrase}
                onChange={(e) => setApplyConfirmPhrase(e.target.value)}
                className="input-text text-center font-mono font-bold tracking-widest text-sm"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button onClick={() => setShowApplyModal(false)} className="btn-secondary text-xs">
                Cancel
              </button>
              <button
                onClick={handleApply}
                disabled={applyConfirmPhrase.trim().toUpperCase() !== 'CONFIRM' || isApplying}
                className="btn-primary bg-emerald-600 hover:bg-emerald-500 text-xs disabled:opacity-50"
              >
                {isApplying ? 'Initiating Apply...' : 'Authorize Apply'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal: Destroy */}
      {showDestroyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="panel p-6 max-w-md w-full space-y-4 border-red-500/40">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-full bg-red-950/60 border border-red-500/40 text-red-400">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Destructive Teardown Required</h3>
                <p className="text-xs text-red-400">High Risk: Resource Deletion</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              All managed resources in workspace <span className="font-mono text-white">{planResult?.workspace_name}</span>{' '}
              will be permanently terminated. To confirm irreversible teardown, type{' '}
              <strong className="text-red-400">DESTROY</strong>.
            </p>

            <div>
              <input
                type="text"
                placeholder="Type DESTROY"
                value={destroyConfirmPhrase}
                onChange={(e) => setDestroyConfirmPhrase(e.target.value)}
                className="input-text text-center font-mono font-bold tracking-widest text-sm border-red-500/50 focus:border-red-400"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button onClick={() => setShowDestroyModal(false)} className="btn-secondary text-xs">
                Cancel
              </button>
              <button
                onClick={handleDestroy}
                disabled={destroyConfirmPhrase.trim() !== 'DESTROY' || isDestroying}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold disabled:opacity-50 transition-colors"
              >
                {isDestroying ? 'Teardown Running...' : 'Execute Destroy'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
