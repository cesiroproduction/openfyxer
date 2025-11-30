import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'
import { authService, LoginRequest } from '../services/authService'

export default function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [requires2FA, setRequires2FA] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>()

  const onSubmit = async (data: LoginRequest) => {
    setLoading(true)
    try {
      const response = await authService.login(data)
      setAuth(response.user, response.access_token)
      toast.success(t('auth.loginSuccess'))
      navigate('/')
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      if (err.response?.data?.detail === '2FA_REQUIRED') {
        setRequires2FA(true)
      } else {
        toast.error(t('auth.loginError'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600">OpenFyxer</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            AI Executive Assistant
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t('auth.email')}
            </label>
            <input
              type="email"
              id="email"
              {...register('email', { required: true })}
              className="input mt-1"
              placeholder="you@example.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{t('errors.validation')}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t('auth.password')}
            </label>
            <input
              type="password"
              id="password"
              {...register('password', { required: true })}
              className="input mt-1"
              placeholder="********"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{t('errors.validation')}</p>
            )}
          </div>

          {requires2FA && (
            <div>
              <label
                htmlFor="totp_code"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {t('auth.enterCode')}
              </label>
              <input
                type="text"
                id="totp_code"
                {...register('totp_code')}
                className="input mt-1"
                placeholder="123456"
                maxLength={6}
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full"
          >
            {loading ? t('common.loading') : t('auth.login')}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
          {t('auth.noAccount')}{' '}
          <Link to="/register" className="text-primary-600 hover:underline">
            {t('auth.register')}
          </Link>
        </p>
      </div>
    </div>
  )
}
