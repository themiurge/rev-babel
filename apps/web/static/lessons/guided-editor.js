/* The engine behind the guided word-processor tutorials (lesson 5: "Scrivi un
   documento", "Il CV di Amina"). A Quill editor on the left, a bilingual
   step-by-step guide on the right. Each step watches the document (text,
   formats, selection, undo stack) and moves on by itself when the student has
   done what it asked; an orange arrow points at the button, menu item or lines
   to use. Nothing the student writes leaves the page: there is no network
   call and no storage.

   A tutorial file calls  GuidedEditor.run(function (h) { return {...}; })
   where `h` holds the helpers below and the returned object has
     steps:        [{ target(), check(lines, ctx), enter?(ctx) }]
     initialText:  optional text the document starts with (and is reset to)
     finalButtons: optional [{ labelKey, run(h) }] extra buttons on the last card */
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

  function run(build) {
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
    document.querySelectorAll("[data-tb]").forEach((el) => {
      const title = hoverTitle(el.dataset.tb);
      el.setAttribute("title", title);
      el.setAttribute("aria-label", str(el.dataset.tb, "it"));
      // Quill swaps a <select> for a <span class="ql-picker"> right after it.
      if (el.tagName === "SELECT" && el.nextElementSibling) {
        el.nextElementSibling.setAttribute("title", title);
      }
    });
    const heading = document.body.dataset.docname;
    $("#doc-name").textContent = str(heading || "ui_docname", "it");
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
    const filled = (line, min) => !!line && line.text.trim().length >= (min || 2);
    /* True if any character of the line carries the inline format `attr`. */
    function anyAttr(line, attr) {
      if (!line || line.len === 0) return false;
      return quill.getContents(line.index, line.len).ops.some((op) => op.attributes && op.attributes[attr]);
    }
    const lineFormat = (line) => quill.getFormat(line.index, Math.max(1, line.len));

    /* ---------- where the arrow points ---------- */
    const tb = (sel) => document.querySelector("#toolbar " + sel);
    const btn = (selector) => () => ({ el: tb(selector), side: "top" });
    const alignBtn = (value) => () => ({ el: tb(`.ql-align[value="${value}"]`), side: "top" });

    /* A text line in the page: arrow in the left margin, pointing right. */
    function lineTarget(pick) {
      return () => {
        const lines = pick(docLines());
        if (!lines || lines.length === 0 || !lines[0]) return null;
        const nodes = lines.map((l) => quill.getLine(l.index)[0]).filter(Boolean).map((b) => b.domNode);
        if (nodes.length === 0) return null;
        const rects = nodes.map((n) => n.getBoundingClientRect());
        const rect = {
          left: Math.min(...rects.map((r) => r.left)),
          right: Math.max(...rects.map((r) => r.right)),
          top: Math.min(...rects.map((r) => r.top)),
          bottom: Math.max(...rects.map((r) => r.bottom)),
        };
        return { rect, side: "left", clip: $("#desk").getBoundingClientRect(), node: nodes[0], key: lines[0].index };
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

    /* "Put the cursor in / select these lines, then use that button": the arrow
       points at the lines until the selection is right, then at the button.
       `inline` formats need the whole text selected; block formats (style,
       alignment, lists) only need the lines touched. */
    function selectThen(pick, buttonTarget, inline) {
      const lineT = lineTarget(pick);
      return () => {
        const lines = pick(docLines());
        // Opening a menu takes the focus (and the selection) out of the page.
        const menuOpen = !!document.querySelector("#toolbar .ql-picker.ql-expanded");
        if (lines && lines.length && (menuOpen || selectionFits(lines, inline))) return buttonTarget();
        return lineT();
      };
    }
    function selectionFits(lines, inline) {
      const sel = quill.getSelection();
      if (!sel || !lines.length || !lines[0]) return false;
      const first = lines[0];
      const last = lines[lines.length - 1];
      const end = sel.index + sel.length;
      if (inline) {
        return sel.index === first.index && end >= last.index + last.len && end <= last.index + last.len + 1;
      }
      return sel.index >= first.index && sel.index <= first.index + first.len &&
        end >= last.index + (lines.length > 1 ? Math.min(1, last.len) : 0) && end <= last.index + last.len + 1;
    }

    /* ---------- the tutorial's own steps ---------- */
    let evaluate = () => {};
    const helpers = {
      quill, str, dual, dualLine, docLines, filled, anyAttr, lineFormat,
      tb, btn, alignBtn, lineTarget, menuTarget, selectThen, selectionFits,
      evaluate: () => evaluate(),
      $,
    };
    const def = build(helpers);
    const STEPS = def.steps;
    const TOTAL = STEPS.length;

    function resetDocument() {
      quill.setText(def.initialText || "", "silent");
      quill.history.clear();
    }
    resetDocument();

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

    evaluate = function () {
      if (current < 0 || stepDone || current >= TOTAL) return;
      if (STEPS[current].check(docLines(), ctx)) completeStep();
    };
    quill.on("editor-change", () => evaluate());

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
        if (def.focusAtStart !== false) quill.focus();
      });
    }

    function finish() {
      current = TOTAL; // no step is active any more
      $("#bar-fill").style.width = "100%";
      const extra = (def.finalButtons || []).map((b, i) =>
        `<button type="button" class="btn-big" data-extra="${i}">${dualLine(b.labelKey)}</button>`).join("");
      overlay.innerHTML = `<div class="overlay-card">
        <div class="o-title">${dualLine("fin_title")}</div>
        ${dual("fin_body")}
        <div class="o-buttons">
          ${extra}
          <button type="button" class="btn-big${extra ? " btn-alt" : ""}" id="free-btn">${dualLine("ui_free")}</button>
          <button type="button" class="btn-big btn-alt" id="again-btn">${dualLine("ui_restart")}</button>
        </div>
      </div>`;
      overlay.hidden = false;
      function freeMode() {
        overlay.hidden = true;
        $("#step-count").innerHTML = dualLine("ui_ok");
        $("#step-title").innerHTML = dualLine("fin_title");
        $("#step-body").innerHTML = STR.fin_free ? dual("fin_free") : "";
        $("#step-hint").hidden = true;
        $("#step-result").hidden = true;
        $("#skip-btn").hidden = true;
        quill.focus();
      }
      $("#free-btn").addEventListener("click", freeMode);
      overlay.querySelectorAll("[data-extra]").forEach((el) => {
        el.addEventListener("click", () => {
          def.finalButtons[Number(el.dataset.extra)].run(helpers);
          quill.history.clear();
          freeMode();
        });
      });
      $("#again-btn").addEventListener("click", () => {
        resetDocument();
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
    let scrolledFor = null;

    function place() {
      requestAnimationFrame(place);
      let target = null;
      if (current >= 0 && current < TOTAL && !stepDone && overlay.hidden) {
        try { target = STEPS[current].target(); } catch (e) { target = null; }
      }
      const rect = target && (target.rect || (target.el && target.el.getBoundingClientRect()));
      if (!rect || (rect.right - rect.left) < 1 || (rect.bottom - rect.top) < 1) {
        arrow.style.display = "none";
        spot.style.display = "none";
        return;
      }
      // A line scrolled out of the desk: bring it into view (once per step and
      // line, so the student can still scroll away), and draw nothing meanwhile.
      if (target.clip && (rect.bottom < target.clip.top || rect.top > target.clip.bottom)) {
        const key = current + ":" + target.key;
        if (target.node && scrolledFor !== key) {
          scrolledFor = key;
          target.node.scrollIntoView({ block: "center", behavior: "smooth" });
        }
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
  }

  window.GuidedEditor = { run };
})();
