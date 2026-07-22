import React, { useEffect, useState } from 'react';
import Overview from './pages/Overview.jsx';
import Phase1 from './pages/Phase1.jsx';
import Phase2 from './pages/Phase2.jsx';
import Phase3 from './pages/Phase3.jsx';
import Phase4 from './pages/Phase4.jsx';

const PAGES = [
  { id: 'overview', label: 'Overview', sub: 'the story & the ladder', el: Overview },
  { id: 'phase1', label: 'Phase 1 · Clean', sub: 'KG accelerates learning', el: Phase1 },
  { id: 'phase2', label: 'Phase 2 · Faults', sub: 'detect · blacklist · re-learn', el: Phase2 },
  { id: 'phase3', label: 'Phase 3 · Dynamics', sub: 'learn delays, write back', el: Phase3 },
  { id: 'phase4', label: 'Phase 4 · Knowledge', sub: 'plug gate & energy', el: Phase4 },
];

function currentPage() {
  const h = window.location.hash.replace(/^#\/?/, '');
  return PAGES.some((p) => p.id === h) ? h : 'overview';
}

export default function App() {
  const [page, setPage] = useState(currentPage);

  useEffect(() => {
    const onHash = () => { setPage(currentPage()); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const go = (id) => { window.location.hash = `/${id}`; };
  const Active = PAGES.find((p) => p.id === page).el;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          MT-Esra Demo
          <small>Knowledge-guided Q-learning for smart-building control</small>
        </div>
        <nav aria-label="phases">
          {PAGES.map((p) => (
            <button key={p.id} type="button"
              className={`navlink ${page === p.id ? 'active' : ''}`}
              onClick={() => go(p.id)}>
              {p.label}
              <span className="sub">{p.sub}</span>
            </button>
          ))}
        </nav>
        <div className="foot">
          All numbers come from the repo's real benchmark logs and registered CI analyses —
          the sandboxes re-implement each lab's exact simulator physics.
        </div>
      </aside>
      <main className="main">
        <Active go={go} />
      </main>
    </div>
  );
}
