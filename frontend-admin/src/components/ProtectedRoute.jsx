import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Protects routes from unauthenticated access.
 * Optionally restricts to specific roles.
 *
 * Props:
 *   children   - The component to render if allowed
 *   roles      - Array of allowed roles e.g. ['admin'] or ['admin','support']
 *                If omitted, any authenticated user is allowed.
 */
export default function ProtectedRoute({ children, roles }) {
  const { user } = useAuth()

  // Not logged in → redirect to login
  if (!user) return <Navigate to="/login" replace />

  // Role restriction: if roles specified, check user's role
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}
