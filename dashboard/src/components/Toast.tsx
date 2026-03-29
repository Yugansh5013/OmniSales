'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './Toast.module.css';

export interface ToastMessage {
  id: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  action?: { label: string; href: string };
}

let toastListeners: Array<(toast: ToastMessage) => void> = [];

export function showToast(toast: Omit<ToastMessage, 'id'>) {
  const msg = { ...toast, id: Date.now().toString() };
  toastListeners.forEach(fn => fn(msg));
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((toast: ToastMessage) => {
    setToasts(prev => [...prev, toast]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== toast.id));
    }, 5000);
  }, []);

  useEffect(() => {
    toastListeners.push(addToast);
    return () => { toastListeners = toastListeners.filter(fn => fn !== addToast); };
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className={styles.container}>
      {toasts.map(toast => (
        <div key={toast.id} className={`${styles.toast} ${styles[toast.type || 'info']} slide-up`}>
          <span className={styles.message}>{toast.message}</span>
          {toast.action && (
            <a href={toast.action.href} className={styles.action}>{toast.action.label}</a>
          )}
        </div>
      ))}
    </div>
  );
}
