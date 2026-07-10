import React from 'react';
import FaultLab from '../components/FaultLab.jsx';
import { HBarChart, Legend } from '../components/charts.jsx';
import { useData, fmt } from '../lib/useData.js';

// the 8 registered Tier-1 confirmatory cells (frozen family, m = 8)
const TIER1 = [
  'lab3_f1dead', 'lab3_f1dead_z2', 'lab3_f1bdead', 'lab3_f1binv',
  'lab2_f1bdead', 'labmon_f1dead', 'lab3_f2dead_lowsun', 'labmon2_f2dead_lowsun',
];
const NICE = {
  lab3_f1dead: 'lab3 · Z1 lamp dead',
  lab3_f1dead_z2: 'lab3 · Z2 lamp dead',
  lab3_f1bdead: 'lab3 · Z1 blind dead',
  lab3_f1binv: 'lab3 · Z1 blind inverted',
  lab2_f1bdead: 'lab2 · Z1 blind dead',
  labmon_f1dead: 'labmon · lamp dead',
  lab3_f2dead_lowsun: 'lab3 · both lamps dead, low sun',
  labmon2_f2dead_lowsun: 'labmon2 · both lamps dead, low sun',
};

function RecoveryResults() {
  const { data } = useData('phase2.json');
  if (!data) return <p className="loading">loading results…</p>;
  const ci = (profile, mode) => data.ci.find((r) => r.profile === profile && r.mode === mode);
  const paired = (profile) => data.paired.find((r) => r.profile === profile && r.metric === 'RecoveryEpisodes');

  const groups = TIER1.map((p) => {
    const t = ci(p, 'ql_true'); const f = ci(p, 'ql_false'); const pr = paired(p);
    if (!t || !f) return null;
    return {
      name: NICE[p] || p,
      note: pr ? `Δ ${fmt(+pr.mean_diff_true_minus_false, 0)} ep · δ ${fmt(+pr.cliffs_delta, 2)} · q ${(+pr.q_bootstrap_bh).toPrecision(2)}` : '',
      bars: [
        { label: 'KG-primed', value: +t.RecoveryEpisodes_mean, lo: +t.RecoveryEpisodes_ci_lo, hi: +t.RecoveryEpisodes_ci_hi, color: 'var(--kg)' },
        { label: 'tabula-rasa', value: +f.RecoveryEpisodes_mean, lo: +f.RecoveryEpisodes_ci_lo, hi: +f.RecoveryEpisodes_ci_hi, color: 'var(--tr)' },
      ],
    };
  }).filter(Boolean);

  return (
    <>
      <Legend items={[{ color: 'var(--kg)', label: 'KG-primed (ql_true)' }, { color: 'var(--tr)', label: 'tabula-rasa (ql_false)' }]} />
      <HBarChart groups={groups} unit="episodes" fmt={(v) => String(Math.round(v))} />
      <p className="note">
        <b>RecoveryEpisodes</b> = episodes from fault detection back to a re-converged policy over the surviving actuators
        (lower is better). Bars are per-arm means over 10 paired seeds, whiskers the bootstrap 95% CI. Note the tabula-rasa
        arm's enormous variance on the blind faults (CI up to ~2,000 episodes): under the ε-boost it sometimes wanders for
        hundreds of episodes, while the KG arm stays tight — the prior is a <b>speed and a reliability</b> lever.
        Detection itself is near-simultaneous in both arms; the gap is pure re-learning speed.
      </p>
      <details className="tblview"><summary>table view — registered paired tests (BH family m = 8)</summary><div className="inner">
        <table className="data">
          <thead><tr><th>cell</th><th className="num">KG mean</th><th className="num">TR mean</th><th className="num">Δ (true−false)</th><th className="num">95% CI</th><th className="num">Wilcoxon p</th><th className="num">Cliff δ</th><th className="num">BH q</th></tr></thead>
          <tbody>
            {TIER1.map((p) => {
              const r = paired(p);
              if (!r) return null;
              return (
                <tr key={p}>
                  <td>{NICE[p] || p}</td>
                  <td className="num">{fmt(+r.ql_true_mean, 0)}</td>
                  <td className="num">{fmt(+r.ql_false_mean, 0)}</td>
                  <td className="num">{fmt(+r.mean_diff_true_minus_false, 0)}</td>
                  <td className="num">[{fmt(+r.ci_lo, 0)}, {fmt(+r.ci_hi, 0)}]</td>
                  <td className="num">{(+r.p_wilcoxon).toPrecision(2)}</td>
                  <td className="num">{fmt(+r.cliffs_delta, 2)}</td>
                  <td className="num">{(+r.q_bootstrap_bh).toPrecision(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div></details>
    </>
  );
}

export default function Phase2() {
  return (
    <div className="page">
      <h1>Phase 2 · The Faulty Ladder</h1>
      <div className="q"><b>Question:</b> when a real actuator silently breaks, can the agent <b>detect</b> it (reality diverges
        from the KG prior), <b>blacklist</b> it, <b>alert</b> the user, and <b>re-learn</b> over what survives — and does the
        KG-primed arm recover faster than tabula-rasa?</div>

      <p className="lede">
        Each faulty lab is a clean Phase-1 parent whose simulator injects exactly one hardware fault (a lamp or blind that is
        <b> dead</b> or <b>inverted</b>) while the KG keeps believing the nominal physics. Both arms warm-load their clean Phase-1
        Q-table, so what is measured is <b>recovery from a working policy</b>, not learning from scratch. Crucially, the agent is
        <b> not allowed to silently adapt</b> — working around broken physics was exactly the behavior the advisors rejected.
      </p>

      <FaultLab />

      <h2>Registered result — recovery speed across the 8 confirmatory cells</h2>
      <div className="card">
        <RecoveryResults />
      </div>
      <p className="note">
        Pre-registered analysis (frozen §9 family, m = 8): all 8 Tier-1 cells significant, max q = 0.0012; the
        <code> lab3_f1dead</code> cell was additionally confirmed on fresh seeds 11–20 as a registered one-shot replication
        (run 28913465680). Detection shows <b>no arm advantage</b> (Δ = +1.7 ep, ns) — by design, since both arms use the same
        detector; the KG advantage is in what happens <i>after</i> the blacklist. Cells where no surviving actuator can reach
        the target (e.g. lab1's only lamp) are <i>ill-posed</i> for recovery and reported descriptively: the agent still
        detects, alerts, and degrades to best-effort instead of pretending to succeed.
      </p>
    </div>
  );
}
