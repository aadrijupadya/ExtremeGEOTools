import React from 'react';

/**
 * Simple brand icon component for displaying engine icons
 * Used throughout the app to show OpenAI and Perplexity logos
 */
function BrandIcon({ name, size = 16, style = {} }) {
  const iconStyle = {
    width: size,
    height: size,
    display: 'inline-block',
    ...style
  };

  // Map engine names to their respective icons
  const getIconSrc = (engineName) => {
    const normalizedName = (engineName || '').toLowerCase();
    
    if (normalizedName.includes('chatgpt') || normalizedName.includes('openai') || normalizedName.includes('gpt')) {
      return '/icons/chatgpt.png';
    }
    
    if (normalizedName.includes('perplexity')) {
      return '/icons/perplexity.png';
    }
    
    // Default fallback
    return '/icons/chatgpt.png';
  };

  const getAltText = (engineName) => {
    const normalizedName = (engineName || '').toLowerCase();
    
    if (normalizedName.includes('chatgpt') || normalizedName.includes('openai') || normalizedName.includes('gpt')) {
      return 'OpenAI';
    }
    
    if (normalizedName.includes('perplexity')) {
      return 'Perplexity';
    }
    
    return 'Engine';
  };

  return (
    <img 
      src={getIconSrc(name)}
      alt={getAltText(name)}
      style={iconStyle}
      onError={(e) => {
        // Fallback to emoji if image fails to load
        e.target.style.display = 'none';
        e.target.nextSibling.style.display = 'inline';
      }}
    />
  );
}

export default BrandIcon;
