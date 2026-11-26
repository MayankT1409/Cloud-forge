export type NavPage =
  | 'dashboard'
  | 'provisioning'
  | 'advisor'
  | 'pricing'
  | 'connect-aws'
  | 'inventory'
  | 'monitoring';

export type CloudProvider = 'aws' | 'azure' | 'gcp';

export interface CloudProviderConnection {
  provider: CloudProvider;
  connected: boolean;
  is_demo: boolean;
  region: string;
  identifier?: string;
  label?: string;
  verified_at?: string;
  message: string;
}

export interface AWSConnectionStatus {
  connected: boolean;
  is_demo: boolean;
  auth_method?: string;
  access_key_id_masked?: string;
  account_id?: string;
  role_arn?: string;
  region: string;
  arn?: string;
  user_id?: string;
  verified_at?: string;
  read_only_access: boolean;
  provisioning_access: boolean;
  missing_permissions: string[];
  message: string;
  azure?: CloudProviderConnection;
  gcp?: CloudProviderConnection;
}

export interface LeastPrivilegePolicyGuide {
  external_id: string;
  trust_policy: Record<string, any>;
  read_only_policy: Record<string, any>;
  provisioning_policy: Record<string, any>;
  setup_steps: string[];
}

export interface DashboardSummary {
  aws_connection: AWSConnectionStatus;
  is_demo: boolean;
  resource_counts: {
    total: number;
    managed: number;
    discovered: number;
    by_type: Record<string, number>;
  };
  recent_operations: OperationRecord[];
  audit_events: AuditEvent[];
  total_reports_generated: number;
  estimated_monthly_spend: number;
  data_notice: string;
}

export interface AuditEvent {
  timestamp: string;
  action: string;
  user: string;
  resource: string;
  status: string;
  details: Record<string, any>;
}

export interface RecommendedService {
  service_name: string;
  category: string;
  purpose: string;
  configuration_details: string;
  is_required: boolean;
  rationale: string;
}

export interface AlternativeOption {
  tier_name: string;
  description: string;
  monthly_cost_estimate: number;
  tradeoffs: string[];
  services_summary: string[];
}

export interface MultiCloudServiceMapping {
  tier_component: string;
  aws_service: string;
  azure_service: string;
  gcp_service: string;
  portability_guidance: string;
}

export interface RecommendationResponse {
  report_id: string;
  created_at: string;
  executive_summary: string;
  recommended_tier: string;
  recommended_services: RecommendedService[];
  compute_sizing: {
    instance_family: string;
    instance_count: number;
    vcpu_total: number;
    ram_total_gb: number;
    storage_gb_per_instance: number;
    storage_type: string;
  };
  database_sizing: {
    engine: string;
    multi_az: boolean;
    allocated_storage_gb: number;
    backup_retention_days: number;
    expected_connections: number;
  };
  networking_and_security: string[];
  disaster_recovery_plan: string[];
  monitoring_and_logging: string[];
  estimated_monthly_cost: number;
  estimated_annual_cost: number;
  cost_currency: string;
  alternatives: AlternativeOption[];
  multi_cloud_mapping: MultiCloudServiceMapping[];
  multi_cloud_comparison: Record<string, any>;
  risks_and_bottlenecks: string[];
  step_by_step_implementation_plan: string[];
  diagram_mermaid: string;
  assumptions: string[];
  is_demo: boolean;
}

export interface QuestionnaireState {
  app_type: string;
  runtime: string;
  environment: 'development' | 'staging' | 'production';
  daily_users: number;
  concurrent_users: number;
  traffic_pattern: 'steady' | 'spiky' | 'predictable_peaks';
  scaling_required: boolean;
  cpu_cores: number;
  ram_gb: number;
  storage_gb: number;
  bandwidth_gb_month: number;
  db_required: boolean;
  db_engine: string;
  db_size_gb: number;
  db_connections: number;
  file_storage_required: boolean;
  file_storage_gb: number;
  network_access: string;
  encryption_at_rest: boolean;
  encryption_in_transit: boolean;
  waf_required: boolean;
  multi_az: boolean;
  sla_target: string;
  backup_retention_days: number;
  monthly_budget_usd: number;
  preferred_region: string;
  existing_constraints: string;
}

export interface CostItem {
  category: string;
  resource_name: string;
  unit: string;
  unit_price_usd: number;
  quantity: number;
  monthly_cost_usd: number;
  assumptions: string;
}

export interface ProviderCostBreakdown {
  provider: 'aws' | 'azure' | 'gcp';
  provider_name: string;
  region_name: string;
  monthly_compute_usd: number;
  monthly_storage_usd: number;
  monthly_database_usd: number;
  monthly_networking_usd: number;
  total_monthly_usd: number;
  total_annual_usd: number;
  items: CostItem[];
}

export interface MultiCloudCostComparison {
  currency: string;
  pricing_date: string;
  data_source: string;
  providers: {
    aws: ProviderCostBreakdown;
    azure: ProviderCostBreakdown;
    gcp: ProviderCostBreakdown;
  };
  cheapest_provider: string;
  most_expensive_provider: string;
  monthly_arbitrage_savings_usd: number;
  annual_arbitrage_savings_usd: number;
  arbitrage_insights: string[];
}

export interface PricingComparison {
  tier: string;
  monthly_cost_usd: number;
  summary: string;
  key_differences: string[];
}

export interface CostEstimationResponse {
  region: string;
  currency: string;
  pricing_date: string;
  data_source: string;
  total_monthly_usd: number;
  total_annual_usd: number;
  items: CostItem[];
  comparisons: PricingComparison[];
  disclaimers: string[];
  is_live_aws_quote: boolean;
}

export interface ResourceItem {
  id: string;
  name: string;
  provider?: CloudProvider;
  resource_type: string;
  region: string;
  status: string;
  created_at?: string;
  managed_by: 'cloudforge' | 'aws_native' | 'azure_native' | 'gcp_native' | 'untracked';
  tags: Record<string, string>;
  metadata: Record<string, string>;
}

export interface InventoryResponse {
  account_id: string;
  region: string;
  is_demo: boolean;
  total_count: number;
  managed_count: number;
  discovered_count: number;
  permission_status: Record<string, boolean>;
  errors: string[];
  resources: ResourceItem[];
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface MetricSeries {
  metric_name: string;
  unit: string;
  resource_id: string;
  resource_name: string;
  data_points: MetricDataPoint[];
}

export interface MonitoringOverviewResponse {
  account_id: string;
  region: string;
  is_demo: boolean;
  time_range_hours: number;
  has_metrics_permission: boolean;
  notice: string;
  metrics: MetricSeries[];
}

export interface PlanResponse {
  plan_id: string;
  provider?: CloudProvider;
  workspace_name: string;
  is_valid: boolean;
  validation_output: string;
  plan_output: string;
  resources_to_add: number;
  resources_to_change: number;
  resources_to_destroy: number;
  resource_changes: Array<{ resource: string; action: string; type: string }>;
  estimated_monthly_cost: number;
  risks_identified: string[];
  has_destructive_actions: boolean;
  state_locked: boolean;
  generated_terraform_code: string;
}

export interface OperationRecord {
  operation_id: string;
  plan_id: string;
  action: 'plan' | 'apply' | 'destroy';
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  started_at: string;
  completed_at?: string;
  exit_code?: number;
  raw_logs: string;
  outputs: Record<string, string>;
  error_message?: string;
}
