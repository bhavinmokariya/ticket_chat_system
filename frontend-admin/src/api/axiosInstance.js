import axios from 'axios'

// Points to the SAME backend but uses /staff routes
const BASE_URL = 'http://localhost:8000/api/auth'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ─────────────────────────────────────────────
// REQUEST INTERCEPTOR
// Automatically attaches the access token to every request.
// ─────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('staff_access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─────────────────────────────────────────────
// RESPONSE INTERCEPTOR
// On 401 errors, attempts to refresh the access token automatically.
// If refresh fails, clears storage and redirects to /login.
// ─────────────────────────────────────────────
let isRefreshing = false
let failedRequestsQueue = []

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

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
      const refreshToken = localStorage.getItem('staff_refresh_token')

      if (!refreshToken) {
        clearAuthAndRedirect()
        return Promise.reject(error)
      }

      try {
        const response = await axios.post(`${BASE_URL}/staff/refresh`, {
          refresh_token: refreshToken,
        })

        const newAccessToken = response.data.access_token
        localStorage.setItem('staff_access_token', newAccessToken)

        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`

        failedRequestsQueue.forEach(({ resolve }) => resolve(newAccessToken))
        failedRequestsQueue = []

        return api(originalRequest)
      } catch (refreshError) {
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
  localStorage.removeItem('staff_access_token')
  localStorage.removeItem('staff_refresh_token')
  localStorage.removeItem('staff_user')
  window.location.href = '/login'
}

export default api
