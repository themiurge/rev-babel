/* "Scrivi un documento" - lesson 5's first tutorial: typing, selecting, bold,
   italic, underline, colour, alignment, undo/redo and lists, one step at a
   time. The engine (arrow, panes, step runner) is ../../guided-editor.js. */
GuidedEditor.run(function (h) {
  "use strict";
  const { quill, filled, anyAttr, lineFormat, btn, alignBtn, lineTarget, menuTarget } = h;

  /* The three "list" lines the student writes after the sentence. */
  function listLines(L) { return L.slice(2).filter((l) => filled(l)); }

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

  return { steps: STEPS };
});
