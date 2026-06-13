import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { parseTrace, viewState } from './lib/parseTrace.js';
import { classifyStep, weaknessHistogram } from './lib/weakness.js';
import ZoneGrid from './components/ZoneGrid.jsx';
import DecisionTrace from './components/DecisionTrace.jsx';
import WeaknessPanel from './components/WeaknessPanel.jsx';
import Timeline from './components/Timeline.jsx';
import RawDrawer from './components/RawDrawer.jsx';
import LiveMode from './components/LiveMode.jsx';

const DEMO = '/demo-traces/custom2-w1-demo.jsonl';
const DEMO_C9 = '/demo-traces/custom9-ql-true-demo.jsonl';

export default function App() {
  const [text, setText] = useState('');
  const [sourceLabel, setSourceLabel] = useState('');
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(2);
  const [showLive, setShowLive] = useState(false);

  // Auto-load demo on first mount.
  useEffect(() => {
    fetch(DEMO).then((r) => r.text()).then((t) => {
      setText(t);
      setSourceLabel(`demo: ${DEMO}`);
    });
  }, []);

  const { schema, steps } = useMemo(() => parseTrace(text || ''), [text]);

  useEffect(() => { setIndex(0); setPlaying(false); }, [text]);

  const step = steps[index];
  const classification = useMemo(
    () => (step ? classifyStep(step, schema) : { observed: [], predicted: [], mismatches: [], tags: [], reasons: [] }),
    [step, schema]
  );
  const view = useMemo(() => (step ? viewState(schema, step.stateAfter) : { zones: {}, shared: {} }), [step, schema]);
  const histogram = useMemo(() => weaknessHistogram(steps, schema), [steps, schema]);

  const onUpload = useCallback((file) => {
    const r = new FileReader();
    r.onload = () => { setText(String(r.result || '')); setSourceLabel(`file: ${file.name}`); };
    r.readAsText(file);
  }, []);

  const loadDemo = () => {
    fetch(DEMO).then((r) => r.text()).then((t) => { setText(t); setSourceLabel(`demo: ${DEMO}`); });
  };

  const loadDemoC9 = () => {
    fetch(DEMO_C9).then((r) => r.text()).then((t) => { setText(t); setSourceLabel(`demo: ${DEMO_C9}`); });
  };

  const classifyTags = useCallback((i) => classifyStep(steps[i], schema).tags, [steps, schema]);
  const mismatchSlots = (classification.mismatches || []).map((m) => m.slot);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">◈</div>
          <div>
            <div className="brand-title">Agent Trace Cockpit</div>
            <div className="brand-sub">MT-Esra · stereotype-guided Q-learning for smart-building illuminance</div>
          </div>
        </div>
        <div className="topbar-actions">
          <label className="upload-btn">
            load .jsonl
            <input type="file" accept=".jsonl,.json,.txt" onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])} hidden />
          </label>
          <button onClick={loadDemo}>load demo (W1)</button>
          <button onClick={loadDemoC9}>load demo (custom9)</button>
          <button className="primary" onClick={() => setShowLive(true)}>live mode</button>
        </div>
      </header>

      <div className="source-strip">
        <span className={`pill ${schema.isDemo ? 'pill-demo' : 'pill-real'}`}>
          {schema.isDemo ? 'DEMO FIXTURE' : 'BENCHMARK TRACE'}
        </span>
        <span className="muted">{sourceLabel || '—'}</span>
        <span className="muted">·</span>
        <span className="muted">{schema.label || ''}</span>
        <span className="muted">·</span>
        <span className="muted">{steps.length} steps</span>
      </div>

      {!step && (
        <div className="empty-state">
          <div>No steps loaded yet. Load a JSONL trace or click <em>load demo (W1)</em>.</div>
        </div>
      )}

      {step && (
        <div className="grid">
          <div className="col left"><ZoneGrid schema={schema} view={view} observed={classification.observed} mismatchSlots={mismatchSlots} /></div>
          <div className="col center">
            <DecisionTrace schema={schema} step={step} classification={classification} totalSteps={steps.length} index={index} />
            <RawDrawer step={step} schema={schema} />
          </div>
          <div className="col right"><WeaknessPanel classification={classification} histogram={histogram} /></div>
        </div>
      )}

      {step && (
        <Timeline
          steps={steps}
          index={index}
          setIndex={setIndex}
          playing={playing}
          setPlaying={setPlaying}
          speed={speed}
          setSpeed={setSpeed}
          classifyTags={classifyTags}
        />
      )}

      <footer className="footer">
        <span>Research question: do component-level stereotypes generalise to whole-lab behaviour, or do unmodelled effects (W1–W6) emerge under composition?</span>
      </footer>

      {showLive && <LiveMode onClose={() => setShowLive(false)} />}
    </div>
  );
}
