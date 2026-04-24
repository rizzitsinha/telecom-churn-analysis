export default function KPICard({ title, value, subtitle, icon, trend, color = 'blue' }) {
  const colorMap = {
    blue: 'from-blue-500/10 to-blue-600/5 border-blue-500/20',
    red: 'from-red-500/10 to-red-600/5 border-red-500/20',
    green: 'from-emerald-500/10 to-emerald-600/5 border-emerald-500/20',
    orange: 'from-orange-500/10 to-orange-600/5 border-orange-500/20',
    purple: 'from-purple-500/10 to-purple-600/5 border-purple-500/20',
  };

  const iconColorMap = {
    blue: 'text-blue-400',
    red: 'text-red-400',
    green: 'text-emerald-400',
    orange: 'text-orange-400',
    purple: 'text-purple-400',
  };

  return (
    <div className={`bg-gradient-to-br ${colorMap[color]} border rounded-xl p-5 animate-fade-in`}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{title}</p>
        {icon && <span className={`${iconColorMap[color]} opacity-70`}>{icon}</span>}
      </div>
      <p className="text-2xl font-bold text-white mb-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs ${trend >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d={trend >= 0 ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
          </svg>
          <span>{Math.abs(trend)}%</span>
        </div>
      )}
    </div>
  );
}
