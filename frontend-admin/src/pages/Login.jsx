import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Login.module.css'

export default function Login() {
  const { login, loading, error, clearError, user } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', password: '' })
  const [localError, setLocalError] = useState('')

  // Already logged in → go to dashboard
  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true })
  }, [user, navigate])

  useEffect(() => {
    if (error) setLocalError(error)
  }, [error])

  const handleChange = (e) => {
    clearError()
    setLocalError('')
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLocalError('')
    if (!form.email || !form.password) {
      setLocalError('Please enter your email and password.')
      return
    }
    const result = await login(form.email, form.password)
    if (result.success) {
      navigate('/dashboard', { replace: true })
    }
  }

  return (
    <div className={styles.page}>
      {/* ── Left decorative panel ── */}
      <aside className={styles.panel}>
        <div className={styles.panelGlow} />
        <div className={styles.panelGlow2} />

        <div className={styles.panelBrand}>
          <div className={styles.panelLogo}>S</div>
          <span className={styles.panelBrandName}>StaffOps</span>
        </div>

        <div className={styles.panelCenter}>
          <h2 className={styles.panelHeading}>
            Internal<br /><span>Staff Portal</span>
          </h2>
          <p className={styles.panelDesc}>
            Restricted access for authorised staff only.
            Contact your administrator if you need an account.
          </p>

          <div className={styles.featureList}>
            <div className={styles.featureItem}>
              <div className={styles.featureIcon}>🛡️</div>
              Role-based access control (Admin / Support)
            </div>
            <div className={styles.featureItem}>
              <div className={styles.featureIcon}>🔑</div>
              JWT with auto-refresh (15 min access tokens)
            </div>
            <div className={styles.featureItem}>
              <div className={styles.featureIcon}>📋</div>
              Ticket management & customer support tools
            </div>
            <div className={styles.featureItem}>
              <div className={styles.featureIcon}>📊</div>
              Admin reports & team management
            </div>
          </div>
        </div>

        <p className={styles.panelFooter}>
          © 2025 StaffOps · Internal use only
        </p>
      </aside>

      {/* ── Right form side ── */}
      <div className={styles.formSide}>
        <div className={styles.card}>
          <div className={styles.header}>
            <div className={styles.headerBadge}>
              <div className={styles.headerDot} />
              Staff Access
            </div>
            <h1 className={styles.title}>Welcome back</h1>
            <p className={styles.subtitle}>
              Sign in with your company credentials to continue.
            </p>
          </div>

          {localError && (
            <div className={styles.errorBox}>
              <span>⚠</span> {localError}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.field}>
              <label className={styles.label}>Company Email</label>
              <div className={styles.inputWrap}>
                <span className={styles.inputIcon}>✉</span>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="you@company.com"
                  className={styles.input}
                  autoComplete="email"
                  disabled={loading}
                />
              </div>
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Password</label>
              <div className={styles.inputWrap}>
                <span className={styles.inputIcon}>🔒</span>
                <input
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className={styles.input}
                  autoComplete="current-password"
                  disabled={loading}
                />
              </div>
            </div>

            <button type="submit" className={styles.button} disabled={loading}>
              {loading ? (
                <span className={styles.spinner} />
              ) : (
                <>Sign In to Staff Portal →</>
              )}
            </button>
          </form>

          <div className={styles.helpNote}>
            <strong>No self-registration.</strong> Staff accounts are created by
            administrators only. Contact{' '}
            <strong>arjun@company.com</strong> to request access.
          </div>
        </div>
      </div>
    </div>
  )
}
