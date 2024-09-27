import React, { useEffect } from 'react';

const AdSenseScript = () => {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.onerror = () => console.error('AdSense script failed to load');
    script.onload = () => console.log('AdSense script loaded successfully');
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  return null;
};

export default AdSenseScript;
