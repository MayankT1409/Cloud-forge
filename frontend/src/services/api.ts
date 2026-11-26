import {
  DashboardSummary,
  AWSConnectionStatus,
  CloudProviderConnection,
  LeastPrivilegePolicyGuide,
  RecommendationResponse,
  QuestionnaireState,
  CostEstimationResponse,
  MultiCloudCostComparison,
  InventoryResponse,
  MonitoringOverviewResponse,
  PlanResponse,
  OperationRecord
} from '../types';

const BASE_URL = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorDetail = `Request failed (${res.status})`;
    try {
      const errObj = await res.json();
      if (errObj && errObj.detail) {
        errorDetail = errObj.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJson<DashboardSummary>('/dashboard/summary'),

  // AWS & Multi-Cloud Connection
  getAWSStatus: () => fetchJson<AWSConnectionStatus>('/aws/status'),
  connectAWS: (access_key_id: string, secret_access_key: string, region: string, session_token?: string) =>
    fetchJson<AWSConnectionStatus>('/aws/connect', {
      method: 'POST',
      body: JSON.stringify({
        access_key_id,
        secret_access_key,
        region,
        session_token: session_token || undefined,
      }),
    }),
  disconnectAWS: () =>
    fetchJson<AWSConnectionStatus>('/aws/disconnect', { method: 'POST' }),
  connectAzure: (subscription_id: string, tenant_id: string, client_id: string, client_secret: string, region: string) =>
    fetchJson<CloudProviderConnection>('/aws/azure/connect', {
      method: 'POST',
      body: JSON.stringify({ subscription_id, tenant_id, client_id, client_secret, region }),
    }),
  disconnectAzure: () =>
    fetchJson<CloudProviderConnection>('/aws/azure/disconnect', { method: 'POST' }),
  connectGCP: (project_id: string, credentials_json: string, region: string, service_account_email?: string) =>
    fetchJson<CloudProviderConnection>('/aws/gcp/connect', {
      method: 'POST',
      body: JSON.stringify({
        project_id,
        credentials_json,
        region,
        service_account_email: service_account_email || undefined,
      }),
    }),
  disconnectGCP: () =>
    fetchJson<CloudProviderConnection>('/aws/gcp/disconnect', { method: 'POST' }),
  toggleDemoMode: (enabled: boolean) =>
    fetchJson<AWSConnectionStatus>('/aws/demo-mode', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
  getLeastPrivilegePolicy: () =>
    fetchJson<LeastPrivilegePolicyGuide>('/aws/policy-guide'),

  // Advisor
  submitQuestionnaire: (data: QuestionnaireState) =>
    fetchJson<RecommendationResponse>('/advisor/recommend', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  listReports: () => fetchJson<Array<{ report_id: string; created_at: string; recommended_tier: string; estimated_monthly_cost: number }>>('/reports'),
  getReportPdfUrl: (report_id: string) => `${BASE_URL}/reports/${report_id}/pdf`,

  // Pricing & Multi-Cloud Cost Arbitrage
  calculateCosts: (data: Record<string, any>) =>
    fetchJson<CostEstimationResponse>('/pricing/estimate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  calculateMultiCloudCosts: (data: Record<string, any>) =>
    fetchJson<MultiCloudCostComparison>('/pricing/multi-cloud-estimate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Provisioning
  generatePlan: (draft: Record<string, any>) =>
    fetchJson<PlanResponse>('/provisioning/plan', {
      method: 'POST',
      body: JSON.stringify(draft),
    }),
  executeApply: (plan_id: string, confirmation_phrase: string) =>
    fetchJson<{ operation_id: string; status: string; message: string }>('/provisioning/apply', {
      method: 'POST',
      body: JSON.stringify({ plan_id, confirmation_phrase }),
    }),
  executeDestroy: (plan_id: string, confirmation_phrase: string) =>
    fetchJson<{ operation_id: string; status: string; message: string }>('/provisioning/destroy', {
      method: 'POST',
      body: JSON.stringify({ plan_id, confirmation_phrase }),
    }),
  getOperationStatus: (operation_id: string) =>
    fetchJson<OperationRecord>(`/provisioning/operations/${operation_id}`),
  listOperations: () => fetchJson<OperationRecord[]>('/provisioning/operations'),

  // Inventory
  getInventory: (region?: string) =>
    fetchJson<InventoryResponse>(`/inventory/resources${region ? `?region=${encodeURIComponent(region)}` : ''}`),

  // Monitoring
  getMonitoring: (hours: number = 6) =>
    fetchJson<MonitoringOverviewResponse>(`/monitoring/overview?hours=${hours}`),
};
