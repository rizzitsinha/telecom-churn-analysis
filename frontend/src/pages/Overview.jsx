import { useState, useEffect } from 'react';
import { DATA_BASE } from '../config';
import KPICard from '../components/KPICard';
import AIRecommendationModal from '../components/AIRecommendationModal';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const COLORS = ['#22c55e', '#f97316', '#ef4444'];

const formatCurrency = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${v}`;
};

export default function Overview() {
  const [data, setData] = useState(null);
  const [modal, setModal] = useState({ open: false, type: '', value: '', stats: {} });

  useEffect(() => {
    fetch(`${DATA_BASE}/overview.json`)
      .then(r => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex gap-2">
          <span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" />
          <span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} />
          <span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} />
        </div>
      </div>
    );
  }

  const pieData = Object.entries(data.churn_type_distribution).map(([name, value]) => ({
    name, value: Math.round(value * 100 * 10) / 10,
  }));

  const histogramData = data.arpu_histogram.bins.slice(0, -1).map((bin, i) => ({
    range: `₹${Math.round(bin)}`,
    count: data.arpu_histogram.counts[i],
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Dashboard Overview</h1>
        <p className="text-sm text-gray-500">Real-time churn analytics for 500K Indian telecom customers</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <KPICard
          title="Total Customers"
          value={data.total_customers.toLocaleString('en-IN')}
          subtitle="Active base"
          color="blue"
        />
        <KPICard
          title="Company Churn Rate"
          value={`${(data.company_churn_rate * 100).toFixed(1)}%`}
          subtitle="Customers leaving"
          color="red"
        />
        <KPICard
          title="Revenue at Risk"
          value={formatCurrency(data.total_revenue_at_risk)}
          subtitle="Monthly potential loss"
          color="orange"
        />
        <KPICard
          title="Avg ARPU"
          value={`₹${data.avg_arpu.toLocaleString('en-IN')}`}
          subtitle="Per user per month"
          color="green"
        />
        <KPICard
          title="Avg CLV"
          value={formatCurrency(data.avg_clv)}
          subtitle="Customer lifetime value"
          color="purple"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Donut Chart */}
        <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Churn Type Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={3}
                dataKey="value"
                strokeWidth={0}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => `${value}%`}
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }}
              />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                formatter={(value) => <span className="text-gray-300 text-xs">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* ARPU Histogram */}
        <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">ARPU Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={histogramData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="range" tick={{ fill: '#9ca3af', fontSize: 10 }} interval={4} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Regions */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">Top 10 Regions by Revenue at Risk</h3>
          <span className="text-[10px] text-gray-500 bg-dark-600 px-2 py-1 rounded-full">Click bar for AI insight</span>
        </div>
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={data.top10_regions_by_revenue_at_risk} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              tickFormatter={formatCurrency}
            />
            <YAxis
              dataKey="region"
              type="category"
              tick={{ fill: '#d1d5db', fontSize: 12 }}
              width={100}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb' }}
              formatter={(value) => formatCurrency(value)}
            />
            <Bar
              dataKey="revenue_at_risk"
              fill="#ef4444"
              radius={[0, 6, 6, 0]}
              cursor="pointer"
              onClick={(entry) => {
                setModal({
                  open: true,
                  type: 'Region',
                  value: entry.region,
                  stats: {
                    revenue_at_risk: entry.revenue_at_risk,
                    avg_arpu: entry.avg_arpu,
                    customer_count: entry.customer_count,
                  },
                });
              }}
            />
          </BarChart>
        </ResponsiveContainer>
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
