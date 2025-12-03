import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import {
  UserCircleIcon,
  EnvelopeIcon,
  CpuChipIcon,
  BellIcon,
  ShieldCheckIcon,
  PaintBrushIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { settingsService, UserSettings, LLMProvider } from '../services/settingsService'
import { emailService, EmailAccount } from '../services/emailService'
import { googleService } from '../services/googleService'
import { authService } from '../services/authService'
import { useAuthStore } from '../store/authStore'
import { useSettingsStore } from '../store/settingsStore'

type SettingsTab = 'profile' | 'email' | 'llm' | 'notifications' | 'security' | 'appearance'

export default function SettingsPage() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const { user, updateUser } = useAuthStore()
  const { theme, setTheme, language, setLanguage } = useSettingsStore()
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [show2FASetup, setShow2FASetup] = useState(false)
  const [qrCode, setQrCode] = useState<string | null>(null)

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsService.getSettings,
  })

  const { data: emailAccounts } = useQuery({
    queryKey: ['email-accounts'],
    queryFn: emailService.getAccounts,
  })

  const { data: googleStatus } = useQuery({
    queryKey: ['google-status'],
    queryFn: googleService.getStatus,
  })

  const { data: llmProviders } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: settingsService.getLLMProviders,
  })

  const updateSettingsMutation = useMutation({
    mutationFn: (data: Partial<UserSettings>) => settingsService.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('Settings saved')
    },
  })

  const removeAccountMutation = useMutation({
    mutationFn: (id: string) => emailService.removeAccount(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-accounts'] })
      toast.success('Account removed')
    },
  })

  const addAccountMutation = useMutation({
    mutationFn: (data: { provider: string; email_address: string; display_name?: string }) =>
      emailService.addAccount(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-accounts'] })
      setShowAddAccount(false)
      toast.success('Email account added')
    },
    onError: () => toast.error('Failed to add email account'),
  })

  const setApiKeyMutation = useMutation({
    mutationFn: ({ provider, apiKey }: { provider: string; apiKey: string }) =>
      settingsService.setLLMApiKey(provider, apiKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
      toast.success('API key saved')
    },
  })

  const testNotificationMutation = useMutation({
    mutationFn: (channel: string) => settingsService.testNotification(channel),
    onSuccess: () => toast.success('Test notification sent'),
    onError: () => toast.error('Failed to send test notification'),
  })

  const changePasswordMutation = useMutation({
    mutationFn: ({ current, newPass }: { current: string; newPass: string }) =>
      authService.changePassword(current, newPass),
    onSuccess: () => toast.success('Password changed'),
    onError: () => toast.error('Failed to change password'),
  })

  const setup2FAMutation = useMutation({
    mutationFn: authService.setup2FA,
    onSuccess: (data) => {
      setQrCode(data.qr_code)
      setShow2FASetup(true)
    },
  })

  const verify2FAMutation = useMutation({
    mutationFn: (code: string) => authService.verify2FA(code),
    onSuccess: () => {
      updateUser({ two_factor_enabled: true })
      setShow2FASetup(false)
      setQrCode(null)
      toast.success('2FA enabled')
    },
    onError: () => toast.error('Invalid code'),
  })

  const disable2FAMutation = useMutation({
    mutationFn: (code: string) => authService.disable2FA(code),
    onSuccess: () => {
      updateUser({ two_factor_enabled: false })
      toast.success('2FA disabled')
    },
  })

  const { register: registerPassword, handleSubmit: handlePasswordSubmit, reset: resetPassword } =
    useForm<{ current: string; newPass: string; confirm: string }>()

  const { register: register2FA, handleSubmit: handle2FASubmit } = useForm<{ code: string }>()

  const tabs = [
    { id: 'profile', label: t('settings.profile'), icon: UserCircleIcon },
    { id: 'email', label: t('settings.emailAccounts'), icon: EnvelopeIcon },
    { id: 'llm', label: t('settings.llmSettings'), icon: CpuChipIcon },
    { id: 'notifications', label: t('settings.notifications'), icon: BellIcon },
    { id: 'security', label: t('settings.security'), icon: ShieldCheckIcon },
    { id: 'appearance', label: t('settings.appearance'), icon: PaintBrushIcon },
  ]

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang)
    setLanguage(lang)
    updateSettingsMutation.mutate({ default_language: lang })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t('settings.title')}
      </h1>

      <div className="flex flex-col lg:flex-row gap-6">
        <div className="lg:w-64">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as SettingsTab)}
                className={clsx(
                  'w-full flex items-center px-4 py-2 rounded-lg transition-colors',
                  activeTab === tab.id
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                )}
              >
                <tab.icon className="w-5 h-5 mr-3" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 card">
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('settings.profile')}
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('auth.email')}
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="input mt-1 bg-gray-100 dark:bg-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={user?.full_name || ''}
                    disabled
                    className="input mt-1 bg-gray-100 dark:bg-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('settings.emailStyle')}
                  </label>
                  <select
                    value={settings?.email_style || 'professional'}
                    onChange={(e) =>
                      updateSettingsMutation.mutate({ email_style: e.target.value })
                    }
                    className="input mt-1"
                  >
                    <option value="formal">{t('settings.formal')}</option>
                    <option value="friendly">{t('settings.friendly')}</option>
                    <option value="professional">{t('settings.professional')}</option>
                    <option value="concise">{t('settings.concise')}</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'email' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('settings.emailAccounts')}
                </h2>
                <div className="flex space-x-2">
                  {googleStatus?.oauth_configured && (
                    <button
                      onClick={() => googleService.connectGoogle()}
                      className="btn btn-primary flex items-center"
                    >
                      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      Connect Google
                    </button>
                  )}
                  <button
                    onClick={() => setShowAddAccount(true)}
                    className="btn btn-secondary flex items-center"
                  >
                    <PlusIcon className="w-5 h-5 mr-2" />
                    {t('settings.addEmailAccount')}
                  </button>
                </div>
              </div>
              
              {!googleStatus?.oauth_configured && (
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900 rounded-lg">
                  <p className="text-sm text-yellow-700 dark:text-yellow-200">
                    Google OAuth is not configured. To connect Gmail and Google Calendar, add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file.
                  </p>
                </div>
              )}
              
              {emailAccounts && emailAccounts.length > 0 ? (
                <ul className="space-y-3">
                  {emailAccounts.map((account: EmailAccount) => (
                    <li
                      key={account.id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {account.email_address}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {account.provider} -{' '}
                          {account.is_active
                            ? t('settings.connected')
                            : t('settings.disconnected')}
                        </p>
                      </div>
                      <button
                        onClick={() => removeAccountMutation.mutate(account.id)}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 text-center py-4">No email accounts configured</p>
              )}
            </div>
          )}

          {activeTab === 'llm' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('settings.llmSettings')}
              </h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('settings.llmProvider')}
                </label>
                <select
                  value={settings?.llm_provider || 'local'}
                  onChange={(e) =>
                    updateSettingsMutation.mutate({ llm_provider: e.target.value })
                  }
                  className="input mt-1"
                >
                  <option value="local">{t('settings.localLLM')}</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="claude">Anthropic Claude</option>
                  <option value="cohere">Cohere</option>
                </select>
              </div>
              {llmProviders && (
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    API Keys
                  </h3>
                  {llmProviders
                    .filter((p: LLMProvider) => p.type === 'cloud')
                    .map((provider: LLMProvider) => (
                      <div key={provider.id} className="flex items-center space-x-2">
                        <input
                          type="password"
                          placeholder={`${provider.name} API Key`}
                          className="input flex-1"
                          onBlur={(e) => {
                            if (e.target.value) {
                              setApiKeyMutation.mutate({
                                provider: provider.id,
                                apiKey: e.target.value,
                              })
                            }
                          }}
                        />
                        <span
                          className={clsx(
                            'text-sm',
                            provider.is_configured ? 'text-green-600' : 'text-gray-400'
                          )}
                        >
                          {provider.is_configured ? 'Configured' : 'Not set'}
                        </span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('settings.notifications')}
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('settings.slackWebhook')}
                  </label>
                  <div className="flex space-x-2 mt-1">
                    <input
                      type="text"
                      placeholder="https://hooks.slack.com/..."
                      defaultValue={settings?.slack_webhook_url || ''}
                      className="input flex-1"
                      onBlur={(e) => {
                        if (e.target.value !== settings?.slack_webhook_url) {
                          updateSettingsMutation.mutate({
                            slack_webhook_url: e.target.value,
                          })
                        }
                      }}
                    />
                    <button
                      onClick={() => testNotificationMutation.mutate('slack')}
                      className="btn btn-secondary"
                    >
                      Test
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('settings.emailNotifications')}
                  </label>
                  <input
                    type="email"
                    placeholder="notifications@example.com"
                    defaultValue={settings?.notification_email || ''}
                    className="input mt-1"
                    onBlur={(e) => {
                      if (e.target.value !== settings?.notification_email) {
                        updateSettingsMutation.mutate({
                          notification_email: e.target.value,
                        })
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('settings.security')}
              </h2>
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Two-Factor Authentication
                  </h3>
                  {user?.two_factor_enabled ? (
                    <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900 rounded-lg">
                      <span className="text-green-700 dark:text-green-200">
                        2FA is enabled
                      </span>
                      <button
                        onClick={() => {
                          const code = prompt('Enter your 2FA code to disable:')
                          if (code) disable2FAMutation.mutate(code)
                        }}
                        className="btn btn-danger"
                      >
                        {t('settings.disable2FA')}
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setup2FAMutation.mutate()}
                      className="btn btn-primary"
                    >
                      {t('settings.enable2FA')}
                    </button>
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('settings.changePassword')}
                  </h3>
                  <form
                    onSubmit={handlePasswordSubmit((data) => {
                      if (data.newPass !== data.confirm) {
                        toast.error('Passwords do not match')
                        return
                      }
                      changePasswordMutation.mutate({
                        current: data.current,
                        newPass: data.newPass,
                      })
                      resetPassword()
                    })}
                    className="space-y-3"
                  >
                    <input
                      type="password"
                      {...registerPassword('current', { required: true })}
                      placeholder={t('settings.currentPassword')}
                      className="input"
                    />
                    <input
                      type="password"
                      {...registerPassword('newPass', { required: true, minLength: 8 })}
                      placeholder={t('settings.newPassword')}
                      className="input"
                    />
                    <input
                      type="password"
                      {...registerPassword('confirm', { required: true })}
                      placeholder={t('auth.confirmPassword')}
                      className="input"
                    />
                    <button type="submit" className="btn btn-primary">
                      {t('settings.changePassword')}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('settings.appearance')}
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('settings.theme')}
                  </label>
                  <div className="flex space-x-2 mt-2">
                    {(['light', 'dark', 'system'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setTheme(t)}
                        className={clsx(
                          'px-4 py-2 rounded-lg',
                          theme === t
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 dark:bg-gray-700'
                        )}
                      >
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('settings.language')}
                  </label>
                  <div className="flex space-x-2 mt-2">
                    <button
                      onClick={() => handleLanguageChange('en')}
                      className={clsx(
                        'px-4 py-2 rounded-lg',
                        language === 'en'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700'
                      )}
                    >
                      English
                    </button>
                    <button
                      onClick={() => handleLanguageChange('ro')}
                      className={clsx(
                        'px-4 py-2 rounded-lg',
                        language === 'ro'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700'
                      )}
                    >
                      Romana
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {showAddAccount && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('settings.addEmailAccount')}
            </h3>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                const formData = new FormData(e.currentTarget)
                addAccountMutation.mutate({
                  provider: formData.get('provider') as string,
                  email_address: formData.get('email_address') as string,
                  display_name: formData.get('display_name') as string || undefined,
                })
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Provider
                </label>
                <select name="provider" className="input mt-1" required>
                  <option value="gmail">Gmail</option>
                  <option value="outlook">Outlook</option>
                  <option value="yahoo">Yahoo</option>
                  <option value="imap">IMAP (Generic)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('auth.email')}
                </label>
                <input
                  type="email"
                  name="email_address"
                  className="input mt-1"
                  placeholder="your@email.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Display Name (optional)
                </label>
                <input
                  type="text"
                  name="display_name"
                  className="input mt-1"
                  placeholder="Work Email"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddAccount(false)}
                  className="btn btn-secondary"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={addAccountMutation.isPending}
                  className="btn btn-primary"
                >
                  {addAccountMutation.isPending ? t('common.loading') : t('common.add')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {show2FASetup && qrCode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Setup Two-Factor Authentication
            </h3>
            <div className="text-center mb-4">
              <img src={qrCode} alt="QR Code" className="mx-auto" />
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Scan this QR code with your authenticator app
              </p>
            </div>
            <form
              onSubmit={handle2FASubmit((data) => verify2FAMutation.mutate(data.code))}
              className="space-y-4"
            >
              <input
                type="text"
                {...register2FA('code', { required: true })}
                placeholder="Enter 6-digit code"
                className="input"
                maxLength={6}
              />
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShow2FASetup(false)
                    setQrCode(null)
                  }}
                  className="btn btn-secondary"
                >
                  {t('common.cancel')}
                </button>
                <button type="submit" className="btn btn-primary">
                  Verify
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
