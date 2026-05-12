import React, { useState } from 'react';

export default function RawDrawer({ step, schema }) {
  const [open, setOpen] = useState(false);
  if (!step) return null;
  return (
    <div className={`raw-drawer ${open ? 'open' : ''}`}>
      <button className="raw-toggle" onClick={() => setOpen((v) => !v)}>
        {open ? '▾' : '▸'} raw evidence (JSONL row)
      </button>
      {open && (
        <pre className="raw-json">{JSON.stringify(step, null, 2)}</pre>
      )}
      {open && schema?.isDemo && (
        <div className="demo-note">
          ⚠ This trace is a clearly-labeled DEMO fixture, not real benchmark output.
          Schema: <code>{schema.label}</code>
        </div>
      )}
    </div>
  );
}
