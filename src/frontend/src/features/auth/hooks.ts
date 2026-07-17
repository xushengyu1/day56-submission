import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { login, register, logout, getMe } from './api'
import type { LoginRequest, RegisterRequest } from '@/api/types'

export function useAuth() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN',
  }
}

export function useLogin() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (req: LoginRequest) => login(req),
    onSuccess: (data) => {
      queryClient.setQueryData(['auth', 'me'], data.user)
      if (data.user.role === 'ADMIN') {
        navigate('/admin')
      } else {
        navigate('/')
      }
    },
  })
}

export function useRegister() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (req: RegisterRequest) => register(req),
    onSuccess: (data) => {
      queryClient.setQueryData(['auth', 'me'], data.user)
      navigate('/')
    },
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return {
    logout: () => {
      logout()
      queryClient.clear()
      navigate('/login')
    },
  }
}
