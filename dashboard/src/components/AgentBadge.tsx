'use client';

import { getAgentBadgeClass, getAgentIcon } from '@/lib/utils';
import styles from './AgentBadge.module.css';

interface AgentBadgeProps {
  agent: string;
  showIcon?: boolean;
  size?: 'sm' | 'md';
}

export default function AgentBadge({ agent, showIcon = true, size = 'md' }: AgentBadgeProps) {
  return (
    <span className={`badge ${getAgentBadgeClass(agent)} ${styles.agentBadge} ${size === 'sm' ? styles.sm : ''}`}>
      {showIcon && <span>{getAgentIcon(agent)}</span>}
      <span>{agent.charAt(0).toUpperCase() + agent.slice(1)}</span>
    </span>
  );
}
