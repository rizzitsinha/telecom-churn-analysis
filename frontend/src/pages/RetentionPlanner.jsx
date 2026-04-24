import { useState, useEffect, useMemo } from 'react';
import { DATA_BASE } from '../config';
import KPICard from '../components/KPICard';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

const formatCurrency = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${v}`;
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-dark-700 border border-dark-600 rounded-lg p-3 text-xs space-y-1 shadow-xl">
      <p className="text-white font-semibold">{d.customer_id}</p>
      <p className="text-gray-400">CLV: <span className="text-white">{formatCurrency(d.clv)}</span></p>
      <p className="text-gray-400">Churn Prob: <span className="text-red-400">{(d.churn_prob * 100).toFixed(1)}%</span></p>
      <p className="text-gray-400">ARPU: <span className="text-white">₹{d.monthly_arpu}</span></p>
      <p className="text-gray-400">Revenue at Risk: <span className="text-orange-400">₹{d.revenue_at_risk.toFixed(0)}</span></p>
    </div>
  );
};

export default function RetentionPlanner() {
  const [allCustomers, setAllCustomers] = useState([]);
  const [retentionCost, setRetentionCost] = useState(500);
  const [threshold, setThreshold] = useState(0.3);

  useEffect(() => {
    fetch(`${DATA_BASE}/retention.json`)
      .then(r => r.json())
      .then(d => setAllCustomers(d.customers));
  }, []);

  const eligible = useMemo(() => {
    return allCustomers.filter(c =>
      c.churn_prob >= threshold &&
      c.churn_prob * c.clv > retentionCost
    );
  }, [allCustomers, retentionCost, threshold]);

  const kpis = useMemo(() => {
    if (eligible.length === 0) return { count: 0, revSaved: 0, spend: 0, roi: 0 };
    const revSaved = eligible.reduce((s, c) => s + c.revenue_at_risk, 0);
    const spend = eligible.length * retentionCost;
    return {
      count: eligible.length,
      revSaved,
      spend,
      roi: spend > 0 ? ((revSaved - spend) / spend * 100) : 0,
    };
  }, [eligible, retentionCost]);

  const scatterData = useMemo(() => {
    if (eligible.length <= 5000) return eligible;
    const step = Math.ceil(eligible.length / 5000);
    return eligible.filter((_, i) => i % step === 0);
  }, [eligible]);

  const top50 = useMemo(() => {
    return [...eligible].sort((a, b) => b.revenue_at_risk - a.revenue_at_risk).slice(0, 50);
  }, [eligible]);

  const exportCSV = () => {
    if (eligible.length === 0) return;
    const cols = Object.keys(eligible[0]);
    const csv = [cols.join(','), ...eligible.map(r => cols.map(c => r[c]).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'retention_plan_export.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  if (allCustomers.length === 0) {
    return <div className="flex items-center justify-center h-full"><div className="flex gap-2"><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} /></div></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Retention Planner</h1>
          <p className="text-sm text-gray-500">Model retention campaigns with cost-benefit analysis</p>
        </div>
        <button onClick={exportCSV} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export
        </button>
      </div>

      {/* Sliders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark-700 border border-dark-600 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-300">Retention Offer Cost</label>
            <span className="text-sm font-bold text-blue-400">₹{retentionCost.toLocaleString()}</span>
          </div>
          <input
            type="range"
            min={100} max={5000} step={100}
            value={retentionCost}
            onChange={e => setRetentionCost(+e.target.value)}
            className="w-full h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <div className="flex justify-between text-[10px] text-gray-500 mt-1">
            <span>₹100</span><span>₹5,000</span>
          </div>
        </div>
        <div className="bg-dark-700 border border-dark-600 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-300">Min Churn Probability</label>
            <span className="text-sm font-bold text-red-400">{(threshold * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min={0.10} max={0.90} step={0.05}
            value={threshold}
            onChange={e => setThreshold(+e.target.value)}
            className="w-full h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer accent-red-500"
          />
          <div className="flex justify-between text-[10px] text-gray-500 mt-1">
            <span>10%</span><span>90%</span>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard title="Eligible Customers" value={kpis.count.toLocaleString()} color="blue" />
        <KPICard title="Revenue Saved" value={formatCurrency(kpis.revSaved)} color="green" />
        <KPICard title="Retention Spend" value={formatCurrency(kpis.spend)} color="orange" />
        <KPICard
          title="Net ROI"
          value={`${kpis.roi.toFixed(1)}%`}
          color={kpis.roi > 0 ? 'green' : 'red'}
        />
      </div>

      {/* Scatter */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">CLV vs Churn Probability</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="churn_prob" type="number" domain={[0, 1]} tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} label={{ value: 'Churn Probability', position: 'bottom', fill: '#6b7280', fontSize: 12 }} />
            <YAxis dataKey="clv" type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={formatCurrency} label={{ value: 'CLV', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Scatter data={scatterData}>
              {scatterData.map((d, i) => {
                const intensity = Math.min(d.revenue_at_risk / 500, 1);
                return <Cell key={i} fill={`rgba(239, 68, 68, ${0.3 + intensity * 0.7})`} r={3} />;
              })}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Top 50 Table */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Top 50 by Revenue at Risk</h3>
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-dark-700">
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-dark-600">
                <th className="text-left py-3 px-4">Customer ID</th>
                <th className="text-right py-3 px-4">ARPU</th>
                <th className="text-right py-3 px-4">CLV</th>
                <th className="text-right py-3 px-4">Churn Prob</th>
                <th className="text-right py-3 px-4">Revenue at Risk</th>
                <th className="text-right py-3 px-4">Tenure</th>
              </tr>
            </thead>
            <tbody>
              {top50.map(c => (
                <tr key={c.customer_id} className="border-b border-dark-600/50 hover:bg-dark-600/30 transition-colors">
                  <td className="py-2.5 px-4 text-blue-400 font-medium">{c.customer_id}</td>
                  <td className="text-right py-2.5 px-4 text-white">₹{c.monthly_arpu.toLocaleString()}</td>
                  <td className="text-right py-2.5 px-4 text-white">{formatCurrency(c.clv)}</td>
                  <td className="text-right py-2.5 px-4 text-red-400">{(c.churn_prob * 100).toFixed(1)}%</td>
                  <td className="text-right py-2.5 px-4 text-orange-400 font-medium">₹{c.revenue_at_risk.toFixed(0)}</td>
                  <td className="text-right py-2.5 px-4 text-gray-400">{c.tenure_months} mo</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
