import api from './axiosInstance'

// Register a new customer account
export const registerCustomer = (name, email, password) =>
  api.post('/customer/register', { name, email, password })

// Login as a customer
export const loginCustomer = (email, password) =>
  api.post('/customer/login', { email, password })

// Refresh access token using refresh token
export const refreshCustomerToken = (refresh_token) =>
  api.post('/customer/refresh', { refresh_token })

// Logout - revokes the refresh token
export const logoutCustomer = (refresh_token) =>
  api.post('/customer/logout', { refresh_token })

// Get current customer profile (protected)
export const getCustomerProfile = () =>
  api.get('/customer/me')
