import React from 'react';

function EngineIcon({ engine, size = 18, style }) {
  const common = { width: size, height: size, style: { display: 'inline-block', verticalAlign: 'text-bottom', ...style } };
  const color = 'currentColor';
  const strokeW = 2;

  if ((engine || '').toLowerCase() === 'openai') {
    // Simplified OpenAI swirl
    return (
      <svg {...common} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3.5c2.2 0 4 1.8 4 4 0 .6-.14 1.17-.39 1.68M9.5 4.4c-1.9.7-3 2.8-2.5 4.8.15.58.43 1.1.8 1.55M5.6 9.5c-.7 1.9.1 4 1.9 4.9.54.27 1.13.41 1.72.41M6.7 14.5c1.3 1.5 3.6 1.8 5.2.6.48-.35.86-.79 1.13-1.28M11.9 16.8c2.1.1 3.9-1.6 4-3.7.02-.6-.1-1.2-.34-1.75M16.6 11.3c.9-1.8.2-4-1.6-5-.52-.3-1.1-.46-1.7-.5" />
        <circle cx="12" cy="12" r="8.5" opacity="0.15" />
      </svg>
    );
  }

  if ((engine || '').toLowerCase() === 'perplexity') {
    // Simplified Perplexity P in a circle
    return (
      <svg {...common} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M9 16V8h4a3 3 0 1 1 0 6h-2" />
      </svg>
    );
  }

  return (
    <svg {...common} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW}>
      <rect x="5" y="5" width="14" height="14" rx="3" />
    </svg>
  );
}

export default EngineIcon;
