import { useState } from 'react';

export default function ProjectCard({ project, onDelete }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(project.id);
    } catch (error) {
      console.error('Failed to delete project:', error);
      setIsDeleting(false);
      setShowConfirm(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="bg-background border border-secondary rounded-lg p-6 hover:shadow-lg hover:border-accent transition-all duration-200">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-heading font-bold text-xl text-text">
          {project.name}
        </h3>
        {!showConfirm ? (
          <button
            onClick={() => setShowConfirm(true)}
            className="text-red-500 hover:text-red-700 transition-colors"
            disabled={isDeleting}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
            >
              {isDeleting ? 'Deleting...' : 'Confirm'}
            </button>
            <button
              onClick={() => setShowConfirm(false)}
              disabled={isDeleting}
              className="px-3 py-1 text-sm bg-secondary text-text rounded hover:bg-secondary/90 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2 text-sm font-body text-text/70">
        <div className="flex justify-between">
          <span className="font-normal">Created:</span>
          <span className="font-normal">{formatDate(project.created_at)}</span>
        </div>
        {project.updated_at && (
          <div className="flex justify-between">
            <span className="font-normal">Updated:</span>
            <span className="font-normal">{formatDate(project.updated_at)}</span>
          </div>
        )}
        <div className="pt-2 border-t border-secondary/30">
          <span className="font-normal text-xs text-text/50">ID: {project.id}</span>
        </div>
      </div>
    </div>
  );
}
