import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  UserCircleIcon,
  EnvelopeIcon,
  CpuChipIcon,
  BellIcon,
  ShieldCheckIcon,
  PaintBrushIcon,
  PlusIcon,
  TrashIcon,
  KeyIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { settingsService, UserSettings } from '../services/settingsService'
import { emailService, EmailAccount } from '../services/emailService'
import { googleService } from '../services/googleService'
import { useAuthStore } from '../store/authStore'
import { useSettingsStore } from '../store/settingsStore'

type SettingsTab = 'profile' | 'email' | 'llm' | 'notifications' | 'security' | 'appearance'

export default function SettingsPage() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const { theme, setTheme, language, setLanguage } = useSettingsStore()
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')
  const [showAddAccount, setShowAddAccount] = useState(false)

  // Fetch settings
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

  // Mutations
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
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('API key saved successfully')
    },
    onError: () => toast.error('Failed to save API key')
  })

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang)
    setLanguage(lang)
    updateSettingsMutation.mutate({ default_language: lang })
  }
  
  const getProviderLabel = (provider: string) => {
    switch(provider) {
      case 'openai': return 'OpenAI API Key';
      case 'gemini': return 'Google Gemini API Key';
      case 'claude': return 'Anthropic API Key';
      case 'cohere': return 'Cohere API Key';
      default: return 'API Key';
    }
  }

  const tabs = [
    { id: 'profile', label: t('settings.profile'), icon: UserCircleIcon },
    { id: 'email', label: t('settings.emailAccounts'), icon: EnvelopeIcon },
    { id: 'llm', label: t('settings.llmSettings'), icon: CpuChipIcon },
    { id: 'notifications', label: t('settings.notifications'), icon: BellIcon },
    { id: 'security', label: t('settings.security'), icon: ShieldCheckIcon },
    { id: 'appearance', label: t('settings.appearance'), icon: PaintBrushIcon },
  ]

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
          {/* PROFILE SETTINGS */}
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
                  <input type="email" value={user?.email || ''} disabled className="input mt-1 bg-gray-100 dark:bg-gray-700" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Full Name
                  </label>
                  <input type="text" value={user?.full_name || ''} disabled className="input mt-1 bg-gray-100 dark:bg-gray-700" />
                </div>
                
                {/* --- SIGNATURE FIELD --- */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Email Signature
                  </label>
                  <p className="text-xs text-gray-500 mb-1">This will be used by the AI to sign your emails.</p>
                  <textarea
                    defaultValue={settings?.email_signature || ''}
                    onBlur={(e) => updateSettingsMutation.mutate({ email_signature: e.target.value })}
                    className="input mt-1 h-24 font-mono text-sm"
                    placeholder="Best regards,&#10;Your Name&#10;Position"
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

          {/* EMAIL ACCOUNTS */}
          {activeTab === 'email' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('settings.emailAccounts')}
                </h2>
                <div className="flex space-x-2">
                  {googleStatus?.oauth_configured && (
                    <button onClick={() => googleService.connectGoogle()} className="btn btn-primary flex items-center">
                      Connect Google
                    </button>
                  )}
                  <button onClick={() => setShowAddAccount(true)} className="btn btn-secondary flex items-center">
                    <PlusIcon className="w-5 h-5 mr-2" />
                    {t('settings.addEmailAccount')}
                  </button>
                </div>
              </div>
              
              {!googleStatus?.oauth_configured && (
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900 rounded-lg">
                  <p className="text-sm text-yellow-700 dark:text-yellow-200">
                    Google OAuth is not configured.
                  </p>
                </div>
              )}
              
              {emailAccounts && emailAccounts.length > 0 ? (
                <ul className="space-y-3">
                  {emailAccounts.map((account: EmailAccount) => (
                    <li key={account.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{account.email_address}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {account.provider} - {account.is_active ? t('settings.connected') : t('settings.disconnected')}
                        </p>
                      </div>
                      <button onClick={() => removeAccountMutation.mutate(account.id)} className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded">
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

          {/* LLM SETTINGS */}
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
                  onChange={(e) => updateSettingsMutation.mutate({ llm_provider: e.target.value })}
                  className="input mt-1"
                >
                  <option value="local">{t('settings.localLLM')} (Ollama)</option>
                  <option value="openai">OpenAI (ChatGPT)</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="claude">Anthropic Claude</option>
                  <option value="cohere">Cohere</option>
                </select>
              </div>

              {settings?.llm_provider && settings.llm_provider !== 'local' && (
                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="flex items-center mb-2">
                    <KeyIcon className="w-5 h-5 mr-2 text-primary-500" />
                    <label className="block text-sm font-medium text-gray-900 dark:text-white">
                      {getProviderLabel(settings.llm_provider)}
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="password"
                      placeholder={`Enter your ${settings.llm_provider} API Key here`}
                      className="input flex-1"
                      onBlur={(e) => {
                        if (e.target.value) {
                          setApiKeyMutation.mutate({
                            provider: settings.llm_provider,
                            apiKey: e.target.value,
                          })
                        }
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Your key is stored securely encrypted.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* APPEARANCE SETTINGS */}
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
                          theme === t ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700'
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
                        language === 'en' ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700'
                      )}
                    >
                      English
                    </button>
                    <button
                      onClick={() => handleLanguageChange('ro')}
                      className={clsx(
                        'px-4 py-2 rounded-lg',
                        language === 'ro' ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700'
                      )}
                    >
                      Romana
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

           {/* Placeholder for other tabs */}
           {['notifications', 'security'].includes(activeTab) && (
              <div className="p-10 text-center text-gray-500">
                  Settings for {activeTab} coming soon in full version.
              </div>
           )}

        </div>
      </div>

      {showAddAccount && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
             <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('settings.addEmailAccount')}</h3>
                <form onSubmit={(e) => {
                    e.preventDefault();
                    const formData = new FormData(e.currentTarget);
                    addAccountMutation.mutate({
                      provider: formData.get('provider') as string,
                      email_address: formData.get('email_address') as string,
                      display_name: formData.get('display_name') as string || undefined,
                    })
                }} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Provider</label>
                        <select name="provider" className="input mt-1" required>
                            <option value="gmail">Gmail</option>
                            <option value="outlook">Outlook</option>
                            <option value="yahoo">Yahoo</option>
                            <option value="imap">IMAP</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
                        <input type="email" name="email_address" className="input mt-1" required />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Display Name</label>
                        <input type="text" name="display_name" className="input mt-1" />
                    </div>
                    <div className="flex justify-end space-x-2">
                        <button type="button" onClick={() => setShowAddAccount(false)} className="btn btn-secondary">Cancel</button>
                        <button type="submit" disabled={addAccountMutation.isPending} className="btn btn-primary">
                            {addAccountMutation.isPending ? 'Adding...' : 'Add'}
                        </button>
                    </div>
                </form>
             </div>
        </div>
      )}
    </div>
  )
}
