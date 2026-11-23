import {
  DashboardSummary,
  AWSConnectionStatus,
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

  // AWS Connection
  getAWSStatus: () => fetchJson<AWSConnectionStatus>('/aws/status'),
  connectAWS: (role_arn: string, external_id: string, account_id: string, region: string) =>
    fetchJson<AWSConnectionStatus>('/aws/connect', {
      method: 'POST',
      body: JSON.stringify({ role_arn, external_id, account_id, region }),
    }),
  disconnectAWS: () =>
    fetchJson<AWSConnectionStatus>('/aws/disconnect', { method: 'POST' }),
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
