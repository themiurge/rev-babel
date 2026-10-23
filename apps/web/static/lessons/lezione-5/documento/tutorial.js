/* "Scrivi un documento" - lesson 5's tutorial. A Quill word processor on the
   left, a bilingual step-by-step guide on the right. Each step watches the
   document (text, formats, selection, undo stack) and moves on by itself
   when the student has done what it asked; an orange arrow points at the
   button or the line to use. Nothing the student writes leaves the page:
   there is no network call and no storage. */
(function () {
  "use strict";

  const CFG = JSON.parse(document.getElementById("doc-config").textContent);
  const STR = JSON.parse(document.getElementById("doc-strings").textContent);
  const LANG = CFG.lang;
  const RTL = CFG.rtl;
  const HINT_AFTER_MS = 20000;

  const $ = (sel) => document.querySelector(sel);

  /* ---------- strings: Italian above, the preferred language below ---------- */
  function str(id, lang) {
    const e = STR[id];
    if (!e) return "";
    return e[lang] || e.it || "";
  }
  function fill(html, vars) {
    return html.replace(/@@N@@/g, vars.n || "").replace(/@@T@@/g, vars.t || "");
  }
  function dual(id, vars) {
    vars = vars || {};
    const it = `<div class="lang-it">${fill(str(id, "it"), vars)}</div>`;
    if (LANG === "it") return `<div class="dual">${it}</div>`;
    const other = `<div class="lang-other" lang="${LANG}" dir="${RTL ? "rtl" : "ltr"}">${fill(str(id, LANG), vars)}</div>`;
    return `<div class="dual">${it}${other}</div>`;
  }
  /* A one-line label: Italian on top, the translation small underneath. */
  function dualLine(id, vars) {
    vars = vars || {};
    const it = `<span class="l-it">${fill(str(id, "it"), vars)}</span>`;
    if (LANG === "it") return it;
    return `${it}<span class="l-other" lang="${LANG}" dir="${RTL ? "rtl" : "ltr"}">${fill(str(id, LANG), vars)}</span>`;
  }

  /* ---------- the word processor ---------- */
  const quill = new Quill("#editor", {
    theme: "snow",
    placeholder: str("ui_placeholder", "it"),
    scrollingContainer: "#desk",
    formats: ["bold", "italic", "underline", "color", "header", "list", "align"],
    modules: {
      toolbar: {
        container: "#toolbar",
        handlers: {
          undo() { this.quill.history.undo(); },
          redo() { this.quill.history.redo(); },
        },
      },
      history: { delay: 200, userOnly: true },
    },
  });
  quill.root.setAttribute("spellcheck", "false");
  quill.root.setAttribute("lang", "it");

  /* Hover text on the toolbar: Italian, then the translation. */
  function hoverTitle(id) {
    const it = str(id, "it");
    return LANG === "it" ? it : `${it} / ${str(id, LANG)}`;
  }
  document.querySelectorAll("#toolbar [data-tb]").forEach((el) => {
    const title = hoverTitle(el.dataset.tb);
    el.setAttribute("title", title);
    el.setAttribute("aria-label", str(el.dataset.tb, "it"));
    // Quill swaps a <select> for a <span class="ql-picker"> right after it.
    if (el.tagName === "SELECT" && el.nextElementSibling) {
      el.nextElementSibling.setAttribute("title", title);
    }
  });
  $("#doc-name").textContent = str("ui_docname", "it");
  $("#privacy").innerHTML = dualLine("ui_privacy");

  /* ---------- reading the document ---------- */
  /* Text lines with their index and length; the final "\n" Quill always
     keeps is not a line of its own. */
  function docLines() {
    const parts = quill.getText().replace(/\n$/, "").split("\n");
    let index = 0;
    return parts.map((text) => {
      const line = { text, index, len: text.length };
      index += text.length + 1;
      return line;
    });
  }
  const filled = (line, min) => line.text.trim().length >= (min || 2);
  /* True if any character of the line carries the inline format `attr`. */
  function anyAttr(line, attr) {
    if (!line || line.len === 0) return false;
    return quill.getContents(line.index, line.len).ops.some((op) => op.attributes && op.attributes[attr]);
  }
  const lineFormat = (line) => quill.getFormat(line.index, Math.max(1, line.len));
  /* The three "list" lines the student writes after the sentence. */
  function listLines(L) { return L.slice(2).filter((l) => filled(l)); }

  /* ---------- where the arrow points ---------- */
  const tb = (sel) => document.querySelector("#toolbar " + sel);
  const btn = (selector) => () => ({ el: tb(selector), side: "top" });
  const alignBtn = (value) => () => ({ el: tb(`.ql-align[value="${value}"]`), side: "top" });

  /* A text line in the page: arrow in the left margin, pointing right. */
  function lineTarget(pick) {
    return () => {
      const L = docLines();
      const lines = pick(L);
      if (!lines || lines.length === 0) return null;
      const nodes = lines.map((l) => quill.getLine(l.index)[0]).filter(Boolean).map((b) => b.domNode);
      if (nodes.length === 0) return null;
      const rects = nodes.map((n) => n.getBoundingClientRect());
      const rect = {
        left: Math.min(...rects.map((r) => r.left)),
        right: Math.max(...rects.map((r) => r.right)),
        top: Math.min(...rects.map((r) => r.top)),
        bottom: Math.max(...rects.map((r) => r.bottom)),
      };
      return { rect, side: "left", clip: document.querySelector("#desk").getBoundingClientRect() };
    };
  }

  /* A menu (style, colour): the menu itself while closed, the wanted item once open. */
  function menuTarget(name, itemValue) {
    return () => {
      const picker = tb(".ql-picker.ql-" + name);
      if (!picker) return null;
      if (picker.classList.contains("ql-expanded")) {
        const item = picker.querySelector(`.ql-picker-item[data-value="${itemValue}"]`);
        if (item) return { el: item, side: "right" };
      }
      return { el: picker, side: "top" };
    };
  }

  /* ---------- the steps ---------- */
  const STEPS = [
    { // 1
      target: lineTarget((L) => [L[L.length - 1]]),
      check: (L) => filled(L[0], 3),
    },
    { // 2
      target: lineTarget((L) => [L[L.length - 1]]),
      check: (L) => L.length >= 2 && filled(L[1], 6),
    },
    { // 3 - select the title line (triple click, or drag)
      target: lineTarget((L) => [L[0]]),
      check: (L) => {
        const sel = quill.getSelection();
        return !!sel && L[0].len >= 3 && sel.index === 0 && sel.length >= L[0].len && sel.length <= L[0].len + 1;
      },
    },
    { // 4 - bold
      target: btn(".ql-bold"),
      check: (L) => L[0].len > 0 && !!quill.getFormat(0, L[0].len).bold,
    },
    { // 5 - title style
      target: menuTarget("header", "1"),
      check: (L) => L[0].len > 0 && !!quill.getFormat(0, L[0].len).header,
    },
    { // 6 - centre
      target: alignBtn("center"),
      check: (L) => L[0].len > 0 && quill.getFormat(0, L[0].len).align === "center",
    },
    { // 7 - select one word of the sentence
      target: lineTarget((L) => [L[1]]),
      check: (L) => {
        const sel = quill.getSelection();
        if (!sel || L.length < 2 || sel.length < 2 || sel.length > 30) return false;
        const sentence = L[1];
        if (sel.index < sentence.index || sel.index + sel.length > sentence.index + sentence.len) return false;
        return !/\s/.test(quill.getText(sel.index, sel.length).trim());
      },
    },
    { // 8 - italic
      target: btn(".ql-italic"),
      check: (L) => anyAttr(L[1], "italic"),
    },
    { // 9 - underline
      target: btn(".ql-underline"),
      check: (L) => anyAttr(L[1], "underline"),
    },
    { // 10 - colour
      target: menuTarget("color", "#d62828"),
      check: (L) => anyAttr(L[1], "color"),
    },
    { // 11 - undo: something is waiting on the redo stack
      target: btn(".ql-undo"),
      check: () => quill.history.stack.redo.length > 0,
    },
    { // 12 - redo: the redo stack shrank since this step began
      target: btn(".ql-redo"),
      enter: (ctx) => { ctx.redoAtStart = quill.history.stack.redo.length; },
      check: (L, ctx) => quill.history.stack.redo.length < ctx.redoAtStart,
    },
    { // 13 - three more lines after the sentence
      target: lineTarget((L) => [L[L.length - 1]]),
      check: (L) => listLines(L).length >= 3,
    },
    { // 14 - select exactly those lines
      target: lineTarget((L) => listLines(L).slice(0, 3)),
      check: (L) => {
        const items = listLines(L);
        const sel = quill.getSelection();
        if (!sel || items.length < 3 || L.length < 3) return false;
        return sel.index >= L[2].index && sel.index <= items[0].index &&
          sel.index + sel.length >= items[2].index + items[2].len;
      },
    },
    { // 15 - bullets
      target: btn('.ql-list[value="bullet"]'),
      check: (L) => {
        const items = listLines(L);
        return items.length >= 3 && items.slice(0, 3).every((l) => lineFormat(l).list === "bullet");
      },
    },
    { // 16 - numbers
      target: btn('.ql-list[value="ordered"]'),
      check: (L) => {
        const items = listLines(L);
        return items.length >= 3 && items.slice(0, 3).every((l) => lineFormat(l).list === "ordered");
      },
    },
  ];
  const TOTAL = STEPS.length;

  /* ---------- state and the right-hand pane ---------- */
  let current = -1;     // -1 = intro card still showing
  let stepDone = false;
  let ctx = {};
  let hintTimer = null;

  function showHint() {
    const box = $("#step-hint");
    box.innerHTML = `<div class="hint-head">${dualLine("ui_hint")}</div>${dual(`s${current + 1}_h`)}`;
    box.hidden = false;
  }

  function renderStep() {
    clearTimeout(hintTimer);
    stepDone = false;
    ctx = {};
    const n = current + 1;
    $("#step-count").innerHTML = dualLine("ui_step", { n: String(n), t: String(TOTAL) });
    $("#bar-fill").style.width = `${(current / TOTAL) * 100}%`;
    $("#step-title").innerHTML = dualLine(`s${n}_t`);
    $("#step-body").innerHTML = dual(`s${n}_b`);
    $("#step-hint").hidden = true;
    $("#step-result").hidden = true;
    $("#skip-btn").hidden = false;
    if (STEPS[current].enter) STEPS[current].enter(ctx);
    hintTimer = setTimeout(() => { if (!stepDone) showHint(); }, HINT_AFTER_MS);
    evaluate();
  }

  function completeStep() {
    stepDone = true;
    clearTimeout(hintTimer);
    $("#step-hint").hidden = true;
    $("#skip-btn").hidden = true;
    $("#bar-fill").style.width = `${((current + 1) / TOTAL) * 100}%`;
    const box = $("#step-result");
    box.innerHTML = `<div class="ok">${dualLine("ui_ok")}</div>` +
      `<button type="button" class="btn-big" id="next-btn">${dualLine("ui_next")}</button>`;
    box.hidden = false;
    const next = $("#next-btn");
    // Keep the selection in the page when the button is pressed.
    next.addEventListener("mousedown", (e) => e.preventDefault());
    next.addEventListener("click", advance);
    $("#pane-body").scrollTop = $("#pane-body").scrollHeight;
  }

  function advance() {
    if (current + 1 >= TOTAL) { finish(); return; }
    current += 1;
    renderStep();
    quill.focus();
  }

  function evaluate() {
    if (current < 0 || stepDone || current >= TOTAL) return;
    if (STEPS[current].check(docLines(), ctx)) completeStep();
  }
  quill.on("editor-change", evaluate);

  /* ---------- intro and finish ---------- */
  const overlay = $("#overlay");

  function showIntro() {
    current = -1;
    $("#step-count").innerHTML = "";
    $("#bar-fill").style.width = "0";
    $("#step-title").innerHTML = "";
    $("#step-body").innerHTML = "";
    $("#step-hint").hidden = true;
    $("#step-result").hidden = true;
    $("#skip-btn").hidden = true;
    overlay.innerHTML = `<div class="overlay-card">
      <div class="o-title">${dualLine("intro_title")}</div>
      ${dual("intro_body")}
      <button type="button" class="btn-big" id="start-btn">${dualLine("ui_start")}</button>
    </div>`;
    overlay.hidden = false;
    $("#start-btn").addEventListener("click", () => {
      overlay.hidden = true;
      current = 0;
      renderStep();
      quill.focus();
    });
  }

  function finish() {
    current = TOTAL; // no step is active any more
    $("#bar-fill").style.width = "100%";
    overlay.innerHTML = `<div class="overlay-card">
      <div class="o-title">${dualLine("fin_title")}</div>
      ${dual("fin_body")}
      <div class="o-buttons">
        <button type="button" class="btn-big" id="free-btn">${dualLine("ui_free")}</button>
        <button type="button" class="btn-big btn-alt" id="again-btn">${dualLine("ui_restart")}</button>
      </div>
    </div>`;
    overlay.hidden = false;
    $("#free-btn").addEventListener("click", () => {
      overlay.hidden = true;
      $("#step-count").innerHTML = dualLine("ui_ok");
      $("#step-title").innerHTML = dualLine("fin_title");
      $("#step-body").innerHTML = "";
      $("#skip-btn").hidden = true;
      quill.focus();
    });
    $("#again-btn").addEventListener("click", () => {
      quill.setContents([{ insert: "\n" }], "silent");
      quill.history.clear();
      showIntro();
    });
  }

  $("#skip-btn").textContent = str("ui_skip", "it");
  if (LANG !== "it") {
    const other = document.createElement("small");
    other.style.display = "block";
    other.style.color = "#4b5563";
    other.setAttribute("lang", LANG);
    other.setAttribute("dir", RTL ? "rtl" : "ltr");
    other.textContent = str("ui_skip", LANG);
    $("#skip-btn").appendChild(other);
  }
  $("#skip-btn").addEventListener("mousedown", (e) => e.preventDefault());
  $("#skip-btn").addEventListener("click", () => { if (!stepDone) advance(); });
  $("#back-link").innerHTML = dualLine("ui_back");

  /* ---------- the arrow ---------- */
  const arrow = $("#arrow");
  const spot = $("#spot");
  const ARROW = 52, GAP = 6, PAD = 4;

  function place() {
    requestAnimationFrame(place);
    let target = null;
    if (current >= 0 && current < TOTAL && !stepDone && overlay.hidden) {
      try { target = STEPS[current].target(); } catch (e) { target = null; }
    }
    let rect = target && (target.rect || (target.el && target.el.getBoundingClientRect()));
    if (!rect || (rect.right - rect.left) < 1 || (rect.bottom - rect.top) < 1) {
      arrow.style.display = "none";
      spot.style.display = "none";
      return;
    }
    // A line scrolled out of the desk: don't draw anything floating over the toolbar.
    if (target.clip && (rect.bottom < target.clip.top || rect.top > target.clip.bottom)) {
      arrow.style.display = "none";
      spot.style.display = "none";
      return;
    }
    spot.style.display = "block";
    spot.style.left = `${rect.left - PAD}px`;
    spot.style.top = `${rect.top - PAD}px`;
    spot.style.width = `${rect.right - rect.left + 2 * PAD}px`;
    spot.style.height = `${rect.bottom - rect.top + 2 * PAD}px`;

    let side = target.side;
    let x, y;
    if (side === "top" || side === "bottom") {
      if (side === "top" && rect.top - ARROW - GAP - PAD < 4) side = "bottom";
      x = (rect.left + rect.right) / 2 - ARROW / 2;
      y = side === "top" ? rect.top - ARROW - GAP - PAD : rect.bottom + GAP + PAD;
    } else {
      y = Math.min(Math.max((rect.top + rect.bottom) / 2 - ARROW / 2, 4), window.innerHeight - ARROW - 4);
      x = side === "left" ? rect.left - ARROW - GAP - PAD : rect.right + GAP + PAD;
      if (side === "left" && x < 4) x = 4;
    }
    arrow.className = "side-" + side;
    arrow.style.display = "block";
    arrow.style.left = `${x}px`;
    arrow.style.top = `${y}px`;
  }
  requestAnimationFrame(place);

  showIntro();
})();
