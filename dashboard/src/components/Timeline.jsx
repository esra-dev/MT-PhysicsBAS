import React, { useEffect, useRef } from 'react';

export default function Timeline({ steps, index, setIndex, playing, setPlaying, speed, setSpeed, classifyTags }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setIndex((i) => {
        if (i >= steps.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, Math.max(60, 1000 / speed));
    return () => clearInterval(id);
  }, [playing, speed, steps.length, setIndex, setPlaying]);

  // keep selected tick in view
  useEffect(() => {
    const el = ref.current?.querySelector(`[data-i="${index}"]`);
    if (el) el.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' });
  }, [index]);

  const prev = () => setIndex((i) => Math.max(0, i - 1));
  const next = () => setIndex((i) => Math.min(steps.length - 1, i + 1));

  return (
    <div className="timeline-panel">
      <div className="tl-controls">
        <button onClick={prev} title="previous">⏮</button>
        <button className="primary" onClick={() => setPlaying((p) => !p)}>
          {playing ? '⏸ pause' : '▶ play'}
        </button>
        <button onClick={next} title="next">⏭</button>
        <label className="speed">
          speed
          <input type="range" min="0.5" max="8" step="0.5" value={speed}
                 onChange={(e) => setSpeed(parseFloat(e.target.value))} />
          <span>{speed.toFixed(1)}×</span>
        </label>
        <span className="tl-counter">step {index + 1} / {steps.length}</span>
      </div>
      <div className="tl-track" ref={ref}>
        {steps.map((s, i) => {
          const tags = classifyTags ? classifyTags(i) : [];
          const cls = ['tick'];
          if (i === index) cls.push('sel');
          if (tags.length > 0) cls.push('fire');
          return (
            <button
              key={i}
              data-i={i}
              className={cls.join(' ')}
              onClick={() => setIndex(i)}
              title={`step ${i + 1} · action #${s.actionIdx}${tags.length ? ' · ' + tags.join(', ') : ''}`}
            >
              <span className="tick-i">{i + 1}</span>
              {tags.length > 0 && <span className="tick-fire">!</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
