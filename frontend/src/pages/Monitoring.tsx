import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  HardDrive,
  Database,
  ArrowDownUp,
  Clock,
  RefreshCw,
  AlertTriangle,
  Info,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';
import { MonitoringOverviewResponse, MetricSeries } from '../types';

export const Monitoring: React.FC = () => {
  const [data, setData] = useState<MonitoringOverviewResponse | null>(null);
  const [hours, setHours] = useState(6);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics(hours);
  }, [hours]);

  const loadMetrics = async (timeRange: number) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.getMonitoring(timeRange);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch monitoring metrics');
    } finally {
      setLoading(false);
    }
  };

  const renderSvgChart = (series: MetricSeries, color: string) => {
    const points = series.data_points;
    if (!points || points.length === 0) {
      return (
        <div className="h-32 flex items-center justify-center text-slate-500 text-xs italic">
          No metric data points available
        </div>
      );
    }

    const values = points.map((p) => p.value);
    const maxVal = Math.max(...values, 1);
    const minVal = Math.min(...values, 0);
    const range = maxVal - minVal || 1;

    const width = 360;
    const height = 90;
    const padding = 10;

    const coordinates = points.map((p, idx) => {
      const x = padding + (idx / (points.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((p.value - minVal) / range) * (height - 2 * padding);
      return `${x},${y}`;
    });

    const pathD = `M ${coordinates.join(' L ')}`;
    const areaD = `${pathD} L ${width - padding},${height} L ${padding},${height} Z`;

    const latestVal = values[values.length - 1];

    return (
      <div className="space-y-2">
        <div className="flex justify-between items-baseline">
          <span className="text-xs text-slate-400 font-mono">Current:</span>
          <span className="text-lg font-bold text-white font-mono">
            {latestVal.toFixed(1)} <span className="text-xs font-normal text-slate-400">{series.unit}</span>
          </span>
        </div>

        <div className="relative bg-surface-dark rounded border border-surface-border p-2 overflow-hidden">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-24 overflow-visible">
            {/* Horizontal guide lines */}
            <line
              x1={padding}
              y1={padding}
              x2={width - padding}
              y2={padding}
              stroke="#334155"
              strokeDasharray="2,2"
              strokeWidth="0.5"
            />
            <line
              x1={padding}
              y1={height / 2}
              x2={width - padding}
              y2={height / 2}
              stroke="#334155"
              strokeDasharray="2,2"
              strokeWidth="0.5"
            />
            <line
              x1={padding}
              y1={height - padding}
              x2={width - padding}
              y2={height - padding}
              stroke="#334155"
              strokeWidth="0.8"
            />

            {/* Gradient area */}
            <defs>
              <linearGradient id={`grad-${series.metric_name}`} x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={color} stopOpacity="0.35" />
                <stop offset="100%" stopColor={color} stopOpacity="0.0" />
              </linearGradient>
            </defs>

            <path d={areaD} fill={`url(#grad-${series.metric_name})`} />
            <path d={pathD} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />

            {/* Latest point highlight */}
            {points.length > 0 && (
              <circle
                cx={coordinates[coordinates.length - 1].split(',')[0]}
                cy={coordinates[coordinates.length - 1].split(',')[1]}
                r="3.5"
                fill={color}
                className="animate-pulse"
              />
            )}
          </svg>
        </div>

        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>{new Date(points[0].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          <span>{new Date(points[points.length - 1].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-brand-primary" />
            CloudWatch Observability & Telemetry
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real AWS CloudWatch metrics for provisioned workloads via least-privilege STS role.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-surface-dark border border-surface-border rounded-lg p-1 text-xs">
            <button
              onClick={() => setHours(1)}
              className={`px-2.5 py-1 rounded transition-colors ${
                hours === 1 ? 'bg-brand-primary text-white font-medium' : 'text-slate-400 hover:text-white'
              }`}
            >
              1h
            </button>
            <button
              onClick={() => setHours(6)}
              className={`px-2.5 py-1 rounded transition-colors ${
                hours === 6 ? 'bg-brand-primary text-white font-medium' : 'text-slate-400 hover:text-white'
              }`}
            >
              6h
            </button>
            <button
              onClick={() => setHours(24)}
              className={`px-2.5 py-1 rounded transition-colors ${
                hours === 24 ? 'bg-brand-primary text-white font-medium' : 'text-slate-400 hover:text-white'
              }`}
            >
              24h
            </button>
          </div>

          <button
            onClick={() => loadMetrics(hours)}
            disabled={loading}
            className="btn-secondary flex items-center gap-2 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Notice / Data Source Banner */}
      {data && (
        <div className="p-3.5 rounded-lg bg-surface-muted border border-surface-border flex items-start sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <Info className="h-4 w-4 text-brand-primary flex-shrink-0" />
            <span>{data.notice}</span>
          </div>
          <div>
            {data.is_demo ? (
              <span className="badge-warning">Simulated Telemetry</span>
            ) : (
              <span className="badge-green">Live CloudWatch Telemetry</span>
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

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {data?.metrics && data.metrics.length > 0 ? (
          data.metrics.map((series, idx) => {
            const colors = ['#38bdf8', '#34d399', '#a78bfa', '#fbbf24', '#f87171'];
            const color = colors[idx % colors.length];

            return (
              <div key={idx} className="panel p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-surface-border pb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-white font-mono">{series.metric_name}</h3>
                    <div className="text-[11px] text-slate-400 truncate max-w-[200px]">
                      {series.resource_name} ({series.resource_id})
                    </div>
                  </div>
                  <div className="p-2 rounded bg-surface-dark border border-surface-border">
                    {series.metric_name.toLowerCase().includes('cpu') ? (
                      <Cpu className="h-4 w-4 text-brand-primary" />
                    ) : series.metric_name.toLowerCase().includes('db') ? (
                      <Database className="h-4 w-4 text-purple-400" />
                    ) : (
                      <ArrowDownUp className="h-4 w-4 text-emerald-400" />
                    )}
                  </div>
                </div>

                {renderSvgChart(series, color)}
              </div>
            );
          })
        ) : (
          <div className="col-span-full panel p-12 text-center text-slate-400 space-y-2">
            <Activity className="h-10 w-10 text-slate-600 mx-auto" />
            <div className="text-white font-medium">No Active Metric Streams</div>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Provision resources or toggle the Demo Sandbox mode in the AWS Connection settings to inspect telemetry charts.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
