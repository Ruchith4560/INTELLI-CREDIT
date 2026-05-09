import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ArrowRight, Shield, Brain, FileSearch, TrendingUp, Zap, CheckCircle, BarChart3, Globe, Lock } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Landing() {
  const { user, demoLogin } = useAuth()
  const navigate = useNavigate()

  const handleDemo = async () => {
    try {
      toast.loading('Logging in as demo user...')
      await demoLogin()
      toast.dismiss()
      toast.success('Welcome to Intelli-Credit!')
      navigate('/dashboard')
    } catch (e) {
      toast.dismiss()
      toast.error('Demo login failed. Is the backend running?')
    }
  }

  const features = [
    { icon: FileSearch, title: 'Automated CAM Generation', desc: 'AI generates comprehensive Credit Appraisal Memos from multi-source documents in minutes.' },
    { icon: Brain, title: 'Explainable AI', desc: 'SHAP-based feature importance shows exactly why a credit decision was made. No black boxes.' },
    { icon: Globe, title: 'Regulatory Intelligence', desc: 'RAG-powered knowledge base with RBI and GST rules for India-specific compliance analysis.' },
    { icon: BarChart3, title: 'Risk Dashboard', desc: 'Real-time financial ratios, GST mismatch detection, and news sentiment analysis.' },
    { icon: Shield, title: 'GSTR-2A vs 3B Analysis', desc: 'Automatic cross-verification of GST returns to detect circular trading and revenue inflation.' },
    { icon: Lock, title: 'Secure & Auditable', desc: 'JWT authentication, RBAC controls, and complete audit trails for regulatory compliance.' },
  ]

  const stats = [
    { value: '< 2 min', label: 'CAM Generation Time', sub: 'vs 2-3 weeks manual' },
    { value: '94.2%', label: 'Accuracy Score', sub: 'on historical data' },
    { value: '5 Cs', label: 'Credit Framework', sub: 'fully automated' },
    { value: '∞', label: 'Scalability', sub: 'concurrent analyses' },
  ]

  return (
    <div className="min-h-screen bg-dark grid-bg text-white overflow-x-hidden">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 glass border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-neon rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-dark" />
            </div>
            <span className="font-bold text-xl">Intelli<span className="text-neon">Credit</span></span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <a href="#features" className="hover:text-neon transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-neon transition-colors">How It Works</a>
            <a href="#stats" className="hover:text-neon transition-colors">Stats</a>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <Link to="/dashboard"
                className="flex items-center gap-2 bg-neon text-dark px-4 py-2 rounded-lg font-semibold text-sm hover:bg-neon-dark transition-colors">
                Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-slate-400 hover:text-white text-sm transition-colors">Sign In</Link>
                <button onClick={handleDemo}
                  className="bg-neon text-dark px-4 py-2 rounded-lg font-semibold text-sm hover:bg-neon-dark transition-all neon-glow">
                  Try Demo
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        {/* Background orbs */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-neon/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-7xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neon/10 border border-neon/20 text-neon text-sm font-medium mb-8">
            <div className="w-2 h-2 bg-neon rounded-full animate-pulse" />
            AI-Powered Credit Intelligence for Indian Banks
          </div>

          <h1 className="text-5xl md:text-7xl font-black mb-6 leading-tight">
            <span className="text-white">Next-Gen Corporate</span><br />
            <span className="gradient-text neon-text">Credit Appraisal</span><br />
            <span className="text-white">Platform</span>
          </h1>

          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Automate end-to-end Credit Appraisal Memos. Upload GST, ITR, Bank Statements & Annual Reports.
            Get AI-powered decisions with full explainability in minutes.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <button onClick={handleDemo}
              className="flex items-center gap-2 bg-neon text-dark px-8 py-4 rounded-xl font-bold text-lg hover:bg-neon-dark transition-all neon-glow group">
              Start Credit Analysis
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <Link to="/login"
              className="flex items-center gap-2 border border-dark-border px-8 py-4 rounded-xl font-semibold text-lg hover:border-neon/30 hover:bg-dark-card transition-all">
              Upload Documents
            </Link>
          </div>

          {/* Mock dashboard preview */}
          <div className="relative max-w-5xl mx-auto">
            <div className="glass rounded-2xl border border-dark-border p-6 neon-glow">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-neon" />
                <span className="text-xs text-slate-500 ml-2 font-mono">intelli-credit.ai/dashboard</span>
              </div>
              <div className="grid grid-cols-4 gap-3 mb-4">
                {['Risk Score: 34.2', 'Decision: APPROVE', 'Loan: ₹42 Cr', 'Rate: 10.5%'].map((item, i) => (
                  <div key={i} className="bg-dark-card rounded-xl p-4 border border-dark-border">
                    <div className={`text-sm font-bold ${i === 1 ? 'text-neon' : 'text-white'}`}>{item}</div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3">
                {['Financial Ratios', 'GST Analysis', 'Research Intel'].map((item, i) => (
                  <div key={i} className="bg-dark-card rounded-xl p-4 border border-dark-border h-20 flex items-end">
                    <div className="flex gap-1 items-end w-full">
                      {[40,65,45,70,55,80,60].map((h, j) => (
                        <div key={j} className="flex-1 bg-neon/30 rounded-sm"
                          style={{ height: `${h * 0.5}px`, background: j === 5 ? '#22c55e' : undefined }} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section id="stats" className="py-20 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <div key={i} className="glass rounded-2xl p-6 text-center border border-dark-border card-hover">
              <div className="text-4xl font-black text-neon mb-2">{stat.value}</div>
              <div className="text-white font-semibold text-sm">{stat.label}</div>
              <div className="text-slate-500 text-xs mt-1">{stat.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black mb-4">Enterprise-Grade <span className="gradient-text">AI Features</span></h2>
            <p className="text-slate-400 text-lg max-w-xl mx-auto">Built for Indian banking context with deep regulatory intelligence</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => {
              const Icon = f.icon
              return (
                <div key={i} className="glass rounded-2xl p-6 border border-dark-border card-hover cursor-default">
                  <div className="w-12 h-12 bg-neon/10 rounded-xl flex items-center justify-center mb-4 border border-neon/20">
                    <Icon className="w-6 h-6 text-neon" />
                  </div>
                  <h3 className="text-white font-bold text-lg mb-2">{f.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black mb-4">How <span className="gradient-text">Intelli-Credit</span> Works</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
            {[
              { step: '01', title: 'Upload Documents', desc: 'GST, ITR, Bank Statements, Annual Reports' },
              { step: '→', title: '', desc: '', arrow: true },
              { step: '02', title: 'AI Extraction', desc: 'NLP + OCR extracts structured financial data' },
              { step: '→', title: '', desc: '', arrow: true },
              { step: '03', title: 'Research Agents', desc: 'Multi-agent web research and compliance check' },
            ].map((s, i) => s.arrow ? (
              <div key={i} className="text-neon text-3xl text-center hidden md:block">→</div>
            ) : (
              <div key={i} className="glass rounded-2xl p-6 border border-dark-border text-center">
                <div className="text-3xl font-black text-neon mb-3">{s.step}</div>
                <div className="text-white font-bold mb-2">{s.title}</div>
                <div className="text-slate-400 text-sm">{s.desc}</div>
              </div>
            ))}
          </div>
          <div className="text-center mt-6 text-neon text-3xl">↓</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            {[
              { step: '04', title: 'Risk Scoring', desc: 'XGBoost + Rule engine computes final credit score' },
              { step: '05', title: 'Explainability', desc: 'SHAP values + LLM explains every decision' },
              { step: '06', title: 'CAM Report', desc: 'Download professional PDF Credit Appraisal Memo' },
            ].map((s, i) => (
              <div key={i} className="glass rounded-2xl p-6 border border-neon/20 text-center bg-neon/5">
                <div className="text-3xl font-black text-neon mb-3">{s.step}</div>
                <div className="text-white font-bold mb-2">{s.title}</div>
                <div className="text-slate-400 text-sm">{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center glass rounded-3xl p-12 border border-neon/20 bg-neon/5 neon-glow">
          <h2 className="text-4xl font-black mb-4">Ready to Transform <span className="gradient-text">Credit Appraisal?</span></h2>
          <p className="text-slate-400 mb-8">Start with a demo. No setup required.</p>
          <button onClick={handleDemo}
            className="inline-flex items-center gap-2 bg-neon text-dark px-10 py-4 rounded-xl font-bold text-lg hover:bg-neon-dark transition-all neon-glow">
            Launch Demo Platform <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-border py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-neon rounded-md flex items-center justify-center">
              <Zap className="w-4 h-4 text-dark" />
            </div>
            <span className="font-bold text-white">Intelli<span className="text-neon">Credit</span></span>
          </div>
          <p className="text-slate-500 text-sm">AI-Powered Credit Decisioning | Built for the Intelli-Credit Hackathon</p>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <CheckCircle className="w-3 h-3 text-neon" />
            <span>RBI Compliant Framework</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
