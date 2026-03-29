'use client';

import { computeSparklinePath, computeTrendDirection } from '@/lib/utils';

interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  color?: string;
}

export default function Sparkline({ values, width = 80, height = 24, color }: SparklineProps) {
  if (!values || values.length < 2) return null;

  const trend = computeTrendDirection(values);
  const strokeColor = color || (trend === 'up' ? 'var(--success)' : trend === 'down' ? 'var(--danger)' : 'var(--text-muted)');
  const path = computeSparklinePath(values, width, height);

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
