import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const remove = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback((opts) => {
    const id = ++idRef.current;
    const toast = {
      id,
      type: opts.type || 'info',
      title: opts.title || null,
      message: opts.message || '',
      duration: typeof opts.duration === 'number' ? opts.duration : 4000,
    };
    setToasts((prev) => [...prev, toast]);
    if (toast.duration > 0) {
      setTimeout(() => remove(id), toast.duration);
    }
    return id;
  }, [remove]);

  const api = useMemo(() => {
    const base = (type) => (message, title, duration) => show({ type, message, title, duration });
    return {
      show,
      remove,
      info: base('info'),
      success: base('success'),
      warning: base('warning'),
      error: base('error'),
    };
  }, [show, remove]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <Toaster toasts={toasts} onClose={remove} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

function Icon({ type }) {
  const common = 'h-5 w-5';
  if (type === 'success') {
    return (
      <svg className={common} viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.707a1 1 0 00-1.414-1.414L9 10.172 7.707 8.879a1 1 0 10-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
      </svg>
    );
  }
  if (type === 'warning') {
    return (
      <svg className={common} viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l6.518 11.59c.75 1.335-.213 3.01-1.743 3.01H3.482c-1.53 0-2.493-1.675-1.743-3.01l6.518-11.59zM11 14a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 102 0V7a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    );
  }
  if (type === 'error') {
    return (
      <svg className={common} viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7.293 7.293a1 1 0 011.414 0L10 8.586l1.293-1.293a1 1 0 111.414 1.414L11.414 10l1.293 1.293a1 1 0 01-1.414 1.414L10 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L8.586 10 7.293 8.707a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    );
  }
  return (
    <svg className={common} viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M18 10A8 8 0 11.001 10 8 8 0 0118 10zM9 9h2v6H9V9zm0-4h2v2H9V5z" />
    </svg>
  );
}

function Toaster({ toasts, onClose }) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`min-w-[260px] max-w-sm border rounded-lg shadow-md px-4 py-3 flex items-start gap-3 transition-all bg-background text-text ${
            t.type === 'success'
              ? 'border-green-300'
              : t.type === 'warning'
              ? 'border-yellow-300'
              : t.type === 'error'
              ? 'border-red-300'
              : 'border-secondary'
          }`}
          role="status"
          aria-live="polite"
        >
          <div
            className={`${
              t.type === 'success'
                ? 'text-green-600'
                : t.type === 'warning'
                ? 'text-yellow-700'
                : t.type === 'error'
                ? 'text-red-600'
                : 'text-accent'
            } mt-0.5`}
          >
            <Icon type={t.type} />
          </div>
          <div className="flex-1">
            {t.title && <div className="font-heading font-bold">{t.title}</div>}
            {t.message && <div className="font-body text-sm text-text/80">{t.message}</div>}
          </div>
          <button
            className="text-text/50 hover:text-text cursor-pointer"
            onClick={() => onClose(t.id)}
            aria-label="Dismiss notification"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}

export default Toaster;

