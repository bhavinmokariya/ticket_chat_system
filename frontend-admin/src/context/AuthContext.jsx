import { createContext, useContext, useState, useCallback } from 'react'
import { loginStaff, logoutStaff } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Read from localStorage so page refresh doesn't log user out
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('staff_user')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // ── Login ─────────────────────────────────
  const login = useCallback(async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await loginStaff(email, password)
      const { access_token, refresh_token, role, name } = res.data

      // Store with "staff_" prefix to avoid clash with customer portal
      localStorage.setItem('staff_access_token', access_token)
      localStorage.setItem('staff_refresh_token', refresh_token)
      const userData = { name, email, role }
      localStorage.setItem('staff_user', JSON.stringify(userData))
      setUser(userData)

      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check your credentials.'
      setError(msg)
      return { success: false, message: msg }
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Logout ────────────────────────────────
  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('staff_refresh_token')
    try {
      if (refreshToken) {
        await logoutStaff(refreshToken)
      }
    } catch {
      // Clear state even if API call fails
    } finally {
      localStorage.removeItem('staff_access_token')
      localStorage.removeItem('staff_refresh_token')
      localStorage.removeItem('staff_user')
      setUser(null)
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
