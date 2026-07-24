import React from 'react';
import FaultLab from '../components/FaultLab.jsx';
import { HBarChart, Legend } from '../components/charts.jsx';
import { useData, fmt } from '../lib/useData.js';

function Tier1Results({ data }) {
  const groups = data.tier1.map((row) => ({
    name: row.name,
    note: `Δ ${fmt(row.mean, 0)} ep · q ${row.q.toPrecision(2)} · ${row.verdict}`
      + (row.censored_ql_true + row.censored_ql_false > 0
        ? ` · censored ${row.censored_ql_true}/${row.censored_ql_false}` : ''),
    bars: [
      { label: 'KG-primed', value: row.mean_ql_true, color: 'var(--kg)' },
      { label: 'tabula-rasa', value: row.mean_ql_false, color: 'var(--tr)' },
    ],
  }));
  return (
    <>
      <Legend items={[{ color: 'var(--kg)', label: 'KG-primed (ql_true, n = 20 seeds)' },
        { color: 'var(--tr)', label: 'tabula-rasa (ql_false, n = 20 seeds)' }]} />
      <HBarChart groups={groups} unit="episodes" fmt={(v) => String(Math.round(v))} />
      <p className="note">
        <b>RecoveryEpisodes</b> = episodes from fault detection back to a re-converged policy over the
        surviving actuators (lower is better). A mean of 4,001 is the censoring bound (horizon 4,000 + 1):
        that arm <b>never detected the fault</b> in those replicas, so it never adapted — a seed pair is
        never dropped. Two-sided exact paired sign-flip tests over seeds 1–20, BH across the frozen m = 8
        family.
      </p>
      <details className="tblview"><summary>table view — registered Tier-1 family (m = 8, n = 20)</summary><div className="inner">
        <table className="data">
          <thead><tr><th>cell</th><th className="num">KG mean</th><th className="num">TR mean</th>
            <th className="num">Δ</th><th className="num">95% CI</th><th className="num">exact p</th>
            <th className="num">BH q</th><th className="num">censored KG/TR</th><th>verdict</th></tr></thead>
          <tbody>
            {data.tier1.map((row) => (
              <tr key={row.cell} className={row.verdict === 'supported' ? 'hl' : ''}>
                <td>{row.name}</td>
                <td className="num">{fmt(row.mean_ql_true, 1)}</td>
                <td className="num">{fmt(row.mean_ql_false, 1)}</td>
                <td className="num">{fmt(row.mean, 2)}</td>
                <td className="num">[{fmt(row.ci_lo, 1)}, {fmt(row.ci_hi, 1)}]</td>
                <td className="num">{row.p.toPrecision(3)}</td>
                <td className="num">{row.q.toPrecision(3)}</td>
                <td className="num">{row.censored_ql_true}/{row.censored_ql_false}</td>
                <td>{row.verdict}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div></details>
    </>
  );
}

export default function Phase2() {
  const { data } = useData('phase2.json');
  if (!data) return <p className="loading">loading corrected Phase 2 evidence…</p>;
  return (
    <div className="page">
      <h1>Phase 2 · The Faulty Ladder</h1>
      <div className="q"><b>Current evidence:</b> protocol <code>{data.protocol_version}</code>, detector
        {' '}<code>{data.detector_version}</code>, runs {Object.values(data.runs).join(' / ')}, 20 paired seeds,
        explicit censoring at horizon+1.</div>
      <div className="warn"><b>Protocol-v1 results are withdrawn.</b> The former "3/8 supported" record
        (and the still-earlier "all 8 significant" reading) ran on a defective scheduler and a detector
        that blacklisted healthy components — see docs/PHASE2_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md.
        The corrected record below governs; full report: docs/thesis_chapter_phase2.md §10.</div>
      <div className="q"><b>Question:</b> when a real actuator silently breaks, can the agent <b>detect</b> it
        (reality diverges from the KG prior), <b>blacklist</b> it, <b>alert</b> the user, and <b>re-learn</b> over
        what survives — and does the KG-primed arm recover faster than tabula-rasa?</div>

      <p className="lede">
        Each faulty lab is a clean Phase-1 parent whose simulator injects exactly one hardware fault (a lamp or
        blind that is <b>dead</b> or <b>inverted</b>) while the KG keeps believing the nominal physics. Both arms
        warm-load a protocol-v2 clean Q-table, so what is measured is <b>recovery from a working policy</b>, not
        learning from scratch. The agent is <b>not allowed to silently adapt</b> — it must detect first.
      </p>

      <FaultLab />

      <h2>Registered result — 2 supported, 3 adverse, 3 null</h2>
      <div className="card">
        <Tier1Results data={data} />
      </div>

      <div className="card">
        <h3>The false-positive / false-negative trade, quantified</h3>
        <p><b>Zero false-positive blacklist events</b> ({data.false_positive_blacklist_events} across all
          38 cells × 20 replicas × both arms, derived from the full per-event record): the repaired detector
          never removes a healthy component. The price is <b>policy-dependent recall</b>: a dead verdict is
          withheld while any co-feeder of the zone is active, and in cross-coupled lab3 the knowledge-primed
          policy — restoring light via the spotlight, blinds, or cross-zone lamp — never visits an unmasked
          state. KG-arm dead-lamp detection is 0/20 in every lab3 dead-lamp cell (tabula-rasa: 11–20/20),
          which is what drives the three adverse cells. Inverted faults detect instantly in both arms
          (opposite-sign evidence is never gated); all lab1/lab2 cells and all blind cells detect identically
          in both arms.</p>
        <p className="note">The corrected claim is two-sided: structural knowledge speeds recovery where
          detection succeeds and the fault demotes previously-relied-on levers (daylight substitution,
          dual-zone triage — both ~1.9× faster), and the same knowledge suppresses dead-fault detectability
          by keeping masking actuators active. Detection results are a new instrument
          (detector v2) and are not comparable to the withdrawn record. All values simulator-conditional.</p>
      </div>

      <p className="note">Sources: <code>{data.source}</code>;
        {' '}phase2_v2_corrected/CAMPAIGN_MANIFEST.md; docs/phase2_correction_registration_2026-07-22.md.</p>
    </div>
  );
}
