import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from 'recharts'
import api from '../utils/api'
import RiskBadge from '../components/RiskBadge'
import {
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  ExternalLink, Brain, FileText, Zap, Globe, Scale,
  Building, Activity, ArrowRight, Info
} from 'lucide-react'

const COLORS = { APPROVE: '#22c55e', REVIEW: '#f59e0b', REJECT: '#ef4444' }

function GaugeArc({ score }) {
  const pct   = score / 100
  const color = score <= 35 ? '#22c55e' : score <= 60 ? '#f59e0b' : '#ef4444'
  const r     = 70
  const cx = 100, cy = 90
  const arc  = (angle) => ({
    x: cx + r * Math.cos((angle * Math.PI) / 180),
    y: cy + r * Math.sin((angle * Math.PI) / 180),
  })
  const start  = arc(180)
  const end    = arc(180 + pct * 180)
  const large  = pct > 0.5 ? 1 : 0
  return (
    <svg viewBox="0 0 200 110" className="w-full max-w-xs mx-auto">
      <path d={`M ${arc(180).x} ${arc(180).y} A ${r} ${r} 0 0 1 ${arc(360).x} ${arc(360).y}`}
        fill="none" stroke="#1e2d3d" strokeWidth="12" strokeLinecap="round" />
      <path d={`M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`}
        fill="none" stroke={color} strokeWidth="12" strokeLinecap="round" />
      <text x={cx} y={cy - 8} textAnchor="middle" fill="white" fontSize="28" fontWeight="900">{score.toFixed(1)}</text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill="#94a3b8" fontSize="11">Risk Score</text>
      <text x="30"  y={cy + 30} fill="#22c55e" fontSize="9" fontWeight="bold">LOW</text>
      <text x="83"  y={cy + 30} fill="#f59e0b" fontSize="9" fontWeight="bold">MED</text>
      <text x="148" y={cy + 30} fill="#ef4444" fontSize="9" fontWeight="bold">HIGH</text>
    </svg>
  )
}

