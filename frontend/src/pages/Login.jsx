import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, Eye, EyeOff, ArrowRight, Shield } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'credit_officer' })
  const { login, register, demoLogin } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(form.name, form.email, form.password, form.role)
      }
      toast.success(`Welcome to Intelli-Credit!`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = async () => {
    setLoading(true)
    try {
      await demoLogin()
      toast.success('Demo login successful!')
      navigate('/dashboard')
    } catch {
      toast.error('Demo login failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark grid-bg flex items-center justify-center px-4">
      <div className="absolute top-20 left-1/4 w-72 h-72 bg-neon/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-20 right-1/4 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2">
            <div className="w-10 h-10 bg-neon rounded-xl flex items-center justify-center neon-glow">
              <Zap className="w-6 h-6 text-dark" />
            </div>
            <span className="font-black text-2xl text-white">Intelli<span className="text-neon">Credit</span></span>
          </Link>
          <p className="text-slate-400 text-sm mt-2">AI Credit Decisioning Platform</p>
        </div>

        <div className="glass rounded-2xl p-8 border border-dark-border">
          {/* Tabs */}
          <div className="flex gap-1 mb-8 bg-dark-card rounded-xl p-1">
            {['login', 'register'].map(m => (
              <button key={m} onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
                  mode === m ? 'bg-neon text-dark' : 'text-slate-400 hover:text-white'
                }`}>
                {m === 'login' ? 'Sign In' : 'Register'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Full Name</label>
                <input type="text" required value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="Rajesh Kumar"
                  className="input-dark w-full px-4 py-3 rounded-xl text-sm" />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email Address</label>
              <input type="email" required value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="officer@bank.com"
                className="input-dark w-full px-4 py-3 rounded-xl text-sm" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <input type={showPass ? 'text' : 'password'} required value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••"
                  className="input-dark w-full px-4 py-3 pr-10 rounded-xl text-sm" />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Role</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
                  className="input-dark w-full px-4 py-3 rounded-xl text-sm">
                  <option value="credit_officer">Credit Officer</option>
                  <option value="manager">Credit Manager</option>
                </select>
              </div>
            )}

            <button type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-neon text-dark py-3 rounded-xl font-bold text-sm hover:bg-neon-dark transition-all neon-glow disabled:opacity-50 mt-2">
              {loading ? (
                <div className="w-4 h-4 border-2 border-dark border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-dark-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-dark-card px-3 text-slate-500">or continue with</span>
            </div>
          </div>

          <button onClick={handleDemo} disabled={loading}
            className="w-full flex items-center justify-center gap-2 border border-neon/30 text-neon py-3 rounded-xl font-semibold text-sm hover:bg-neon/5 transition-all">
            <Shield className="w-4 h-4" />
            Try Demo Account
          </button>
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">
          By continuing, you agree to use this platform for authorized credit analysis only.
        </p>
      </div>
    </div>
  )
}
