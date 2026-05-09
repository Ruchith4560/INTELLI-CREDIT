import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import api from '../utils/api'
import {
  Upload, FileText, Building2, Play, Clock,
  CheckCircle, XCircle, AlertCircle, Trash2,
  TrendingUp, Cpu, Zap
} from 'lucide-react'
import RiskBadge from '../components/RiskBadge'

const STEPS = [
  'Parsing documents…',
  'Validating data quality…',
  'Extracting financial entities…',
  'Running Research Agents…',
  'Checking Regulatory Knowledge Base…',
  'Computing financial ratios & GST…',
  'Running Scoring Engine…',
  'Generating SHAP explainability…',
  'Preparing AI narrative…',
  'Finalising credit decision…',
]

export default function Dashboard() {
  const navigate                  = useNavigate()
  const [company, setCompany]     = useState('')
  const [notes, setNotes]         = useState('')
  const [files, setFiles]         = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [stepIdx, setStepIdx]     = useState(0)
  const [history, setHistory]     = useState([])
  const [histLoaded, setHistLoaded] = useState(false)

  // Load history lazily
  const loadHistory = async () => {
    if (histLoaded) return
    try {
      const r = await api.get('/analysis/history')
      setHistory(r.data.history || [])
      setHistLoaded(true)
    } catch {}
  }
  useState(() => { loadHistory() }, [])

  // Dropzone
  const onDrop = useCallback((accepted) => {
    setFiles(prev => [...prev, ...accepted.map(f => ({ file: f, name: f.name, status: 'ready' }))])
  }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/csv': ['.csv'], 'application/vnd.ms-excel': ['.xls', '.xlsx'] },
    multiple: true,
  })

  const removeFile = (i) => setFiles(prev => prev.filter((_, idx) => idx !== i))

  // Upload
  const handleUpload = async () => {
    if (!company.trim()) return toast.error('Enter company name first')
    if (files.length === 0) return toast.error('Add at least one document')
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('company_name', company)
      files.forEach(f => fd.append('files', f.file))
      const r = await api.post('/documents/upload-documents', fd)
      setSessionId(r.data.session_id)
      setFiles(prev => prev.map(f => ({ ...f, status: 'uploaded' })))
      toast.success(`${files.length} document(s) uploaded!`)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  // Analyse
  const handleAnalyse = async () => {
    if (!sessionId) return toast.error('Upload documents first')
    setAnalyzing(true)
    setStepIdx(0)

    // Progress animation
    const interval = setInterval(() => {
      setStepIdx(prev => prev < STEPS.length - 1 ? prev + 1 : prev)
    }, 2200)

    try {
      const r = await api.post('/analysis/run', {
        session_id:        sessionId,
        company_name:      company,
        qualitative_notes: notes,
        run_web_research:  true,
      })
      clearInterval(interval)
      toast.success(`Analysis complete — ${r.data.decision}`)
      navigate(`/analysis/${sessionId}`)
    } catch (e) {
      clearInterval(interval)
      toast.error(e.response?.data?.detail || 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const docTypeColor = { annual_report: 'text-blue-400', gst: 'text-yellow-400', bank_statement: 'text-purple-400', csv: 'text-cyan-400', other: 'text-slate-400' }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-white">Credit Analysis Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Upload financial documents and run AI-powered credit appraisal</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Left panel ── */}
        <div className="lg:col-span-2 space-y-5">
          {/* Company */}
          <div className="glass rounded-2xl p-6 border border-dark-border">
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              <Building2 className="w-4 h-4 inline mr-2 text-neon" />
              Company Name *
            </label>
            <input
              className="input-dark w-full rounded-xl px-4 py-3 text-sm"
              placeholder="e.g. Tata Steel Ltd, Bharat Forge Ltd"
              value={company}
              onChange={e => setCompany(e.target.value)}
            />
          </div>

          {/* Dropzone */}
          <div className="glass rounded-2xl p-6 border border-dark-border">
            <p className="text-sm font-semibold text-slate-300 mb-3">
              <Upload className="w-4 h-4 inline mr-2 text-neon" />
              Upload Documents
            </p>
            <div {...getRootProps()} className={`
              border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
              ${isDragActive ? 'border-neon bg-neon/5' : 'border-dark-border hover:border-neon/40'}
            `}>
              <input {...getInputProps()} />
              <Upload className="w-8 h-8 text-neon mx-auto mb-3" />
              <p className="text-white font-semibold text-sm">
                {isDragActive ? 'Drop files here' : 'Drag & drop or click to browse'}
              </p>
              <p className="text-slate-500 text-xs mt-1">PDF, CSV, XLSX — Annual Report, GST Return, Bank Statement</p>
            </div>

            {/* File list */}
            {files.length > 0 && (
              <div className="mt-4 space-y-2">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-3 bg-dark/50 rounded-lg px-3 py-2">
                    <FileText className="w-4 h-4 text-neon flex-shrink-0" />
                    <span className="text-sm text-slate-300 truncate flex-1">{f.name}</span>
                    {f.status === 'uploaded'
                      ? <CheckCircle className="w-4 h-4 text-neon" />
                      : <button onClick={() => removeFile(i)}><Trash2 className="w-4 h-4 text-red-400 hover:text-red-300" /></button>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Qualitative notes */}
          <div className="glass rounded-2xl p-6 border border-dark-border">
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Officer Qualitative Notes
              <span className="text-slate-500 font-normal ml-2">(optional — factory visit, management interview)</span>
            </label>
            <textarea
              rows={4}
              className="input-dark w-full rounded-xl px-4 py-3 text-sm resize-none"
              placeholder="e.g. Factory found operating at 40% capacity. Management was evasive about receivables. New export contract signed worth ₹80 Crore..."
              value={notes}
              onChange={e => setNotes(e.target.value)}
            />
            <p className="text-xs text-slate-500 mt-1">
              Keywords like "strong management", "low capacity", "expanding" affect the risk score.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
              className="flex-1 py-3 rounded-xl font-semibold text-sm border border-neon/30 text-neon hover:bg-neon/10 disabled:opacity-40 transition-all flex items-center justify-center gap-2"
            >
              {uploading ? <div className="w-4 h-4 border-2 border-neon border-t-transparent rounded-full animate-spin" /> : <Upload className="w-4 h-4" />}
              {uploading ? 'Uploading…' : '1. Upload Documents'}
            </button>
            <button
              onClick={handleAnalyse}
              disabled={analyzing || !sessionId}
              className="flex-1 py-3 rounded-xl font-bold text-sm bg-neon text-dark hover:bg-neon-dark disabled:opacity-40 transition-all flex items-center justify-center gap-2 neon-glow"
            >
              {analyzing ? <div className="w-4 h-4 border-2 border-dark border-t-transparent rounded-full animate-spin" /> : <Play className="w-4 h-4" />}
              {analyzing ? 'Analysing…' : '2. Run Credit Analysis'}
            </button>
          </div>

          {/* Analysis progress */}
          {analyzing && (
            <div className="glass rounded-2xl p-6 border border-neon/20 bg-neon/5">
              <div className="flex items-center gap-3 mb-4">
                <Cpu className="w-5 h-5 text-neon animate-pulse" />
                <p className="font-semibold text-white text-sm">AI Engine Processing…</p>
                <span className="ml-auto text-xs text-neon font-mono">{stepIdx + 1}/{STEPS.length}</span>
              </div>
              <div className="w-full bg-dark rounded-full h-1.5 mb-4">
                <div
                  className="h-1.5 bg-neon rounded-full transition-all duration-500"
                  style={{ width: `${((stepIdx + 1) / STEPS.length) * 100}%` }}
                />
              </div>
              <div className="space-y-1.5">
                {STEPS.map((s, i) => (
                  <div key={i} className={`flex items-center gap-2 text-xs transition-all ${i < stepIdx ? 'text-neon' : i === stepIdx ? 'text-white' : 'text-slate-600'}`}>
                    {i < stepIdx
                      ? <CheckCircle className="w-3 h-3 text-neon flex-shrink-0" />
                      : i === stepIdx
                        ? <div className="w-3 h-3 border border-neon border-t-transparent rounded-full animate-spin flex-shrink-0" />
                        : <div className="w-3 h-3 rounded-full border border-slate-700 flex-shrink-0" />}
                    {s}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Right panel — history ── */}
        <div className="space-y-4">
          <div className="glass rounded-2xl p-5 border border-dark-border">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-neon" />
              Recent Analyses
            </h3>
            {history.length === 0 ? (
              <p className="text-slate-500 text-xs text-center py-6">No analyses yet.<br />Run your first credit analysis.</p>
            ) : (
              <div className="space-y-2">
                {history.slice(0, 8).map((h) => (
                  <button
                    key={h.session_id}
                    onClick={() => navigate(`/analysis/${h.session_id}`)}
                    className="w-full text-left p-3 rounded-xl bg-dark/50 hover:bg-dark border border-dark-border hover:border-neon/30 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-white group-hover:text-neon truncate">{h.company_name}</p>
                      <RiskBadge decision={h.decision} size="sm" />
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-500">Score: {h.risk_score?.toFixed(1)}</span>
                      {h.scoring_method === 'XGBoost ML Model' && (
                        <span className="text-xs text-neon flex items-center gap-1">
                          <Zap className="w-2.5 h-2.5" />ML
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">{new Date(h.created_at).toLocaleDateString('en-IN')}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Quick guide */}
          <div className="glass rounded-2xl p-5 border border-dark-border">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4 text-neon" />
              Quick Guide
            </h3>
            <ol className="space-y-2 text-xs text-slate-400">
              {[
                'Enter company name',
                'Upload Annual Report PDF',
                'Upload GST Return PDF',
                'Upload Bank Statement PDF',
                'Add officer notes (optional)',
                'Click Upload Documents',
                'Click Run Credit Analysis',
                'View risk score & decision',
                'Download CAM PDF report',
              ].map((s, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-neon font-bold flex-shrink-0">{i + 1}.</span>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}
