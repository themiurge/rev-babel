/* "Il CV di Amina" - lesson 5's second tutorial. The student tidies a plain,
   invented CV (Amina Hassan: every name, address, phone number and email on
   it is made up) with titles, bold, italic, bullet lists, colour, copy and
   paste, then prints it or saves it as a PDF through the browser's print
   dialog. At the end a blank, pre-styled skeleton lets them write their own;
   nothing is saved or sent. The engine is ../../guided-editor.js. */
GuidedEditor.run(function (h) {
  "use strict";
  const { quill, filled, anyAttr, lineFormat, btn, alignBtn, lineTarget, menuTarget, selectThen } = h;

  const HEADINGS = ["Profilo", "Esperienza lavorativa", "Istruzione", "Lingue", "Competenze"];
  const AUTH = "autorizzo il trattamento dei dati personali";
  const INITIAL_TEXT = [
    "Amina Hassan",
    "Via Esempio 1, 40100 Bologna · 333 000 0000 · amina.esempio@example.com",
    "Profilo",
    "Cerco lavoro come aiuto cuoca o addetta alle pulizie. Sono puntuale, precisa e lavoro bene in squadra.",
    "Esperienza lavorativa",
    "Aiuto cuoca - Ristorante Da Esempio, Bologna",
    "2023 - 2025",
    "Preparo le verdure e pulisco la cucina.",
    "Addetta alle pulizie - Hotel Esempio, Bologna",
    "2021 - 2023",
    "Pulisco le camere e cambio la biancheria.",
    "Istruzione",
    "Diploma di scuola media - 2012",
    "Corso di italiano, livello A2 - 2024",
    "Lingue",
    "Arabo: madrelingua",
    "Italiano: livello A2",
    "Inglese: livello base",
    "Competenze",
    "Cucina",
    "Pulizia",
    "Lavoro di squadra",
  ].join("\n");

  /* The student's own CV starts from this: styled headings, plain prompts. */
  const SKELETON = [
    { insert: "Nome e cognome" }, { insert: "\n", attributes: { header: 1, align: "center" } },
    { insert: "Indirizzo · Telefono · Email" }, { insert: "\n", attributes: { align: "center" } },
    { insert: "Profilo" }, { insert: "\n", attributes: { header: 2 } },
    { insert: "Scrivi qui due frasi su di te e sul lavoro che cerchi.\n" },
    { insert: "Esperienza lavorativa" }, { insert: "\n", attributes: { header: 2 } },
    { insert: "Lavoro - Dove, Città", attributes: { bold: true } }, { insert: "\n" },
    { insert: "Anno - Anno", attributes: { italic: true } }, { insert: "\n" },
    { insert: "Scrivi qui che cosa facevi.\n" },
    { insert: "Istruzione" }, { insert: "\n", attributes: { header: 2 } },
    { insert: "Scuola o corso - Anno" }, { insert: "\n", attributes: { list: "bullet" } },
    { insert: "Lingue" }, { insert: "\n", attributes: { header: 2 } },
    { insert: "Lingua: livello" }, { insert: "\n", attributes: { list: "bullet" } },
    { insert: "Competenze" }, { insert: "\n", attributes: { header: 2 } },
    { insert: "Una cosa che sai fare" }, { insert: "\n", attributes: { list: "bullet" } },
  ];

  /* ---------- finding things in the document ---------- */
  const norm = (text) => text.replace(/\s+/g, " ").trim();
  const findLine = (L, text) => L.find((l) => norm(l.text) === text);
  /* The lines under a heading, up to the next heading or a blank line. */
  function section(L, heading) {
    const start = L.findIndex((l) => norm(l.text) === heading);
    if (start < 0) return [];
    const out = [];
    for (let k = start + 1; k < L.length; k++) {
      if (HEADINGS.includes(norm(L[k].text)) || norm(L[k].text) === "") break;
      out.push(L[k]);
    }
    return out;
  }
  const jobLines = (L) => L.filter((l) => /^(Aiuto cuoca|Addetta alle pulizie) - /.test(l.text));
  const dateLines = (L) => L.filter((l) => /^\d{4} - \d{4}$/.test(norm(l.text)));
  const wholeLine = (l, attr) => l.len > 0 && quill.getFormat(l.index, l.len)[attr] === true;
  /* A `pick` for selectThen: the first of `lines` that is not done yet. */
  const nextUndone = (lines, isDone) => (L) => {
    const todo = lines(L).find((l) => !isDone(l));
    return todo ? [todo] : [];
  };
  const isBullet = (l) => lineFormat(l).list === "bullet";
  const bulletsCheck = (heading, min) => (L) => {
    const lines = section(L, heading);
    return lines.length >= min && lines.every(isBullet);
  };
  const bulletsStep = (heading, min) => ({
    target: selectThen((L) => section(L, heading), btn('.ql-list[value="bullet"]'), false),
    check: bulletsCheck(heading, min),
  });

  /* ---------- print / save as PDF ---------- */
  let printed = false;
  const titleBefore = document.title;
  document.getElementById("print-btn").addEventListener("click", () => window.print());
  window.addEventListener("beforeprint", () => {
    printed = true;
    document.title = "CV"; // the suggested name of the PDF file
    h.evaluate();
  });
  window.addEventListener("afterprint", () => { document.title = titleBefore; });

  const STEPS = [
    { // 1 - the name is a Title
      target: selectThen((L) => [L[0]], menuTarget("header", "1"), false),
      check: (L) => !!lineFormat(L[0]).header,
    },
    { // 2 - centre the name
      target: selectThen((L) => [L[0]], alignBtn("center"), false),
      check: (L) => lineFormat(L[0]).align === "center",
    },
    { // 3 - centre the contact line
      target: selectThen((L) => [L[1]], alignBtn("center"), false),
      check: (L) => !!L[1] && lineFormat(L[1]).align === "center",
    },
    { // 4 - "Profilo" is a Sottotitolo
      target: selectThen((L) => [findLine(L, "Profilo")], menuTarget("header", "2"), false),
      check: (L) => { const l = findLine(L, "Profilo"); return !!l && lineFormat(l).header === 2; },
    },
    { // 5 - the other four headings
      target: selectThen(
        nextUndone((L) => HEADINGS.map((t) => findLine(L, t)).filter(Boolean), (l) => lineFormat(l).header === 2),
        menuTarget("header", "2"), false),
      check: (L) => HEADINGS.every((t) => { const l = findLine(L, t); return !!l && lineFormat(l).header === 2; }),
    },
    { // 6 - the two jobs in bold
      target: selectThen(nextUndone(jobLines, (l) => wholeLine(l, "bold")), btn(".ql-bold"), true),
      check: (L) => jobLines(L).length === 2 && jobLines(L).every((l) => wholeLine(l, "bold")),
    },
    { // 7 - the two dates in italic
      target: selectThen(nextUndone(dateLines, (l) => wholeLine(l, "italic")), btn(".ql-italic"), true),
      check: (L) => dateLines(L).length === 2 && dateLines(L).every((l) => wholeLine(l, "italic")),
    },
    bulletsStep("Competenze", 3), // 8 - skills as a bulleted list
    bulletsStep("Lingue", 3), // 9 - languages
    bulletsStep("Istruzione", 2), // 10 - education
    { // 11 - colour for the name
      target: selectThen((L) => [L[0]], menuTarget("color", "#1a56c4"), true),
      check: (L) => anyAttr(L[0], "color"),
    },
    { // 12 - one more skill, typed
      target: lineTarget((L) => section(L, "Competenze").slice(-1)),
      check: (L) => L.some((l) => /computer/i.test(l.text) && isBullet(l)),
    },
    { // 13 - copy the privacy sentence from the pane and paste it below the list
      target: lineTarget((L) => [L[L.length - 1]]),
      check: (L) => L.some((l) => norm(l.text).toLowerCase().includes(AUTH) && !lineFormat(l).list),
    },
    { // 14 - print / PDF
      target: () => ({ el: document.getElementById("print-btn"), side: "top" }),
      enter: () => { printed = false; },
      check: () => printed,
    },
  ];

  return {
    steps: STEPS,
    focusAtStart: false,
    initialText: INITIAL_TEXT,
    finalButtons: [{
      labelKey: "ui_owncv",
      run() {
        quill.setContents(SKELETON, "silent");
        quill.setSelection(0, 0, "silent");
      },
    }],
  };
});
