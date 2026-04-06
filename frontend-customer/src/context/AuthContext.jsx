import { createContext, useContext, useState, useCallback } from 'react'
import { loginCustomer, logoutCustomer, registerCustomer } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Initialize state from localStorage so refresh doesn't log user out
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // ── Register ──────────────────────────────
  const register = useCallback(async (name, email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await registerCustomer(name, email, password)
      return { success: true, message: res.data.message }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed.'
      setError(msg)
      return { success: false, message: msg }
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Login ─────────────────────────────────
  const login = useCallback(async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await loginCustomer(email, password)
      const { access_token, refresh_token, role, name } = res.data

      // Persist tokens and user info
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      const userData = { name, email, role }
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)

      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check credentials.'
      setError(msg)
      return { success: false, message: msg }
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Logout ────────────────────────────────
  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    try {
      if (refreshToken) {
        await logoutCustomer(refreshToken)
      }
    } catch {
      // Even if the API call fails, clear local state
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      setUser(null)
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return (
    <AuthContext.Provider value={{ user, loading, error, register, login, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook for easy access
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
