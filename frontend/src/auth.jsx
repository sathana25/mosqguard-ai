import { createContext, useContext, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!getToken())

  useEffect(() => {
    if (!getToken()) return
    api('/api/auth/me')
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false))
  }, [])

  const signIn = async (path, body) => {
    const res = await api(path, { method: 'POST', body })
    setToken(res.token)
    setUser(res.user)
    return res.user
  }

  const value = {
    user,
    loading,
    login: (username, password) => signIn('/api/auth/login', { username, password }),
    register: (data) => signIn('/api/auth/register', data),
    logout: () => {
      setToken(null)
      setUser(null)
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
