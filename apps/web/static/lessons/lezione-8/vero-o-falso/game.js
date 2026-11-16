/* Vero o falso? (lesson 8). The teacher drives this page on the projector;
 * students vote with paper cards. No network call except the media, which
 * are preloaded into memory when the game starts. The points of each item
 * come from the server (cfg.items[].points); this file only adds numbers.
 * State is mirrored to localStorage: team names and points only. */
(function () {
  "use strict";

  var cfg = JSON.parse(document.getElementById("vof-config").textContent);
  var app = document.getElementById("app");
  var UI = cfg.ui;
  var ITEMS = {};
  cfg.items.forEach(function (it) { ITEMS[it.id] = it; });
  var ANSWER = {};
  cfg.answers.forEach(function (a) { ANSWER[a.id] = a; });
  var COLOR = { green: "c-green", red: "c-red", yellow: "c-yellow", blue: "c-blue" };

  // ---- state ----------------------------------------------------------
  var S = freshState();
  var saved = loadSaved();
  // Runtime only (never saved).
  var R = { queue: [], pos: 0, reveal: false, remaining: 0, paused: false, timerId: null,
            blobs: {}, failed: [], muted: false, media: null, timerEl: null, progress: 0, total: 0 };

  function freshState() {
    return { teams: [{ name: "" }, { name: "" }], timer: cfg.defaults.timer, scoring: true, lang: "it",
             include: {}, votes: {}, done: {}, screen: "start", cat: null };
  }

  function loadSaved() {
    try {
      var raw = localStorage.getItem(cfg.storageKey);
      if (!raw) return null;
      var s = JSON.parse(raw);
      return s && s.teams && s.votes ? s : null;
    } catch (e) { return null; }
  }

  function save() {
    try { localStorage.setItem(cfg.storageKey, JSON.stringify(S)); } catch (e) { /* private mode */ }
  }

  function clearSaved() {
    try { localStorage.removeItem(cfg.storageKey); } catch (e) { /* ignore */ }
  }

  // ---- small helpers --------------------------------------------------
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") el.className = attrs[k];
        else if (k === "text") el.textContent = attrs[k];
        else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), attrs[k]);
        else el.setAttribute(k, attrs[k]);
      });
    }
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null || c === false) continue;
      el.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return el;
  }

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  function btn(label, onclick, cls) {
    var b = h("button", { type: "button", class: "btn " + (cls || "") }, label);
    b.addEventListener("click", function () { b.blur(); onclick(); });
    return b;
  }

  function icon(id) {
    var t = document.getElementById("icon-" + id);
    return t && t.content.firstElementChild ? t.content.firstElementChild.cloneNode(true) : h("span");
  }

  // Italian line plus, when a language is chosen and present, a smaller second line.
  function bi(obj, tag) {
    var box = h(tag || "span", {}, h("span", { text: (obj && obj.it) || "" }));
    var l = S.lang;
    if (l !== "it" && obj && obj[l]) {
      var second = h("span", { class: "l2", text: obj[l], lang: l });
      if (cfg.rtl.indexOf(l) >= 0) second.setAttribute("dir", "rtl");
      box.appendChild(second);
    }
    return box;
  }

  function ui(key) { return bi(UI[key]); }
  function uiText(key) { return (UI[key] && UI[key].it) || ""; }

  function teamName(i) {
    return S.teams[i].name || uiText("team" + (i + 1));
  }

  function scoreOf(teamIndex) {
    var total = 0;
    Object.keys(S.votes).forEach(function (id) {
      var v = S.votes[id][teamIndex];
      if (v && ITEMS[id]) total += ITEMS[id].points[v] || 0;
    });
    return total;
  }

  function go(screen) {
    stopTimer();
    S.screen = screen;
    save();
    render();
  }

  // ---- timer ----------------------------------------------------------
  function stopTimer() {
    if (R.timerId) { clearInterval(R.timerId); R.timerId = null; }
  }

  function paintTimer() {
    if (!R.timerEl) return;
    if (R.paused) {
      R.timerEl.textContent = "⏸ " + uiText("paused");
      R.timerEl.className = "timer";
    } else if (R.remaining <= 0) {
      R.timerEl.textContent = "🗳️ " + uiText("vote");
      R.timerEl.className = "timer vote";
    } else {
      R.timerEl.textContent = String(R.remaining);
      R.timerEl.className = "timer";
    }
  }

  function startTimer() {
    stopTimer();
    R.timerId = setInterval(function () {
      if (R.paused || R.reveal) return;
      if (R.remaining > 0) {
        R.remaining -= 1;
        paintTimer();
        if (R.remaining === 0) stopTimer();
      }
    }, 1000);
  }

  function togglePause() {
    if (S.screen !== "item" || R.remaining <= 0) return;
    R.paused = !R.paused;
    if (!R.paused && !R.timerId) startTimer();
    paintTimer();
    var vid = R.media && R.media.tagName === "VIDEO" ? R.media : null;
    if (vid) { if (R.paused) vid.pause(); else vid.play(); }
  }

  // ---- sound (a gentle chime on the reveal, nothing for wrong answers) -
  function chime() {
    if (R.muted) return;
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      var ctx = new Ctx();
      [660, 880].forEach(function (freq, i) {
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        gain.gain.value = 0.08;
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + i * 0.15);
        osc.stop(ctx.currentTime + i * 0.15 + 0.15);
      });
      setTimeout(function () { ctx.close(); }, 600);
    } catch (e) { /* no audio: fine */ }
  }

  // ---- preloading -----------------------------------------------------
  function mediaSrc(item) {
    return R.blobs[item.id] || item.mediaUrl;
  }

  function preload(done) {
    var list = cfg.items.filter(function (it) { return it.available && it.mediaUrl; });
    R.progress = 0;
    R.total = list.length;
    R.failed = [];
    R.blobs = {};
    S.screen = "loading";
    render();
    if (!list.length) { done(); return; }
    var i = 0;
    function next() {
      if (i >= list.length) { done(); return; }
      var item = list[i++];
      fetch(item.mediaUrl)
        .then(function (r) { if (!r.ok) throw new Error("bad"); return r.blob(); })
        .then(function (b) { R.blobs[item.id] = URL.createObjectURL(b); })
        .catch(function () { R.failed.push(item.id); })
        .then(function () { R.progress += 1; paintProgress(); next(); });
    }
    next();
  }

  function paintProgress() {
    var el = document.getElementById("progress");
    if (el) el.textContent = R.progress + " / " + R.total;
  }

  // ---- queues ---------------------------------------------------------
  function catById(id) {
    for (var i = 0; i < cfg.categories.length; i++) if (cfg.categories[i].id === id) return cfg.categories[i];
    return null;
  }

  function included(id) { return S.include[id] !== false; }

  function playable(id) {
    var it = ITEMS[id];
    return it && it.available && included(id) && !S.done[id];
  }

  function startCategory(catId) {
    var cat = catById(catId);
    R.queue = cat.items.filter(playable);
    S.cat = catId;
    R.pos = 0;
    if (!R.queue.length) { go("catend"); return; }
    openItem();
  }

  function openItem() {
    R.reveal = false;
    R.paused = false;
    R.remaining = S.timer;
    S.screen = "item";
    save();
    render();
    startTimer();
  }

  function nextItem() {
    var id = R.queue[R.pos];
    if (id) S.done[id] = true;
    R.pos += 1;
    if (R.pos >= R.queue.length) { go("catend"); return; }
    openItem();
  }

  function skipItem() {
    R.pos += 1;
    if (R.pos >= R.queue.length) { go("catend"); return; }
    openItem();
  }

  function revealItem() {
    stopTimer();
    R.reveal = true;
    S.screen = "reveal";
    save();
    render();
    chime();
  }

  function backToItem() {
    stopTimer();
    R.reveal = false;
    R.paused = true;
    S.screen = "item";
    save();
    render();
    paintTimer();
  }

  // ---- media ----------------------------------------------------------
  function mediaBlock(item, small) {
    R.media = null;
    var box = h("div", { class: small ? "stage small" : "stage" });
    if (item.mockHtml) {
      var wrap = h("div", { class: "mock-wrap" });
      wrap.innerHTML = item.mockHtml; // committed content; teacher text already escaped by the server
      box.appendChild(wrap);
    } else if (item.mediaType === "image") {
      box.appendChild(h("img", { src: mediaSrc(item), alt: item.alt || "" }));
    } else if (item.mediaType === "video") {
      var v = h("video", { src: mediaSrc(item), playsinline: "", preload: "auto" });
      if (small) v.controls = true;
      else { v.autoplay = true; R.media = v; }
      box.appendChild(v);
      if (!small) {
        box.appendChild(btn("↻ " + uiText("replay"), function () { v.currentTime = 0; v.play(); }, "small"));
      }
    } else if (item.mediaType === "audio") {
      var a = new Audio(mediaSrc(item));
      var label = h("span", { text: "▶ " + uiText("listen") });
      var play = h("button", { type: "button", class: "playbtn" }, label);
      play.addEventListener("click", function () {
        a.currentTime = 0;
        a.play();
        label.textContent = "↻ " + uiText("replay");
      });
      R.media = a;
      box.appendChild(play);
    }
    return box;
  }

  function tags(item) {
    var out = [];
    if (item.invented) out.push(h("span", { class: "tag", text: "🧪 " + uiText("invented") }));
    return out;
  }

  // ---- screens --------------------------------------------------------
  function renderStart() {
    var root = h("div", { class: "center" });
    root.appendChild(h("h1", {}, bi(UI.title)));
    root.appendChild(h("p", {}, bi(UI.subtitle)));
    if (saved) {
      root.appendChild(btn("▶ " + uiText("resume"), function () {
        S = saved;
        saved = null;
        S.screen = "menu";
        preload(function () { go("menu"); });
      }, "primary"));
      root.appendChild(document.createTextNode(" "));
      root.appendChild(btn(uiText("newGame"), function () { clearSaved(); saved = null; render(); }));
    }
    var form = h("div", { class: "center" });

    var counts = h("div", { class: "seg" });
    [2, 3].forEach(function (n) {
      var b = h("button", { type: "button", "aria-pressed": String(S.teams.length === n), text: String(n) });
      b.addEventListener("click", function () {
        while (S.teams.length < n) S.teams.push({ name: "" });
        S.teams.length = n;
        render();
      });
      counts.appendChild(b);
    });
    form.appendChild(h("div", { class: "row" }, h("span", { class: "lbl", text: uiText("teams") }), counts));

    var names = h("div", { class: "row" });
    S.teams.forEach(function (t, i) {
      var inp = h("input", { type: "text", maxlength: "20", placeholder: uiText("team" + (i + 1)), "aria-label": uiText("team" + (i + 1)) });
      inp.value = t.name;
      inp.addEventListener("input", function () { S.teams[i].name = inp.value; });
      names.appendChild(inp);
    });
    form.appendChild(names);

    var timers = h("div", { class: "seg" });
    cfg.defaults.timers.forEach(function (s) {
      var b = h("button", { type: "button", "aria-pressed": String(S.timer === s), text: String(s) });
      b.addEventListener("click", function () { S.timer = s; render(); });
      timers.appendChild(b);
    });
    form.appendChild(h("div", { class: "row" }, h("span", { class: "lbl", text: uiText("timer") }), timers,
      h("span", { text: uiText("seconds") })));

    var sc = h("div", { class: "seg" });
    [[true, "scoringOn"], [false, "scoringOff"]].forEach(function (pair) {
      var b = h("button", { type: "button", "aria-pressed": String(S.scoring === pair[0]), text: uiText(pair[1]) });
      b.addEventListener("click", function () { S.scoring = pair[0]; render(); });
      sc.appendChild(b);
    });
    form.appendChild(h("div", { class: "row" }, h("span", { class: "lbl", text: uiText("scoring") }), sc));

    if (cfg.langs.length > 1) {
      var ls = h("div", { class: "seg" });
      cfg.langs.forEach(function (l) {
        var b = h("button", { type: "button", "aria-pressed": String(S.lang === l), text: cfg.langNames[l] || l });
        b.addEventListener("click", function () { S.lang = l; render(); });
        ls.appendChild(b);
      });
      form.appendChild(h("div", { class: "row" }, h("span", { class: "lbl", text: uiText("language") }), ls));
    }
    root.appendChild(form);

    var missing = cfg.items.filter(function (it) { return !it.available; });
    var fallback = cfg.items.filter(function (it) { return it.available && it.usesFallback; });
    if (missing.length) {
      root.appendChild(h("div", { class: "note warn" },
        "📦 " + uiText("missing") + ": " + missing.map(function (it) { return it.id; }).join(", ") + " ➜ ",
        h("a", { href: cfg.materialsUrl, target: "_blank", rel: "noopener", text: cfg.materialsUrl })));
    }
    if (fallback.length) {
      root.appendChild(h("div", { class: "note" },
        "🧪 " + uiText("fallbackTag") + ": " + fallback.map(function (it) { return it.id; }).join(", ")));
    }
    root.appendChild(h("p", {}, btn(uiText("start"), function () {
      S.screen = "menu";
      preload(function () { go("menu"); });
    }, "primary")));
    return root;
  }

  function renderLoading() {
    var root = h("div", { class: "center" });
    root.appendChild(h("h2", {}, bi(UI.preparing)));
    root.appendChild(h("p", { id: "progress", text: R.progress + " / " + R.total }));
    return root;
  }

  function renderMenu() {
    var root = h("div", {});
    root.appendChild(h("div", { class: "topbar" },
      h("h2", { class: "grow" }, bi(UI.menu)),
      btn("🔈", function () { R.muted = !R.muted; }, "small"),
      btn("⛶", toggleFullscreen, "small")));
    if (R.failed.length) {
      root.appendChild(h("div", { class: "note warn", text: "⚠️ " + R.failed.join(", ") }));
    }
    var tiles = h("div", { class: "tiles" });
    cfg.categories.forEach(function (cat) {
      var doneCount = cat.items.filter(function (id) { return S.done[id]; }).length;
      var tile = h("div", { class: "tile" });
      var goBtn = h("button", { type: "button", class: "go" },
        h("span", { class: "emoji", text: cat.emoji }),
        bi(cat.label),
        h("span", { class: "count", text: doneCount + " / " + cat.items.length + " ✓" }));
      goBtn.addEventListener("click", function () { startCategory(cat.id); });
      tile.appendChild(goBtn);
      var chips = h("div", { class: "chips" });
      cat.items.forEach(function (id) {
        var it = ITEMS[id];
        var mark = S.done[id] ? " ✓" : !it.available ? " 📦" : it.usesFallback ? " 🧪" : "";
        var chip = h("button", { type: "button", class: "chip", text: id + mark, "aria-pressed": String(included(id)) });
        if (!it.available) chip.disabled = true;
        chip.addEventListener("click", function () {
          S.include[id] = !included(id);
          save();
          chip.setAttribute("aria-pressed", String(included(id)));
        });
        chips.appendChild(chip);
      });
      tile.appendChild(chips);
      tiles.appendChild(tile);
    });
    root.appendChild(tiles);
    root.appendChild(h("p", { class: "center" }, btn("🏁 " + uiText("finish"), function () { go("final"); }, "primary")));
    return root;
  }

  function answerReminders() {
    var row = h("div", { class: "reminders" });
    cfg.answers.forEach(function (a) {
      row.appendChild(h("div", { class: "reminder " + COLOR[a.color] }, icon(a.id), bi(a.word)));
    });
    return row;
  }

  function teamVotes(item) {
    var box = h("div", {});
    S.teams.forEach(function (t, ti) {
      var row = h("div", { class: "teamrow" }, h("span", { class: "tname", text: teamName(ti) }));
      cfg.answers.forEach(function (a) {
        var b = h("button", { type: "button", class: "vote-btn " + COLOR[a.color], "aria-pressed": "false", "aria-label": a.word.it },
          icon(a.id), h("span", { text: a.word.it }));
        var current = S.votes[item.id] && S.votes[item.id][ti];
        if (current === a.id) b.setAttribute("aria-pressed", "true");
        b.addEventListener("click", function () {
          if (!S.votes[item.id]) S.votes[item.id] = {};
          S.votes[item.id][ti] = a.id;
          save();
          Array.prototype.forEach.call(row.querySelectorAll(".vote-btn"), function (other) {
            other.setAttribute("aria-pressed", String(other === b));
          });
          b.blur();
        });
        row.appendChild(b);
      });
      box.appendChild(row);
    });
    return box;
  }

  function renderItem() {
    var item = ITEMS[R.queue[R.pos]];
    var cat = catById(S.cat);
    var root = h("div", { style: "display:flex;flex-direction:column;gap:0.5em;flex:1;" });
    R.timerEl = h("div", { class: "timer" });
    var langBtn = cfg.langs.length > 1 ? btn("🌐 " + (cfg.langNames[S.lang] || S.lang), nextLang, "small") : null;
    root.appendChild(h("div", { class: "topbar" },
      h("div", { class: "grow" }, bi(cat.label), " " + cat.emoji + " " + (R.pos + 1) + " / " + R.queue.length),
      R.timerEl, langBtn,
      btn(R.muted ? "🔇" : "🔈", function () { R.muted = !R.muted; render(); }, "small"),
      btn("⛶", toggleFullscreen, "small")));
    var stage = mediaBlock(item, false);
    var cap = item.caption && item.caption.it ? h("div", { class: "caption", text: item.caption.it }) : null;
    if (cap) stage.insertBefore(cap, stage.firstChild);
    tags(item).forEach(function (t) { stage.appendChild(t); });
    root.appendChild(stage);
    root.appendChild(answerReminders());
    if (S.scoring) root.appendChild(teamVotes(item));
    root.appendChild(h("div", { class: "controls" },
      btn("⏸ " + uiText("paused"), togglePause, "small"),
      btn(uiText("reveal"), revealItem, "primary"),
      btn(uiText("skip"), skipItem, "small")));
    paintTimer();
    return root;
  }

  function renderReveal() {
    var item = ITEMS[R.queue[R.pos]];
    var a = ANSWER[item.answer];
    var root = h("div", { style: "display:flex;flex-direction:column;gap:0.5em;flex:1;" });
    root.appendChild(h("div", { class: "answer-panel " + COLOR[a.color] },
      icon(a.id),
      h("div", {}, h("div", { class: "big" }, bi(a.word)), h("div", { class: "sub" }, bi(a.sub)))));
    var stage = mediaBlock(item, true);
    root.appendChild(stage);
    var info = h("div", { class: "info" });
    info.appendChild(h("p", {}, "💡 ", h("strong", { text: uiText("clue") + ": " }), bi(item.clue)));
    info.appendChild(h("p", {}, "👉 ", h("strong", { text: uiText("action") + ": " }), bi(item.action)));
    if (item.invented) info.appendChild(h("p", {}, h("span", { class: "tag", text: "🧪 " + uiText("invented") })));
    if (item.link) {
      var p = h("p", {}, h("strong", { text: uiText("source") + ": " }));
      if (/^https?:\/\//.test(item.link)) {
        p.appendChild(h("a", { href: item.link, target: "_blank", rel: "noopener", text: item.link }));
      } else {
        p.appendChild(document.createTextNode(item.link));
      }
      info.appendChild(p);
    }
    var wrap = h("div", { class: "center" }, info);
    wrap.firstChild.style.margin = "0 auto";
    root.appendChild(wrap);
    root.appendChild(h("div", { class: "controls" },
      btn("← " + uiText("back"), backToItem, "small"),
      btn(uiText("next") + " →", nextItem, "primary")));
    return root;
  }

  function scoreBars() {
    var bars = h("div", { class: "bars" });
    var max = 1;
    S.teams.forEach(function (t, i) { max = Math.max(max, scoreOf(i)); });
    S.teams.forEach(function (t, i) {
      var s = scoreOf(i);
      var fill = h("div", { text: s + " " + uiText("points") });
      fill.style.width = Math.max(18, Math.round((100 * s) / max)) + "%";
      bars.appendChild(h("div", {}, h("div", { text: teamName(i), style: "font-weight:800" }), h("div", { class: "bar" }, fill)));
    });
    return bars;
  }

  function renderCatEnd() {
    var root = h("div", { class: "center" });
    root.appendChild(h("h1", {}, bi(UI.categoryDone), " 🎉"));
    if (S.scoring) root.appendChild(scoreBars());
    root.appendChild(btn(uiText("toMenu"), function () { go("menu"); }, "primary"));
    return root;
  }

  function renderFinal() {
    var root = h("div", { class: "center" });
    root.appendChild(h("h1", {}, bi(UI.final)));
    if (S.scoring) root.appendChild(scoreBars());
    root.appendChild(h("h2", {}, bi(UI.habitsTitle)));
    var ul = h("ul", { class: "habits" });
    cfg.habits.forEach(function (hb) { ul.appendChild(h("li", {}, hb.emoji + " ", bi(hb))); });
    root.appendChild(ul);
    root.appendChild(h("p", {}, btn(uiText("toMenu"), function () { go("menu"); }, "small"), " ",
      btn(uiText("newGame"), function () { clearSaved(); saved = null; S = freshState(); R.queue = []; go("start"); clearSaved(); })));
    return root;
  }

  function render() {
    R.timerEl = null;
    if (R.media && R.media.pause) { try { R.media.pause(); } catch (e) { /* ignore */ } }
    R.media = null;
    clear(app);
    var screens = { start: renderStart, loading: renderLoading, menu: renderMenu, item: renderItem,
                    reveal: renderReveal, catend: renderCatEnd, final: renderFinal };
    app.appendChild((screens[S.screen] || renderStart)());
  }

  // ---- keys and misc --------------------------------------------------
  function nextLang() {
    var i = cfg.langs.indexOf(S.lang);
    S.lang = cfg.langs[(i + 1) % cfg.langs.length];
    save();
    var keep = R.remaining;
    render();
    R.remaining = keep;
    paintTimer();
  }

  function toggleFullscreen() {
    try {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen();
    } catch (e) { /* not available */ }
  }

  function playMedia() {
    var m = R.media;
    if (!m) return;
    try { m.currentTime = 0; m.play(); } catch (e) { /* ignore */ }
  }

  document.addEventListener("keydown", function (e) {
    var t = e.target;
    if (t && /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return;
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    var k = e.key;
    var isBtn = t && t.tagName === "BUTTON";
    if (k === "f" || k === "F") { toggleFullscreen(); return; }
    if (k === "l" || k === "L") { if (cfg.langs.length > 1) nextLang(); return; }
    if (S.screen === "item") {
      if (k === " ") { e.preventDefault(); togglePause(); }
      else if (k === "r" || k === "R" || k === "ArrowRight") { revealItem(); }
      else if (k === "s" || k === "S") { skipItem(); }
      else if (k === "p" || k === "P") { playMedia(); }
      else if (k === "m" || k === "M") { go("menu"); }
    } else if (S.screen === "reveal") {
      if (k === "ArrowRight" || (k === "Enter" && !isBtn)) { nextItem(); }
      else if (k === "ArrowLeft") { backToItem(); }
      else if (k === "m" || k === "M") { go("menu"); }
    }
  });

  render();
})();
