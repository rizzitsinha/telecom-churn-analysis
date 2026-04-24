import { useState, useEffect } from 'react';
import { DATA_BASE } from '../config';
import AIRecommendationModal from '../components/AIRecommendationModal';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea, Cell,
} from 'recharts';

const formatCurrency = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${v}`;
};

const RISK_STYLES = {
  High: { border: 'border-red-500', badge: 'bg-red-500/15 text-red-400', emoji: '🔴' },
  Moderate: { border: 'border-yellow-500', badge: 'bg-yellow-500/15 text-yellow-400', emoji: '🟡' },
  Low: { border: 'border-green-500', badge: 'bg-green-500/15 text-green-400', emoji: '🟢' },
};

const FESTIVAL_COLORS = {
  "Diwali Peak": '#ef4444',
  "Pre-Diwali": '#f97316',
  "End of FY": '#f59e0b',
  "New Year": '#f59e0b',
  "Post-IPL": '#f59e0b',
};

export default function SeasonalAnalysis() {
  const [data, setData] = useState(null);
  const [modal, setModal] = useState({ open: false, type: '', value: '', stats: {} });

  useEffect(() => {
    fetch(`${DATA_BASE}/seasonal.json`)
      .then(r => r.json())
      .then(setData);
  }, []);

  if (!data) {
    return <div className="flex items-center justify-center h-full"><div className="flex gap-2"><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} /></div></div>;
  }

  const highRiskMonths = data.monthly.filter(m => m.is_high_risk);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Seasonal Analysis</h1>
        <p className="text-sm text-gray-500">Churn patterns aligned with Indian festivals and seasonal trends</p>
      </div>

      {/* Section 1: Monthly Churn Rate Line Chart */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Monthly Churn Rate Trend</h3>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data.monthly} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="month_name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }}
              formatter={(v) => `${(v * 100).toFixed(2)}%`}
            />
            {/* Red band for Oct-Nov (Diwali season) */}
            <ReferenceArea x1="October" x2="November" fill="#ef4444" fillOpacity={0.08} />
            {/* Yellow band for March (FY end) */}
            <ReferenceArea x1="March" x2="March" fill="#f59e0b" fillOpacity={0.08} />
            {/* Reference lines for high-risk months */}
            {highRiskMonths.map(m => (
              <ReferenceLine
                key={m.month}
                x={m.month_name}
                stroke={FESTIVAL_COLORS[m.label] || '#f97316'}
                strokeDasharray="4 4"
                strokeOpacity={0.6}
                label={{ value: m.label, position: 'top', fill: '#9ca3af', fontSize: 9 }}
              />
            ))}
            <Line
              type="monotone"
              dataKey="avg_churn_rate"
              stroke="#3b82f6"
              strokeWidth={2.5}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6, fill: '#60a5fa' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Section 2: Monthly Revenue at Risk Bar Chart */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">Monthly Revenue at Risk</h3>
          <span className="text-[10px] text-gray-500 bg-dark-600 px-2 py-1 rounded-full">Click bar for AI insight</span>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data.monthly}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="month_name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={formatCurrency} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }}
              formatter={(v) => formatCurrency(v)}
            />
            <Bar
              dataKey="total_revenue_at_risk"
              radius={[6, 6, 0, 0]}
              cursor="pointer"
              onClick={(entry) => {
                setModal({
                  open: true,
                  type: 'Month',
                  value: entry.month_name,
                  stats: {
                    avg_churn_rate: entry.avg_churn_rate,
                    total_revenue_at_risk: entry.total_revenue_at_risk,
                    label: entry.label || 'Regular month',
                  },
                });
              }}
            >
              {data.monthly.map((m, i) => (
                <Cell key={i} fill={m.is_high_risk ? '#ef4444' : '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Section 3: Quarterly Summary Cards */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Quarterly Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {data.quarterly.map(q => {
            const style = RISK_STYLES[q.risk_level] || RISK_STYLES.Low;
            return (
              <button
                key={q.quarter}
                className={`bg-dark-700 border-2 ${style.border}/30 rounded-xl p-5 text-left hover:bg-dark-600/50 transition-all duration-200 cursor-pointer group`}
                onClick={() => setModal({
                  open: true,
                  type: 'Quarter',
                  value: q.quarter,
                  stats: {
                    months: q.months,
                    avg_churn_rate: q.avg_churn_rate,
                    total_revenue_at_risk: q.total_revenue_at_risk,
                    risk_level: q.risk_level,
                  },
                })}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-lg font-bold text-white">{q.quarter}</span>
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold ${style.badge}`}>
                    {style.emoji} {q.risk_level}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-3">{q.months}</p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Churn Rate</span>
                    <span className="text-white font-medium">{(q.avg_churn_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Revenue at Risk</span>
                    <span className="text-orange-400 font-medium">{formatCurrency(q.total_revenue_at_risk)}</span>
                  </div>
                </div>
                <p className="text-[10px] text-gray-600 mt-3 group-hover:text-gray-500 transition-colors">
                  Click for AI recommendations →
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Section 4: Festival Context Panel */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Festival & Event Context</h3>
        <div className="space-y-3">
          {Object.entries(data.festival_context).map(([month, context]) => {
            const festName = context.split(':')[0];
            const isDiwali = month === 'Nov' || month === 'Oct';
            return (
              <div
                key={month}
                className={`bg-dark-700 border border-dark-600 rounded-xl p-5 border-l-4 ${
                  isDiwali ? 'border-l-red-500' : 'border-l-orange-500'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-sm font-semibold text-white">{festName}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-dark-600 text-gray-400">{month}</span>
                </div>
                <p className="text-sm text-gray-400 leading-relaxed">{context.split(': ').slice(1).join(': ')}</p>
              </div>
            );
          })}
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
