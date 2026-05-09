import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import RiskAnalysis from './pages/RiskAnalysis'
import Explainability from './pages/Explainability'
import CAMReport from './pages/CAMReport'
import Layout from './components/Layout'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen bg-dark flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-2 border-neon border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Loading Intelli-Credit...</p>
      </div>
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
      <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/analysis/:sessionId" element={<ProtectedRoute><Layout><RiskAnalysis /></Layout></ProtectedRoute>} />
      <Route path="/explainability/:sessionId" element={<ProtectedRoute><Layout><Explainability /></Layout></ProtectedRoute>} />
      <Route path="/cam/:sessionId" element={<ProtectedRoute><Layout><CAMReport /></Layout></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: '#1a2236', color: '#e2e8f0', border: '1px solid rgba(34,197,94,0.2)' },
            success: { iconTheme: { primary: '#22c55e', secondary: '#0a0f1a' } },
            error: { iconTheme: { primary: '#ef4444', secondary: '#0a0f1a' } },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  )
}
