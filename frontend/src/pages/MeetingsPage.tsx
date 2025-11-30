import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import {
  PlusIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  SparklesIcon,
  EnvelopeIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { meetingService, Meeting } from '../services/meetingService'
import { format } from 'date-fns'

interface MeetingFormData {
  title: string
  description?: string
  meeting_date?: string
  participants?: string
}

export default function MeetingsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null)
  const [uploadingFor, setUploadingFor] = useState<string | null>(null)

  const { register, handleSubmit, reset } = useForm<MeetingFormData>()

  const { data: meetings, isLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: () => meetingService.getMeetings(),
  })

  const createMutation = useMutation({
    mutationFn: (data: MeetingFormData) =>
      meetingService.createMeeting({
        title: data.title,
        description: data.description,
        meeting_date: data.meeting_date,
        participants: data.participants?.split(',').map((p) => p.trim()),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] })
      setShowCreateModal(false)
      reset()
      toast.success('Meeting created')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => meetingService.deleteMeeting(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] })
      setSelectedMeeting(null)
      toast.success('Meeting deleted')
    },
  })

  const uploadAudioMutation = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) =>
      meetingService.uploadAudio(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] })
      toast.success('Audio uploaded')
    },
    onError: () => toast.error('Upload failed'),
  })

  const transcribeMutation = useMutation({
    mutationFn: (id: string) => meetingService.transcribe(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] })
      toast.success('Transcription started')
    },
  })

  const summarizeMutation = useMutation({
    mutationFn: (id: string) => meetingService.summarize(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] })
      toast.success('Summarization started')
    },
  })

  const generateFollowUpMutation = useMutation({
    mutationFn: (id: string) => meetingService.generateFollowUpEmail(id),
    onSuccess: (data) => {
      toast.success('Follow-up email generated')
      navigator.clipboard.writeText(data.content)
      toast.success('Copied to clipboard')
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && uploadingFor) {
      uploadAudioMutation.mutate({ id: uploadingFor, file })
      setUploadingFor(null)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="badge bg-gray-100 text-gray-800">Pending</span>
      case 'transcribing':
        return <span className="badge bg-yellow-100 text-yellow-800">Transcribing</span>
      case 'transcribed':
        return <span className="badge bg-blue-100 text-blue-800">Transcribed</span>
      case 'summarized':
        return <span className="badge bg-green-100 text-green-800">Summarized</span>
      case 'error':
        return <span className="badge bg-red-100 text-red-800">Error</span>
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('meetings.title')}
        </h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          {t('meetings.newMeeting')}
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*,video/*"
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {t('meetings.title')}
          </h2>
          {isLoading ? (
            <div className="text-center py-4 text-gray-500">{t('common.loading')}</div>
          ) : meetings && meetings.length > 0 ? (
            <ul className="space-y-2">
              {meetings.map((meeting) => (
                <li
                  key={meeting.id}
                  onClick={() => setSelectedMeeting(meeting)}
                  className={clsx(
                    'p-3 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700',
                    selectedMeeting?.id === meeting.id && 'bg-gray-100 dark:bg-gray-700'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {meeting.title}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {meeting.meeting_date
                          ? format(new Date(meeting.meeting_date), 'MMM d, yyyy')
                          : format(new Date(meeting.created_at), 'MMM d, yyyy')}
                      </p>
                    </div>
                    {getStatusBadge(meeting.status)}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-center py-4 text-gray-500">{t('meetings.noMeetings')}</p>
          )}
        </div>

        <div className="lg:col-span-2 card">
          {selectedMeeting ? (
            <div className="space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {selectedMeeting.title}
                  </h2>
                  {selectedMeeting.description && (
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                      {selectedMeeting.description}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => deleteMutation.mutate(selectedMeeting.id)}
                  className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded"
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>

              {selectedMeeting.participants && selectedMeeting.participants.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('meetings.participants')}
                  </h3>
                  <p className="text-gray-900 dark:text-white">
                    {selectedMeeting.participants.join(', ')}
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => {
                    setUploadingFor(selectedMeeting.id)
                    fileInputRef.current?.click()
                  }}
                  className="btn btn-secondary flex items-center"
                >
                  <MicrophoneIcon className="w-5 h-5 mr-2" />
                  {t('meetings.uploadAudio')}
                </button>

                {selectedMeeting.audio_file_path && selectedMeeting.status === 'pending' && (
                  <button
                    onClick={() => transcribeMutation.mutate(selectedMeeting.id)}
                    disabled={transcribeMutation.isPending}
                    className="btn btn-secondary flex items-center"
                  >
                    <DocumentTextIcon className="w-5 h-5 mr-2" />
                    {transcribeMutation.isPending
                      ? t('meetings.transcribing')
                      : t('meetings.transcribe')}
                  </button>
                )}

                {selectedMeeting.transcript && selectedMeeting.status === 'transcribed' && (
                  <button
                    onClick={() => summarizeMutation.mutate(selectedMeeting.id)}
                    disabled={summarizeMutation.isPending}
                    className="btn btn-secondary flex items-center"
                  >
                    <SparklesIcon className="w-5 h-5 mr-2" />
                    {t('meetings.summarize')}
                  </button>
                )}

                {selectedMeeting.summary && (
                  <button
                    onClick={() => generateFollowUpMutation.mutate(selectedMeeting.id)}
                    disabled={generateFollowUpMutation.isPending}
                    className="btn btn-primary flex items-center"
                  >
                    <EnvelopeIcon className="w-5 h-5 mr-2" />
                    {t('meetings.generateFollowUp')}
                  </button>
                )}
              </div>

              {selectedMeeting.audio_duration_seconds && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Audio Duration
                  </h3>
                  <p className="text-gray-900 dark:text-white">
                    {Math.floor(selectedMeeting.audio_duration_seconds / 60)}m{' '}
                    {Math.floor(selectedMeeting.audio_duration_seconds % 60)}s
                  </p>
                </div>
              )}

              {selectedMeeting.transcript && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                    {t('meetings.transcript')}
                  </h3>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg max-h-48 overflow-y-auto">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {selectedMeeting.transcript}
                    </p>
                  </div>
                </div>
              )}

              {selectedMeeting.summary && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                    {t('meetings.summary')}
                  </h3>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {selectedMeeting.summary}
                    </p>
                  </div>
                </div>
              )}

              {selectedMeeting.action_items && selectedMeeting.action_items.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                    {t('meetings.actionItems')}
                  </h3>
                  <ul className="list-disc list-inside space-y-1">
                    {selectedMeeting.action_items.map((item, idx) => (
                      <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedMeeting.key_decisions && selectedMeeting.key_decisions.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                    {t('meetings.keyDecisions')}
                  </h3>
                  <ul className="list-disc list-inside space-y-1">
                    {selectedMeeting.key_decisions.map((decision, idx) => (
                      <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                        {decision}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Select a meeting to view details
            </div>
          )}
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('meetings.newMeeting')}
            </h3>
            <form onSubmit={handleSubmit((data) => createMutation.mutate(data))} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Title
                </label>
                <input
                  type="text"
                  {...register('title', { required: true })}
                  className="input mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Date
                </label>
                <input
                  type="datetime-local"
                  {...register('meeting_date')}
                  className="input mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('meetings.participants')} (comma separated)
                </label>
                <input type="text" {...register('participants')} className="input mt-1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Description
                </label>
                <textarea {...register('description')} className="input mt-1" rows={3} />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    reset()
                  }}
                  className="btn btn-secondary"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="btn btn-primary"
                >
                  {createMutation.isPending ? t('common.loading') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
