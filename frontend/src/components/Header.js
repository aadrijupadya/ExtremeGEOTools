import React, { useEffect, useState } from 'react';
import { getHealth } from '../services/api';

function Header() {
  const [isHealthy, setIsHealthy] = useState(false);

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

  return (
    <header className="header">
      <div className="header-content">
        <h1>ExtremeGEOTools Dashboard</h1>
        <p>Competitive Intelligence & Market Research</p>
        <div className="health-badge" aria-label="backend-health" title={isHealthy ? 'API Online' : 'API Offline'}>
          {isHealthy ? '🟢API' : '🔴API'}
        </div>
      </div>
    </header>
  );
}

export default Header;
