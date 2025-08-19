import React from 'react';

function BrandIcon({ name, size = 18, alt, style, autoInvert = false }) {
  const getTheme = () => {
    try { return document.documentElement.getAttribute('data-theme') || 'dark'; } catch { return 'dark'; }
  };

  const buildCandidates = (iconName, theme) => {
    // Provide simple aliases, e.g., 'openai' → 'chatgpt'
    const alias = iconName === 'openai' ? 'chatgpt' : iconName;
    const themed = (base) => (
      theme === 'light'
        ? [
            `/icons/${base}-dark.png`,
            `/icons/${base}.png`,
            `/icons/${base}-dark.svg`,
            `/icons/${base}.svg`
          ]
        : [
            `/icons/${base}-light.png`,
            `/icons/${base}.png`,
            `/icons/${base}-light.svg`,
            `/icons/${base}.svg`
          ]
    );
    // Try requested name first, then alias
    return [...themed(iconName), ...(alias !== iconName ? themed(alias) : [])];
  };

  const [theme, setTheme] = React.useState(getTheme());
  const [candidates, setCandidates] = React.useState(() => buildCandidates(name, theme));
  const [index, setIndex] = React.useState(0);

  React.useEffect(() => {
    const observer = new MutationObserver(() => setTheme(getTheme()));
    try { observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] }); } catch {}
    return () => { try { observer.disconnect(); } catch {} };
  }, []);

  React.useEffect(() => {
    setCandidates(buildCandidates(name, theme));
    setIndex(0);
  }, [name, theme]);

  const src = candidates[index] || '';

  const handleError = () => {
    setIndex(prev => (prev + 1 < candidates.length ? prev + 1 : prev));
  };

  const filterStyle = autoInvert && theme !== 'light' ? { filter: 'invert(1) brightness(1.1)' } : undefined;
  const [fitStyle, setFitStyle] = React.useState({ objectFit: 'contain' });

  const handleLoad = (e) => {
    const w = e?.currentTarget?.naturalWidth || 0;
    const h = e?.currentTarget?.naturalHeight || 0;
    if (w > h * 1.2) {
      setFitStyle({ objectFit: 'cover', objectPosition: 'left center' });
    } else {
      setFitStyle({ objectFit: 'contain' });
    }
  };

  return (
    <img
      src={src}
      onError={handleError}
      onLoad={handleLoad}
      alt={alt || name}
      width={size}
      height={size}
      style={{ display: 'inline-block', verticalAlign: 'text-bottom', ...fitStyle, ...filterStyle, ...style }}
      loading="lazy"
    />
  );
}

export default BrandIcon;