export default function RiskAnalysis() {
  const { sessionId }       = useParams()
  const navigate            = useNavigate()
  const [data, setData]     = useState(null)
  const [loading, setLoad]  = useState(true)
  const [error, setError]   = useState(null)

  useEffect(() => {
    api.get(`/analysis/result/${sessionId}`)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load'))
      .finally(() => setLoad(false))
  }, [sessionId])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-10 h-10 border-2 border-neon border-t-transparent rounded-full animate-spin" />
    </div>
  )
  if (error) return (
    <div className="glass rounded-2xl p-8 border border-red-500/30 text-center">
      <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
      <p className="text-red-400 font-semibold">{error}</p>
      <button onClick={() => navigate('/dashboard')} className="mt-4 text-neon text-sm hover:underline">← Back to Dashboard</button>
    </div>
  )

  const ratios   = data.financial_ratios || {}
  const gst      = data.risk_breakdown?.gst_data || {}
  const bank     = data.risk_breakdown?.bank_data || {}
  const news     = data.news_sentiment || {}
  const lit      = data.litigation_risk || {}
  const fiveCs   = data.risk_breakdown?.five_cs || {}
  const anomalies = data.risk_breakdown?.anomalies || []
  const reasons  = data.decision_reasons || []

  const ratioBar = [
    { name: 'Current Ratio',     value: +(ratios.current_ratio     || 0).toFixed(2), benchmark: 1.3  },
    { name: 'Debt/Equity',       value: +(ratios.debt_to_equity    || 0).toFixed(2), benchmark: 2.0  },
    { name: 'Interest Coverage', value: +(ratios.interest_coverage || 0).toFixed(2), benchmark: 2.5  },
    { name: 'EBITDA Margin %',   value: +(ratios.ebitda_margin     || 0).toFixed(2), benchmark: 10   },
    { name: 'Net Profit %',      value: +(ratios.net_profit_margin || 0).toFixed(2), benchmark: 5    },
    { name: 'Revenue Growth %',  value: +(ratios.revenue_growth    || 0).toFixed(2), benchmark: 5    },
  ]

  const radarData = Object.entries(fiveCs).map(([k, v]) => ({
    subject: k.charAt(0).toUpperCase() + k.slice(1),
    score:   v?.score || 0,
  }))

  const gstTrend = (gst.monthly_gst_trend || []).map((v, i) => ({
    month: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'][i] || `M${i + 1}`,
    gst: v,
  }))

  const bankTrend = (bank.monthly_credits || []).map((c, i) => ({
    month:   ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'][i] || `M${i + 1}`,
    credits: c,
    debits:  (bank.monthly_debits || [])[i] || 0,
  }))

  const color      = COLORS[data.decision] || '#f59e0b'
  const isApprove  = data.decision === 'APPROVE'
  const isReject   = data.decision === 'REJECT'

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">{data.company_name}</h1>
          <p className="text-slate-400 text-sm mt-0.5">Credit Risk Analysis Report</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {data.scoring_method && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-neon/10 text-neon border border-neon/20 flex items-center gap-1">
              <Zap className="w-3 h-3" />{data.scoring_method}
            </span>
          )}
          <button onClick={() => navigate(`/explainability/${sessionId}`)}
            className="flex items-center gap-2 text-sm text-neon hover:underline">
            <Brain className="w-4 h-4" />Explainability <ArrowRight className="w-3 h-3" />
          </button>
          <button onClick={() => navigate(`/cam/${sessionId}`)}
            className="flex items-center gap-2 text-sm bg-neon text-dark px-4 py-2 rounded-xl font-semibold hover:bg-neon-dark transition-all">
            <FileText className="w-4 h-4" />CAM Report
          </button>
        </div>
      </div>

      {/* Decision cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Decision',      value: <RiskBadge decision={data.decision} size="lg" />, icon: CheckCircle },
          { label: 'Risk Score',    value: `${data.risk_score?.toFixed(1)}/100`, icon: Activity, color: color },
          { label: 'Loan Amount',   value: data.loan_amount > 0 ? `₹${data.loan_amount?.toFixed(1)} Cr` : 'N/A', icon: TrendingUp, color: '#22c55e' },
          { label: 'Interest Rate', value: data.interest_rate > 0 ? `${data.interest_rate?.toFixed(2)}%` : 'N/A', icon: TrendingDown, color: '#f59e0b' },
        ].map(({ label, value, icon: Icon, color: c }) => (
          <div key={label} className="glass rounded-2xl p-5 border border-dark-border">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{label}</p>
            {typeof value === 'string'
              ? <p className="text-2xl font-black" style={{ color: c || 'white' }}>{value}</p>
              : <div className="mt-1">{value}</div>}
          </div>
        ))}
      </div>

      {/* Gauge + Decision reasons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-neon" />Risk Gauge
          </h3>
          <GaugeArc score={data.risk_score || 0} />
          <div className="grid grid-cols-3 gap-3 mt-4">
            {[['Low Risk', '0–35', '#22c55e'], ['Review', '36–65', '#f59e0b'], ['High Risk', '66–100', '#ef4444']].map(([l, r, c]) => (
              <div key={l} className="text-center p-2 rounded-lg" style={{ background: `${c}15` }}>
                <p className="text-xs font-bold" style={{ color: c }}>{l}</p>
                <p className="text-xs text-slate-400">{r}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Info className="w-4 h-4 text-neon" />Decision Factors
          </h3>
          {reasons.length === 0
            ? <p className="text-slate-500 text-sm">No specific factors recorded.</p>
            : <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {reasons.map((r, i) => (
                  <div key={i} className={`flex items-start gap-2 p-2.5 rounded-lg text-xs ${r.type === 'positive' ? 'bg-neon/10' : 'bg-red-500/10'}`}>
                    {r.type === 'positive'
                      ? <CheckCircle className="w-3.5 h-3.5 text-neon mt-0.5 flex-shrink-0" />
                      : <AlertTriangle className="w-3.5 h-3.5 text-red-400 mt-0.5 flex-shrink-0" />}
                    <div>
                      <p className={`font-semibold ${r.type === 'positive' ? 'text-neon' : 'text-red-400'}`}>{r.factor}</p>
                      <p className="text-slate-400 mt-0.5">{r.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
          }
        </div>
      </div>

      {/* Financial Ratios chart */}
      <div className="glass rounded-2xl p-6 border border-dark-border">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-neon" />Financial Ratios vs Benchmark
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={ratioBar} margin={{ top: 0, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
            <Tooltip contentStyle={{ background: '#1a2236', border: '1px solid #1e2d3d', borderRadius: 8, fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="value"     fill="#22c55e" name="Actual"    radius={[4, 4, 0, 0]} />
            <Bar dataKey="benchmark" fill="#334155" name="Benchmark" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Five Cs + GST + Bank row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Five Cs Radar */}
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Building className="w-4 h-4 text-neon" />Five Cs of Credit
          </h3>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1e2d3d" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Radar dataKey="score" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-500 text-sm text-center py-8">No data</p>}
        </div>

        {/* GST Trend */}
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
            <Globe className="w-4 h-4 text-neon" />GST Intelligence
          </h3>
          <div className="flex items-center gap-3 mb-3">
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${gst.filing_compliance === 'Compliant' ? 'bg-neon/15 text-neon' : 'bg-red-500/15 text-red-400'}`}>
              {gst.filing_compliance || 'N/A'}
            </span>
            <span className="text-xs text-slate-400">Mismatch: {gst.gstr2a_vs_3b_mismatch_pct?.toFixed(1) || 0}%</span>
          </div>
          {gstTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={gstTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1a2236', border: '1px solid #1e2d3d', borderRadius: 8, fontSize: 11 }} />
                <Line dataKey="gst" stroke="#22c55e" strokeWidth={2} dot={false} name="GST (Cr)" />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-500 text-xs text-center py-8">No trend data</p>}
        </div>

        {/* Bank Statement */}
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-neon" />Bank Statement
          </h3>
          <div className="flex items-center gap-3 mb-3">
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${bank.emi_regularity === 'Regular' ? 'bg-neon/15 text-neon' : 'bg-red-500/15 text-red-400'}`}>
              {bank.emi_regularity || 'N/A'}
            </span>
            <span className="text-xs text-slate-400">Bounce: {bank.bounce_rate_pct?.toFixed(1) || 0}%</span>
          </div>
          {bankTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={bankTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1a2236', border: '1px solid #1e2d3d', borderRadius: 8, fontSize: 11 }} />
                <Bar dataKey="credits" fill="#22c55e" name="Credits (Cr)" radius={[2, 2, 0, 0]} />
                <Bar dataKey="debits"  fill="#334155" name="Debits (Cr)"  radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-500 text-xs text-center py-8">No data</p>}
        </div>
      </div>

      {/* News + Litigation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* News */}
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
            <Globe className="w-4 h-4 text-neon" />News Sentiment
          </h3>
          <div className="flex items-center gap-3 mb-4">
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold capitalize ${
              news.overall_sentiment === 'positive' ? 'bg-neon/15 text-neon'
              : news.overall_sentiment === 'negative' ? 'bg-red-500/15 text-red-400'
              : 'bg-yellow-500/15 text-yellow-400'
            }`}>{news.overall_sentiment || 'N/A'}</span>
            <span className="text-xs text-slate-500">{news.source}</span>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {(news.news_items || []).map((item, i) => (
              <div key={i} className="flex items-start gap-2 text-xs p-2 rounded-lg bg-dark/40">
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                  item.sentiment === 'positive' ? 'bg-neon'
                  : item.sentiment === 'negative' ? 'bg-red-400' : 'bg-yellow-400'}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-slate-300 leading-tight">{item.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-slate-600">{item.source}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-slate-600">{item.date}</span>
                    {item.url && (
                      <a href={item.url} target="_blank" rel="noreferrer" className="text-neon hover:underline">
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Litigation */}
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
            <Scale className="w-4 h-4 text-neon" />Litigation Risk
          </h3>
          <div className="flex items-center gap-3 mb-4">
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${(lit.case_count || 0) > 3 ? 'bg-red-500/15 text-red-400' : 'bg-neon/15 text-neon'}`}>
              {lit.case_count || 0} Cases
            </span>
            <span className="text-xs text-slate-500">{lit.source}</span>
          </div>
          {(lit.cases || []).length === 0
            ? <p className="text-slate-500 text-sm text-center py-6">No litigation cases found</p>
            : <div className="space-y-2 max-h-48 overflow-y-auto">
                {lit.cases.map((c, i) => (
                  <div key={i} className="text-xs p-2.5 rounded-lg bg-dark/40 border border-dark-border">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-slate-300 font-medium">{c.nature}</p>
                      <span className={`flex-shrink-0 px-1.5 py-0.5 rounded text-xs font-semibold ${c.status === 'Disposed' ? 'bg-neon/10 text-neon' : 'bg-red-500/10 text-red-400'}`}>
                        {c.status}
                      </span>
                    </div>
                    <p className="text-slate-500 mt-0.5">{c.court} · {c.case_id}</p>
                    {c.url && (
                      <a href={c.url} target="_blank" rel="noreferrer" className="text-neon text-xs hover:underline flex items-center gap-1 mt-0.5">
                        View source <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
          }
        </div>
      </div>

      {/* Anomalies */}
      {anomalies.length > 0 && (
        <div className="glass rounded-2xl p-6 border border-red-500/20 bg-red-500/5">
          <h3 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />Anomalies Detected ({anomalies.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {anomalies.map((a, i) => (
              <div key={i} className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs">
                <span className={`px-1.5 py-0.5 rounded text-xs font-bold flex-shrink-0 ${a.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  {a.severity}
                </span>
                <div>
                  <p className="font-semibold text-red-300">{a.type.replace(/_/g, ' ')}</p>
                  <p className="text-red-400/80 mt-0.5">{a.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Nav buttons */}
      <div className="flex gap-3 pt-2">
        <button onClick={() => navigate('/dashboard')} className="px-4 py-2 text-sm text-slate-400 hover:text-white border border-dark-border rounded-xl transition-all">
          ← Dashboard
        </button>
        <button onClick={() => navigate(`/explainability/${sessionId}`)} className="px-4 py-2 text-sm text-neon border border-neon/30 rounded-xl hover:bg-neon/10 transition-all flex items-center gap-2">
          <Brain className="w-4 h-4" />Explainability
        </button>
        <button onClick={() => navigate(`/cam/${sessionId}`)} className="ml-auto px-4 py-2 text-sm bg-neon text-dark rounded-xl font-semibold hover:bg-neon-dark transition-all flex items-center gap-2">
          <FileText className="w-4 h-4" />Generate CAM Report
        </button>
      </div>
    </div>
  )
}
