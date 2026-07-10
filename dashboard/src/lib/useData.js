import { useEffect, useState } from 'react';

const cache = new Map();

// fetch a JSON file from public/data with a tiny module-level cache
export function useData(file) {
  const [data, setData] = useState(cache.get(file) || null);
  const [error, setError] = useState(null);
  useEffect(() => {
    let live = true;
    if (cache.has(file)) { setData(cache.get(file)); return; }
    fetch(`${import.meta.env.BASE_URL}data/${file}`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status} ${file}`); return r.json(); })
      .then((j) => { cache.set(file, j); if (live) setData(j); })
      .catch((e) => { if (live) setError(e); });
    return () => { live = false; };
  }, [file]);
  return { data, error };
}

export const fmt = (v, d = 1) =>
  v == null || Number.isNaN(v) ? '–' : Number(v).toFixed(d).replace(/\.0+$/, (m) => (d === 0 ? '' : m));

export const fmtInt = (v) => (v == null ? '–' : Math.round(Number(v)).toLocaleString('en-US'));
