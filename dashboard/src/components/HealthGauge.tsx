'use client';

import { computeGaugeArc, computeHealthColor } from '@/lib/utils';

interface HealthGaugeProps {
  score: number;       // 0–1
  size?: number;
  showLabel?: boolean;
}

export default function HealthGauge({ score, size = 44, showLabel = true }: HealthGaugeProps) {
  const radius = (size - 6) / 2;
  const { circumference, offset } = computeGaugeArc(score, radius);
  const color = computeHealthColor(score);
  const displayScore = Math.round(score * 100);

  return (
    <div style={{ position: 'relative', width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-highest)"
          strokeWidth="3"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      {showLabel && (
        <span style={{
          position: 'absolute',
          fontSize: size < 40 ? '0.6rem' : '0.7rem',
          fontWeight: 700,
          fontFamily: 'var(--font-mono)',
          color,
        }}>
          {displayScore}
        </span>
      )}
    </div>
  );
}
