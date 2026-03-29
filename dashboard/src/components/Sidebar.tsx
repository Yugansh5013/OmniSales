'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';
import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { href: '/dashboard', icon: '🏠', label: 'Command Center' },
  { href: '/dashboard/prospecting', icon: '🎯', label: 'Prospecting' },
  { href: '/dashboard/pipeline', icon: '📊', label: 'Deal Pipeline' },
  { href: '/dashboard/churn', icon: '🛡️', label: 'Churn Monitor' },
  { href: '/dashboard/approvals', icon: '✅', label: 'Approvals', badge: true },
  { href: '/dashboard/thinking', icon: '🧠', label: 'Agent Thinking' },
  { href: '/dashboard/audit', icon: '📋', label: 'Audit Trail' },
  { href: '/dashboard/architecture', icon: '🔗', label: 'Architecture' },
];

interface SidebarProps {
  pendingApprovals?: number;
}

export default function Sidebar({ pendingApprovals = 0 }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      <div className={styles.logo} onClick={() => setCollapsed(!collapsed)}>
        <div className={styles.logoIcon}>⚡</div>
        {!collapsed && <span className={styles.logoText}>OmniSales</span>}
      </div>

      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/dashboard' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${isActive ? styles.active : ''}`}
              title={collapsed ? item.label : undefined}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              {!collapsed && (
                <span className={styles.navLabel}>{item.label}</span>
              )}
              {item.badge && pendingApprovals > 0 && (
                <span className={`${styles.badge} ${pendingApprovals > 0 ? styles.badgePulse : ''}`}>
                  {pendingApprovals}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className={styles.footer}>
        {!collapsed && (
          <div className={styles.userInfo}>
            <div className={styles.avatar}>A</div>
            <div className={styles.userDetails}>
              <div className={styles.userName}>Admin</div>
              <div className={styles.userOrg}>OmniSales Demo</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
