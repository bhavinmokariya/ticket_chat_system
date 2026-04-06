import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getStaffProfile } from '../api/auth'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [profileError, setProfileError] = useState('')

  const isAdmin = user?.role === 'admin'

  // Fetch full profile from protected /staff/me endpoint
  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await getStaffProfile()
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

  // Role-based permissions map
  const rolePermissions = {
    admin: [
      'create_ticket', 'view_all_tickets', 'take_ticket',
      'send_message', 'resolve_ticket', 'close_ticket',
      'manage_users', 'view_reports',
    ],
    support: [
      'create_ticket', 'view_all_tickets', 'take_ticket',
      'send_message', 'resolve_ticket',
    ],
  }
  const permissions = rolePermissions[user?.role] || []

  return (
    <div className={styles.page}>

      {/* ── Top Navigation ── */}
      <nav className={styles.nav}>
        <div className={styles.navLeft}>
          <div className={styles.navLogo}>S</div>
          <span className={styles.navTitle}>StaffOps</span>
          <div className={styles.navDivider} />
          <span className={styles.navSubtitle}>
            {isAdmin ? 'Admin Console' : 'Support Dashboard'}
          </span>
        </div>

        <div className={styles.navRight}>
          <div className={`${styles.roleBadge} ${isAdmin ? styles.roleBadgeAdmin : styles.roleBadgeSupport}`}>
            <span className={styles.roleDot} />
            {user?.role}
          </div>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className={styles.main}>

        {/* Welcome Row */}
        <div className={styles.welcomeRow}>
          <div className={styles.welcomeLeft}>
            <div className={`${styles.avatar} ${isAdmin ? styles.avatarAdmin : styles.avatarSupport}`}>
              {user?.name?.charAt(0)?.toUpperCase() || 'S'}
            </div>
            <div>
              <h1 className={styles.welcomeTitle}>
                Hey, {user?.name?.split(' ')[0]} 👋
              </h1>
              <p className={styles.welcomeSub}>
                {isAdmin ? 'You have full admin access.' : 'You are logged in as Support Engineer.'}
              </p>
            </div>
          </div>

          <div className={styles.statusPill}>
            <span className={styles.statusDot} />
            Online
          </div>
        </div>

        {/* Stats Row */}
        <div className={styles.statsRow}>
          <div className={styles.statCard}>
            <div className={styles.statIcon}>🎫</div>
            <div className={styles.statValue}>—</div>
            <div className={styles.statLabel}>Open Tickets</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statIcon}>✅</div>
            <div className={styles.statValue}>—</div>
            <div className={styles.statLabel}>Resolved Today</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statIcon}>⏱️</div>
            <div className={styles.statValue}>—</div>
            <div className={styles.statLabel}>Avg. Response</div>
          </div>
          {isAdmin ? (
            <div className={styles.statCard}>
              <div className={styles.statIcon}>👥</div>
              <div className={styles.statValue}>—</div>
              <div className={styles.statLabel}>Total Customers</div>
            </div>
          ) : (
            <div className={styles.statCard}>
              <div className={styles.statIcon}>📬</div>
              <div className={styles.statValue}>—</div>
              <div className={styles.statLabel}>My Assigned</div>
            </div>
          )}
        </div>

        {/* Profile + Session Cards */}
        <div className={styles.grid}>

          {/* Profile Card */}
          <div className={styles.card}>
            <div className={styles.cardTitle}>Account Details</div>

            {loadingProfile ? (
              <>
                <div className={styles.skeletonLine} />
                <div className={styles.skeletonLine} style={{ width: '75%' }} />
                <div className={styles.skeletonLine} style={{ width: '55%' }} />
                <div className={styles.skeletonLine} style={{ width: '65%' }} />
              </>
            ) : profileError ? (
              <p className={styles.errorText}>{profileError}</p>
            ) : (
              <div className={styles.profileList}>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Full Name</span>
                  <span className={`${styles.profileVal} ${styles.profileValNormal}`}>
                    {profile?.name}
                  </span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Email</span>
                  <span className={styles.profileVal}>{profile?.email}</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Staff ID</span>
                  <span className={styles.profileVal}>#{profile?.support_id}</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Department</span>
                  <span className={`${styles.profileVal} ${styles.profileValNormal}`}>
                    {profile?.department}
                  </span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Role</span>
                  <span className={`${styles.badge} ${isAdmin ? styles.badgeAdmin : styles.badgeSupport}`}>
                    {user?.role}
                  </span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Status</span>
                  <span className={`${styles.badge} ${styles.badgeGreen}`}>Active</span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Last Seen</span>
                  <span className={`${styles.profileVal} ${styles.profileValNormal}`}>
                    {formatDate(profile?.last_seen)}
                  </span>
                </div>
                <div className={styles.profileRow}>
                  <span className={styles.profileKey}>Joined</span>
                  <span className={`${styles.profileVal} ${styles.profileValNormal}`}>
                    {formatDate(profile?.created_at)}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Session & Permissions Card */}
          <div className={styles.card}>
            <div className={styles.cardTitle}>Session & Permissions</div>
            <div className={styles.profileList}>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Auth Method</span>
                <span className={styles.profileVal}>JWT Bearer</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Access Token</span>
                <span className={styles.profileVal}>15 min expiry</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Refresh Token</span>
                <span className={styles.profileVal}>7 days (auto)</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileKey}>Role Level</span>
                <span className={`${styles.badge} ${isAdmin ? styles.badgeAdmin : styles.badgeSupport}`}>
                  {isAdmin ? 'Full Admin' : 'Support Engineer'}
                </span>
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <div className={styles.cardTitle}>Your Permissions</div>
              <div className={styles.permGrid}>
                {permissions.map((perm) => (
                  <span key={perm} className={styles.permTag}>{perm}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Admin-only Section */}
        {isAdmin && (
          <div className={styles.adminSection}>
            <div className={styles.adminSectionTitle}>
              🔐 Admin Controls
            </div>
            <div className={styles.adminQuickLinks}>
              <button className={styles.adminLink}>
                👥 Manage Staff
              </button>
              <button className={styles.adminLink}>
                📊 View Reports
              </button>
              <button className={styles.adminLink}>
                🎫 All Tickets
              </button>
              <button className={styles.adminLink}>
                ⚙️ System Settings
              </button>
              <button className={styles.adminLink}>
                📋 Audit Logs
              </button>
            </div>
          </div>
        )}

        {/* Info Notice */}
        <div className={styles.notice} style={{ marginTop: 18 }}>
          <span className={styles.noticeIcon}>🔒</span>
          <div>
            <strong>Secure session active.</strong> Your access token refreshes automatically every 15 minutes.
            {isAdmin
              ? ' As an admin, you have unrestricted access to all system features.'
              : ' You have access to ticket management and customer support tools.'}
          </div>
        </div>

      </main>
    </div>
  )
}
