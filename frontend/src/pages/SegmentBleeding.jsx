import { useState, useEffect } from 'react';
import { DATA_BASE } from '../config';
import AIRecommendationModal from '../components/AIRecommendationModal';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TABS = [
  { key: 'by_region', label: 'By Region' },
  { key: 'by_plan_tier', label: 'By Plan Tier' },
  { key: 'by_bundle', label: 'By Bundle' },
  { key: 'by_contract_type', label: 'By Contract Type' },
];

const formatCurrency = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${v}`;
};

export default function SegmentBleeding() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('by_region');
  const [modal, setModal] = useState({ open: false, type: '', value: '', stats: {} });

  useEffect(() => {
    fetch(`${DATA_BASE}/segment_bleeding.json`)
      .then(r => r.json())
      .then(setData);
  }, []);

  if (!data) {
    return <div className="flex items-center justify-center h-full"><div className="flex gap-2"><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} /></div></div>;
  }

  const tabData = data[activeTab] || [];
  const tabLabel = TABS.find(t => t.key === activeTab)?.label || '';
  const hotspotType = tabLabel.replace('By ', '');

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Segment Bleeding Analysis</h1>
        <p className="text-sm text-gray-500">Revenue at risk breakdown by customer segments</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-dark-700 border border-dark-600 rounded-xl p-1.5 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              ${activeTab === tab.key
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/20'
                : 'text-gray-400 hover:text-gray-300 hover:bg-dark-600'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">Revenue at Risk — {tabLabel}</h3>
          <span className="text-[10px] text-gray-500 bg-dark-600 px-2 py-1 rounded-full">Click bar for AI insight</span>
        </div>
        <ResponsiveContainer width="100%" height={Math.max(300, tabData.length * 42)}>
          <BarChart data={tabData} layout="vertical">
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#f97316" stopOpacity={0.9} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={formatCurrency} />
            <YAxis dataKey="name" type="category" tick={{ fill: '#d1d5db', fontSize: 12 }} width={120} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }}
              formatter={(value) => formatCurrency(value)}
            />
            <Bar
              dataKey="total_revenue_at_risk"
              fill="url(#barGradient)"
              radius={[0, 6, 6, 0]}
              cursor="pointer"
              onClick={(entry) => {
                setModal({
                  open: true,
                  type: hotspotType,
                  value: entry.name,
                  stats: {
                    customer_count: entry.customer_count,
                    avg_churn_prob: entry.avg_churn_prob,
                    avg_arpu: entry.avg_arpu,
                    total_revenue_at_risk: entry.total_revenue_at_risk,
                  },
                });
              }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Table */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Detailed Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-dark-600">
                <th className="text-left py-3 px-4">Segment</th>
                <th className="text-right py-3 px-4">Customers</th>
                <th className="text-right py-3 px-4">Avg ARPU</th>
                <th className="text-right py-3 px-4">Avg Churn Prob</th>
                <th className="text-right py-3 px-4">Revenue at Risk</th>
              </tr>
            </thead>
            <tbody>
              {tabData.map(row => (
                <tr key={row.name} className="border-b border-dark-600/50 hover:bg-dark-600/30 transition-colors">
                  <td className="py-3 px-4 text-gray-300 font-medium">{row.name}</td>
                  <td className="text-right py-3 px-4 text-white">{row.customer_count.toLocaleString()}</td>
                  <td className="text-right py-3 px-4 text-white">₹{row.avg_arpu.toLocaleString()}</td>
                  <td className="text-right py-3 px-4 text-red-400">{(row.avg_churn_prob * 100).toFixed(1)}%</td>
                  <td className="text-right py-3 px-4 text-orange-400 font-medium">{formatCurrency(row.total_revenue_at_risk)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <AIRecommendationModal
        isOpen={modal.open}
        onClose={() => setModal(m => ({ ...m, open: false }))}
        hotspotType={modal.type}
        hotspotValue={modal.value}
        stats={modal.stats}
      />
    </div>
  );
}
