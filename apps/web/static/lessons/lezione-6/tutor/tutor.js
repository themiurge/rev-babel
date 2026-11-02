// Lesson 6: "Impara a usare un chatbot". Seven short missions beside a chat
// with the tutor. Every label is shown in Italian with the student's language
// under it. The conversation lives only in this page's memory (no cookie, no
// localStorage) and is wiped when the mission changes or the tab closes; the
// server keeps none of it either. See docs/decisions/0018-lesson-6-tutor-chatbot.md.
(function () {
  "use strict";

  const CFG = JSON.parse(document.getElementById("tutor-config").textContent);
  const UI = CFG.content.ui;
  const MISSIONS = CFG.content.missions;
  const LANG = CFG.lang;
  const DIR = CFG.rtl ? "rtl" : "ltr";
  const RECAP = MISSIONS.length; // index of the closing "rules" page

  const state = {
    index: 0,
    done: new Set(),
    history: [], // [{role, text}] for the current mission only
    replyLang: LANG === "it" ? "it" : "both",
    busy: false,
  };

  const $ = (id) => document.getElementById(id);
  const log = $("log");
  const input = $("input");
  const send = $("send");

  // ---- small builders ----

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function fill(text, vars) {
    return Object.keys(vars || {}).reduce((t, k) => t.split(`@@${k}@@`).join(vars[k]), text);
  }

  // Italian on top, the student's language under it (absent for Italian).
  function dual(node, pair, vars) {
    node.replaceChildren();
    node.append(el("span", "l-it", fill(pair.it, vars)));
    if (pair.other) {
      const other = el("span", "l-other", fill(pair.other, vars));
      other.lang = LANG;
      other.dir = DIR;
      node.append(other);
    }
    return node;
  }

  function ui(key, vars) {
    return dual(el("span"), UI[key], vars);
  }

  // Same patterns as tutor.py: the server is the guarantee, this check just
  // means such a message never leaves the browser at all.
  const SENSITIVE = [
    /\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b/i,
    /\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/i,
    /[\w.+-]+@[\w-]+\.[\w.-]+/,
    /(?:\+?\d[\s.\-\/]?){9,}/,
    /\b[A-Z]{2}\d{5,}[A-Z]{0,2}\b/i,
    /\b(?:password|passw|pin|otp)\b[^.?!\n]{0,20}?(?:\sè(?=\s|$)|:|=)\s*\S+/i,
  ];
  const looksSensitive = (text) => SENSITIVE.some((re) => re.test(text));

  // ---- the static parts ----

  function renderChrome() {
    dual($("back"), UI.back);
    dual($("title"), UI.title);
    dual(send, UI.send);
    dual($("clear"), UI.clear);
    input.placeholder = UI.placeholder.it;
    input.maxLength = CFG.maxLength;

    const head = $("chat-head");
    head.replaceChildren();
    const privacy = dual(el("div", "privacy"), UI.privacy);
    const note = el("div", "note");
    note.append(ui(CFG.live ? "note_live" : "note_clear"));
    if (CFG.live) note.append(ui("note_clear"));
    head.append(privacy, note);

    if (!CFG.live) {
      $("offline").hidden = false;
      dual($("offline"), UI.offline_banner);
    }

    // "Rispondi in:" only makes sense when there is a second language.
    if (LANG !== "it") {
      const reply = $("reply");
      reply.hidden = false;
      reply.setAttribute("aria-label", UI.reply_in.it);
      reply.append(dual(el("span", "lbl"), UI.reply_in));
      const options = [
        ["it", UI.italiano.it],
        [LANG, CFG.langName],
        ["both", `${UI.both.it}${UI.both.other ? " · " + UI.both.other : ""}`],
      ];
      for (const [value, label] of options) {
        const b = el("button", "", label);
        b.type = "button";
        b.dataset.value = value;
        b.addEventListener("click", () => {
          state.replyLang = value;
          syncReply();
        });
        reply.append(b);
      }
      syncReply();
    }
  }

  function syncReply() {
    for (const b of $("reply").querySelectorAll("button")) {
      b.setAttribute("aria-pressed", String(b.dataset.value === state.replyLang));
    }
  }

  function renderStrip() {
    const strip = $("strip");
    strip.replaceChildren();
    MISSIONS.forEach((m, i) => {
      const b = el("button", state.done.has(m.id) ? "done" : "", `${m.icon} ${i + 1}`);
      b.type = "button";
      b.title = m.title.it + (m.title.other ? " · " + m.title.other : "");
      if (i === state.index) b.setAttribute("aria-current", "step");
      b.addEventListener("click", () => go(i));
      strip.append(b);
    });
    const r = el("button", "", `⭐ ${UI.recap_nav.it}`);
    r.type = "button";
    if (state.index === RECAP) r.setAttribute("aria-current", "step");
    r.addEventListener("click", () => go(RECAP));
    strip.append(r);
  }

  // ---- the mission pane ----

  function useText(text) {
    input.value = text;
    input.focus();
    input.setSelectionRange(text.length, text.length);
    if (window.matchMedia("(max-width: 900px)").matches) {
      input.scrollIntoView({behavior: "smooth", block: "center"});
    }
    updateCounter();
  }

  function renderMission() {
    const body = $("mission-body");
    const foot = $("mission-foot");
    body.replaceChildren();
    foot.replaceChildren();
    body.scrollTop = 0;

    if (state.index === RECAP) {
      body.append(dual(el("div", "m-title"), UI.recap_title));
      const rules = el("ol", "rules");
      for (const key of ["r1", "r2", "r3", "r4", "r5"]) rules.append(dual(el("li"), UI[key]));
      body.append(rules);
      body.append(dual(el("p", "tip"), UI.finished));
      const restart = dual(el("button", "btn alt"), UI.restart);
      restart.type = "button";
      restart.addEventListener("click", () => {
        state.done.clear();
        go(0);
      });
      foot.append(restart);
      return;
    }

    const m = MISSIONS[state.index];
    body.append(el("div", "count", fill(UI.mission_n.it, {N: state.index + 1, T: MISSIONS.length})));
    const title = dual(el("div", "m-title"), m.title);
    title.firstChild.textContent = `${m.icon} ${m.title.it}`;
    body.append(title, dual(el("p", "goal"), m.goal));
    if (m.tip) body.append(dual(el("div", "tip"), m.tip));

    if (m.bad && m.good !== null && m.good !== undefined) {
      const good = m.chips[m.good].prompt;
      const compare = el("div", "compare");
      const bad = el("div", "ex bad");
      bad.append(dual(el("div", "tag"), UI.bad_label), dual(el("div", "q"), m.bad));
      const ok = el("div", "ex good");
      ok.append(dual(el("div", "tag"), UI.good_label), dual(el("div", "q"), good));
      const use = dual(el("button", "use"), UI.use_this);
      use.type = "button";
      use.addEventListener("click", () => useText(good.it));
      ok.append(use);
      compare.append(bad, ok);
      body.append(compare);
    }

    const why = el("div", "why");
    why.append(dual(el("b"), UI.why), dual(el("div"), m.why));
    body.append(why);

    body.append(dual(el("div", "chips-lbl"), UI.chips_label));
    const chips = el("div", "chips");
    for (const chip of m.chips) {
      const b = dual(el("button", "chip"), chip.prompt);
      b.type = "button";
      b.addEventListener("click", () => useText(chip.prompt.it));
      chips.append(b);
    }
    body.append(chips);

    const prev = dual(el("button", "btn alt"), UI.prev);
    prev.type = "button";
    prev.disabled = state.index === 0;
    prev.style.visibility = state.index === 0 ? "hidden" : "visible";
    prev.addEventListener("click", () => go(state.index - 1));
    const next = dual(el("button", "btn"), UI.next);
    next.type = "button";
    next.addEventListener("click", () => go(state.index + 1));
    foot.append(prev, next);
  }

  // ---- the chat ----

  function scrollLog() {
    log.scrollTop = log.scrollHeight;
  }

  function addYou(text) {
    const li = el("li", "msg you");
    li.append(el("div", "who", UI.you.it), el("p", "", text));
    li.lastChild.dir = "auto";
    log.append(li);
    scrollLog();
  }

  function addBot(blocks, opts) {
    opts = opts || {};
    const li = el("li", "msg bot" + (opts.cls ? " " + opts.cls : ""));
    const who = el("div", "who", "🤖 Tutor");
    if (opts.example) who.append(el("span", "ex-tag", UI.example_tag.it));
    li.append(who);
    for (const text of blocks) {
      const p = el("p", "", text);
      p.dir = "auto";
      li.append(p);
    }
    if (opts.notice) li.append(dual(el("div", "notice"), UI[opts.notice]));
    log.append(li);
    scrollLog();
    return li;
  }

  function addWarning(noticeKey) {
    const li = el("li", "msg warn");
    li.append(dual(el("p"), UI[noticeKey]));
    log.append(li);
    scrollLog();
  }

  function hello() {
    const pair = UI.bot_hello;
    addBot(pair.other ? [pair.it, pair.other] : [pair.it]);
  }

  function clearChat() {
    state.history = [];
    log.replaceChildren();
    hello();
  }

  function updateCounter() {
    const left = CFG.maxLength - input.value.length;
    $("counter").textContent = left < 80 ? String(left) : "";
  }

  function setBusy(busy) {
    state.busy = busy;
    send.disabled = busy;
  }

  async function submit() {
    const text = input.value.trim();
    if (!text || state.busy || state.index === RECAP) return;
    if (looksSensitive(text)) {
      // Not sent, not kept on screen: the warning is the lesson.
      input.value = "";
      updateCounter();
      addWarning("notice_blocked");
      return;
    }
    input.value = "";
    updateCounter();
    addYou(text);
    setBusy(true);
    const typing = addBot([UI.typing.it], {cls: "typing"});
    const mission = MISSIONS[state.index].id;
    let data = null;
    try {
      const response = await fetch("/api/tutor", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          mission,
          reply_lang: state.replyLang,
          message: text,
          history: state.history.slice(-CFG.historyTurns),
        }),
      });
      if (response.status === 401) {
        location.href = "/";
        return;
      }
      data = (response.headers.get("content-type") || "").includes("json")
        ? await response.json()
        : null;
      if (response.status === 400 || response.status === 422) {
        data = {kind: "invalid", blocks: [], notice: "notice_invalid"};
      }
    } catch (err) {
      data = null;
    } finally {
      typing.remove();
      setBusy(false);
    }
    // The mission may have changed while waiting: that chat is gone.
    if (MISSIONS[state.index] === undefined || MISSIONS[state.index].id !== mission) return;

    if (!data || !data.kind) {
      addBot([], {notice: "notice_error"});
      return;
    }
    if (data.kind === "blocked") {
      log.lastChild.remove(); // her bubble: don't leave personal data on screen
      addWarning("notice_blocked");
      return;
    }
    if (data.kind === "limited" || data.kind === "invalid") {
      addWarning(data.notice);
      return;
    }
    addBot(data.blocks, {
      example: data.kind === "offline" || data.kind === "error",
      notice: data.kind === "error" ? data.notice : null,
    });
    // Trimmed to the server's per-turn cap, so a long reply can't make the
    // next message bounce.
    state.history.push({role: "user", text});
    state.history.push({role: "assistant", text: data.blocks.join("\n").slice(0, CFG.maxTurn)});
    state.history = state.history.slice(-CFG.historyTurns);
    state.done.add(mission);
    renderStrip();
  }

  // ---- navigation ----

  function go(index) {
    state.index = Math.max(0, Math.min(RECAP, index));
    renderStrip();
    renderMission();
    clearChat();
    if (state.index === RECAP) input.blur();
  }

  function fitHeight() {
    const chrome = $("top").offsetHeight + $("strip").offsetHeight;
    document.documentElement.style.setProperty("--chrome", `${chrome}px`);
  }

  // ---- wiring ----

  $("compose").addEventListener("submit", (e) => {
    e.preventDefault();
    submit();
  });
  // Enter sends, Shift+Enter starts a new line - like most chat apps.
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      submit();
    }
  });
  input.addEventListener("input", updateCounter);
  $("clear").addEventListener("click", clearChat);
  window.addEventListener("resize", fitHeight);

  renderChrome();
  go(0);
  fitHeight();
})();
