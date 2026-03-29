'use client';

import { useState, useRef, useEffect } from 'react';
import { orchestratorChat } from '@/lib/api';
import styles from './OrchestratorChat.module.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SUGGESTED_PROMPTS = [
  'What is the current pipeline status?',
  'Show me at-risk deals',
  'Which accounts have high churn risk?',
  'Run a full system scan',
];

export default function OrchestratorChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const msg = text || input;
    if (!msg.trim() || isLoading) return;

    const userMsg: Message = { role: 'user', content: msg, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await orchestratorChat(msg) as { response?: string };
      const assistantMsg: Message = {
        role: 'assistant',
        content: res.response || JSON.stringify(res),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to reach orchestrator'}`,
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* FAB Button */}
      <button className={styles.fab} onClick={() => setIsOpen(!isOpen)} title="Chat with Orchestrator">
        <span className={styles.fabIcon}>{isOpen ? '✕' : '🧠'}</span>
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className={`${styles.panel} slide-right`}>
          <div className={styles.header}>
            <div className={styles.headerLeft}>
              <span className={styles.headerIcon}>🧠</span>
              <div>
                <div className={styles.headerTitle}>Orchestrator</div>
                <div className={styles.headerSub}>OmniSales AI Command</div>
              </div>
            </div>
            <button className={styles.closeBtn} onClick={() => setIsOpen(false)}>✕</button>
          </div>

          <div className={styles.messages}>
            {messages.length === 0 && (
              <div className={styles.welcome}>
                <div className={styles.welcomeIcon}>🧠</div>
                <h3>OmniSales Orchestrator</h3>
                <p>Ask me about pipeline, deals, risks, or trigger agent scans.</p>
                <div className={styles.suggestions}>
                  {SUGGESTED_PROMPTS.map(p => (
                    <button key={p} className={styles.suggestion} onClick={() => sendMessage(p)}>
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`${styles.message} ${styles[msg.role]}`}>
                <div className={styles.messageContent}>{msg.content}</div>
                <div className={styles.messageTime}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className={`${styles.message} ${styles.assistant}`}>
                <div className={styles.typing}>
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className={styles.inputArea}>
            <input
              className={styles.input}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Ask the Orchestrator..."
              disabled={isLoading}
            />
            <button className={styles.sendBtn} onClick={() => sendMessage()} disabled={isLoading || !input.trim()}>
              ↑
            </button>
          </div>
        </div>
      )}
    </>
  );
}
