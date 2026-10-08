/* "Entra con SPID!" - lesson 4's simulator. A fake browser in the middle, a
   bilingual explanation on the right, and the task list further right.
   Everything on the fake sites is invented; only the phone approval touches
   the server (/api/spid-game/challenge). */
(function () {
  "use strict";

  const CFG = JSON.parse(document.getElementById("spid-config").textContent);
  const STR = JSON.parse(document.getElementById("spid-strings").textContent);
  const LANG = CFG.lang;
  const RTL = CFG.rtl;
  const USER = "maria";
  const PASS = "farfalla27";
  const POLL_MS = 1500;

  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---------- strings: Italian above, the preferred language below ---------- */
  function fill(html, vars) {
    return html
      .replace(/@@CREDS@@/g, vars.creds || "")
      .replace(/@@SITE@@/g, esc(vars.site || ""))
      .replace(/@@N@@/g, esc(vars.n || ""));
  }
  function str(id, lang) {
    const e = STR[id];
    if (!e) return "";
    return e[lang] || e.it || "";
  }
  function dual(id, vars) {
    vars = vars || {};
    const it = `<div class="lang-it">${fill(str(id, "it"), vars)}</div>`;
    if (LANG === "it") return `<div class="dual">${it}</div>`;
    const other = `<div class="lang-other" lang="${LANG}" dir="${RTL ? "rtl" : "ltr"}">${fill(str(id, LANG), vars)}</div>`;
    return `<div class="dual">${it}${other}</div>`;
  }
  /* A one-line label: Italian bold, translation small underneath. */
  function dualLine(id) {
    const it = `<span class="l-it">${str(id, "it")}</span>`;
    if (LANG === "it") return it;
    return `${it}<span class="l-other" lang="${LANG}" dir="${RTL ? "rtl" : "ltr"}">${str(id, LANG)}</span>`;
  }

  /* ---------- the five tasks ---------- */
  const COMMON_HEAD = [
    { key: "search", label: "sb_search" },
    { key: "spid", label: "sb_spid" },
    { key: "provider", label: "sb_provider" },
    { key: "login", label: "sb_login" },
    { key: "phone", label: "sb_phone" },
  ];
  const COMMON_TAIL = [{ key: "logout", label: "sb_logout" }];
  const TASKS = [
    { id: "fse", title: "tk_1", search: "Fascicolo sanitario", specific: [{ key: "open", label: "sb_1" }],
      keywords: ["fascicolo sanitario", "fse", "salute", "referti", "sanitario"] },
    { id: "comune", title: "tk_2", search: "Comune di Parma",
      specific: [{ key: "pick", label: "sb_2a" }, { key: "download", label: "sb_2b" }],
      keywords: ["comune di parma", "comune", "parma", "certificati", "anagrafe", "residenza"] },
    { id: "inps", title: "tk_3", search: "INPS", specific: [{ key: "detail", label: "sb_3" }],
      keywords: ["inps", "assegno unico", "assegno", "figli"] },
    { id: "scuola", title: "tk_4", search: "Iscrizioni scuola",
      specific: [{ key: "choose", label: "sb_4a" }, { key: "send", label: "sb_4b" }],
      keywords: ["iscrizioni scuola", "scuola", "iscrizioni", "iscrizione", "istruzione"] },
    { id: "questura", title: "tk_5", search: "Questura",
      specific: [{ key: "day", label: "sb_5a" }, { key: "confirm", label: "sb_5b" }],
      keywords: ["questura", "permesso di soggiorno", "appuntamento", "prenotafacile", "prenota facile", "prenotazione"] },
  ];
  TASKS.forEach((t) => { t.subtasks = COMMON_HEAD.concat(t.specific, COMMON_TAIL); });

  /* ---------- the fake sites ---------- */
  const SITES = {
    fse: {
      name: "Fascicolo Sanitario Elettronico", addr: "fascicolo-sanitario.example", color: "#0b6e4f",
      resultTitle: "Fascicolo Sanitario Elettronico: il tuo fascicolo online",
      snippet: "Referti, ricette e vaccinazioni sempre con te. Accedi con SPID.",
      info: "Il Fascicolo Sanitario Elettronico raccoglie i tuoi documenti sanitari: referti, ricette, vaccinazioni. Puoi anche prenotare visite ed esami e cambiare il medico di famiglia.",
      spidPlace: "box",
    },
    comune: {
      name: "Comune di Parma", addr: "comune.parma.example", color: "#1a56c4",
      resultTitle: "Comune di Parma: servizi online",
      snippet: "Certificati, appuntamenti agli sportelli e servizi per i cittadini.",
      info: "Servizi online del Comune: certificati, appuntamenti agli sportelli, cambio di residenza. Con lo SPID li usi da casa, a qualsiasi ora.",
      spidPlace: "menu",
    },
    inps: {
      name: "INPS · Servizi al cittadino", addr: "inps.example", color: "#0d4c8b",
      resultTitle: "INPS: assegno unico, pensioni e servizi",
      snippet: "Assegno unico per i figli, pensioni, indennità. Accedi ai servizi.",
      info: "Pensioni, assegno unico per i figli, indennità. Accedi per vedere le tue domande e i tuoi pagamenti.",
      spidPlace: "topbutton",
    },
    scuola: {
      name: "Iscrizioni online a scuola", addr: "iscrizioni.scuola.example", color: "#7a3fb0",
      resultTitle: "Iscrizioni online: scuola dei figli",
      snippet: "Iscrivi tuo figlio a scuola da casa, di solito a gennaio e febbraio.",
      info: "Le iscrizioni a scuola si fanno online, di solito tra gennaio e febbraio. Se hai bisogno di aiuto, la segreteria della scuola può aiutarti.",
      spidPlace: "sidebar",
    },
    questura: {
      name: "Prenotazioni · Ufficio immigrazione", addr: "prenotazioni.questura.example", color: "#31478a",
      resultTitle: "Prenotazioni Questura: appuntamenti online",
      snippet: "Prenota un appuntamento per il permesso di soggiorno.",
      info: "Prenota un appuntamento per il tuo permesso di soggiorno. Porta sempre con te un documento valido.",
      spidPlace: "footer",
    },
  };

  /* ---------- state ---------- */
  const STORE_KEY = "spidGame.v1." + CFG.studentId;
  const state = {
    taskIdx: 0,
    done: [false, false, false, false, false],
    subs: {},        // completed subtask keys for the current task
    screen: "search_home",
    history: [],
    query: "",
    results: [],
    menuOpen: false,
    fails: 0,
    challenge: null, // {code, display, qr_svg}
    pollTimer: null,
    loggedIn: false,
    picked: {},      // per-task selections inside the logged-in site
    actionDone: false,
    started: false,
  };

  function save() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify({ done: state.done })); } catch (e) { /* storage may be blocked */ }
  }
  function load() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
      if (raw && Array.isArray(raw.done) && raw.done.length === 5) state.done = raw.done.map(Boolean);
    } catch (e) { /* ignore */ }
  }

  const task = () => TASKS[state.taskIdx];
  const site = () => SITES[task().id];

  /* ---------- panes ---------- */
  function setPane(keys, vars) {
    vars = Object.assign({ n: state.taskIdx + 1, site: task().search }, vars || {});
    $("#pane-body").innerHTML = keys.map((k) => dual(k, vars)).join('<hr class="pane-sep">');
    $("#pane-body").scrollTop = 0;
  }
  const CREDS_HTML =
    '<div class="creds"><div><span>Nome utente</span><b>' + USER + "</b></div><div><span>Password</span><b>" + PASS + "</b></div></div>";

  function renderTasks() {
    const html = TASKS.map((t, i) => {
      const done = state.done[i];
      const current = i === state.taskIdx && state.started && !done;
      const cls = ["task", done ? "is-done" : "", current ? "is-current" : "", !done && !current ? "is-idle" : ""].join(" ");
      let subs = "";
      if (current) {
        const next = t.subtasks.find((s) => !state.subs[s.key]);
        subs = '<ul class="subtasks">' + t.subtasks.map((s) => {
          const ok = !!state.subs[s.key];
          const here = next && next.key === s.key;
          return `<li class="${ok ? "sub-done" : ""} ${here ? "sub-now" : ""}"><span class="tick">${ok ? "✓" : here ? "▶" : "○"}</span><span class="sub-text">${dualLine(s.label)}</span></li>`;
        }).join("") + "</ul>";
      }
      return `<li class="${cls}"><div class="task-head"><span class="task-num">${done ? "✓" : i + 1}</span><span class="task-title">${dualLine(t.title)}</span></div>${subs}</li>`;
    }).join("");
    $("#task-list").innerHTML = html;
  }

  function completeSub(key) {
    if (state.subs[key]) return;
    state.subs[key] = true;
    renderTasks();
    const t = task();
    if (t.subtasks.every((s) => state.subs[s.key])) finishTask();
  }

  /* ---------- browser chrome ---------- */
  function chrome(addr, title) {
    $("#addr-text").textContent = addr;
    $("#tab-title").textContent = title;
    $("#btn-back").disabled = state.history.length === 0 || state.loggedIn || state.screen === "spid_qr";
  }

  function go(screen, opts) {
    opts = opts || {};
    if (!opts.replace && state.screen && !["spid_qr"].includes(state.screen)) state.history.push({ screen: state.screen, query: state.query, menuOpen: state.menuOpen });
    state.screen = screen;
    stopPolling();
    render();
  }

  function back() {
    const h = state.history.pop();
    if (!h) return;
    state.screen = h.screen;
    state.query = h.query;
    state.menuOpen = h.menuOpen;
    stopPolling();
    render();
  }

  /* ---------- screens ---------- */
  function render() {
    const v = $("#viewport");
    const s = state.screen;
    state.loggedIn = s === "in_site";
    if (s === "search_home" || s === "search_results") return renderSearch(v);
    if (s === "wrong_site") return renderWrong(v);
    if (s === "site") return renderSite(v);
    if (s === "spid_chooser") return renderChooser(v);
    if (s === "spid_login") return renderLogin(v);
    if (s === "spid_qr") return renderQr(v);
    if (s === "in_site") return renderIn(v);
  }

  function renderSearch(v) {
    const hasResults = state.screen === "search_results";
    chrome("cercatutto.example" + (hasResults ? "/cerca?q=" + encodeURIComponent(state.query) : ""), "Cercatutto");
    let results = "";
    if (hasResults) {
      if (!state.results.length) {
        results = '<p class="no-results">Nessun risultato per «' + esc(state.query) + "».</p>";
      } else {
        results = state.results.map((r) => {
          const si = SITES[r.id];
          return `<div class="result"><div class="r-url">${si.addr}</div><a href="#" class="r-title" data-action="open-result" data-id="${r.id}">${esc(si.resultTitle)}</a><div class="r-snip">${esc(si.snippet)}</div></div>`;
        }).join("");
      }
    }
    v.innerHTML = `
      <div class="page search ${hasResults ? "with-results" : ""}">
        <div class="logo">Cerca<span>tutto</span></div>
        <form id="search-form" class="search-form" autocomplete="off">
          <input id="q" type="text" value="${esc(state.query)}" aria-label="Cerca" placeholder="Scrivi qui cosa cerchi" autofocus>
          <button type="submit">Cerca</button>
        </form>
        <div class="results">${results}</div>
      </div>`;
    if (!hasResults) setPane(state.history.length === 0 && !state.subs.search ? ["task_" + (state.taskIdx + 1), "search_blank"] : ["search_blank"]);
    else setPane([state.results.length ? "search_results" : "search_none"]);
    const q = $("#q");
    if (q) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
  }

  function doSearch(query) {
    state.query = query;
    state.results = window.SpidFuzzy.search(query, TASKS).slice(0, 3);
    go("search_results", { replace: state.screen === "search_results" });
  }

  function openResult(id) {
    if (id !== task().id) { go("wrong_site"); return; }
    completeSub("search");
    state.menuOpen = false;
    go("site");
  }

  function renderWrong(v) {
    chrome("cercatutto.example", "Cercatutto");
    v.innerHTML = `<div class="page center-msg"><div class="big">🧭</div><h2>Questo sito è per un altro compito</h2><p>Fai clic su «Indietro» e cerca: <strong>${esc(task().search)}</strong></p></div>`;
    setPane(["wrong_site"]);
  }

  function siteHeader(si, extra) {
    return `<header class="s-head" style="background:${si.color}"><div class="s-name">${esc(si.name)}</div>${extra || ""}</header>`;
  }
  const INERT_NAV = '<nav class="s-nav"><a href="#" data-action="inert">Home</a><a href="#" data-action="inert">Servizi</a><a href="#" data-action="inert">Notizie</a><a href="#" data-action="inert">Contatti</a></nav>';
  const SPID_BTN = '<button class="spid-btn" data-action="spid">Accedi con SPID</button>';
  const CIE_BTN = '<button class="cie-btn" data-action="inert">Entra con CIE</button>';

  function renderSite(v) {
    const si = site();
    chrome(si.addr, si.name);
    const body = `<div class="s-body"><h2>Benvenuta</h2><p>${esc(si.info)}</p><p class="muted">Sito finto, creato per il gioco.</p></div>`;
    let head = "", main = "", side = "", foot = "";
    if (si.spidPlace === "menu") {
      head = siteHeader(si, `<div class="s-menu"><button class="s-menubtn" data-action="toggle-menu">Servizi online ▾</button>${state.menuOpen ? `<div class="s-drop">${SPID_BTN}${CIE_BTN}</div>` : ""}</div>`);
      main = INERT_NAV + body;
    } else if (si.spidPlace === "topbutton") {
      head = siteHeader(si, `<div class="s-menu"><button class="s-menubtn" data-action="toggle-menu">Accedi ai servizi</button>${state.menuOpen ? `<div class="s-drop">${SPID_BTN}${CIE_BTN}<button class="cie-btn" data-action="inert">Entra con CNS</button></div>` : ""}</div>`);
      main = INERT_NAV + body;
    } else if (si.spidPlace === "box") {
      head = siteHeader(si);
      main = INERT_NAV + body + `<div class="login-box"><h3>Entra nel tuo fascicolo</h3><p>Per vedere i tuoi documenti devi accedere.</p>${SPID_BTN}${CIE_BTN}</div>`;
    } else if (si.spidPlace === "sidebar") {
      head = siteHeader(si);
      side = `<aside class="s-side"><h3>Area riservata</h3><p>Accedi per iscrivere tuo figlio.</p>${SPID_BTN}${CIE_BTN}</aside>`;
      main = INERT_NAV + body;
    } else {
      head = siteHeader(si);
      main = INERT_NAV + body + '<div class="filler">Informazioni utili</div><ul class="filler-list"><li>Orari degli sportelli</li><li>Documenti necessari</li><li>Come arrivare</li><li>Domande frequenti</li></ul>';
      foot = `<footer class="s-foot"><h3>Prenotazioni online</h3><p>Per prenotare devi accedere.</p>${SPID_BTN}${CIE_BTN}</footer>`;
    }
    v.innerHTML = `<div class="page site">${head}<div class="s-layout">${side}<div class="s-main">${main}</div></div>${foot}</div>`;
    setPane([state.menuOpen && (si.spidPlace === "menu" || si.spidPlace === "topbutton") ? "site_menu" : "site_home"]);
  }

  function renderChooser(v) {
    chrome("accesso.spid.example/scegli-il-gestore", "Entra con SPID");
    const providers = ["Aruba ID", "InfoCert ID", "Poste ID", "Sielte ID", "TIM ID", "Namirial ID"];
    v.innerHTML = `<div class="page spid"><div class="spid-card"><h2>Entra con SPID</h2><p>Scegli il tuo gestore di identità digitale.</p><div class="providers">${providers.map((p) => `<button class="provider" data-action="provider" data-name="${p}">${p}</button>`).join("")}</div></div></div>`;
    setPane(["spid_chooser"]);
  }

  function renderLogin(v, msg) {
    chrome("accesso.posteid.example/login", "Poste ID · Accesso");
    v.innerHTML = `<div class="page spid"><div class="spid-card login"><div class="gestore">Poste ID <small>(finto)</small></div><h2>Accedi</h2>
      <p class="muted">Per entrare in: <strong>${esc(site().name)}</strong></p>
      <form id="login-form" autocomplete="off">
        <label for="u">Nome utente</label><input id="u" type="text" autocomplete="off" autocapitalize="none" spellcheck="false">
        <label for="p">Password</label><div class="pw"><input id="p" type="password" autocomplete="off" autocapitalize="none" spellcheck="false"><button type="button" class="eye" data-action="eye" title="Mostra o nascondi la password" aria-label="Mostra o nascondi la password">👁</button></div>
        <div class="form-msg" id="form-msg">${msg ? esc(msg) : ""}</div>
        ${state.fails >= 3 ? '<button type="button" class="helpbtn" data-action="autofill">Scrivi per me</button>' : ""}
        <button type="submit" class="enter">Entra</button>
      </form></div></div>`;
    const keys = [state.fails === 0 ? "spid_login" : "spid_login_wrong"];
    if (state.fails >= 3) keys.push("spid_login_help");
    setPane(keys, { creds: CREDS_HTML });
    const u = $("#u"); if (u) u.focus();
  }

  function tryLogin() {
    const u = $("#u").value.trim().toLowerCase();
    const p = $("#p").value.trim().toLowerCase();
    if (u === USER && p === PASS) {
      state.fails = 0;
      completeSub("login");
      startChallenge();
      return;
    }
    state.fails += 1;
    renderLogin($("#viewport"), "Nome utente o password non corretti.");
  }

  /* ---------- phone approval ---------- */
  function renderQr(v, mode) {
    chrome("accesso.posteid.example/verifica", "Poste ID · Verifica");
    const c = state.challenge;
    if (mode === "rejected" || mode === "expired" || mode === "error") {
      const text = { rejected: "Accesso rifiutato dal telefono.", expired: "Il codice è scaduto.", error: "Non riesco a creare il codice." }[mode];
      v.innerHTML = `<div class="page spid"><div class="spid-card"><div class="big">${mode === "rejected" ? "🚫" : "⌛"}</div><h2>${text}</h2><button class="enter" data-action="retry">Riprova</button></div></div>`;
      setPane(["spid_" + mode]);
      return;
    }
    if (!c) {
      v.innerHTML = '<div class="page spid"><div class="spid-card"><h2>Un momento…</h2></div></div>';
      return;
    }
    v.innerHTML = `<div class="page spid"><div class="spid-card qr"><h2>Conferma con il telefono</h2>
      <p>Inquadra il codice QR con la fotocamera del telefono e premi <strong>Approva</strong>.</p>
      <div class="qr-box">${c.qr_svg}</div>
      <p class="muted small">Il codice non funziona? Scrivi sul telefono:</p>
      <div class="qr-url">${esc(c.display)}</div>
      <div class="waiting"><span class="spin"></span> In attesa dell'approvazione…</div></div></div>`;
    setPane(["spid_qr"]);
  }

  function startChallenge() {
    state.challenge = null;
    state.screen = "spid_qr";
    renderQr($("#viewport"));
    fetch("/api/spid-game/challenge", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ service: task().id }),
    })
      .then((r) => { if (!r.ok) throw new Error("http " + r.status); return r.json(); })
      .then((c) => {
        if (state.screen !== "spid_qr") return;
        state.challenge = c;
        renderQr($("#viewport"));
        startPolling(c.code);
      })
      .catch(() => { if (state.screen === "spid_qr") renderQr($("#viewport"), "error"); });
  }

  function startPolling(code) {
    stopPolling();
    state.pollTimer = setInterval(() => {
      fetch("/api/spid-game/challenge/" + encodeURIComponent(code))
        .then((r) => (r.ok ? r.json() : { state: "error" }))
        .then((d) => {
          if (state.screen !== "spid_qr" || !state.challenge || state.challenge.code !== code) return;
          if (d.state === "approved") {
            stopPolling();
            completeSubThenEnter();
          } else if (d.state === "rejected") {
            stopPolling(); renderQr($("#viewport"), "rejected");
          } else if (d.state === "expired") {
            stopPolling(); renderQr($("#viewport"), "expired");
          }
        })
        .catch(() => { /* a missed poll is fine, the next one retries */ });
    }, POLL_MS);
  }
  function stopPolling() { if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; } }

  function completeSubThenEnter() {
    state.challenge = null;
    state.picked = {};
    state.actionDone = false;
    state.screen = "in_site";
    state.history = [];
    render();
    completeSub("phone");
  }

  /* ---------- inside the service (logged in) ---------- */
  function userBar(si) {
    return siteHeader(si, '<div class="s-user"><span>👤 Maria Rossi <small>(profilo di prova)</small></span><button class="exit-btn" data-action="logout">Esci</button></div>');
  }

  function renderIn(v) {
    const si = site();
    chrome(si.addr + "/area-personale", si.name);
    const id = task().id;
    const p = state.picked;
    let main = "";
    if (id === "fse") {
      main = `<h2>I tuoi documenti</h2><ul class="doc-list">
        <li><a href="#" data-action="doc" data-doc="blood">Analisi del sangue <small>· 12 marzo</small></a></li>
        <li><a href="#" data-action="doc" data-doc="vacc">Vaccinazione <small>· 4 novembre</small></a></li>
        <li><a href="#" data-action="doc" data-doc="visit">Visita dal medico <small>· 21 giugno</small></a></li></ul>
        ${p.doc ? `<div class="doc-view"><h3>${esc(p.doc.title)}</h3><p>${esc(p.doc.text)}</p><p class="muted small">Documento finto.</p></div>` : ""}`;
    } else if (id === "comune") {
      const kinds = [["res", "Certificato di residenza"], ["fam", "Stato di famiglia"], ["nas", "Certificato di nascita"]];
      main = `<h2>Certificati online</h2><div class="cards">${kinds.map(([k, l]) => `<button class="card ${p.cert === k ? "sel" : ""}" data-action="cert" data-cert="${k}">${l}</button>`).join("")}</div>
        <div class="row"><button class="primary" data-action="download">Scarica PDF</button></div>
        <div class="flash ${p.msg ? "show" : ""}">${p.msg ? esc(p.msg) : ""}</div>`;
    } else if (id === "inps") {
      main = `<h2>Le tue domande</h2><table class="tbl"><tr><th>Prestazione</th><th>Stato</th><th></th></tr>
        <tr><td>Assegno unico per i figli</td><td>In pagamento</td><td><button class="primary" data-action="detail">Vedi il dettaglio</button></td></tr>
        <tr><td>ISEE</td><td>Non presentata</td><td></td></tr></table>
        ${p.detail ? '<div class="doc-view"><h3>Assegno unico per i figli</h3><p>Stato: domanda accolta.</p><p>Il prossimo pagamento arriva a fine mese. <span class="muted">(Esempio finto, non è un importo vero.)</span></p></div>' : ""}`;
    } else if (id === "scuola") {
      main = `<h2>Iscrizione a scuola</h2><div class="form-grid">
        <label>Figlio o figlia</label><select id="sel-child" data-action="school-change"><option value="">Scegli…</option><option value="sara">Sara</option><option value="luca">Luca</option></select>
        <label>Scuola</label><select id="sel-school" data-action="school-change"><option value="">Scegli…</option><option value="a">Scuola primaria «Collodi»</option><option value="b">Scuola primaria «Rodari»</option></select></div>
        <div class="row"><button class="primary" data-action="send">Invia domanda</button></div>
        <div class="flash ${p.msg ? "show" : ""}">${p.msg ? esc(p.msg) : ""}</div>`;
    } else {
      const days = [["mar", "Martedì · ore 10:00"], ["mer", "Mercoledì · ore 11:30"], ["gio", "Giovedì · ore 9:00"]];
      main = `<h2>Scegli il giorno</h2><div class="cards">${days.map(([k, l]) => `<button class="card ${p.day === k ? "sel" : ""}" data-action="day" data-day="${k}">${l}</button>`).join("")}</div>
        <div class="row"><button class="primary" data-action="confirm">Conferma</button></div>
        <div class="flash ${p.msg ? "show" : ""}">${p.msg ? esc(p.msg) : ""}</div>`;
    }
    v.innerHTML = `<div class="page site">${userBar(si)}<div class="s-layout"><div class="s-main">${main}<p class="muted small foot">Sito finto, creato per il gioco.</p></div></div></div>`;
    if (id === "scuola") {
      if (p.child) $("#sel-child").value = p.child;
      if (p.school) $("#sel-school").value = p.school;
    }
    setPane([state.actionDone ? "after_action" : "in_" + (state.taskIdx + 1)]);
  }

  function actionDone() { state.actionDone = true; }
  function flash(msg) { state.picked.msg = msg; }

  function onInAction(a, el) {
    const id = task().id;
    const p = state.picked;
    if (id === "fse" && a === "doc") {
      const docs = { blood: ["Analisi del sangue", "Emocromo e valori principali: tutto nella norma."], vacc: ["Vaccinazione", "Vaccino registrato. Prossimo richiamo: tra dieci anni."], visit: ["Visita dal medico", "Visita di controllo. Nessun problema."] };
      p.doc = { title: docs[el.dataset.doc][0], text: docs[el.dataset.doc][1] };
      if (el.dataset.doc === "blood") { completeSub("open"); actionDone(); }
    } else if (id === "comune" && a === "cert") {
      p.cert = el.dataset.cert; p.msg = "";
      if (p.cert === "res") completeSub("pick");
    } else if (id === "comune" && a === "download") {
      if (p.cert !== "res") p.msg = "Prima scegli «Certificato di residenza».";
      else { p.msg = "✅ PDF scaricato (finto, nessun file vero)."; completeSub("download"); actionDone(); }
    } else if (id === "inps" && a === "detail") {
      p.detail = true; completeSub("detail"); actionDone();
    } else if (id === "scuola" && a === "school-change") {
      p.child = $("#sel-child").value; p.school = $("#sel-school").value; p.msg = "";
      if (p.child && p.school) completeSub("choose");
    } else if (id === "scuola" && a === "send") {
      if (!(p.child && p.school)) p.msg = "Prima scegli il figlio e la scuola.";
      else { p.msg = "✅ Domanda inviata (finta). Riceverai una conferma."; completeSub("send"); actionDone(); }
    } else if (id === "questura" && a === "day") {
      p.day = el.dataset.day; p.msg = ""; completeSub("day");
    } else if (id === "questura" && a === "confirm") {
      if (!p.day) p.msg = "Prima scegli un giorno.";
      else { p.msg = "✅ Appuntamento confermato (finto). Porta la ricevuta e un documento."; completeSub("confirm"); actionDone(); }
    } else { return false; }
    if (state.screen === "in_site") renderIn($("#viewport"));
    return true;
  }

  function logout() {
    const t = task();
    const allSpecific = t.specific.every((s) => state.subs[s.key]);
    if (!allSpecific) {
      state.picked.msg = "Prima finisci il compito. Poi premi «Esci».";
      renderIn($("#viewport"));
      const f = document.querySelector(".flash");
      if (!f) {
        const b = document.createElement("div");
        b.className = "flash show"; b.textContent = state.picked.msg;
        document.querySelector(".s-main").prepend(b);
      }
      return;
    }
    completeSub("logout");
  }

  /* ---------- splash / intro ---------- */
  function showOverlay(html) { const o = $("#overlay"); o.innerHTML = '<div class="overlay-card">' + html + "</div>"; o.hidden = false; }
  function hideOverlay() { $("#overlay").hidden = true; $("#overlay").innerHTML = ""; }

  function finishTask() {
    state.done[state.taskIdx] = true;
    save();
    renderTasks();
    stopPolling();
    const last = state.done.every(Boolean);
    if (last) {
      showOverlay(`<div class="confetti">🏆 🎉 ⭐</div><div class="o-title">${dualLine("final_title")}</div>${dual("final_body")}<button class="btn-big" data-action="restart">${dualLine("ui_playagain")}</button>`);
    } else {
      showOverlay(`<div class="confetti">🎉 ⭐ 🎉</div><div class="o-title">${dualLine("splash_title")}</div>${dual("splash_body", { n: state.taskIdx + 1 })}<button class="btn-big" data-action="next-task">${dualLine("ui_next")}</button>`);
    }
  }

  function startTask(i) {
    state.taskIdx = i;
    state.subs = {};
    state.history = [];
    state.query = "";
    state.results = [];
    state.menuOpen = false;
    state.fails = 0;
    state.challenge = null;
    state.picked = {};
    state.actionDone = false;
    state.screen = "search_home";
    state.started = true;
    hideOverlay();
    renderTasks();
    render();
  }

  function nextTask() {
    const next = state.done.findIndex((d) => !d);
    startTask(next === -1 ? 0 : next);
  }

  function restart() {
    state.done = [false, false, false, false, false];
    save();
    startTask(0);
  }

  function showIntro() {
    renderTasks();
    $("#viewport").innerHTML = "";
    showOverlay(`<div class="o-title">${dualLine("intro_title")}</div>${dual("intro_body")}<button class="btn-big" data-action="start">${dualLine("ui_start")}</button>`);
  }

  /* ---------- events ---------- */
  document.addEventListener("click", function (ev) {
    const el = ev.target.closest("[data-action]");
    if (!el) return;
    const a = el.dataset.action;
    if (a === "start") { if (state.done.every(Boolean)) { restart(); } else nextTask(); return; }
    if (a === "next-task") return nextTask();
    if (a === "restart") return restart();
    if (el.tagName === "A") ev.preventDefault();
    if (a === "inert" || a === "school-change") return;
    if (a === "open-result") return openResult(el.dataset.id);
    if (a === "toggle-menu") { state.menuOpen = !state.menuOpen; return render(); }
    if (a === "spid") { completeSub("spid"); return go("spid_chooser"); }
    if (a === "provider") {
      if (el.dataset.name !== "Poste ID") { const m = document.createElement("div"); m.className = "flash show"; m.textContent = "Nel gioco il tuo gestore è «Poste ID»."; document.querySelector(".spid-card").appendChild(m); return; }
      completeSub("provider"); state.fails = 0; return go("spid_login");
    }
    if (a === "eye") { const p = $("#p"); p.type = p.type === "password" ? "text" : "password"; return; }
    if (a === "autofill") { $("#u").value = USER; $("#p").value = PASS; $("#p").type = "text"; return; }
    if (a === "retry") { return startChallenge(); }
    if (a === "logout") return logout();
    onInAction(a, el);
  });
  document.addEventListener("change", function (ev) {
    const el = ev.target.closest("[data-action]");
    if (el && el.dataset.action === "school-change") onInAction("school-change", el);
  });
  document.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (ev.target.id === "search-form") return doSearch($("#q").value);
    if (ev.target.id === "login-form") return tryLogin();
  });
  $("#btn-back").addEventListener("click", back);

  /* ---------- go ---------- */
  load();
  $("#pane-head").innerHTML = dualLine("ui_now");
  $("#tasks-head").innerHTML = dualLine("ui_tasks");
  showIntro();
  window.__spid = { state, startTask, TASKS }; // for the headless test
})();
