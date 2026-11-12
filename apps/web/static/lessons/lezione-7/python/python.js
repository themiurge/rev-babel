/* Lesson 7: "Python con l'assistente". The page logic.

   Her Python runs in a Web Worker (worker.js + runner.py): her code, its
   output and her answers to input() never leave this page. The only network
   call is POST /api/python-helper, made when she presses an assistant button.
   No cookie, no localStorage, no sessionStorage: all state is in memory and
   goes when the tab closes. Student and model text is only ever put in the
   page with textContent. See docs/decisions/0019. */
(function () {
  "use strict";

  var CFG = JSON.parse(document.getElementById("py-config").textContent);
  var UI = CFG.content.ui;
  var STEPS = CFG.content.steps;
  var RULES = CFG.content.rules;
  var RULES_INDEX = STEPS.length; // the last pill: the 5 rules card

  function $(id) {
    return document.getElementById(id);
  }
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }
  function fill(template, n, t) {
    return String(template).replace("@@N@@", n).replace("@@T@@", t);
  }
  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  var state = {
    index: 0,
    done: {},
    codes: {},
    answers: [],
    seed: 0,
    lastError: null,
    ranSinceEdit: false,
    busy: false,
    pythonReady: false,
    hintsShown: {},
    assistantLog: [],
    asking: false,
    runId: 0
  };
  STEPS.forEach(function (s) {
    state.codes[s.id] = s.start;
    state.hintsShown[s.id] = 0;
  });

  var worker = null;
  var runTimer = null;
  var bootTimer = null;
  var slowTimer = null;

  var statusEl = $("status");
  var codeEl = $("code");
  var gutterEl = $("gutter");
  var runBtn = $("run");
  var stopBtn = $("stop");
  var resetBtn = $("reset");
  var printBtn = $("print");
  var outputEl = $("output");
  var errorEl = $("error");
  var noteEl = $("note");
  var askInputEl = $("ask-input");
  var doneEl = $("done");

  function currentStep() {
    // The rules card sits after step 7 and shares its editor.
    return STEPS[Math.min(state.index, STEPS.length - 1)];
  }

  function setStatus(text, ok) {
    statusEl.textContent = text || "";
    statusEl.className = "status" + (ok ? " ok" : "");
  }

  // ---- Python worker ---------------------------------------------------------

  function updateRunButton() {
    runBtn.disabled = !(CFG.pythonInstalled && state.pythonReady && !state.busy);
  }

  function stopBootTimers() {
    clearTimeout(bootTimer);
    clearInterval(slowTimer);
  }

  function bootFailed() {
    stopBootTimers();
    state.pythonReady = false;
    setStatus(UI.load_failed, false);
    updateRunButton();
  }

  function startWorker() {
    stopBootTimers();
    if (worker) {
      worker.terminate();
      worker = null;
    }
    state.pythonReady = false;
    updateRunButton();
    setStatus(UI.loading, false);
    var w;
    try {
      w = new Worker(CFG.workerUrl);
    } catch (err) {
      bootFailed();
      return;
    }
    worker = w;
    var started = Date.now();
    slowTimer = setInterval(function () {
      var seconds = Math.round((Date.now() - started) / 1000);
      if (seconds >= 10) setStatus(fill(UI.loading_slow, seconds, ""), false);
    }, 1000);
    bootTimer = setTimeout(bootFailed, CFG.bootTimeoutMs);
    w.onmessage = function (event) {
      if (w !== worker) return;
      var msg = event.data || {};
      if (msg.type === "ready") {
        stopBootTimers();
        state.pythonReady = true;
        setStatus("", true);
        updateRunButton();
      } else if (msg.type === "boot-failed") {
        bootFailed();
      } else if (msg.type === "result") {
        if (msg.id === state.runId && state.busy) onResult(msg.result);
      } else if (msg.type === "crashed") {
        if (msg.id === state.runId && state.busy) abortRun(UI.crashed);
      }
    };
    w.onerror = function () {
      if (w !== worker) return;
      if (state.busy) abortRun(UI.crashed);
      else if (!state.pythonReady) bootFailed();
    };
    w.postMessage({
      type: "boot",
      pyodideUrl: CFG.pyodideUrl,
      runnerUrl: CFG.runnerUrl
    });
  }

  // Stop the worker (it may be stuck in one huge operation) and start a new one.
  function abortRun(message) {
    clearTimeout(runTimer);
    state.busy = false;
    stopBtn.hidden = true;
    state.runId++;
    if (message) showNote(message);
    startWorker();
  }

  // ---- steps -----------------------------------------------------------------

  function renderStrip() {
    var strip = $("strip");
    clear(strip);
    STEPS.forEach(function (s, i) {
      var b = el("button", state.done[s.id] ? "done" : "", s.icon + " " + (i + 1));
      b.type = "button";
      b.title = s.title;
      if (i === state.index) b.setAttribute("aria-current", "step");
      b.addEventListener("click", function () {
        goTo(i);
      });
      strip.appendChild(b);
    });
    var last = el("button", "", "🏁");
    last.type = "button";
    last.title = UI.rules_title;
    if (state.index === RULES_INDEX) last.setAttribute("aria-current", "step");
    last.addEventListener("click", function () {
      goTo(RULES_INDEX);
    });
    strip.appendChild(last);
  }

  function renderHints(box, step) {
    clear(box);
    var shown = state.hintsShown[step.id];
    for (var i = 0; i < shown; i++) {
      var h = el("div", "hint");
      h.appendChild(el("b", "", fill(UI.hint_n, i + 1, "")));
      h.appendChild(document.createTextNode(step.hints[i]));
      box.appendChild(h);
    }
    if (shown < step.hints.length) {
      var btn = el("button", "hint-btn", UI.hint_btn);
      btn.type = "button";
      btn.addEventListener("click", function () {
        state.hintsShown[step.id]++;
        renderHints(box, step);
      });
      box.insertBefore(btn, box.firstChild);
    }
  }

  function renderGuide() {
    var guide = $("guide");
    var foot = $("guide-foot");
    clear(guide);
    clear(foot);
    if (state.index === RULES_INDEX) {
      guide.appendChild(el("div", "s-title", "🏁 " + UI.rules_title));
      var ol = el("ol", "rules");
      RULES.forEach(function (r) {
        ol.appendChild(el("li", "", r));
      });
      guide.appendChild(ol);
      guide.appendChild(el("p", "goal", UI.finish));
      var back = el("button", "btn alt", UI.prev);
      back.type = "button";
      back.addEventListener("click", function () {
        goTo(STEPS.length - 1);
      });
      foot.appendChild(back);
      return;
    }
    var step = STEPS[state.index];
    guide.appendChild(el("div", "count", fill(UI.step_n, state.index + 1, STEPS.length)));
    guide.appendChild(el("div", "s-title", step.icon + " " + step.title));
    guide.appendChild(el("p", "goal", step.goal));
    guide.appendChild(el("div", "lbl", UI.do_label));
    var list = el("ol", "do");
    step.do.forEach(function (line) {
      list.appendChild(el("li", "", line));
    });
    guide.appendChild(list);
    guide.appendChild(el("div", "lbl", UI.expected_label));
    var expected = el("pre", "expected", step.expected);
    expected.dir = "ltr";
    guide.appendChild(expected);
    var hints = el("div", "hints");
    guide.appendChild(hints);
    renderHints(hints, step);
    if (step.bonus && state.done[step.id]) {
      var bonus = el("div", "bonus");
      bonus.appendChild(el("b", "", UI.bonus_label));
      bonus.appendChild(el("div", "", step.bonus));
      guide.appendChild(bonus);
    }
    var prev = el("button", "btn alt", UI.prev);
    prev.type = "button";
    prev.disabled = state.index === 0;
    prev.addEventListener("click", function () {
      goTo(state.index - 1);
    });
    var next = el("button", "btn", UI.next);
    next.type = "button";
    next.addEventListener("click", function () {
      goTo(state.index + 1);
    });
    foot.appendChild(prev);
    foot.appendChild(next);
  }

  function clearResults() {
    clear(outputEl);
    errorEl.hidden = true;
    noteEl.hidden = true;
    askInputEl.hidden = true;
    doneEl.hidden = true;
    state.lastError = null;
    state.answers = [];
    state.ranSinceEdit = false;
  }

  function goTo(i) {
    if (i < 0 || i > RULES_INDEX) return;
    if (state.busy) abortRun("");
    state.index = i;
    state.assistantLog = [];
    clearResults();
    renderStrip();
    renderGuide();
    loadEditor();
    renderAssistantAnswers();
    updateAskButtons();
    updatePrintButton();
  }

  // ---- editor ----------------------------------------------------------------

  function updateGutter() {
    var n = codeEl.value.split("\n").length;
    var rows = [];
    for (var i = 1; i <= n; i++) rows.push(i);
    gutterEl.textContent = rows.join("\n");
    gutterEl.scrollTop = codeEl.scrollTop;
  }

  function loadEditor() {
    codeEl.value = state.codes[currentStep().id];
    updateGutter();
  }

  function onEdit() {
    state.codes[currentStep().id] = codeEl.value;
    state.ranSinceEdit = false;
    askInputEl.hidden = true;
    doneEl.hidden = true;
    updateGutter();
  }

  function insertText(text, back) {
    if (codeEl.value.length + text.length > CFG.limits.editor) return;
    var start = codeEl.selectionStart;
    var end = codeEl.selectionEnd;
    codeEl.setRangeText(text, start, end, "end");
    var caret = start + text.length - (back || 0);
    codeEl.setSelectionRange(caret, caret);
    codeEl.focus();
    onEdit();
  }

  function renderKeys() {
    var keys = $("keys");
    keys.appendChild(el("span", "klabel", UI.keys_label));
    [
      ['"  "', '""', 1],
      ["( )", "()", 1],
      ["[ ]", "[]", 1],
      [":", ":", 0],
      [",", ",", 0],
      ["=", "=", 0],
      ["==", "==", 0],
      ["#", "#", 0]
    ].forEach(function (k) {
      var b = el("button", "", k[0]);
      b.type = "button";
      b.dir = "ltr";
      b.addEventListener("click", function () {
        insertText(k[1], k[2]);
      });
      keys.appendChild(b);
    });
    var sp = el("button", "", UI.spaces_key);
    sp.type = "button";
    sp.style.fontFamily = "inherit";
    sp.addEventListener("click", function () {
      insertText("    ", 0);
    });
    keys.appendChild(sp);
  }

  codeEl.maxLength = CFG.limits.editor;
  codeEl.addEventListener("input", onEdit);
  codeEl.addEventListener("scroll", function () {
    gutterEl.scrollTop = codeEl.scrollTop;
  });
  codeEl.addEventListener("keydown", function (event) {
    if (event.key === "Tab" && !event.ctrlKey && !event.altKey && !event.metaKey) {
      event.preventDefault();
      insertText("    ", 0);
    } else if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      pressRun();
    } else if (event.key === "Enter" && !event.shiftKey && !event.altKey) {
      var start = codeEl.selectionStart;
      var lineStart = codeEl.value.lastIndexOf("\n", start - 1) + 1;
      var line = codeEl.value.slice(lineStart, start);
      var indent = line.match(/^ */)[0];
      if (/:\s*$/.test(line)) indent += "    ";
      event.preventDefault();
      insertText("\n" + indent, 0);
    }
  });

  // ---- running ---------------------------------------------------------------

  function showNote(text) {
    noteEl.textContent = text;
    noteEl.hidden = !text;
  }

  function pressRun() {
    if (runBtn.disabled) return;
    state.seed = Math.floor(Math.random() * 1e9);
    state.answers = [];
    runOnce();
  }

  function runOnce() {
    if (!worker || !state.pythonReady) return;
    state.busy = true;
    state.runId++;
    askInputEl.hidden = true;
    doneEl.hidden = true;
    setStatus(UI.running, false);
    stopBtn.hidden = false;
    updateRunButton();
    clearTimeout(runTimer);
    runTimer = setTimeout(function () {
      abortRun(UI.timeout);
    }, CFG.runTimeoutMs);
    worker.postMessage({
      type: "run",
      id: state.runId,
      code: codeEl.value,
      answers: state.answers,
      seed: state.seed,
      step: currentStep().id
    });
  }

  function renderOutput(text, isEmptyOk) {
    clear(outputEl);
    if (isEmptyOk) {
      outputEl.appendChild(el("span", "empty", UI.output_empty));
      return;
    }
    var lines = text.split("\n");
    if (lines.length && lines[lines.length - 1] === "") lines.pop();
    lines.forEach(function (line) {
      var row = el("span", "ln", line === "" ? " " : line);
      row.dir = "auto";
      outputEl.appendChild(row);
    });
  }

  function renderError(error) {
    clear(errorEl);
    if (!error) {
      errorEl.hidden = true;
      return;
    }
    errorEl.appendChild(el("div", "e-title", UI.error_title));
    errorEl.appendChild(el("div", "e-text", error.text));
    if (error.line) {
      errorEl.appendChild(el("div", "", fill(UI.error_line, error.line, "")));
      if (error.line_text) errorEl.appendChild(el("div", "e-code", error.line_text));
    }
    if (error.original) {
      var orig = el("div", "e-orig", UI.error_original + " ");
      orig.appendChild(el("code", "", error.original));
      errorEl.appendChild(orig);
    }
    errorEl.hidden = false;
  }

  function onResult(result) {
    clearTimeout(runTimer);
    state.busy = false;
    stopBtn.hidden = true;
    setStatus("", true);
    updateRunButton();
    renderOutput(result.output || "", result.ok && !result.output);
    renderError(result.error);
    state.lastError = result.error
      ? { line: result.error.line, original: result.error.original }
      : null;
    state.ranSinceEdit = true;
    showNote(result.note || "");
    updateAskButtons();
    if (result.need_input !== null && result.need_input !== undefined) {
      showInputBox(result.need_input);
      return;
    }
    var step = currentStep();
    if (result.done && !state.done[step.id]) {
      state.done[step.id] = true;
      renderStrip();
      renderGuide();
      showDoneBanner(step);
      updatePrintButton();
    }
  }

  function showInputBox(prompt) {
    clear(askInputEl);
    askInputEl.appendChild(el("div", "prompt", UI.input_label + " " + prompt));
    var form = el("form");
    form.autocomplete = "off";
    var field = el("input");
    field.type = "text";
    field.maxLength = 200;
    field.setAttribute("aria-label", UI.input_label);
    var send = el("button", "btn", UI.input_send);
    send.type = "submit";
    form.appendChild(field);
    form.appendChild(send);
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      state.answers.push(field.value.slice(0, 200));
      askInputEl.hidden = true;
      runOnce();
    });
    askInputEl.appendChild(form);
    askInputEl.hidden = false;
    field.focus();
  }

  function showDoneBanner(step) {
    clear(doneEl);
    doneEl.appendChild(el("div", "d-title", UI.done_title));
    doneEl.appendChild(el("div", "d-joy", step.joy));
    var next = el("button", "btn", UI.next);
    next.type = "button";
    next.addEventListener("click", function () {
      goTo(state.index + 1);
    });
    doneEl.appendChild(next);
    doneEl.hidden = false;
  }

  function updatePrintButton() {
    var step = currentStep();
    printBtn.hidden = !(step.id === "s7" && state.done.s7);
  }

  // ---- the assistant ---------------------------------------------------------

  var chipButtons = {};
  var askField = null;
  var askSend = null;
  var thinkingEl = null;
  var answersEl = null;

  function buildAssistant() {
    var box = $("assistant");
    box.appendChild(el("h2", "", UI.assistant_title));
    box.appendChild(el("p", "privacy", UI.assistant_privacy));
    box.appendChild(el("p", "local", UI.assistant_local));
    if (!CFG.live) box.appendChild(el("div", "offline", UI.offline_banner));
    var chips = el("div", "chips");
    ["errore", "prossimo", "riga", "idea"].forEach(function (kind) {
      var b = el("button", "chip", UI["ask_" + kind]);
      b.type = "button";
      b.addEventListener("click", function () {
        ask(kind, "");
      });
      chipButtons[kind] = b;
      chips.appendChild(b);
    });
    box.appendChild(chips);
    var form = el("form", "ask-form");
    form.autocomplete = "off";
    askField = el("input");
    askField.type = "text";
    askField.maxLength = CFG.limits.question;
    askField.placeholder = UI.ask_placeholder;
    askField.setAttribute("aria-label", UI.ask_placeholder);
    askSend = el("button", "btn", UI.ask_send);
    askSend.type = "submit";
    form.appendChild(askField);
    form.appendChild(askSend);
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var q = askField.value.trim();
      if (q) ask("libera", q);
    });
    box.appendChild(form);
    thinkingEl = el("div", "thinking", UI.assistant_thinking);
    thinkingEl.hidden = true;
    box.appendChild(thinkingEl);
    answersEl = el("div", "answers");
    box.appendChild(answersEl);
    updateAskButtons();
  }

  function updateAskButtons() {
    var off = state.asking;
    Object.keys(chipButtons).forEach(function (kind) {
      var disabled = off || (kind === "errore" && !state.lastError);
      chipButtons[kind].disabled = disabled;
      chipButtons[kind].title = kind === "errore" && !state.lastError ? UI.run_first : "";
    });
    if (askSend) askSend.disabled = off;
    if (askField) askField.disabled = off;
  }

  function addBubble(segments, notice, warn, showCheck) {
    var bubble = { segments: segments || [], notice: notice || "", warn: !!warn, check: !!showCheck };
    state.assistantLog.unshift(bubble);
    state.assistantLog = state.assistantLog.slice(0, 3);
    renderAssistantAnswers();
  }

  function renderAssistantAnswers() {
    if (!answersEl) return;
    clear(answersEl);
    state.assistantLog.forEach(function (b) {
      var node = el("div", "bubble" + (b.warn ? " warn" : ""));
      b.segments.forEach(function (seg) {
        if (seg.type === "code") {
          var pre = el("pre", "", seg.text);
          pre.dir = "ltr";
          node.appendChild(pre);
        } else {
          node.appendChild(el("p", "", seg.text));
        }
      });
      if (b.notice) node.appendChild(el("div", "notice", b.notice));
      if (b.check) node.appendChild(el("p", "check", UI.assistant_check));
      answersEl.appendChild(node);
    });
  }

  function ask(kind, question) {
    if (state.asking) return;
    var code = codeEl.value;
    if (code.length > CFG.limits.code) {
      addBubble([], UI.code_too_long, true, false);
      return;
    }
    var err = "";
    if (state.lastError) {
      err = ("riga " + (state.lastError.line || "?") + ": " + (state.lastError.original || "")).slice(
        0,
        CFG.limits.error
      );
    }
    state.asking = true;
    thinkingEl.hidden = false;
    updateAskButtons();
    fetch("/api/python-helper", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        step: currentStep().id,
        ask: kind,
        question: question,
        code: code,
        error: err
      })
    })
      .then(function (res) {
        if (res.status === 400 || res.status === 422) {
          addBubble([], UI.notice_invalid, true, false);
          return null;
        }
        return res.json();
      })
      .then(function (data) {
        if (!data) return;
        var blocked = data.kind === "blocked" || data.kind === "limited";
        addBubble(data.segments, data.notice ? UI[data.notice] || "" : "", blocked, !blocked);
        if (kind === "libera" && !blocked) askField.value = "";
      })
      .catch(function () {
        addBubble([], UI.notice_error, true, false);
      })
      .then(function () {
        state.asking = false;
        thinkingEl.hidden = true;
        updateAskButtons();
      });
  }

  // ---- start -----------------------------------------------------------------

  $("back").textContent = UI.back;
  $("title").textContent = UI.title;
  $("output-label").textContent = UI.output_label;
  runBtn.textContent = UI.run;
  stopBtn.textContent = UI.stop;
  resetBtn.textContent = UI.reset;
  printBtn.textContent = UI.print_btn;
  renderKeys();
  buildAssistant();
  renderStrip();
  renderGuide();
  loadEditor();

  runBtn.addEventListener("click", pressRun);
  stopBtn.addEventListener("click", function () {
    abortRun("");
  });
  resetBtn.addEventListener("click", function () {
    if (!window.confirm(UI.reset_confirm)) return;
    state.codes[currentStep().id] = currentStep().start;
    clearResults();
    loadEditor();
    updateAskButtons();
  });
  printBtn.addEventListener("click", function () {
    window.print();
  });

  if (!CFG.pythonInstalled) {
    setStatus(UI.not_installed, false);
    runBtn.disabled = true;
  } else {
    startWorker();
  }
})();
