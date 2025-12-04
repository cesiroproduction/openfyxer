import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import { format } from 'date-fns';
import {
  SparklesIcon,
  PaperAirplaneIcon,
  ArchiveBoxIcon, 
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { emailService, Draft } from '../services/emailService'; 

export default function DraftsPage() {
  const queryClient = useQueryClient();
  const [selectedDraft, setSelectedDraft] = useState<Draft | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [tone, setTone] = useState('');

  const { data: drafts, isLoading, refetch } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => emailService.getDrafts(), 
  });

  const handleDraftSelect = (draft: Draft) => {
    setSelectedDraft(draft);
    setEditingContent(draft.content);
  };

  const updateDraftMutation = useMutation({
    mutationFn: (content: string) => emailService.updateDraft(selectedDraft!.id, content),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      setSelectedDraft(data);
      setEditingContent(data.content);
      toast.success('Draft updated');
    },
    onError: () => toast.error('Failed to update draft'),
  });

  const sendDraftMutation = useMutation({
    mutationFn: () => emailService.sendDraft(selectedDraft!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      setSelectedDraft(null);
      toast.success('Email sent successfully');
    },
    onError: () => toast.error('Failed to send email'),
  });
  
  const regenerateDraftMutation = useMutation({
    mutationFn: () => emailService.regenerateDraft(selectedDraft!.id, tone || undefined),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      setSelectedDraft(data);
      setEditingContent(data.content);
      toast.success('Draft regenerated');
    },
    onError: () => toast.error('Failed to regenerate draft'),
  });

  const isSaving = updateDraftMutation.isPending || sendDraftMutation.isPending || regenerateDraftMutation.isPending;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Drafts ({drafts?.length || 0})
        </h1>
        <button onClick={() => refetch()} disabled={isLoading} className="btn btn-secondary flex items-center">
          <ArrowPathIcon className={clsx('w-5 h-5 mr-2', isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      <div className="flex-1 flex bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {/* Left Panel: List */}
        <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading...</div>
          ) : drafts && drafts.length > 0 ? (
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {drafts.map((draft) => (
                <li
                  key={draft.id}
                  onClick={() => handleDraftSelect(draft)}
                  className={clsx(
                    'p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700',
                    selectedDraft?.id === draft.id && 'bg-gray-100 dark:bg-gray-700'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {draft.subject || 'No Subject'}
                      </p>
                      <p className="text-xs text-gray-700 dark:text-gray-300 truncate mt-1">
                        {draft.content?.substring(0, 50)}...
                      </p>
                    </div>
                    <div className="ml-2 flex flex-col items-end">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {format(new Date(draft.updated_at), 'MMM d')}
                      </span>
                      <span className={clsx('badge mt-1', draft.status === 'pending' ? 'badge-info' : 'badge-success')}>
                        {draft.status}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-4 text-center text-gray-500">No drafts found</div>
          )}
        </div>

        {/* Right Panel: Editor */}
        <div className="flex-1 flex flex-col">
          {selectedDraft ? (
            <>
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {selectedDraft.subject || 'No Subject'}
                </h2>
              </div>

              <div className="flex-1 p-4 overflow-y-auto">
                <textarea
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="w-full h-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white resize-none focus:ring-primary-500 focus:border-primary-500"
                  rows={20}
                />
              </div>

              <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <div className="flex items-center space-x-2">
                    <select 
                        value={tone} onChange={(e) => setTone(e.target.value)}
                        className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                    >
                        <option value="">Default Tone</option>
                        <option value="formal">Formal</option>
                        <option value="casual">Casual</option>
                        <option value="friendly">Friendly</option>
                    </select>
                    <button onClick={() => regenerateDraftMutation.mutate()} disabled={isSaving} className="btn btn-secondary flex items-center">
                        <SparklesIcon className="w-5 h-5 mr-2" /> Regenerate
                    </button>
                </div>

                <div className="flex space-x-3">
                  <button onClick={() => updateDraftMutation.mutate(editingContent)} disabled={isSaving || editingContent === selectedDraft.content} className="btn btn-info flex items-center">
                    <ArchiveBoxIcon className="w-5 h-5 mr-2" /> Save
                  </button>
                  <button onClick={() => sendDraftMutation.mutate()} disabled={isSaving} className="btn btn-primary flex items-center">
                    <PaperAirplaneIcon className="w-5 h-5 mr-2" /> Send
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">Select a draft to view</div>
          )}
        </div>
      </div>
    </div>
  );
}
