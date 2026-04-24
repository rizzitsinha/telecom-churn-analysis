import { useState, useEffect } from 'react';
import { DATA_BASE } from '../config';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts';

const QUADRANT_COLORS = {
  High_Risk_High_Value: '#ef4444',
  High_Risk_Low_Value: '#f97316',
  Low_Risk_High_Value: '#22c55e',
  Low_Risk_Low_Value: '#6b7280',
};

const QUADRANT_LABELS = {
  High_Risk_High_Value: '🔴 High Risk, High Value',
  High_Risk_Low_Value: '🟠 High Risk, Low Value',
  Low_Risk_High_Value: '🟢 Low Risk, High Value',
  Low_Risk_Low_Value: '⚪ Low Risk, Low Value',
};

const formatCurrency = (v) => {
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
      <p className="text-gray-400">Type: <span className="text-white">{d.predicted_churn_type}</span></p>
      <p className="text-gray-400">ARPU: <span className="text-white">₹{d.monthly_arpu}</span></p>
      <p className="text-gray-400">CLV: <span className="text-white">{formatCurrency(d.clv)}</span></p>
      <p className="text-gray-400">Tenure: <span className="text-white">{d.tenure_months} mo</span></p>
      <p className="text-gray-400">Churn Prob: <span className="text-red-400">{(d.churn_prob * 100).toFixed(1)}%</span></p>
    </div>
  );
};

export default function Segmentation() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${DATA_BASE}/segmentation.json`)
      .then(r => r.json())
      .then(setData);
  }, []);

  if (!data) {
    return <div className="flex items-center justify-center h-full"><div className="flex gap-2"><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} /></div></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Customer Segmentation</h1>
        <p className="text-sm text-gray-500">Churn probability vs. ARPU with quadrant analysis (20K sample)</p>
      </div>

      {/* Scatter Chart */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <div className="flex items-center gap-4 mb-4 flex-wrap">
          {Object.entries(QUADRANT_LABELS).map(([k, label]) => (
            <div key={k} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: QUADRANT_COLORS[k] }} />
              <span className="text-xs text-gray-400">{label}</span>
            </div>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={480}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="churn_prob"
              type="number"
              name="Churn Probability"
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              label={{ value: 'Churn Probability', position: 'bottom', fill: '#6b7280', fontSize: 12 }}
              domain={[0, 1]}
              tickFormatter={v => `${(v * 100).toFixed(0)}%`}
            />
            <YAxis
              dataKey="monthly_arpu"
              type="number"
              name="Monthly ARPU"
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              label={{ value: 'Monthly ARPU (₹)', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={data.medians.churn_prob} stroke="#4b5563" strokeDasharray="5 5" label={{ value: 'Median Risk', fill: '#6b7280', fontSize: 10 }} />
            <ReferenceLine y={data.medians.monthly_arpu} stroke="#4b5563" strokeDasharray="5 5" label={{ value: 'Median ARPU', fill: '#6b7280', fontSize: 10 }} />
            <Scatter data={data.scatter_points} shape="circle">
              {data.scatter_points.map((point, i) => (
                <Cell key={i} fill={QUADRANT_COLORS[point.quadrant]} fillOpacity={0.5} r={2.5} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Quadrant Summary Table */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Quadrant Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-dark-600">
                <th className="text-left py-3 px-4">Quadrant</th>
                <th className="text-right py-3 px-4">Customers</th>
                <th className="text-right py-3 px-4">Avg ARPU</th>
                <th className="text-right py-3 px-4">Avg CLV</th>
                <th className="text-right py-3 px-4">Avg Churn Prob</th>
                <th className="text-right py-3 px-4">Revenue at Risk</th>
              </tr>
            </thead>
            <tbody>
              {data.quadrant_summary.map(q => (
                <tr key={q.quadrant} className="border-b border-dark-600/50 hover:bg-dark-600/30 transition-colors">
                  <td className="py-3 px-4 flex items-center gap-2">
                    <div className="w-1 h-8 rounded-full" style={{ backgroundColor: QUADRANT_COLORS[q.quadrant] }} />
                    <span className="text-gray-300 font-medium">{q.quadrant.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="text-right py-3 px-4 text-white">{q.count.toLocaleString()}</td>
                  <td className="text-right py-3 px-4 text-white">₹{q.avg_arpu.toLocaleString()}</td>
                  <td className="text-right py-3 px-4 text-white">{formatCurrency(q.avg_clv)}</td>
                  <td className="text-right py-3 px-4 text-red-400">{(q.avg_churn_prob * 100).toFixed(1)}%</td>
                  <td className="text-right py-3 px-4 text-orange-400">{formatCurrency(q.total_revenue_at_risk)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
