import { useEffect, useState, type ReactNode } from 'react'
import { api, refreshSessionTokens } from '../lib/api'
import { AuthContext } from './context'
import { clearTokens, getTokens, saveTokens, type AuthTokens } from './tokenStore'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setCurrentTokens] = useState<AuthTokens | null>(() => getTokens())

  useEffect(() => {
    const handleLogout = () => setCurrentTokens(null)
    const handleTokens = (event: Event) => {
      setCurrentTokens((event as CustomEvent<AuthTokens>).detail)
    }
    window.addEventListener('auth:logout', handleLogout)
    window.addEventListener('auth:tokens', handleTokens)
    return () => {
      window.removeEventListener('auth:logout', handleLogout)
      window.removeEventListener('auth:tokens', handleTokens)
    }
  }, [])

  useEffect(() => {
    if (!tokens) return
    const expiresAt = (tokens.stored_at ?? Date.now()) + tokens.expires_in * 1000
    const refreshIn = Math.max(expiresAt - Date.now() - 60_000, 0)
    const timer = window.setTimeout(() => {
      void refreshSessionTokens().catch(() => undefined)
    }, refreshIn)
    return () => window.clearTimeout(timer)
  }, [tokens])

  async function login(email: string, senha: string) {
    const response = await api.post<AuthTokens>('/auth/login', { email, senha })
    setCurrentTokens(saveTokens(response.data))
  }

  async function logout() {
    const currentTokens = getTokens()
    try {
      if (currentTokens) {
        await api.post('/auth/logout', { refresh_token: currentTokens.refresh_token })
      }
    } finally {
      clearTokens()
      setCurrentTokens(null)
    }
  }

  const value = {
    isAuthenticated: Boolean(tokens?.access_token),
    accessToken: tokens?.access_token ?? null,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
