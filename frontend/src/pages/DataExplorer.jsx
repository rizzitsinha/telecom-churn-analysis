import { useState, useEffect, useMemo } from 'react';
import { DATA_BASE } from '../config';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const FILTER_KEYS = ['region', 'plan_tier', 'contract_type', 'bundle_name'];

function getColor(val) {
  if (val > 0.5) return `rgb(239, 68, 68)`;
  if (val > 0) return `rgb(${Math.round(55 + val * 368)}, ${Math.round(65 + (1 - val) * 186)}, ${Math.round(81 + (1 - val) * 174)})`;
  if (val < -0.5) return `rgb(59, 130, 246)`;
  if (val < 0) return `rgb(${Math.round(55 + (1 + val) * 4)}, ${Math.round(65 + (1 + val) * 65)}, ${Math.round(81 + (1 + val) * 165)})`;
  return '#374151';
}

export default function DataExplorer() {
  const [data, setData] = useState(null);
  const [filters, setFilters] = useState({});
  const [expandedFilter, setExpandedFilter] = useState(null);

  useEffect(() => {
    fetch(`${DATA_BASE}/explorer.json`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        const f = {};
        FILTER_KEYS.forEach(k => {
          const unique = [...new Set(d.rows.map(r => r[k]))].sort();
          f[k] = { options: unique, selected: new Set(unique) };
        });
        setFilters(f);
      });
  }, []);

  const filteredRows = useMemo(() => {
    if (!data) return [];
    return data.rows.filter(row =>
      FILTER_KEYS.every(k => filters[k]?.selected?.has(row[k]))
    );
  }, [data, filters]);

  const filteredStats = useMemo(() => {
    if (filteredRows.length === 0) return {};
    const churned = filteredRows.filter(r => r.churn_type !== 'Stayed').length;
    return {
      total: filteredRows.length,
      churnRate: ((churned / filteredRows.length) * 100).toFixed(1),
      avgArpu: (filteredRows.reduce((s, r) => s + r.monthly_arpu, 0) / filteredRows.length).toFixed(0),
      avgNetwork: (filteredRows.reduce((s, r) => s + r.avg_network_score, 0) / filteredRows.length).toFixed(1),
    };
  }, [filteredRows]);

  const toggleFilter = (key, value) => {
    setFilters(prev => {
      const updated = { ...prev };
      const sel = new Set(updated[key].selected);
      sel.has(value) ? sel.delete(value) : sel.add(value);
      updated[key] = { ...updated[key], selected: sel };
      return updated;
    });
  };

  const selectAll = (key) => {
    setFilters(prev => {
      const updated = { ...prev };
      updated[key] = { ...updated[key], selected: new Set(updated[key].options) };
      return updated;
    });
  };

  const selectNone = (key) => {
    setFilters(prev => {
      const updated = { ...prev };
      updated[key] = { ...updated[key], selected: new Set() };
      return updated;
    });
  };

  const exportCSV = () => {
    if (filteredRows.length === 0) return;
    const cols = Object.keys(filteredRows[0]);
    const csv = [cols.join(','), ...filteredRows.map(r => cols.map(c => r[c]).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'churn_data_export.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  if (!data) {
    return <div className="flex items-center justify-center h-full"><div className="flex gap-2"><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} /></div></div>;
  }

  const contractData = Object.entries(data.churn_rate_by_contract_type).map(([k, v]) => ({
    name: k, rate: Math.round(v * 1000) / 10,
  }));

  const { features, values } = data.correlation_matrix;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Data Explorer</h1>
          <p className="text-sm text-gray-500">Filter and explore customer data interactively</p>
        </div>
        <button onClick={exportCSV} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export CSV
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Filters</h3>
          {FILTER_KEYS.map(key => (
            <div key={key} className="bg-dark-700 border border-dark-600 rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedFilter(expandedFilter === key ? null : key)}
                className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-300 hover:bg-dark-600 transition-colors"
              >
                <span>{key.replace(/_/g, ' ')}</span>
                <span className="text-xs text-gray-500">{filters[key]?.selected?.size}/{filters[key]?.options?.length}</span>
              </button>
              {expandedFilter === key && (
                <div className="px-4 pb-3 space-y-1 max-h-48 overflow-y-auto border-t border-dark-600 pt-2">
                  <div className="flex gap-2 mb-2">
                    <button onClick={() => selectAll(key)} className="text-[10px] text-blue-400 hover:text-blue-300">All</button>
                    <button onClick={() => selectNone(key)} className="text-[10px] text-gray-500 hover:text-gray-400">None</button>
                  </div>
                  {filters[key]?.options?.map(opt => (
                    <label key={opt} className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer hover:text-gray-300">
                      <input
                        type="checkbox"
                        checked={filters[key].selected.has(opt)}
                        onChange={() => toggleFilter(key, opt)}
                        className="w-3.5 h-3.5 rounded border-dark-500 bg-dark-600 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Summary stats */}
          <div className="bg-dark-700 border border-dark-600 rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Filtered Summary</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Rows</span><span className="text-white font-medium">{filteredStats.total?.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Churn Rate</span><span className="text-red-400 font-medium">{filteredStats.churnRate}%</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Avg ARPU</span><span className="text-white font-medium">₹{filteredStats.avgArpu}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Avg Network</span><span className="text-white font-medium">{filteredStats.avgNetwork}/10</span></div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="lg:col-span-3 space-y-6">
          {/* Churn by contract type */}
          <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-300">Churn Rate by Contract Type</h3>
              <span className="text-[10px] text-gray-500 bg-dark-600 px-2 py-1 rounded-full">Pre-computed</span>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={contractData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `${v}%`} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }} formatter={v => `${v}%`} />
                <Bar dataKey="rate" fill="#f97316" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Correlation heatmap */}
          <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Feature Correlation Matrix</h3>
            <div className="overflow-x-auto">
              <div className="inline-grid gap-[2px]" style={{ gridTemplateColumns: `80px repeat(${features.length}, 1fr)` }}>
                {/* Header */}
                <div />
                {features.map(f => (
                  <div key={f} className="text-[9px] text-gray-500 text-center px-1 py-2 truncate" title={f}>
                    {f.replace(/_/g, ' ').substring(0, 10)}
                  </div>
                ))}
                {/* Rows */}
                {features.map((f, i) => (
                  <>
                    <div key={`label-${i}`} className="text-[9px] text-gray-500 flex items-center pr-2 truncate" title={f}>
                      {f.replace(/_/g, ' ').substring(0, 12)}
                    </div>
                    {values[i].map((v, j) => (
                      <div
                        key={`${i}-${j}`}
                        className="w-full aspect-square flex items-center justify-center rounded-sm text-[8px] font-medium min-w-[36px]"
                        style={{ backgroundColor: getColor(v), color: Math.abs(v) > 0.3 ? '#fff' : '#9ca3af' }}
                        title={`${features[i]} × ${features[j]}: ${v}`}
                      >
                        {v.toFixed(2)}
                      </div>
                    ))}
                  </>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
