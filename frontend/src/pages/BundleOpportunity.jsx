import { useState, useEffect, useMemo } from 'react';
import { DATA_BASE } from '../config';
import KPICard from '../components/KPICard';

const formatCurrency = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${v}`;
};

// Sankey SVG component
function SankeyDiagram({ nodes, links }) {
  if (!nodes || !links || links.length === 0) return <p className="text-gray-500 text-sm">No Sankey data available.</p>;

  const width = 800;
  const height = 500;
  const padding = 40;
  const nodeWidth = 20;
  const nodePadding = 8;

  // Split into source (left) and target (right) groups
  const sourceIndices = new Set(links.map(l => l.source));
  const targetIndices = new Set(links.map(l => l.target));

  const sourceNodes = [...sourceIndices].sort((a, b) => a - b);
  const targetNodes = [...targetIndices].sort((a, b) => a - b);

  // Compute node heights by total flow
  const maxFlow = Math.max(
    ...sourceNodes.map(i => links.filter(l => l.source === i).reduce((s, l) => s + l.value, 0)),
    ...targetNodes.map(i => links.filter(l => l.target === i).reduce((s, l) => s + l.value, 0)),
    1
  );

  const availableHeight = height - padding * 2 - (Math.max(sourceNodes.length, targetNodes.length) - 1) * nodePadding;

  const getNodeY = (indices, nodeIdx) => {
    const totalFlow = indices.reduce((s, i) => {
      const flow = i === nodeIdx
        ? links.filter(l => l.source === i || l.target === i).reduce((s, l) => s + l.value, 0)
        : links.filter(l => l.source === i || l.target === i).reduce((s, l) => s + l.value, 0);
      return s + flow;
    }, 0);

    let y = padding;
    for (const i of indices) {
      if (i === nodeIdx) return y;
      const flow = links.filter(l => l.source === i || l.target === i).reduce((s, l) => s + l.value, 0);
      const h = Math.max((flow / maxFlow) * availableHeight, 12);
      y += h + nodePadding;
    }
    return y;
  };

  const getNodeHeight = (idx) => {
    const flow = links.filter(l => l.source === idx || l.target === idx).reduce((s, l) => s + l.value, 0);
    return Math.max((flow / maxFlow) * availableHeight, 12);
  };

  const leftX = padding;
  const rightX = width - padding - nodeWidth;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '500px' }}>
      {/* Links */}
      {links.map((link, i) => {
        const sy = getNodeY(sourceNodes, link.source);
        const sh = getNodeHeight(link.source);
        const ty = getNodeY(targetNodes, link.target);
        const th = getNodeHeight(link.target);

        // Compute offset within source/target node
        const sourceLinks = links.filter(l => l.source === link.source);
        const sourceBefore = sourceLinks.slice(0, sourceLinks.indexOf(link));
        const sourceOffset = sourceBefore.reduce((s, l) => s + (l.value / links.filter(ll => ll.source === link.source).reduce((s, l) => s + l.value, 0)) * sh, 0);
        const linkHeight = (link.value / links.filter(l => l.source === link.source).reduce((s, l) => s + l.value, 0)) * sh;

        const targetLinks = links.filter(l => l.target === link.target);
        const targetBefore = targetLinks.slice(0, targetLinks.indexOf(link));
        const targetOffset = targetBefore.reduce((s, l) => s + (l.value / links.filter(ll => ll.target === link.target).reduce((s, l) => s + l.value, 0)) * th, 0);

        const x0 = leftX + nodeWidth;
        const y0 = sy + sourceOffset + linkHeight / 2;
        const x1 = rightX;
        const y1 = ty + targetOffset + linkHeight / 2;

        const opacity = Math.min(0.2 + (link.value / maxFlow) * 0.6, 0.7);

        return (
          <path
            key={i}
            d={`M${x0},${y0} C${(x0 + x1) / 2},${y0} ${(x0 + x1) / 2},${y1} ${x1},${y1}`}
            fill="none"
            stroke="#3b82f6"
            strokeOpacity={opacity}
            strokeWidth={Math.max(linkHeight, 1)}
          />
        );
      })}

      {/* Source nodes */}
      {sourceNodes.map(idx => {
        const y = getNodeY(sourceNodes, idx);
        const h = getNodeHeight(idx);
        return (
          <g key={`s-${idx}`}>
            <rect x={leftX} y={y} width={nodeWidth} height={h} rx={4} fill="#3b82f6" />
            <text x={leftX - 6} y={y + h / 2} textAnchor="end" dominantBaseline="middle" fill="#d1d5db" fontSize={10}>
              {(nodes[idx] || '').trim()}
            </text>
          </g>
        );
      })}

      {/* Target nodes */}
      {targetNodes.map(idx => {
        const y = getNodeY(targetNodes, idx);
        const h = getNodeHeight(idx);
        return (
          <g key={`t-${idx}`}>
            <rect x={rightX} y={y} width={nodeWidth} height={h} rx={4} fill="#22c55e" />
            <text x={rightX + nodeWidth + 6} y={y + h / 2} textAnchor="start" dominantBaseline="middle" fill="#d1d5db" fontSize={10}>
              {(nodes[idx] || '').trim()}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function BundleOpportunity() {
  const [data, setData] = useState(null);
  const [switchThreshold, setSwitchThreshold] = useState(0.3);
  const [conversionRate, setConversionRate] = useState(20);

  useEffect(() => {
    fetch(`${DATA_BASE}/bundle.json`)
      .then(r => r.json())
      .then(setData);
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.customers.filter(c => c.bundle_switch_prob >= switchThreshold);
  }, [data, switchThreshold]);

  const kpis = useMemo(() => {
    if (filtered.length === 0) return { count: 0, projRevenue: 0, avgDelta: 0, riskFromInaction: 0 };
    const totalDelta = filtered.reduce((s, c) => s + c.arpu_delta, 0);
    const projRevenue = totalDelta * (conversionRate / 100);
    const avgDelta = totalDelta / filtered.length;
    const riskFromInaction = filtered.reduce((s, c) => s + c.company_churn_prob * c.monthly_arpu, 0);
    return { count: filtered.length, projRevenue, avgDelta, riskFromInaction };
  }, [filtered, conversionRate]);

  const top100 = useMemo(() => {
    return [...filtered].sort((a, b) => b.priority_score - a.priority_score).slice(0, 100);
  }, [filtered]);

  if (!data) {
    return <div className="flex items-center justify-center h-full"><div className="flex gap-2"><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} /><span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} /></div></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Bundle Opportunity</h1>
        <p className="text-sm text-gray-500">Identify bundle upgrade candidates and projected revenue uplift</p>
      </div>

      {/* Sliders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark-700 border border-dark-600 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-300">Min Bundle Switch Probability</label>
            <span className="text-sm font-bold text-blue-400">{(switchThreshold * 100).toFixed(0)}%</span>
          </div>
          <input type="range" min={0.1} max={0.9} step={0.05} value={switchThreshold} onChange={e => setSwitchThreshold(+e.target.value)} className="w-full h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer accent-blue-500" />
          <div className="flex justify-between text-[10px] text-gray-500 mt-1"><span>10%</span><span>90%</span></div>
        </div>
        <div className="bg-dark-700 border border-dark-600 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-300">Expected Conversion Rate</label>
            <span className="text-sm font-bold text-green-400">{conversionRate}%</span>
          </div>
          <input type="range" min={5} max={50} step={1} value={conversionRate} onChange={e => setConversionRate(+e.target.value)} className="w-full h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer accent-green-500" />
          <div className="flex justify-between text-[10px] text-gray-500 mt-1"><span>5%</span><span>50%</span></div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard title="Eligible for Upsell" value={kpis.count.toLocaleString()} color="blue" />
        <KPICard title="Projected Monthly Upsell" value={formatCurrency(kpis.projRevenue)} color="green" />
        <KPICard title="Avg ARPU Delta" value={`₹${kpis.avgDelta.toFixed(0)}`} color="purple" />
        <KPICard title="Risk from Inaction" value={formatCurrency(kpis.riskFromInaction)} color="red" />
      </div>

      {/* Sankey */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Bundle Migration Flow</h3>
        <SankeyDiagram nodes={data.sankey.nodes} links={data.sankey.links} />
      </div>

      {/* Priority Table */}
      <div className="bg-dark-700 border border-dark-600 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Top 100 by Priority Score</h3>
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-dark-700">
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-dark-600">
                <th className="text-left py-3 px-4">Customer ID</th>
                <th className="text-left py-3 px-4">Current Bundle</th>
                <th className="text-left py-3 px-4">Suggested Bundle</th>
                <th className="text-right py-3 px-4">ARPU Delta</th>
                <th className="text-right py-3 px-4">Switch Prob</th>
                <th className="text-right py-3 px-4">Priority</th>
              </tr>
            </thead>
            <tbody>
              {top100.map(c => (
                <tr key={c.customer_id} className="border-b border-dark-600/50 hover:bg-dark-600/30 transition-colors">
                  <td className="py-2.5 px-4 text-blue-400 font-medium">{c.customer_id}</td>
                  <td className="py-2.5 px-4 text-gray-400">{c.bundle_name}</td>
                  <td className="py-2.5 px-4 text-green-400">{c.suggested_bundle}</td>
                  <td className="text-right py-2.5 px-4 text-white">₹{c.arpu_delta}</td>
                  <td className="text-right py-2.5 px-4 text-blue-400">{(c.bundle_switch_prob * 100).toFixed(1)}%</td>
                  <td className="text-right py-2.5 px-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                      ${c.priority_score > 0.5 ? 'bg-green-500/15 text-green-400' :
                        c.priority_score > 0.3 ? 'bg-yellow-500/15 text-yellow-400' :
                        'bg-gray-500/15 text-gray-400'}`}
                    >
                      {c.priority_score.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
