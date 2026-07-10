import React, { useState } from 'react';

// ---------- shared tooltip ----------
export function useTip() {
  const [tip, setTip] = useState(null); // {x, y, html}
  const show = (e, html) => setTip({ x: e.clientX + 12, y: e.clientY + 12, html });
  const hide = () => setTip(null);
  const node = tip ? (
    <div className="charttip" style={{ left: tip.x, top: tip.y }}
      dangerouslySetInnerHTML={{ __html: tip.html }} />
  ) : null;
  return { show, hide, node };
}

function niceTicks(max, n = 5) {
  if (max <= 0) return [0, 1];
  const raw = max / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || 10 * mag;
  const ticks = [];
  for (let v = 0; v <= max + 1e-9; v += step) ticks.push(+v.toFixed(6));
  return ticks;
}

/**
 * Horizontal grouped bar chart with optional CI whiskers.
 * groups: [{name, note, bars: [{label, value, lo, hi, color}]}]
 */
export function HBarChart({ groups, unit = '', xMax = null, refValue = null, refLabel = '', fmt = (v) => String(Math.round(v)), width = 760 }) {
  const { show, hide, node } = useTip();
  const barH = 16; const barGap = 6; const groupPad = 14; const labelW = 232; const rightPad = 74;
  const plotW = width - labelW - rightPad;
  const maxVal = xMax || Math.max(
    ...groups.flatMap((g) => g.bars.map((b) => Math.max(b.hi ?? 0, b.value))),
  ) * 1.05;
  const x = (v) => labelW + (Math.max(0, v) / maxVal) * plotW;
  const ticks = niceTicks(maxVal);

  let y = refValue != null ? 26 : 6; // leave headroom for the reference-line label
  const rows = groups.map((g) => {
    const gy = y;
    y += g.bars.length * (barH + barGap) - barGap + groupPad;
    return { ...g, y: gy };
  });
  const axisY = y + 4;
  const height = axisY + 26;

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="bar chart">
        {ticks.map((t) => (
          <g key={t}>
            <line className="gline" x1={x(t)} x2={x(t)} y1={2} y2={axisY} />
            <text className="tick" x={x(t)} y={axisY + 14} textAnchor="middle">{t}{unit && t === ticks[ticks.length - 1] ? ` ${unit}` : ''}</text>
          </g>
        ))}
        {refValue != null && (
          <g>
            <line x1={x(refValue)} x2={x(refValue)} y1={16} y2={axisY} stroke="var(--critical)" strokeWidth="1.5" />
            <text className="lbl" x={x(refValue)} y={11} fill="var(--critical)" textAnchor="middle">{refLabel}</text>
          </g>
        )}
        {rows.map((g) => (
          <g key={g.name}>
            <text className="name" x={0} y={g.y + barH - 3}>{g.name}</text>
            {g.note && <text className="lbl" x={0} y={g.y + barH + 11} fill="var(--muted)">{g.note}</text>}
            {g.bars.map((b, bi) => {
              const by = g.y + bi * (barH + barGap);
              const bw = Math.max(1.5, x(b.value) - labelW);
              return (
                <g key={b.label}
                  onMouseMove={(e) => show(e, `<b>${g.name} — ${b.label}</b><br/>${fmt(b.value)}${unit ? ` ${unit}` : ''}${b.lo != null ? `<br/>95% CI [${fmt(b.lo)}, ${fmt(b.hi)}]` : ''}`)}
                  onMouseLeave={hide}>
                  <rect x={labelW} y={by} width={bw} height={barH} fill={b.color} rx="4"
                    style={{ cursor: 'default' }} />
                  <rect x={labelW} y={by} width={Math.min(4, bw)} height={barH} fill={b.color} />
                  {b.lo != null && b.hi != null && (
                    <g stroke="var(--ink-2)" strokeWidth="1.2">
                      <line x1={x(b.lo)} x2={x(b.hi)} y1={by + barH / 2} y2={by + barH / 2} />
                      <line x1={x(b.lo)} x2={x(b.lo)} y1={by + 3.5} y2={by + barH - 3.5} />
                      <line x1={x(b.hi)} x2={x(b.hi)} y1={by + 3.5} y2={by + barH - 3.5} />
                    </g>
                  )}
                  <text className="val" x={Math.max(x(b.hi ?? b.value), x(b.value)) + 6} y={by + barH - 4}>{fmt(b.value)}</text>
                </g>
              );
            })}
          </g>
        ))}
        <line className="bline" x1={labelW} x2={labelW} y1={2} y2={axisY} />
      </svg>
      {node}
    </div>
  );
}

