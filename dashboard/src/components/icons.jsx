import React from 'react';

// tiny inline icon set (stroke = currentColor)
const I = ({ children, size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

export const LampIcon = ({ on, size }) => (
  <I size={size}>
    <path d="M9 18h6" /><path d="M10 21h4" />
    <path d="M12 3a6 6 0 0 1 3.6 10.8c-.6.5-.9 1.3-.9 2.2h-5.4c0-.9-.3-1.7-.9-2.2A6 6 0 0 1 12 3z"
      fill={on ? 'currentColor' : 'none'} fillOpacity={on ? 0.28 : 0} />
    {on && <><path d="M12 0.6v1" /><path d="M4.2 4.2l1 1" /><path d="M19.8 4.2l-1 1" /></>}
  </I>
);

export const BlindIcon = ({ on, size }) => (
  <I size={size}>
    <rect x="4" y="3" width="16" height="18" rx="1.5" />
    {on
      ? <><path d="M4 7h16" /><circle cx="12" cy="10" r="1" fill="currentColor" /><path d="M12 8.6v-2" /></>
      : <><path d="M4 7h16" /><path d="M4 10.5h16" /><path d="M4 14h16" /><path d="M4 17.5h16" /></>}
  </I>
);

export const SpotIcon = ({ on, size }) => (
  <I size={size}>
    <path d="M8 4h8l-1.5 5h-5z" fill={on ? 'currentColor' : 'none'} fillOpacity={on ? 0.28 : 0} />
    <path d="M12 2v2" />
    {on && <><path d="M9.5 11l-2.5 8" /><path d="M14.5 11l2.5 8" /><path d="M12 11v9" /></>}
  </I>
);

export const PlugIcon = ({ on, size }) => (
  <I size={size}>
    <path d="M9 3v5" /><path d="M15 3v5" />
    <path d="M6 8h12v3a6 6 0 0 1-6 6 6 6 0 0 1-6-6z"
      fill={on ? 'currentColor' : 'none'} fillOpacity={on ? 0.28 : 0} />
    <path d="M12 17v4" />
  </I>
);

export const SunIcon = ({ size = 20 }) => (
  <I size={size}>
    <circle cx="12" cy="12" r="4.2" fill="currentColor" fillOpacity="0.3" />
    <path d="M12 2.5v2.5" /><path d="M12 19v2.5" /><path d="M2.5 12h2.5" /><path d="M19 12h2.5" />
    <path d="M5 5l1.8 1.8" /><path d="M17.2 17.2l1.8 1.8" /><path d="M5 19l1.8-1.8" /><path d="M17.2 6.8l1.8-1.8" />
  </I>
);

export const MoonIcon = ({ size = 20 }) => (
  <I size={size}><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z" fill="currentColor" fillOpacity="0.15" /></I>
);

export const AlertIcon = ({ size = 18 }) => (
  <I size={size}>
    <path d="M12 3L2.5 20h19z" /><path d="M12 9.5v4.5" /><circle cx="12" cy="17" r="0.4" fill="currentColor" />
  </I>
);

export function actuatorIcon(kind, on, size = 16) {
  switch (kind) {
    case 'lamp': case 'lampBad': return <LampIcon on={on} size={size} />;
    case 'blind': return <BlindIcon on={on} size={size} />;
    case 'spot': return <SpotIcon on={on} size={size} />;
    case 'plug': return <PlugIcon on={on} size={size} />;
    default: return <LampIcon on={on} size={size} />;
  }
}
