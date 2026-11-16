// Lesson 8 materials page (ADR 0020): one card per photo, screenshot, video
// or voice the teacher provides. Talks to /admin/api/materials. Every piece
// of text, from the manifest or from the server, goes in through textContent
// (never innerHTML), and nothing is kept in localStorage or cookies by this
// script.
(function () {
  "use strict";

  var app = document.getElementById("app");
  if (!app) return;

  var ANSWERS = {
    vero: "✅ VERO",
    falso_ia: "🤖 FALSO / IA",
    truffa: "🎣 TRUFFA",
    verificare: "🔍 DEVO VERIFICARE"
  };
  var KIND_FAMILY = { image: "image", screenshot: "image", video: "video", audio: "audio" };
  var WANTS = { image: "una foto o uno screenshot", video: "un video", audio: "un audio" };
  var MAX_RECORD_MS = 60000;

  var data = null;
  var tab = "all";
  var cards = {};      // slot id -> card element
  var lastJson = {};   // slot id -> JSON of the status drawn in its card
  var busy = {};       // slot id -> true while uploading or recording
  var unfolded = {};   // slot id -> true when the teacher opened a ready card
  var folded = {};     // slot id -> true when the teacher folded a missing card
  var activeId = null;
  var listSignature = "";
  var els = {};        // header, tabs, list, danger zone

  // ---- small helpers ------------------------------------------------------

  function h(tag, props, kids) {
    var el = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      if (k === "class") el.className = props[k];
      else if (k === "text") el.textContent = props[k];
      else if (k === "on") {
        Object.keys(props.on).forEach(function (ev) { el.addEventListener(ev, props.on[ev]); });
      } else el.setAttribute(k, props[k]);
    });
    (kids || []).forEach(function (kid) {
      if (kid) el.appendChild(typeof kid === "string" ? document.createTextNode(kid) : kid);
    });
    return el;
  }

  function fmtSize(n) {
    if (n >= 1048576) return (n / 1048576).toFixed(1).replace(".", ",") + " MB";
    return Math.max(1, Math.round(n / 1024)) + " KB";
  }

  var toastTimer = null;
  function toast(msg) {
    var old = document.querySelector(".toast");
    if (old) old.remove();
    var t = h("div", { class: "toast", role: "status", text: msg });
    document.body.appendChild(t);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.remove(); }, 3500);
  }

  function api(method, path, body) {
    var opt = { method: method, headers: {}, credentials: "same-origin" };
    if (body !== undefined) {
      opt.headers["Content-Type"] = "application/json";
      opt.body = JSON.stringify(body);
    }
    return fetch(path, opt).then(function (r) {
      if (r.status === 401) {
        location.reload();
        throw new Error("Serve la chiave dei materiali.");
      }
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) {
          throw new Error(typeof j.detail === "string" ? j.detail : "Errore " + r.status);
        }
        return j;
      });
    });
  }

  function findSlot(id) {
    for (var i = 0; i < data.slots.length; i++) if (data.slots[i].id === id) return data.slots[i];
    return null;
  }

  function isRequiredMissing(s) {
    return s.needed === "required" &&
      (s.status.state === "mancante" || s.status.state === "incompleto");
  }

  function isOptionalMissing(s) {
    return s.needed !== "required" &&
      (s.status.state === "mancante" || s.status.state === "incompleto");
  }

  function badgeText(s) {
    var st = s.status.state;
    if (st === "saltato") return "⚪ Saltato";
    if (st === "pronto") return "🟢 Pronto";
    if (st === "incompleto") return "🟠 Incompleto";
    if (s.needed === "fallback") return "🟡 C'è un esempio di riserva";
    if (s.needed === "optional") return "⚪ Facoltativo";
    return "🔴 Mancante";
  }

  function setError(id, msg) {
    var card = cards[id];
    if (!card) return;
    var box = card.querySelector(".error");
    box.textContent = msg || "";
    box.hidden = !msg;
  }

  // ---- data ---------------------------------------------------------------

  function load() {
    return api("GET", "/admin/api/materials").then(function (d) {
      data = d;
    });
  }

  function refresh() {
    return load().then(function () {
      renderHeader();
      data.slots.forEach(function (s) {
        var json = JSON.stringify(s.status);
        if (json !== lastJson[s.id] && !busy[s.id]) replaceCard(s);
      });
      renderList();
    });
  }

  function applyStatus(id, status) {
    var s = findSlot(id);
    if (s) s.status = status;
    return s;
  }

  // ---- header -------------------------------------------------------------

  function missingCount() {
    return data.slots.filter(isRequiredMissing).length;
  }

  function renderHeader() {
    var box = els.progress;
    box.textContent = "";
    data.artifacts.forEach(function (a) {
      var row;
      if (a.nothingNeeded) {
        row = h("div", { class: "progress-row done" }, [
          h("span", { text: a.title }),
          h("span", { text: "niente da fornire ✅" })
        ]);
      } else {
        var pct = a.total ? Math.round((a.ready * 100) / a.total) : 100;
        var fill = h("span");
        fill.style.width = pct + "%";
        row = h("div", { class: "progress-row" }, [
          h("span", { text: a.title }),
          h("div", { class: "bar" }, [fill]),
          h("span", { text: a.ready + " di " + a.total })
        ]);
      }
      box.appendChild(row);
    });
    els.tabAll.setAttribute("aria-pressed", tab === "all" ? "true" : "false");
    els.tabMissing.setAttribute("aria-pressed", tab === "missing" ? "true" : "false");
    els.tabMissing.textContent = "Cosa manca (" + missingCount() + ")";
  }

  // ---- list ---------------------------------------------------------------

  function artifactHeading(a) {
    var node = h("h2", { text: a.title });
    if (a.nothingNeeded) node = h("div", {}, [node, h("p", { text: "Niente da fornire ✅" })]);
    return node;
  }

  function renderList() {
    var wanted = [];
    if (tab === "all") {
      data.artifacts.forEach(function (a) {
        wanted.push({ type: "heading", artifact: a });
        data.slots.forEach(function (s) {
          if (s.artifact === a.id) wanted.push({ type: "card", id: s.id });
        });
      });
    } else {
      var req = data.slots.filter(isRequiredMissing);
      var opt = data.slots.filter(isOptionalMissing);
      var lastArtifact = null;
      req.forEach(function (s) {
        if (s.artifact !== lastArtifact) {
          lastArtifact = s.artifact;
          wanted.push({ type: "heading", artifact: artifactById(s.artifact) });
        }
        wanted.push({ type: "card", id: s.id });
      });
      if (!req.length) wanted.push({ type: "text", text: "Non manca niente di obbligatorio. 🎉" });
      if (opt.length) {
        wanted.push({ type: "divider", text: "Facoltativi: c'è già un esempio" });
        opt.forEach(function (s) { wanted.push({ type: "card", id: s.id }); });
      }
    }
    var signature = tab + "|" + wanted.map(function (w) {
      return w.type + (w.id || (w.artifact && w.artifact.id) || w.text);
    }).join(",");
    var inList = els.list.querySelectorAll(".card").length;
    if (signature === listSignature && inList) return;
    listSignature = signature;
    els.list.textContent = "";
    wanted.forEach(function (w) {
      if (w.type === "heading") els.list.appendChild(artifactHeading(w.artifact));
      else if (w.type === "divider") els.list.appendChild(h("h3", { class: "divider", text: w.text }));
      else if (w.type === "text") els.list.appendChild(h("p", { text: w.text }));
      else {
        if (!cards[w.id]) {
          var s = findSlot(w.id);
          cards[w.id] = buildCard(s);
          lastJson[w.id] = JSON.stringify(s.status);
        }
        els.list.appendChild(cards[w.id]);
      }
    });
    els.copyBtn.hidden = tab !== "missing";
  }

  function artifactById(id) {
    for (var i = 0; i < data.artifacts.length; i++) if (data.artifacts[i].id === id) return data.artifacts[i];
    return { id: id, title: id, nothingNeeded: false };
  }

  function replaceCard(s) {
    var old = cards[s.id];
    var fresh = buildCard(s);
    cards[s.id] = fresh;
    lastJson[s.id] = JSON.stringify(s.status);
    if (old && old.parentNode) old.parentNode.replaceChild(fresh, old);
    if (activeId === s.id) fresh.classList.add("active");
  }

  // ---- one card -----------------------------------------------------------

  function isFolded(s) {
    var st = s.status.state;
    if (st === "pronto" || st === "saltato") return !unfolded[s.id];
    return !!folded[s.id];
  }

  function fillHead(head, s) {
    head.textContent = "";
    var f = s.status.file;
    var thumb;
    if (f && f.family === "image") {
      thumb = h("img", { class: "thumb", src: f.url, alt: "", loading: "lazy" });
    } else {
      thumb = h("span", {
        class: "thumb",
        text: f ? (f.family === "video" ? "🎬" : "🎙️") : (KIND_FAMILY[s.kind] === "image" ? "🖼️" : KIND_FAMILY[s.kind] === "video" ? "🎬" : "🎙️")
      });
    }
    head.appendChild(thumb);
    head.appendChild(h("span", { class: "meta" }, [
      h("strong", { text: s.id }),
      " · " + s.where
    ]));
    head.appendChild(h("span", { class: "badge", text: badgeText(s) }));
    head.appendChild(h("span", { "aria-hidden": "true", text: "▸" }));
  }

  function buildCard(s) {
    var id = s.id;
    var st = s.status;
    var family = KIND_FAMILY[s.kind];
    var card = h("div", {
      class: "card state-" + st.state + (isFolded(s) ? " folded" : ""),
      tabindex: "0",
      "data-id": id
    });
    var head = h("button", { class: "card-head", type: "button" });
    fillHead(head, s);
    head.addEventListener("click", function () {
      var nowFolded = !card.classList.contains("folded");
      card.classList.toggle("folded", nowFolded);
      var state = (findSlot(id) || s).status.state;
      if (state === "pronto" || state === "saltato") unfolded[id] = !nowFolded;
      else folded[id] = nowFolded;
    });
    card.appendChild(head);
    card.addEventListener("focusin", function () { setActive(id); });
    card.addEventListener("click", function () { setActive(id); });

    var body = h("div", { class: "card-body" });
    body.appendChild(h("div", { class: "card-title", text: s.title }));
    var ul = h("ul");
    s.instructions.forEach(function (t) { ul.appendChild(h("li", { text: t })); });
    body.appendChild(ul);
    if (s.safety && s.safety.length) {
      var safety = h("div", { class: "safety" });
      s.safety.forEach(function (t) { safety.appendChild(h("p", { text: "⚠️ " + t })); });
      body.appendChild(safety);
    }
    if (s.noFaces) body.appendChild(h("span", { class: "nofaces", text: "🙅 Niente volti" }));
    if (s.answer && ANSWERS[s.answer]) {
      body.appendChild(h("div", { class: "answer", text: "Risposta nel gioco: " + ANSWERS[s.answer] }));
    }

    // file chooser: a hidden input, a label as the big drop zone
    var accept = family === "image" ? "image/*" : family === "video" ? "video/*" : "audio/*,.m4a,.mp3,.ogg,.opus,.wav";
    var input = h("input", { type: "file", id: "f-" + id, accept: accept, hidden: "" });
    input.addEventListener("change", function () {
      if (input.files && input.files[0]) sendFile(s, input.files[0]);
      input.value = "";
    });
    body.appendChild(input);
    if (!st.file) {
      var label = h("label", { class: "drop", for: "f-" + id }, [
        h("span", {
          class: "drop-emoji",
          text: family === "image" ? "📷" : family === "video" ? "🎬" : "🎙️"
        }),
        family === "image" ? "Tocca per scegliere o fotografare"
          : family === "video" ? "Tocca per scegliere o filmare"
          : "Tocca per scegliere un file audio",
        h("small", { text: family === "image" ? "oppure trascina qui · Ctrl+V" : "oppure trascina qui" })
      ]);
      body.appendChild(label);
    }

    var actions = h("div", { class: "actions" });
    if (family === "image" && navigator.clipboard && navigator.clipboard.read) {
      actions.appendChild(h("button", {
        type: "button", text: "📋 Incolla",
        on: { click: function () { pasteFromButton(s); } }
      }));
    }
    var recorder = h("div", { class: "recorder" });
    if (family === "audio" && window.MediaRecorder && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      actions.appendChild(h("button", {
        type: "button", text: "🎙️ Registra",
        on: { click: function () { startRecording(s, recorder); } }
      }));
    }
    if (actions.childNodes.length) body.appendChild(actions);
    body.appendChild(recorder);

    var bar = h("div", { class: "uploadbar", hidden: "" }, [h("span")]);
    body.appendChild(bar);
    body.appendChild(h("div", { class: "error", role: "alert", hidden: "" }));

    if (st.file) body.appendChild(buildPreview(s, input));

    (s.fields || []).forEach(function (fd) { body.appendChild(buildField(s, fd)); });

    var skip = h("label", { class: "skip" });
    var cb = h("input", { type: "checkbox" });
    cb.checked = !!st.skipped;
    cb.addEventListener("change", function () {
      api("POST", "/admin/api/materials/" + encodeURIComponent(id) + "/skip", { skipped: cb.checked })
        .then(function (status) {
          var slot = applyStatus(id, status);
          replaceCard(slot);
          return refresh();
        })
        .catch(function (e) { cb.checked = !cb.checked; setError(id, e.message); });
    });
    skip.appendChild(cb);
    skip.appendChild(document.createTextNode("Salta questo materiale"));
    body.appendChild(skip);

    card.appendChild(body);
    wireDrop(card, s);
    if (activeId === id) card.classList.add("active");
    return card;
  }

  function buildPreview(s, input) {
    var f = s.status.file;
    var box = h("div", { class: "preview" });
    if (f.family === "image") box.appendChild(h("img", { src: f.url, alt: s.alt }));
    else if (f.family === "video") box.appendChild(h("video", { src: f.url, controls: "", playsinline: "", preload: "metadata" }));
    else box.appendChild(h("audio", { src: f.url, controls: "", preload: "metadata" }));
    var info = fmtSize(f.size) + (f.removed && f.removed.length ? " · 🧹 Tolti i dati nascosti (posizione, data...)" : "");
    box.appendChild(h("div", { class: "fileinfo", text: info }));
    var row = h("div", { class: "actions" });
    row.appendChild(h("button", {
      type: "button", text: "🔁 Sostituisci",
      on: { click: function () { input.click(); } }
    }));
    row.appendChild(h("button", {
      type: "button", class: "danger", text: "🗑️ Elimina",
      on: {
        click: function () {
          if (!window.confirm("Eliminare questo file?")) return;
          api("DELETE", "/admin/api/materials/" + encodeURIComponent(s.id) + "/file")
            .then(function (status) {
              replaceCard(applyStatus(s.id, status));
              return refresh();
            })
            .catch(function (e) { setError(s.id, e.message); });
        }
      }
    }));
    box.appendChild(row);
    return box;
  }

  function buildField(s, fd) {
    var wrap = h("div", { class: "field" });
    var inputId = "fld-" + s.id + "-" + fd.key;
    var saved = h("span", { class: "saved", hidden: "", text: "✓ salvato" });
    wrap.appendChild(h("label", { for: inputId }, [fd.label + (fd.required ? " *" : ""), saved]));
    var input = h("input", {
      type: fd.type === "url" ? "url" : "text",
      id: inputId,
      maxlength: String(fd.max),
      placeholder: fd.placeholder || ""
    });
    input.value = (s.status.fields && s.status.fields[fd.key]) || "";
    var last = input.value;
    input.addEventListener("change", save);
    input.addEventListener("blur", save);
    function save() {
      var value = input.value.trim();
      if (value === last) return;
      var payload = {};
      payload[fd.key] = value;
      api("POST", "/admin/api/materials/" + encodeURIComponent(s.id) + "/fields", { fields: payload })
        .then(function (status) {
          last = value;
          var slot = applyStatus(s.id, status);
          lastJson[s.id] = JSON.stringify(status);
          setError(s.id, "");
          var card = cards[s.id];
          if (card) {
            card.className = card.className.replace(/state-\S+/, "state-" + status.state);
            fillHead(card.querySelector(".card-head"), slot);
          }
          saved.hidden = false;
          setTimeout(function () { saved.hidden = true; }, 2000);
          return refresh();
        })
        .catch(function (e) { setError(s.id, e.message); });
    }
    return wrap;
  }

  function setActive(id) {
    activeId = id;
    Object.keys(cards).forEach(function (k) {
      cards[k].classList.toggle("active", k === id);
    });
  }

  // ---- choosing, dropping, pasting ----------------------------------------

  function wireDrop(card, s) {
    card.addEventListener("dragover", function (ev) {
      ev.preventDefault();
      card.classList.add("dragover");
    });
    card.addEventListener("dragleave", function () { card.classList.remove("dragover"); });
    card.addEventListener("drop", function (ev) {
      ev.preventDefault();
      card.classList.remove("dragover");
      var files = ev.dataTransfer && ev.dataTransfer.files;
      if (files && files[0]) sendFile(s, files[0]);
    });
  }

  document.addEventListener("paste", function (ev) {
    var t = ev.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return;
    var items = (ev.clipboardData && ev.clipboardData.items) || [];
    var file = null;
    for (var i = 0; i < items.length; i++) {
      if (items[i].kind === "file" && items[i].type.indexOf("image/") === 0) {
        file = items[i].getAsFile();
        break;
      }
    }
    if (!file) return;
    ev.preventDefault();
    var s = activeId && findSlot(activeId);
    if (!s) { toast("Tocca prima una scheda, poi incolla"); return; }
    if (KIND_FAMILY[s.kind] !== "image") { toast("Questo spazio vuole " + WANTS[KIND_FAMILY[s.kind]] + "."); return; }
    sendFile(s, file);
  });

  function pasteFromButton(s) {
    navigator.clipboard.read().then(function (items) {
      for (var i = 0; i < items.length; i++) {
        var types = items[i].types;
        for (var j = 0; j < types.length; j++) {
          if (types[j].indexOf("image/") === 0) {
            return items[i].getType(types[j]).then(function (blob) { sendFile(s, blob); });
          }
        }
      }
      toast("Negli appunti non c'è nessuna immagine.");
    }).catch(function () {
      toast("Non riesco a leggere gli appunti: usa Ctrl + V.");
    });
  }

  // ---- upload -------------------------------------------------------------

  function reencode(s, file) {
    if (typeof createImageBitmap !== "function" || !file.type || file.type.indexOf("image/") !== 0) {
      return Promise.resolve(file);
    }
    return createImageBitmap(file, { imageOrientation: "from-image" }).then(function (bmp) {
      var maxSide = s.kind === "screenshot" ? 2400 : 2000;
      var scale = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
      var w = Math.max(1, Math.round(bmp.width * scale));
      var hgt = Math.max(1, Math.round(bmp.height * scale));
      var canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = hgt;
      var ctx = canvas.getContext("2d");
      var asPng = s.kind === "screenshot" && file.type === "image/png";
      if (!asPng) {
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, w, hgt);
      }
      ctx.drawImage(bmp, 0, 0, w, hgt);
      if (bmp.close) bmp.close();
      return new Promise(function (resolve) {
        canvas.toBlob(function (blob) { resolve(blob || file); },
          asPng ? "image/png" : "image/jpeg", asPng ? undefined : 0.88);
      });
    }).catch(function () { return file; });
  }

  function sendFile(s, file) {
    var id = s.id;
    var family = KIND_FAMILY[s.kind];
    var limit = data.limits[family];
    setError(id, "");
    if (limit && file.size > limit) {
      setError(id, "File troppo grande: massimo " + Math.floor(limit / 1048576) + " MB.");
      return;
    }
    busy[id] = true;
    var prepared = family === "image" ? reencode(s, file) : Promise.resolve(file);
    prepared.then(function (blob) {
      var card = cards[id];
      var bar = card.querySelector(".uploadbar");
      var fill = bar.firstChild;
      bar.hidden = false;
      fill.style.width = "0%";
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/admin/api/materials/" + encodeURIComponent(id) + "/file");
      xhr.setRequestHeader("Content-Type", blob.type || "application/octet-stream");
      xhr.upload.onprogress = function (ev) {
        if (ev.lengthComputable) fill.style.width = Math.round((ev.loaded * 100) / ev.total) + "%";
      };
      xhr.onerror = function () {
        busy[id] = false;
        bar.hidden = true;
        setError(id, "Non riesco a collegarmi. Riprova.");
      };
      xhr.onload = function () {
        busy[id] = false;
        var body = {};
        try { body = JSON.parse(xhr.responseText); } catch (e) { body = {}; }
        if (xhr.status === 401) { location.reload(); return; }
        if (xhr.status >= 200 && xhr.status < 300) {
          unfolded[id] = true;
          replaceCard(applyStatus(id, body));
          refresh();
        } else {
          bar.hidden = true;
          setError(id, typeof body.detail === "string" ? body.detail : "Errore " + xhr.status);
        }
      };
      xhr.send(blob);
    });
  }

  // ---- recording ----------------------------------------------------------

  function startRecording(s, box) {
    var id = s.id;
    setError(id, "");
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      var rec = new MediaRecorder(stream);
      var chunks = [];
      var timer = null;
      busy[id] = true;
      rec.ondataavailable = function (ev) { if (ev.data && ev.data.size) chunks.push(ev.data); };
      rec.onstop = function () {
        stream.getTracks().forEach(function (t) { t.stop(); });
        clearTimeout(timer);
        var blob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
        showTake(s, box, blob);
      };
      var stop = h("button", {
        type: "button", class: "danger", text: "⏹ Stop",
        on: { click: function () { if (rec.state !== "inactive") rec.stop(); } }
      });
      box.textContent = "";
      box.appendChild(h("p", { text: "🔴 Sto registrando… (massimo 60 secondi)" }));
      box.appendChild(stop);
      rec.start();
      timer = setTimeout(function () { if (rec.state !== "inactive") rec.stop(); }, MAX_RECORD_MS);
    }).catch(function () {
      busy[id] = false;
      setError(id, "Non posso usare il microfono. Controlla il permesso del browser.");
    });
  }

  function showTake(s, box, blob) {
    var url = URL.createObjectURL(blob);
    box.textContent = "";
    box.appendChild(h("audio", { src: url, controls: "" }));
    var row = h("div", { class: "actions" });
    row.appendChild(h("button", {
      type: "button", class: "primary", text: "⬆️ Usa questa registrazione",
      on: { click: function () {
        URL.revokeObjectURL(url);
        box.textContent = "";
        sendFile(s, blob);
      } }
    }));
    row.appendChild(h("button", {
      type: "button", text: "Rifai",
      on: { click: function () {
        URL.revokeObjectURL(url);
        box.textContent = "";
        busy[s.id] = false;
      } }
    }));
    box.appendChild(row);
  }

  // ---- build the page -----------------------------------------------------

  function copyList() {
    var lines = data.slots.filter(isRequiredMissing).concat(data.slots.filter(isOptionalMissing))
      .map(function (s) { return s.id + " - " + s.where + " - " + s.title; });
    var text = lines.join("\n");
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); toast("Lista copiata"); } catch (e) { toast("Non riesco a copiare."); }
      ta.remove();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast("Lista copiata"); }, fallback);
    } else fallback();
  }

  function buildShell() {
    app.textContent = "";
    els.progress = h("div", { class: "progress-list" });
    els.tabAll = h("button", { type: "button", text: "Tutto", on: { click: function () { setTab("all"); } } });
    els.tabMissing = h("button", { type: "button", text: "Cosa manca", on: { click: function () { setTab("missing"); } } });
    els.copyBtn = h("button", { type: "button", text: "📋 Copia la lista", hidden: "", on: { click: copyList } });
    els.list = h("div", { class: "list" });
    app.appendChild(els.progress);
    app.appendChild(h("div", { class: "tabs" }, [els.tabAll, els.tabMissing]));
    if (!data.keyConfigured) {
      app.appendChild(h("div", { class: "warn", text: "ℹ️ Pagina senza chiave: chi conosce questo indirizzo può caricare file. Aggiungi MATERIALS_KEY nel file .env." }));
    }
    app.appendChild(h("div", { class: "actions" }, [els.copyBtn]));
    app.appendChild(els.list);
    app.appendChild(buildDangerZone());
  }

  function setTab(name) {
    tab = name;
    renderHeader();
    renderList();
  }

  function buildDangerZone() {
    var zone = h("div", { class: "danger-zone" });
    zone.appendChild(h("p", { text: "I file restano solo su questo computer (data/materials), mai su GitHub." }));
    var reveal = h("button", { type: "button", class: "danger", text: "🗑️ Elimina tutto il materiale" });
    var row = h("div", { class: "row", hidden: "" });
    var input = h("input", { type: "text", placeholder: "Scrivi ELIMINA per confermare", autocomplete: "off" });
    var go = h("button", { type: "button", class: "danger", text: "Elimina tutto" });
    go.disabled = true;
    input.addEventListener("input", function () { go.disabled = input.value !== "ELIMINA"; });
    reveal.addEventListener("click", function () { row.hidden = !row.hidden; });
    go.addEventListener("click", function () {
      api("POST", "/admin/api/materials/delete-all", { confirm: input.value })
        .then(function () {
          input.value = "";
          go.disabled = true;
          row.hidden = true;
          cards = {};
          lastJson = {};
          listSignature = "";
          unfolded = {};
          folded = {};
          toast("Tutto il materiale è stato eliminato.");
          return refresh();
        })
        .catch(function (e) { toast(e.message); });
    });
    row.appendChild(input);
    row.appendChild(go);
    zone.appendChild(reveal);
    zone.appendChild(row);
    return zone;
  }

  load().then(function () {
    buildShell();
    renderHeader();
    renderList();
  }).catch(function (e) {
    app.textContent = "";
    app.appendChild(h("p", { class: "error", text: "Non riesco a caricare i materiali: " + e.message }));
  });
})();
