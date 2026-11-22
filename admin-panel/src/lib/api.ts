import axios from 'axios'
import { clearTokens, getTokens, saveTokens, type AuthTokens } from '../auth/tokenStore'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const tokens = getTokens()
  if (tokens?.access_token) {
    config.headers.Authorization = `Bearer ${tokens.access_token}`
  }
  return config
})

let refreshRequest: Promise<AuthTokens> | null = null

export function refreshSessionTokens() {
  refreshRequest ??= (async () => {
    const tokens = getTokens()
    if (!tokens?.refresh_token) throw new Error('Sessao sem refresh token')

    const { data } = await axios.post<AuthTokens>(
      `${api.defaults.baseURL}/auth/refresh`,
      { refresh_token: tokens.refresh_token },
    )
    const storedTokens = saveTokens(data)
    window.dispatchEvent(new CustomEvent<AuthTokens>('auth:tokens', { detail: storedTokens }))
    return storedTokens
  })().catch((error: unknown) => {
    clearTokens()
    window.dispatchEvent(new Event('auth:logout'))
    throw error
  }).finally(() => { refreshRequest = null })

  return refreshRequest
}

api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error

    const originalRequest = error.config as (NonNullable<typeof error.config> & { _authRetried?: boolean }) | undefined
    if (!originalRequest || originalRequest.url?.includes('/auth/')) throw error
    if (originalRequest._authRetried) throw error

    const tokens = getTokens()
    if (!tokens?.refresh_token) {
      clearTokens()
      window.dispatchEvent(new Event('auth:logout'))
      throw error
    }

    const refreshedTokens = await refreshSessionTokens()
    originalRequest._authRetried = true
    originalRequest.headers.Authorization = `Bearer ${refreshedTokens.access_token}`
    return await api(originalRequest)
  },
)
