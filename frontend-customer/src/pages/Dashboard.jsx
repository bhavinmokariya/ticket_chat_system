import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getCustomerProfile } from '../api/auth'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [profileError, setProfileError] = useState('')

  // Fetch the full profile from the protected /me endpoint
  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await getCustomerProfile()
        setProfile(res.data)
      } catch {
        setProfileError('Could not load profile data.')
      } finally {
        setLoadingProfile(false)
      }
    }
    fetchProfile()
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  }

  return (
    <div className={styles.page}>
      {/* Top Navigation */}
      <nav className={styles.nav}>
        <div className={styles.navBrand}>
          <div className={styles.navLogo}>C</div>
          <span className={styles.navTitle}>Customer Portal</span>
        </div>
        <div className={styles.navRight}>
          <span className={styles.navRole}>Customer</span>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Welcome Header */}
        <div className={styles.welcomeSection}>
          <div className={styles.avatarCircle}>
            {user?.name?.charAt(0)?.toUpperCase() || 'C'}
          </div>
          <div>
            <h1 className={styles.welcomeTitle}>
              Welcome back, {user?.name?.split(' ')[0]}! 👋
            </h1>
            <p className={styles.welcomeSub}>Here's your account overview</p>
          </div>
        </div>

        {/* Profile Card */}
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Account Details</h2>
            {loadingProfile ? (
              <div className={styles.loadingBlock}>
                <div className={styles.skeletonLine} />
                <div className={styles.skeletonLine} style={{ width: '70%' }} />
                <div className={styles.skeletonLine} style={{ width: '55%' }} />
              </div>
            ) : profileError ? (
              <p className={styles.errorText}>{profileError}</p>
            ) : (
              <div className={styles.profileList}>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Full Name</span>
                  <span className={styles.profileVal}>{profile?.name}</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Email</span>
                  <span className={styles.profileVal}>{profile?.email}</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Customer ID</span>
                  <span className={styles.profileVal}>#{profile?.customer_id}</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Account Status</span>
                  <span className={`${styles.profileVal} ${styles.badge} ${profile?.is_active ? styles.badgeGreen : styles.badgeRed}`}>
                    {profile?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Joined</span>
                  <span className={styles.profileVal}>{formatDate(profile?.created_at)}</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Last Login</span>
                  <span className={styles.profileVal}>{formatDate(profile?.last_login)}</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Stats Card */}
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Session Info</h2>
            <div className={styles.profileList}>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Role</span>
                <span className={`${styles.profileVal} ${styles.badge} ${styles.badgeBlue}`}>
                  {user?.role}
                </span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Auth Type</span>
                <span className={styles.profileVal}>JWT Bearer</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Token Expiry</span>
                <span className={styles.profileVal}>15 minutes</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Refresh Token</span>
                <span className={styles.profileVal}>7 days (auto-renew)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Info Banner */}
        <div className={styles.infoBanner}>
          <div className={styles.infoIcon}>🔒</div>
          <div>
            <strong>Your session is secure.</strong> Access tokens expire every 15 minutes and are automatically refreshed using your refresh token stored securely.
          </div>
        </div>
      </main>
    </div>
  )
}
