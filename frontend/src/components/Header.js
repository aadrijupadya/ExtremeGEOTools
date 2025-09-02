import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { getHealth } from '../services/api';

function Header() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'dark';
    return localStorage.getItem('egt.theme') || 'dark';
  });

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await getHealth();
        if (mounted) setIsHealthy(!!res?.ok);
      } catch (_) {
        if (mounted) setIsHealthy(false);
      }
    };
    check();
    const id = setInterval(check, 15000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  useEffect(() => {
    try {
      const root = document.documentElement;
      if (theme === 'light') root.setAttribute('data-theme', 'light');
      else root.removeAttribute('data-theme');
      localStorage.setItem('egt.theme', theme);
    } catch {}
  }, [theme]);

  return (
    <header className="header" style={{ borderBottom: '1px solid var(--border)' }}>
      <div className="header-content" style={{ maxWidth: 1200, margin: '0 auto', textAlign: 'left', padding: '0 1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <img 
              src="/geo_logo.png" 
              alt="GEO Logo" 
              style={{ 
                width: '40px', 
                height: '40px', 
                borderRadius: '8px',
                objectFit: 'contain'
              }} 
            />
            <div>
              <h1 style={{ margin: 0 }}>GEO Dashboard</h1>
              <p style={{ margin: 0 }}>Competitive Intelligence & Market Research</p>
            </div>
          </div>
          <nav style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : undefined} style={{ textDecoration: 'none', color: 'var(--muted)', padding: '0.5rem 0.75rem', borderRadius: 8 }}>Home</NavLink>
            <NavLink to="/query" className={({ isActive }) => isActive ? 'active' : undefined} style={{ textDecoration: 'none', color: 'var(--muted)', padding: '0.5rem 0.75rem', borderRadius: 8 }}>Query</NavLink>
            <NavLink to="/costs" className={({ isActive }) => isActive ? 'active' : undefined} style={{ textDecoration: 'none', color: 'var(--muted)', padding: '0.5rem 0.75rem', borderRadius: 8 }}>Costs</NavLink>
            <NavLink to="/results" className={({ isActive }) => isActive ? 'active' : undefined} style={{ textDecoration: 'none', color: 'var(--muted)', padding: '0.5rem 0.75rem', borderRadius: 8 }}>Results</NavLink>
            <NavLink to="/metrics" className={({ isActive }) => isActive ? 'active' : undefined} style={{ textDecoration: 'none', color: 'var(--muted)', padding: '0.5rem 0.75rem', borderRadius: 8 }}>Metrics</NavLink>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginLeft: 8 }}>
              <div className="theme-switch" role="switch" aria-checked={theme === 'light'} onClick={() => setTheme(prev => (prev === 'light' ? 'dark' : 'light'))}>
                <span className="icon moon">🌙</span>
                <span className="icon sun">☀️</span>
                <div className="knob" />
              </div>
              <span className={`health-dot ${isHealthy ? 'ok' : 'err'}`} title={isHealthy ? 'API online' : 'API offline'} />
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header;
