'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth';
import { useWebSocket, WSEvent } from '@/lib/websocket';
import { fetchDashboardStats } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import ToastContainer, { showToast } from '@/components/Toast';
import OrchestratorChat from '@/components/OrchestratorChat';
import styles from './dashboard.module.css';

function DashboardShell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [pendingApprovals, setPendingApprovals] = useState(0);

  // Fetch initial approval count
  useEffect(() => {
    fetchDashboardStats()
      .then(stats => setPendingApprovals(stats.pending_approvals))
      .catch(() => { /* API not available */ });
  }, [pathname]);

  const handleWSEvent = useCallback((event: WSEvent) => {
    if (event.type === 'new_approval') {
      setPendingApprovals(prev => prev + 1);
      showToast({ message: `New approval from ${event.agent || 'agent'}`, type: 'info' });
    }
    if (event.type === 'approval_resolved') {
      setPendingApprovals(prev => Math.max(0, prev - 1));
    }
    if (event.type === 'stats_update' && typeof event.pending_approvals === 'number') {
      setPendingApprovals(event.pending_approvals as number);
    }
  }, []);

  useWebSocket(handleWSEvent);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <span>Loading OmniSales...</span>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className={styles.shell}>
      <Sidebar pendingApprovals={pendingApprovals} />
      <main className={styles.main}>
        {children}
      </main>
      <OrchestratorChat />
      <ToastContainer />
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <DashboardShell>{children}</DashboardShell>
    </AuthProvider>
  );
}
