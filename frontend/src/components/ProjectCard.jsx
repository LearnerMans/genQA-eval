import { useEffect, useRef, useState } from 'react';

export default function ProjectCard({ project, onDelete, onOpen }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const onDocClick = (e) => {
      if (!menuRef.current) return;
      if (!menuRef.current.contains(e.target)) {
        setMenuOpen(false);
        setConfirming(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(project.id);
    } catch (error) {
      // error toast handled by parent
    } finally {
      setIsDeleting(false);
      setMenuOpen(false);
      setConfirming(false);
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

  const handleCardActivate = () => {
    if (isDeleting) return;
    onOpen && onOpen(project);
  };

  const stop = (e) => e.stopPropagation();

  return (
    <div
      className="group bg-background border border-secondary rounded-xl p-6 hover:shadow-xl hover:border-accent hover:scale-[1.02] transition-all duration-300 cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent/60"
      role="button"
      tabIndex={0}
      onClick={handleCardActivate}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleCardActivate();
        }
      }}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-accent/40 to-accent/20 text-primary flex items-center justify-center flex-shrink-0 shadow-sm">
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 3h12a1 1 0 011 1v10.382a1 1 0 01-.553.894l-6 3a1 1 0 01-.894 0l-6-3A1 1 0 013 14.382V4a1 1 0 011-1z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-heading font-bold text-xl text-text truncate mb-1" title={project.name}>
              {project.name}
            </h3>
            <p className="text-xs text-text/50 font-mono">ID: {project.id}</p>
          </div>
        </div>
        <div className="relative ml-2" ref={menuRef} onClick={stop}>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="p-2 rounded-lg hover:bg-secondary/60 text-text/70 hover:text-text transition-all duration-200 cursor-pointer"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            aria-label="Open options menu"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zm0 6a2 2 0 110-4 2 2 0 010 4zm0 6a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </button>
          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 mt-2 w-48 bg-background border border-secondary rounded-lg shadow-xl overflow-hidden z-10 animate-in fade-in slide-in-from-top-2 duration-200"
            >
              {!confirming ? (
                <div className="py-1">
                  <button
                    className="w-full text-left px-4 py-2.5 text-sm font-body text-text hover:bg-accent/20 cursor-pointer transition-colors duration-150 flex items-center gap-2"
                    onClick={() => {
                      setMenuOpen(false);
                      onOpen && onOpen(project);
                    }}
                  >
                    <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                    </svg>
                    Open Project
                  </button>
                  <button
                    className="w-full text-left px-4 py-2.5 text-sm font-body text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 cursor-pointer transition-colors duration-150 flex items-center gap-2"
                    onClick={() => setConfirming(true)}
                  >
                    <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd"/>
                    </svg>
                    Delete Project
                  </button>
                </div>
              ) : (
                <div className="px-4 py-3 text-sm">
                  <div className="font-semibold mb-3 text-text">Delete this project?</div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleDelete}
                      disabled={isDeleting}
                      className="flex-1 px-3 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-150 font-medium text-xs"
                    >
                      {isDeleting ? 'Deleting…' : 'Delete'}
                    </button>
                    <button
                      onClick={() => {
                        setConfirming(false);
                        setMenuOpen(false);
                      }}
                      disabled={isDeleting}
                      className="flex-1 px-3 py-2 rounded-md bg-secondary text-text hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-150 font-medium text-xs"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-2.5 text-sm font-body">
        <div className="flex justify-between items-center py-2 px-3 bg-secondary/20 rounded-lg">
          <span className="font-medium text-text/60 flex items-center gap-2">
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
            </svg>
            Created
          </span>
          <span className="font-semibold text-text">{formatDate(project.created_at)}</span>
        </div>
        {project.updated_at && (
          <div className="flex justify-between items-center py-2 px-3 bg-secondary/20 rounded-lg">
            <span className="font-medium text-text/60 flex items-center gap-2">
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
              </svg>
              Updated
            </span>
            <span className="font-semibold text-text">{formatDate(project.updated_at)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
