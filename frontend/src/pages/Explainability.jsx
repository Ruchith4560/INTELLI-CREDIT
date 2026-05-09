import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts'
import api from '../utils/api'
import RiskBadge from '../components/RiskBadge'
import { Brain, AlertTriangle, FileText, ArrowRight, Zap, Info, CheckCircle } from 'lucide-react'

const renderMarkdown = (text = '') =>
  text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
    .replace(/\n/g, '<br/>')

export default function Explainability() {
  const { sessionId }      = useParams()
  const navigate           = useNavigate()
  const [data, setData]    = useState(null)
  const [loading, setLoad] = useState(true)
  const [error, setError]  = useState(null)
  const [feedback, setFeedback] = useState({ show: false, agreed: null, comments: '' })
  const [fbSent, setFbSent]    = useState(false)

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
      <button onClick={() => navigate('/dashboard')} className="mt-4 text-neon text-sm hover:underline">← Dashboard</button>
    </div>
  )

  const shap      = data.shap_values || {}
  const ranking   = data.feature_importance_ranking ||
    Object.entries(shap).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
  const fiveCs    = data.risk_breakdown?.five_cs || {}

  const shapChart = ranking.map(([feat, val]) => ({
    name:  feat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: typeof val === 'number' ? val : (Array.isArray(val) ? val[1] : 0),
  }))

  const totalShap    = shapChart.reduce((s, d) => s + Math.abs(d.value), 0) || 1
  const shapWithPct  = shapChart.map(d => ({
    ...d,
    pct: Math.round((Math.abs(d.value) / totalShap) * 100),
  }))

  const submitFeedback = async () => {
    try {
      await api.post('/feedback/submit', {
        session_id: sessionId,
        agreed_with_decision: feedback.agreed,
        comments: feedback.comments,
      })
      setFbSent(true)
    } catch {}
  }

  const FIVE_C_COLORS = { character: '#22c55e', capacity: '#0ea5e9', capital: '#a855f7', collateral: '#f59e0b', conditions: '#ec4899' }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-3">
            <Brain className="w-6 h-6 text-neon" />
            Explainability Report
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">{data.company_name} — Why the AI made this decision</p>
        </div>
        <div className="flex items-center gap-3">
          <RiskBadge decision={data.decision} size="lg" />
          <span className="text-lg font-black text-white">{data.risk_score?.toFixed(1)}/100</span>
          {data.scoring_method && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-neon/10 text-neon border border-neon/20 flex items-center gap-1">
              <Zap className="w-3 h-3" />{data.scoring_method}
            </span>
          )}
        </div>
      </div>

      {/* SHAP Chart */}
      <div className="glass rounded-2xl p-6 border border-dark-border">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-neon" />
            SHAP Feature Importance
          </h3>
          <span className="text-xs text-slate-500">
            {data.scoring_method === 'XGBoost ML Model' ? '✅ Real SHAP values from ML model' : '⚠️ Formula-based (add ML model for real SHAP)'}
          </span>
        </div>
        <p className="text-xs text-slate-500 mb-5">
          Positive values (red) push towards REJECT. Negative values (green) push towards APPROVE.
        </p>

        {/* Bar chart */}
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={shapChart} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={v => v.toFixed(2)} />
            <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={130} />
            <Tooltip
              contentStyle={{ background: '#1a2236', border: '1px solid #1e2d3d', borderRadius: 8, fontSize: 12 }}
              formatter={(v) => [`${v.toFixed(4)} SHAP`, 'Impact']}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {shapChart.map((d, i) => (
                <Cell key={i} fill={d.value > 0 ? '#ef4444' : '#22c55e'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Percentage breakdown */}
        <div className="mt-5 space-y-2">
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">Feature Contribution %</p>
          {shapWithPct.map((d, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="text-xs text-slate-400 w-36 truncate">{d.name}</span>
              <div className="flex-1 h-2 bg-dark rounded-full overflow-hidden">
                <div
                  className="h-2 rounded-full transition-all"
                  style={{ width: `${d.pct}%`, background: d.value > 0 ? '#ef4444' : '#22c55e' }}
                />
              </div>
              <span className={`text-xs font-bold w-10 text-right ${d.value > 0 ? 'text-red-400' : 'text-neon'}`}>
                {d.pct}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* LLM Explanation */}
      <div className="glass rounded-2xl p-6 border border-dark-border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Brain className="w-4 h-4 text-neon" />
            AI Credit Narrative
          </h3>
          <span className="text-xs text-slate-500">
            {process.env.NODE_ENV === 'development'
              ? 'Set OPENAI_API_KEY in .env for GPT-generated narrative'
              : 'Powered by AI'}
          </span>
        </div>
        <div
          className="text-sm text-slate-300 leading-relaxed space-y-2 max-h-[500px] overflow-y-auto pr-2"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(data.explanation_text || 'No explanation available.') }}
        />
      </div>

      {/* Five Cs detail */}
      {Object.keys(fiveCs).length > 0 && (
        <div className="glass rounded-2xl p-6 border border-dark-border">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Info className="w-4 h-4 text-neon" />Five Cs of Credit — Detailed Breakdown
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(fiveCs).map(([key, val]) => {
              const c = FIVE_C_COLORS[key] || '#22c55e'
              return (
                <div key={key} className="p-4 rounded-xl bg-dark/50 border border-dark-border">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-bold text-white capitalize">{key}</p>
                    <span className="text-lg font-black" style={{ color: c }}>{val?.score?.toFixed(0)}</span>
                  </div>
                  <div className="w-full h-1.5 bg-dark rounded-full mb-2">
                    <div className="h-1.5 rounded-full" style={{ width: `${val?.score || 0}%`, background: c }} />
                  </div>
                  <p className="text-xs text-slate-400">{val?.summary}</p>
                  {val?.factors && (
                    <ul className="mt-2 space-y-0.5">
                      {val.factors.map((f, i) => (
                        <li key={i} className="text-xs text-slate-500 flex items-center gap-1">
                          <span style={{ color: c }}>·</span> {f}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Human-in-the-Loop Feedback */}
      <div className="glass rounded-2xl p-6 border border-neon/20 bg-neon/5">
        <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-neon" />
          Officer Feedback — Human-in-the-Loop
        </h3>
        <p className="text-xs text-slate-400 mb-4">Your feedback trains the model to improve over time.</p>

        {fbSent ? (
          <div className="flex items-center gap-2 text-neon text-sm">
            <CheckCircle className="w-4 h-4" />
            Feedback submitted. Thank you!
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-3">
              <button
                onClick={() => setFeedback(f => ({ ...f, agreed: true }))}
                className={`px-4 py-2 rounded-xl text-sm font-semibold border transition-all ${feedback.agreed === true ? 'bg-neon text-dark border-neon' : 'border-dark-border text-slate-400 hover:border-neon/40'}`}
              >
                ✓ Agree with AI Decision
              </button>
              <button
                onClick={() => setFeedback(f => ({ ...f, show: true, agreed: false }))}
                className={`px-4 py-2 rounded-xl text-sm font-semibold border transition-all ${feedback.agreed === false ? 'bg-red-500/20 text-red-400 border-red-500/40' : 'border-dark-border text-slate-400 hover:border-red-500/30'}`}
              >
                ✗ Disagree
              </button>
            </div>
            {(feedback.show || feedback.agreed !== null) && (
              <textarea
                rows={2}
                className="input-dark w-full rounded-xl px-3 py-2 text-sm resize-none"
                placeholder="Optional comments for model improvement…"
                value={feedback.comments}
                onChange={e => setFeedback(f => ({ ...f, comments: e.target.value }))}
              />
            )}
            {feedback.agreed !== null && (
              <button onClick={submitFeedback} className="px-4 py-2 bg-neon text-dark text-sm font-bold rounded-xl hover:bg-neon-dark transition-all">
                Submit Feedback
              </button>
            )}
          </div>
        )}
      </div>

      {/* Nav */}
      <div className="flex gap-3 pt-2">
        <button onClick={() => navigate(`/analysis/${sessionId}`)} className="px-4 py-2 text-sm text-slate-400 hover:text-white border border-dark-border rounded-xl transition-all">
          ← Risk Analysis
        </button>
        <button onClick={() => navigate(`/cam/${sessionId}`)} className="ml-auto px-4 py-2 text-sm bg-neon text-dark rounded-xl font-semibold hover:bg-neon-dark transition-all flex items-center gap-2">
          <FileText className="w-4 h-4" />Generate CAM Report <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}
