'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth';
import styles from './login.module.css';

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('admin@omnisales.ai');
  const [password, setPassword] = useState('hackathon2026');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`${styles.container} gradient-bg`}>
      <div className={styles.card}>
        <div className={styles.logoArea}>
          <div className={styles.logo}>⚡</div>
          <h1 className={styles.title}>OmniSales</h1>
          <p className={styles.subtitle}>The Autonomous Revenue Department</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className={styles.input}
              placeholder="admin@omnisales.ai"
              required
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className={styles.input}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button type="submit" className={`btn btn-primary ${styles.submit}`} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In →'}
          </button>
        </form>

        <div className={styles.demo}>
          <span className="text-label">Demo Credentials</span>
          <div className={styles.demoCredentials}>
            <code>admin@omnisales.ai</code> / <code>hackathon2026</code>
          </div>
        </div>

        <div className={styles.footer}>
          <span>Powered by</span>
          <span className={styles.footerTech}>LangGraph · MCP · A2A</span>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthProvider>
      <LoginForm />
    </AuthProvider>
  );
}
