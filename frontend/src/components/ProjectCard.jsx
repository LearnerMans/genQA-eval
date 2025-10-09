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
      className="group bg-background border border-secondary rounded-xl p-5 hover:shadow-lg hover:border-accent transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent/60"
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
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="h-8 w-8 rounded-md bg-accent/30 text-primary flex items-center justify-center">
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 3h12a1 1 0 011 1v10.382a1 1 0 01-.553.894l-6 3a1 1 0 01-.894 0l-6-3A1 1 0 013 14.382V4a1 1 0 011-1z" />
            </svg>
          </div>
          <h3 className="font-heading font-bold text-lg text-text truncate" title={project.name}>
            {project.name}
          </h3>
        </div>
        <div className="relative" ref={menuRef} onClick={stop}>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="p-1.5 rounded-md hover:bg-secondary/40 text-text/70 hover:text-text transition-colors cursor-pointer"
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
              className="absolute right-0 mt-2 w-44 bg-background border border-secondary rounded-lg shadow-lg overflow-hidden z-10"
            >
              {!confirming ? (
                <div className="py-1">
                  <button
                    className="w-full text-left px-3 py-2 text-sm font-body text-text hover:bg-accent/20 cursor-pointer"
                    onClick={() => {
                      setMenuOpen(false);
                      onOpen && onOpen(project);
                    }}
                  >
                    Open Project
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm font-body text-red-600 hover:bg-red-50 cursor-pointer"
                    onClick={() => setConfirming(true)}
                  >
                    Delete
                  </button>
                </div>
              ) : (
                <div className="px-3 py-2 text-sm">
                  <div className="font-body mb-2 text-text">Delete this project?</div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleDelete}
                      disabled={isDeleting}
                      className="px-3 py-1 rounded bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                      {isDeleting ? 'Deleting…' : 'Confirm'}
                    </button>
                    <button
                      onClick={() => {
                        setConfirming(false);
                        setMenuOpen(false);
                      }}
                      disabled={isDeleting}
                      className="px-3 py-1 rounded bg-secondary text-text hover:bg-secondary/90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
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

      <div className="space-y-2 text-sm font-body text-text/70">
        <div className="flex justify-between">
          <span className="font-normal">Created</span>
          <span className="font-normal">{formatDate(project.created_at)}</span>
        </div>
        {project.updated_at && (
          <div className="flex justify-between">
            <span className="font-normal">Updated</span>
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
