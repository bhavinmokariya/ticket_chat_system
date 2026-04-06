import axios from 'axios'

// Base URL pointing to FastAPI backend
const BASE_URL = 'http://localhost:8000/api/auth'

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ─────────────────────────────────────────────
// REQUEST INTERCEPTOR
// Attaches the access token to every request automatically.
// ─────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─────────────────────────────────────────────
// RESPONSE INTERCEPTOR
// Handles 401 errors by automatically refreshing the access token.
// If refresh fails, clears storage and redirects to login.
// ─────────────────────────────────────────────
let isRefreshing = false
let failedRequestsQueue = []

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If error is 401 and we haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // If a refresh is already in-flight, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedRequestsQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      isRefreshing = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // No refresh token - clear everything and redirect
        clearAuthAndRedirect()
        return Promise.reject(error)
      }

      try {
        // Call the refresh endpoint
        const response = await axios.post(`${BASE_URL}/customer/refresh`, {
          refresh_token: refreshToken,
        })

        const newAccessToken = response.data.access_token
        localStorage.setItem('access_token', newAccessToken)

        // Update original request header and retry
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`

        // Retry all queued requests with the new token
        failedRequestsQueue.forEach(({ resolve }) => resolve(newAccessToken))
        failedRequestsQueue = []

        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed - logout
        failedRequestsQueue.forEach(({ reject }) => reject(refreshError))
        failedRequestsQueue = []
        clearAuthAndRedirect()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

function clearAuthAndRedirect() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  window.location.href = '/login'
}

export default api