/**
 * Line chart for early-training curves.
 * series: [{name, color, points: [{x, y}]}]
 */
export function LineChart({ series: rawSeries, xLabel = '', yLabel = '', yMax = null, width = 760, height = 240 }) {
  const { show, hide, node } = useTip();
  const series = rawSeries.filter((s) => s.points.length > 0);
  if (series.length === 0) return <p className="note">no curve data</p>;
  const padL = 44; const padR = 110; const padT = 12; const padB = 34;
  const xs = series.flatMap((s) => s.points.map((p) => p.x));
  const xMin = Math.min(...xs); const xMax = Math.max(...xs);
  const my = yMax || Math.max(...series.flatMap((s) => s.points.map((p) => p.y))) * 1.08;
  const X = (v) => padL + ((v - xMin) / (xMax - xMin || 1)) * (width - padL - padR);
  const Y = (v) => padT + (1 - v / my) * (height - padT - padB);
  const yTicks = niceTicks(my, 4);
  const xTicks = niceTicks(xMax, 5).filter((t) => t >= xMin);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="line chart">
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line className="gline" x1={padL} x2={width - padR} y1={Y(t)} y2={Y(t)} />
            <text className="tick" x={padL - 6} y={Y(t) + 3.5} textAnchor="end">{t}</text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} className="tick" x={X(t)} y={height - padB + 16} textAnchor="middle">{t}</text>
        ))}
        <line className="bline" x1={padL} x2={width - padR} y1={Y(0)} y2={Y(0)} />
        {xLabel && <text className="lbl" x={(padL + width - padR) / 2} y={height - 4} textAnchor="middle">{xLabel}</text>}
        {yLabel && <text className="lbl" x={padL} y={10}>{yLabel}</text>}
        {series.map((s, si) => {
          const d = s.points.map((p, i) => `${i ? 'L' : 'M'}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`).join('');
          const last = s.points[s.points.length - 1];
          // suppress end labels when series converge at the right edge — the legend carries identity
          const collides = series.some((o, oi) => oi !== si
            && Math.abs(Y(o.points[o.points.length - 1].y) - Y(last.y)) < 15);
          return (
            <g key={s.name}>
              <path d={d} fill="none" stroke={s.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
              <circle cx={X(last.x)} cy={Y(last.y)} r="4" fill={s.color} stroke="var(--surface)" strokeWidth="2" />
              {!collides && <text className="lbl" x={X(last.x) + 8} y={Y(last.y) + 4}>{s.name}</text>}
              {s.points.map((p) => (
                <circle key={p.x} cx={X(p.x)} cy={Y(p.y)} r="9" fill="transparent"
                  onMouseMove={(e) => show(e, `<b>${s.name}</b><br/>${xLabel || 'x'} ${p.x}: ${p.y}${p.extra ? `<br/>${p.extra}` : ''}`)}
                  onMouseLeave={hide} />
              ))}
            </g>
          );
        })}
      </svg>
      {node}
    </div>
  );
}

export function Legend({ items }) {
  return (
    <div className="legend">
      {items.map((it) => (
        <span className="key" key={it.label}>
          <span className="swatch" style={{ background: it.color }} />{it.label}
        </span>
      ))}
    </div>
  );
}

export function Tile({ label, value, unit, delta, deltaDir, sub }) {
  return (
    <div className="tile">
      <div className="tlabel">{label}</div>
      <div className="tvalue">{value}{unit && <small> {unit}</small>}</div>
      {delta && <div className={`tdelta ${deltaDir || 'flat'}`}>{delta}</div>}
      {sub && <div className="note" style={{ marginTop: 4 }}>{sub}</div>}
    </div>
  );
}
