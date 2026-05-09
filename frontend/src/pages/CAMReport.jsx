import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../utils/api'
import RiskBadge from '../components/RiskBadge'
import { FileText, Download, AlertTriangle, CheckCircle, Brain, Zap, ArrowLeft } from 'lucide-react'

const renderMd = (text = '') =>
  text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
    .replace(/\n/g, '<br/>')

export default function CAMReport() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoad] = useState(true)
  const [generating, setGen] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get(`/analysis/result/${sessionId}`)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load'))
      .finally(() => setLoad(false))
  }, [sessionId])

  const handleGenerate = async () => {
    setGen(true)
    try {
      await api.post(`/cam/generate/${sessionId}`)
      setGenerated(true)
      toast.success('CAM report generated!')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Generation failed')
    } finally {
      setGen(false)
    }
  }

  const handleDownload = async () => {
    try {
      const response = await api.get(`/cam/download/${sessionId}`, {
        responseType: 'blob',
      })
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `CAM_${data?.company_name || 'report'}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Download failed')
    }
  }

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

  const ratios = data?.financial_ratios || {}
  const fiveCs = data?.risk_breakdown?.five_cs || {}
  const gst = data?.risk_breakdown?.gst_data || {}
  const bank = data?.risk_breakdown?.bank_data || {}
  const lit = data?.litigation_risk || {}
  const news = data?.news_sentiment || {}
  const anomalies = data?.risk_breakdown?.anomalies || []

  const creditGrade = (s) =>
    s < 25 ? 'A+' : s < 35 ? 'A' : s < 50 ? 'BBB' : s < 65 ? 'BB' : 'B'

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-3">
            <FileText className="w-6 h-6 text-neon" />
            Credit Appraisal Memo
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">{data?.company_name}</p>
        </div>
        <div className="flex items-center gap-3">
          {!generated ? (
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-5 py-2.5 bg-neon text-dark text-sm font-bold rounded-xl hover:bg-neon-dark disabled:opacity-50 transition-all neon-glow"
            >
              {generating
                ? <div className="w-4 h-4 border-2 border-dark border-t-transparent rounded-full animate-spin" />
                : <Zap className="w-4 h-4" />}
              {generating ? 'Generating PDF…' : 'Generate CAM PDF'}
            </button>
          ) : (
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-5 py-2.5 bg-neon text-dark text-sm font-bold rounded-xl hover:bg-neon-dark transition-all neon-glow"
            >
              <Download className="w-4 h-4" />
              Download PDF
            </button>
          )}
        </div>
      </div>

      {/* CAM Preview Card */}
      <div className="glass rounded-2xl border border-dark-border overflow-hidden">
        {/* CAM Header Band */}
        <div className="bg-gradient-to-r from-dark-2 to-dark-card px-8 py-6 border-b border-dark-border">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Credit Appraisal Memorandum</p>
              <h2 className="text-xl font-black text-white">{data?.company_name}</h2>
              <p className="text-xs text-slate-400 mt-1">Prepared by Intelli-Credit AI Engine · {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
            </div>
            <div className="text-right">
              <RiskBadge decision={data?.decision} size="lg" />
              <p className="text-2xl font-black text-white mt-2">{data?.risk_score?.toFixed(1)}<span className="text-sm text-slate-400">/100</span></p>
              <p className="text-xs text-slate-500">Grade: {creditGrade(data?.risk_score || 50)}</p>
            </div>
          </div>
        </div>

        <div className="p-8 space-y-8">
          {/* Executive Summary */}
          <section>
            <h3 className="text-xs font-bold text-neon uppercase tracking-widest mb-3 border-b border-dark-border pb-1">
              Executive Summary
            </h3>
            <div
              className="text-sm text-slate-300 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: renderMd(data?.explanation_text || '') }}
            />
          </section>

          {/* Key Financials */}
          <section>
            <h3 className="text-xs font-bold text-neon uppercase tracking-widest mb-3 border-b border-dark-border pb-1">
              Key Financial Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                ['Current Ratio', ratios.current_ratio?.toFixed(2), '>1.3'],
                ['Debt/Equity', ratios.debt_to_equity?.toFixed(2), '<2.0'],
                ['Interest Coverage', ratios.interest_coverage?.toFixed(2), '>2.5x'],
                ['EBITDA Margin', `${ratios.ebitda_margin?.toFixed(1)}%`, '>10%'],
                ['Net Profit Margin', `${ratios.net_profit_margin?.toFixed(1)}%`, '>5%'],
                ['Revenue Growth', `${ratios.revenue_growth?.toFixed(1)}%`, '>5%'],
                ['ROE', `${ratios.roe?.toFixed(1)}%`, '>12%'],
                ['Revenue', `₹${ratios.revenue_crore?.toFixed(0)} Cr`, '—'],
              ].map(([label, val, bm]) => (
                <div key={label} className="p-3 rounded-xl bg-dark/50 border border-dark-border">
                  <p className="text-xs text-slate-500 mb-0.5">{label}</p>
                  <p className="text-sm font-bold text-white">{val || 'N/A'}</p>
                  <p className="text-xs text-slate-600">Benchmark: {bm}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Recommendation Box */}
          <section>
            <h3 className="text-xs font-bold text-neon uppercase tracking-widest mb-3 border-b border-dark-border pb-1">
              Final Recommendation
            </h3>
            <div className={`p-5 rounded-xl border ${data?.decision === 'APPROVE' ? 'bg-neon/10 border-neon/30'
                : data?.decision === 'REJECT' ? 'bg-red-500/10 border-red-500/30'
                  : 'bg-yellow-500/10 border-yellow-500/30'
              }`}>
              <div className="flex items-center gap-3 mb-3">
                <RiskBadge decision={data?.decision} size="lg" />
                {data?.loan_amount > 0 && (
                  <span className="text-sm font-bold text-white">
                    Limit: ₹{data.loan_amount?.toFixed(1)} Cr @ {data.interest_rate?.toFixed(2)}% p.a.
                  </span>
                )}
                <span className="text-xs text-slate-400 ml-auto flex items-center gap-1">
                  <Zap className="w-3 h-3 text-neon" />
                  {data?.scoring_method || 'Rule-Based'}
                </span>
              </div>
              {anomalies.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-red-400 mb-1">Key Risk Flags:</p>
                  {anomalies.map((a, i) => (
                    <p key={i} className="text-xs text-red-400/80 flex items-start gap-1">
                      <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                      [{a.severity}] {a.detail}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Five Cs */}
          {Object.keys(fiveCs).length > 0 && (
            <section>
              <h3 className="text-xs font-bold text-neon uppercase tracking-widest mb-3 border-b border-dark-border pb-1">
                Five Cs of Credit
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(fiveCs).map(([key, val]) => (
                  <div key={key} className="p-4 rounded-xl bg-dark/50 border border-dark-border">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-bold text-white capitalize">{key}</p>
                      <span className="text-sm font-black text-neon">{val?.score?.toFixed(0)}/100</span>
                    </div>
                    <div className="w-full h-1 bg-dark rounded-full mb-2">
                      <div className="h-1 bg-neon rounded-full" style={{ width: `${val?.score || 0}%` }} />
                    </div>
                    <p className="text-xs text-slate-400">{val?.summary}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* GST + Bank + Litigation quick summary */}
          <section>
            <h3 className="text-xs font-bold text-neon uppercase tracking-widest mb-3 border-b border-dark-border pb-1">
              Compliance & External Risk
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-dark/50 border border-dark-border">
                <p className="font-bold text-white mb-1">GST Compliance</p>
                <p className="text-slate-400">GSTR Mismatch: {gst.gstr2a_vs_3b_mismatch_pct?.toFixed(1) || 0}%</p>
                <p className={gst.filing_compliance === 'Compliant' ? 'text-neon' : 'text-red-400'}>
                  {gst.filing_compliance || 'N/A'}
                </p>
                <p className="text-slate-500">ITC Utilisation: {gst.itc_utilization_pct?.toFixed(1) || 0}%</p>
              </div>
              <div className="p-3 rounded-xl bg-dark/50 border border-dark-border">
                <p className="font-bold text-white mb-1">Banking Behaviour</p>
                <p className="text-slate-400">Bounce Rate: {bank.bounce_rate_pct?.toFixed(1) || 0}%</p>
                <p className={bank.emi_regularity === 'Regular' ? 'text-neon' : 'text-red-400'}>
                  EMI: {bank.emi_regularity || 'N/A'}
                </p>
                <p className="text-slate-500">Avg Balance: ₹{bank.average_balance_crore?.toFixed(1) || 0} Cr</p>
              </div>
              <div className="p-3 rounded-xl bg-dark/50 border border-dark-border">
                <p className="font-bold text-white mb-1">External Research</p>
                <p className="text-slate-400">Litigation: {lit.case_count || 0} cases</p>
                <p className={news.overall_sentiment === 'positive' ? 'text-neon' : news.overall_sentiment === 'negative' ? 'text-red-400' : 'text-yellow-400'}>
                  News: {news.overall_sentiment || 'N/A'}
                </p>
                <p className="text-slate-500 truncate">{news.source || ''}</p>
              </div>
            </div>
          </section>

          {/* Disclaimer */}
          <div className="text-xs text-slate-600 border-t border-dark-border pt-4">
            <p className="font-semibold text-slate-500 mb-1">Disclaimer</p>
            <p>This Credit Appraisal Memo has been generated by the Intelli-Credit AI Engine using multi-source financial data analysis. All recommendations are indicative and must be reviewed and approved by a qualified credit officer before disbursement. The AI analysis is a decision-support tool and does not constitute final lending approval.</p>
          </div>
        </div>
      </div>

      {/* Generate / Download again */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-3">
          <button onClick={() => navigate(`/analysis/${sessionId}`)} className="px-4 py-2 text-sm text-slate-400 border border-dark-border rounded-xl hover:text-white transition-all flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />Risk Analysis
          </button>
          <button onClick={() => navigate(`/explainability/${sessionId}`)} className="px-4 py-2 text-sm text-neon border border-neon/30 rounded-xl hover:bg-neon/10 transition-all flex items-center gap-2">
            <Brain className="w-4 h-4" />Explainability
          </button>
        </div>
        <div className="flex gap-3">
          {!generated ? (
            <button onClick={handleGenerate} disabled={generating}
              className="flex items-center gap-2 px-5 py-2.5 bg-neon text-dark text-sm font-bold rounded-xl hover:bg-neon-dark disabled:opacity-50 transition-all neon-glow">
              {generating ? <div className="w-4 h-4 border-2 border-dark border-t-transparent rounded-full animate-spin" /> : <Zap className="w-4 h-4" />}
              {generating ? 'Generating…' : 'Generate PDF'}
            </button>
          ) : (
            <button onClick={handleDownload}
              className="flex items-center gap-2 px-5 py-2.5 bg-neon text-dark text-sm font-bold rounded-xl hover:bg-neon-dark transition-all neon-glow">
              <Download className="w-4 h-4" />Download CAM PDF
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
