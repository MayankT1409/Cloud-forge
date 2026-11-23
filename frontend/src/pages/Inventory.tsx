import React, { useState, useEffect } from 'react';
import {
  Boxes,
  Server,
  Database,
  HardDrive,
  Globe,
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Info,
  Shield,
  Tag
} from 'lucide-react';
import { api } from '../services/api';
import { InventoryResponse, ResourceItem } from '../types';

export const Inventory: React.FC = () => {
  const [data, setData] = useState<InventoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [managementFilter, setManagementFilter] = useState('all');
  const [selectedRegion, setSelectedRegion] = useState('us-east-1');

  useEffect(() => {
    loadInventory(selectedRegion);
  }, [selectedRegion]);

  const loadInventory = async (region: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.getInventory(region);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch inventory');
    } finally {
      setLoading(false);
    }
  };

  const getFilteredResources = (): ResourceItem[] => {
    if (!data?.resources) return [];

    return data.resources.filter((item) => {
      const matchesSearch =
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType =
        typeFilter === 'all' || item.resource_type.toLowerCase() === typeFilter.toLowerCase();

      const matchesManagement =
        managementFilter === 'all' || item.managed_by.toLowerCase() === managementFilter.toLowerCase();

      return matchesSearch && matchesType && matchesManagement;
    });
  };

  const filtered = getFilteredResources();

  const getIconForType = (type: string) => {
    switch (type.toLowerCase()) {
      case 'ec2':
        return <Server className="h-4 w-4 text-emerald-400" />;
      case 'rds':
        return <Database className="h-4 w-4 text-purple-400" />;
      case 's3':
        return <HardDrive className="h-4 w-4 text-amber-400" />;
      case 'vpc':
      case 'subnet':
        return <Globe className="h-4 w-4 text-blue-400" />;
      default:
        return <Boxes className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Boxes className="h-6 w-6 text-brand-primary" />
            Resource Inventory
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time discovered and CloudForge-managed infrastructure in target cloud account.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="input-select text-xs w-40"
          >
            <option value="us-east-1">us-east-1 (N. Virginia)</option>
            <option value="us-west-2">us-west-2 (Oregon)</option>
            <option value="eu-west-1">eu-west-1 (Ireland)</option>
            <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
          </select>

          <button
            onClick={() => loadInventory(selectedRegion)}
            disabled={loading}
            className="btn-secondary flex items-center gap-2 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Mode Notification */}
      {data && (
        <div className="p-3 rounded-lg bg-surface-muted border border-surface-border flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <Info className="h-4 w-4 text-brand-primary" />
            <span>
              Target Account: <strong className="text-white font-mono">{data.account_id}</strong> &bull; Region:{' '}
              <strong className="text-white font-mono">{data.region}</strong>
            </span>
          </div>
          <div>
            {data.is_demo ? (
              <span className="badge-warning">Demo Sandbox Mode</span>
            ) : (
              <span className="badge-green">Live STS Discovery</span>
            )}
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>{errorMsg}</div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="panel p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Resources</div>
            <div className="text-2xl font-bold text-white mt-1">{data?.total_count ?? 0}</div>
          </div>
          <div className="p-3 rounded-lg bg-brand-primary/10 border border-brand-primary/20 text-brand-primary">
            <Boxes className="h-6 w-6" />
          </div>
        </div>

        <div className="panel p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">CloudForge Managed</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{data?.managed_count ?? 0}</div>
          </div>
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Shield className="h-6 w-6" />
          </div>
        </div>

        <div className="panel p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Native Discovered</div>
            <div className="text-2xl font-bold text-blue-400 mt-1">{data?.discovered_count ?? 0}</div>
          </div>
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Globe className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="panel p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by resource name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-text text-xs pl-9 w-full"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="h-3.5 w-3.5" />
            <span>Type:</span>
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="input-select text-xs w-28"
          >
            <option value="all">All Types</option>
            <option value="ec2">EC2</option>
            <option value="rds">RDS</option>
            <option value="s3">S3</option>
            <option value="vpc">VPC</option>
          </select>

          <select
            value={managementFilter}
            onChange={(e) => setManagementFilter(e.target.value)}
            className="input-select text-xs w-36"
          >
            <option value="all">All Management</option>
            <option value="cloudforge">CloudForge</option>
            <option value="aws_native">AWS Native</option>
          </select>
        </div>
      </div>

      {/* Resources Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-dark border-b border-surface-border text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Resource Name / Identifier</th>
                <th className="py-3 px-4">Resource ID</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Management</th>
                <th className="py-3 px-4">Tags & Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border text-slate-300">
              {filtered.length > 0 ? (
                filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-muted/40 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getIconForType(item.resource_type)}
                        <span className="font-mono uppercase font-medium">{item.resource_type}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-medium text-white whitespace-nowrap">
                      {item.name}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                      {item.id}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
                          item.status === 'running' || item.status === 'available'
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {item.managed_by === 'cloudforge' ? (
                        <span className="badge-blue font-medium">CloudForge Managed</span>
                      ) : (
                        <span className="badge-gray font-medium">Discovered Native</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {item.tags &&
                          Object.entries(item.tags).map(([k, v]) => (
                            <span
                              key={k}
                              className="px-1.5 py-0.5 rounded bg-surface-dark border border-surface-border text-[10px] font-mono text-slate-400"
                            >
                              {k}: {v}
                            </span>
                          ))}
                        {item.metadata &&
                          Object.entries(item.metadata).map(([k, v]) => (
                            <span
                              key={k}
                              className="px-1.5 py-0.5 rounded bg-brand-primary/10 border border-brand-primary/20 text-[10px] font-mono text-brand-primary"
                            >
                              {k}: {v}
                            </span>
                          ))}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No resources matched the active filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
