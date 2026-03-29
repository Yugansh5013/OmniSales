'use client';

import styles from './StatCard.module.css';
import Sparkline from './Sparkline';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: number[];
  trendLabel?: string;
  icon?: string;
  color?: 'blue' | 'green' | 'amber' | 'rose' | 'purple';
  pulse?: boolean;
}

export default function StatCard({ label, value, trend, trendLabel, icon, color = 'blue', pulse }: StatCardProps) {
  const colorMap: Record<string, string> = {
    blue: 'var(--closer)',
    green: 'var(--guardian)',
    amber: 'var(--warning)',
    rose: 'var(--danger)',
    purple: 'var(--prospector)',
  };

  return (
    <div className={`${styles.card} ${pulse ? 'pulse' : ''}`} style={{ borderTopColor: colorMap[color] }}>
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        {icon && <span className={styles.icon}>{icon}</span>}
      </div>
      <div className={styles.value} style={{ color: colorMap[color] }}>{value}</div>
      <div className={styles.footer}>
        {trend && trend.length > 1 && <Sparkline values={trend} width={60} height={20} color={colorMap[color]} />}
        {trendLabel && <span className={styles.trendLabel}>{trendLabel}</span>}
      </div>
    </div>
  );
}
