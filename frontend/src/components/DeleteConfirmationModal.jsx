export default function DeleteConfirmationModal({ isOpen, onClose, onConfirm, itemType, itemName }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-overlay-strong backdrop-blur-sm">
      <div className="w-full max-w-lg bg-background rounded-xl shadow-xl border border-border/60 dark:border-surface-darker overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-border dark:border-surface-darker">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-danger-soft dark:bg-danger-stronger/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-danger dark:text-danger-contrast" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-heading font-bold text-lg sm:text-xl text-text truncate">Confirm Deletion</h3>
              <p className="font-body text-xs sm:text-sm text-text/70">This action cannot be undone.</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-4">
          <p className="font-body text-text/80 text-sm sm:text-base">
            Are you sure you want to delete this {itemType}?
          </p>
          <div className="rounded-lg border border-border dark:border-surface-darker bg-surface dark:bg-surface-dark/40 p-4">
            <p className="font-body font-medium text-danger-strong dark:text-danger-border text-sm break-all">
              {itemName}
            </p>
          </div>
          <p className="font-body text-xs text-text/60">
            This will permanently remove the {itemType} and all associated data.
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-background/80 flex flex-col-reverse sm:flex-row sm:justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-lg border border-border-strong dark:border-border-stronger text-text hover:bg-surface-subtle/60 dark:hover:bg-surface-darker/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ring dark:focus-visible:ring-ring-dark cursor-pointer font-body font-semibold"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2.5 rounded-lg bg-danger hover:bg-danger-strong text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-danger-accent cursor-pointer font-body font-semibold flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete {itemType}
          </button>
        </div>
      </div>
    </div>
  );
}
