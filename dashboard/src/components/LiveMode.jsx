import React, { useEffect, useState } from 'react';

// Live mode: poll /sim/was/rl/status (proxied by Vite to the Node-RED simulator)
// and let the user POST simple actions to /sim/was/rl/action.
export default function LiveMode({ onClose }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [ms, setMs] = useState(1000);
  const [actionType, setActionType] = useState('');
  const [actionValue, setActionValue] = useState('true');

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const r = await fetch('/sim/was/rl/status');
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!cancelled) { setStatus(data); setError(null); }
      } catch (e) {
        if (!cancelled) setError(String(e.message || e));
      }
    };
    poll();
    const id = setInterval(poll, ms);
    return () => { cancelled = true; clearInterval(id); };
  }, [ms]);

  const sendAction = async () => {
    try {
      const body = { actionType };
      try { body.value = JSON.parse(actionValue); } catch { body.value = actionValue; }
      const r = await fetch('/sim/was/rl/action', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setError(null);
    } catch (e) {
      setError(String(e.message || e));
    }
  };

  return (
    <div className="live-modal">
      <div className="live-card">
        <div className="live-head">
          <h3>Live Mode · Node-RED simulator</h3>
          <button onClick={onClose}>close</button>
        </div>
        <div className="live-body">
          <div className="live-row">
            <label>poll interval (ms)
              <input type="number" min="200" step="100" value={ms} onChange={(e) => setMs(parseInt(e.target.value, 10) || 1000)} />
            </label>
            <span className="muted">proxied to <code>{window.location.origin}/sim → Node-RED</code> (default <code>http://localhost:1882</code>)</span>
          </div>
          {error && <div className="error">⚠ {error}</div>}
          <div className="live-status">
            <div className="live-status-title">GET /was/rl/status</div>
            <pre>{status ? JSON.stringify(status, null, 2) : 'waiting…'}</pre>
          </div>
          <div className="live-action">
            <div className="live-status-title">POST /was/rl/action</div>
            <div className="live-row">
              <input placeholder="actionType (e.g. http://example.org/Z1Light)"
                     value={actionType} onChange={(e) => setActionType(e.target.value)} />
              <input placeholder="value (true/false/number)"
                     value={actionValue} onChange={(e) => setActionValue(e.target.value)} />
              <button onClick={sendAction} disabled={!actionType}>send</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
