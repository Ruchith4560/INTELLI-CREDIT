export default function StatCard({ label, value, sub, icon: Icon, color = "text-neon", trend }) {
  return (
    <div className="glass rounded-2xl p-5 border border-dark-border card-hover">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">{label}</p>
        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-neon/10 flex items-center justify-center">
            <Icon className={`w-4 h-4 ${color}`} />
          </div>
        )}
      </div>
      <p className={`text-2xl font-black ${color}`}>{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${trend >= 0 ? 'text-neon' : 'text-red-400'}`}>
          <span>{trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%</span>
          <span className="text-slate-500 font-normal">vs last month</span>
        </div>
      )}
    </div>
  )
}
