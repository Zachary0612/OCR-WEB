import axios from 'axios'

const authApi = axios.create({ baseURL: '/api/auth' })

export const getAuthStatus = () => authApi.get('/me')

export const login = (username, password) => authApi.post('/login', { username, password })

export const logout = () => authApi.post('/logout')
