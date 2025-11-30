import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PaperAirplaneIcon, TrashIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'
import { chatService, ChatMessage } from '../services/chatService'
import { format } from 'date-fns'

export default function ChatPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [message, setMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: history } = useQuery({
    queryKey: ['chat-history'],
    queryFn: chatService.getHistory,
  })

  const { data: suggestions } = useQuery({
    queryKey: ['chat-suggestions'],
    queryFn: chatService.getSuggestions,
  })

  const sendMessageMutation = useMutation({
    mutationFn: (msg: string) => chatService.sendMessage(msg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-history'] })
      setMessage('')
    },
  })

  const clearHistoryMutation = useMutation({
    mutationFn: chatService.clearHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-history'] })
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  const handleSend = () => {
    if (!message.trim()) return
    sendMessageMutation.mutate(message.trim())
  }

  const handleSuggestionClick = (text: string) => {
    setMessage(text)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('chat.title')}
        </h1>
        <button
          onClick={() => clearHistoryMutation.mutate()}
          className="btn btn-secondary flex items-center"
        >
          <TrashIcon className="w-5 h-5 mr-2" />
          {t('chat.clearHistory')}
        </button>
      </div>

      <div className="flex-1 flex gap-6">
        <div className="flex-1 flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {history && history.length > 0 ? (
              history.map((msg: ChatMessage) => (
                <div
                  key={msg.id}
                  className={clsx(
                    'flex',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={clsx(
                      'max-w-3xl rounded-lg px-4 py-2',
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                        <p className="text-xs opacity-75 mb-1">Sources:</p>
                        <ul className="text-xs space-y-1">
                          {msg.sources.map((source, idx) => (
                            <li key={idx} className="opacity-75">
                              [{source.type}] {source.title}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <p
                      className={clsx(
                        'text-xs mt-1',
                        msg.role === 'user' ? 'text-primary-200' : 'text-gray-500'
                      )}
                    >
                      {format(new Date(msg.timestamp), 'HH:mm')}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                {t('chat.noMessages')}
              </div>
            )}
            {sendMessageMutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex space-x-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                placeholder={t('chat.placeholder')}
                className="input flex-1"
                disabled={sendMessageMutation.isPending}
              />
              <button
                onClick={handleSend}
                disabled={sendMessageMutation.isPending || !message.trim()}
                className="btn btn-primary"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        <div className="w-64 hidden lg:block">
          <div className="card">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
              {t('chat.suggestions')}
            </h3>
            {suggestions && suggestions.length > 0 ? (
              <ul className="space-y-2">
                {suggestions.map((suggestion, idx) => (
                  <li key={idx}>
                    <button
                      onClick={() => handleSuggestionClick(suggestion.text)}
                      className="w-full text-left text-sm p-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                    >
                      {suggestion.text}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() =>
                      handleSuggestionClick('What urgent emails do I have?')
                    }
                    className="w-full text-left text-sm p-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                  >
                    What urgent emails do I have?
                  </button>
                </li>
                <li>
                  <button
                    onClick={() =>
                      handleSuggestionClick('Summarize my meetings this week')
                    }
                    className="w-full text-left text-sm p-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                  >
                    Summarize my meetings this week
                  </button>
                </li>
                <li>
                  <button
                    onClick={() =>
                      handleSuggestionClick('Find emails about project X')
                    }
                    className="w-full text-left text-sm p-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                  >
                    Find emails about project X
                  </button>
                </li>
                <li>
                  <button
                    onClick={() =>
                      handleSuggestionClick("What's on my calendar today?")
                    }
                    className="w-full text-left text-sm p-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                  >
                    What's on my calendar today?
                  </button>
                </li>
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
