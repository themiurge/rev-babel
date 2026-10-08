/* Typo-tolerant matching for the SPID game's fake search engine.
   Works in the browser (window.SpidFuzzy) and in Node (module.exports). */
(function (root) {
  const STOP = new Set(["di", "il", "la", "lo", "del", "della", "e", "a", "in", "per", "un", "una", "le", "i"]);

  function norm(s) {
    return String(s)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9 ]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  // Optimal-string-alignment distance: a swapped pair of letters costs 1.
  function distance(a, b) {
    const m = a.length, n = b.length;
    const d = [];
    for (let i = 0; i <= m; i++) { d.push(new Array(n + 1).fill(0)); d[i][0] = i; }
    for (let j = 0; j <= n; j++) d[0][j] = j;
    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
        }
      }
    }
    return d[m][n];
  }

  function similarity(a, b) {
    if (!a.length || !b.length) return 0;
    return 1 - distance(a, b) / Math.max(a.length, b.length);
  }

  function tokens(s) {
    return norm(s).split(" ").filter((t) => t && !STOP.has(t));
  }

  // How well a typed query matches one keyword (0..1).
  function keywordScore(query, keyword) {
    const q = norm(query), k = norm(keyword);
    if (!q || !k) return 0;
    let best = similarity(q, k);
    const qt = tokens(q), kt = tokens(k);
    if (qt.length && kt.length) {
      let total = 0;
      for (const t of qt) {
        let top = 0;
        for (const w of kt) {
          // Very short words must match exactly: one wrong letter in "fse" is a different word.
          const s = Math.min(t.length, w.length) <= 3 ? (t === w ? 1 : 0) : similarity(t, w);
          if (s > top) top = s;
        }
        total += top;
      }
      best = Math.max(best, total / qt.length);
    }
    return best;
  }

  const THRESHOLD = 0.74;

  // services: [{id, keywords: [...]}]  ->  [{id, score}] best first, only real matches.
  function search(query, services) {
    const out = [];
    for (const svc of services) {
      let top = 0;
      for (const kw of svc.keywords) top = Math.max(top, keywordScore(query, kw));
      if (top >= THRESHOLD) out.push({ id: svc.id, score: top });
    }
    out.sort((x, y) => y.score - x.score);
    return out;
  }

  const api = { norm, distance, similarity, keywordScore, search, THRESHOLD };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SpidFuzzy = api;
})(typeof window !== "undefined" ? window : globalThis);
