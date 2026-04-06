import api from './axiosInstance'

// Login as admin or support engineer
export const loginStaff = (email, password) =>
  api.post('/staff/login', { email, password })

// Refresh access token
export const refreshStaffToken = (refresh_token) =>
  api.post('/staff/refresh', { refresh_token })

// Logout - revokes refresh token
export const logoutStaff = (refresh_token) =>
  api.post('/staff/logout', { refresh_token })

// Get current staff member profile (protected)
export const getStaffProfile = () =>
  api.get('/staff/me')
