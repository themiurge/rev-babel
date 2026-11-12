"""Lesson 7: runs a student's Python program, inside her browser.

This file is served as a static asset and executed by Pyodide in a Web
Worker (static/lessons/lezione-7/python/worker.js). It is also imported by
the test suite under CPython, which is why it uses nothing but the standard
library and never imports `js` or `pyodide`. See
docs/decisions/0019-lesson-7-python-in-the-browser.md.

Nothing here touches the network. The student's code, its output and her
answers to input() stay in the page.

The fences below (allowed modules, builtins, step and output budgets) keep a
beginner's program focused and keep the page responsive. They are not a
security boundary: the program runs in the student's own browser tab, and
the browser is the boundary.
"""

from __future__ import annotations

import builtins
import difflib
import json
import random
import sys
import traceback

FILENAME = "<il tuo programma>"
MAX_STEPS = 200_000  # traced line events per run: an endless loop stops here
MAX_LINES = 200  # output lines
MAX_CHARS = 5_000  # output characters
MAX_ANSWERS = 10  # answers to input() in one run
RECURSION_LIMIT = 120  # frames above the runner's own
ALLOWED_MODULES = {"random", "math"}

_TYPOS = str.maketrans(
    {
        "\u201c": '"',  # left double quotation mark
        "\u201d": '"',  # right double quotation mark
        "\u201e": '"',  # low double quotation mark
        "\u00ab": '"',  # guillemet
        "\u00bb": '"',  # guillemet
        "\u2018": "'",  # left single quotation mark
        "\u2019": "'",  # right single quotation mark / apostrophe
        "\u00a0": " ",  # non-breaking space
        "\t": "    ",
    }
)

_SAFE_BUILTINS = (
    "abs bool dict enumerate float int isinstance len list max min range "
    "reversed round set sorted str sum tuple type zip "
    "Exception IndexError KeyError NameError TypeError ValueError ZeroDivisionError"
).split()
# Real builtins a beginner might reach for that this lesson leaves out.
_BLOCKED_NAMES = {
    "open",
    "eval",
    "exec",
    "compile",
    "globals",
    "locals",
    "vars",
    "dir",
    "help",
    "exit",
    "quit",
    "breakpoint",
    "getattr",
    "setattr",
    "delattr",
    "memoryview",
}
_KEYWORDS_CAPS = {
    "For": "for",
    "If": "if",
    "Else": "else",
    "Elif": "elif",
    "While": "while",
    "In": "in",
    "Print": "print",
    "Input": "input",
    "Range": "range",
}
_CLOSERS = {"(": ")", "[": "]", "{": "}"}

# Every sentence the student can see from this file. Italian, short, A2.
MESSAGES = {
    "syntax_quote": 'Manca una virgoletta ". '
    "Un testo ha una virgoletta all'inizio e una alla fine.",
    "syntax_paren": "Manca una parentesi {closer} . Ogni {opener} vuole la sua {closer} .",
    "syntax_colon": "Mancano i due punti : alla fine della riga.",
    "syntax_print": 'Dopo print servono le parentesi. Così: print("ciao")',
    "syntax_equals": "Per confrontare usa due uguali ==. Un solo = mette una cosa nella scatola.",
    "syntax_comma": "Forse manca una virgola , tra due cose.",
    "syntax_caps": "Scrivi «{right}» con la lettera piccola, non «{wrong}».",
    "syntax_other": "Python non capisce come è scritta questa riga. "
    'Controlla le virgolette " ", le parentesi ( ) e i due punti :',
    "indent_expected": "Le righe dentro for, if o else vogliono 4 spazi davanti.",
    "indent_unexpected": "Questa riga ha spazi davanti, ma non deve. "
    "Cancella gli spazi all'inizio.",
    "indent_mismatch": "Gli spazi davanti non sono allineati. Usa 4 spazi, come le altre righe.",
    "name_typo": "Python non conosce «{name}». Forse volevi scrivere «{close}»?",
    "name_text": 'Python non conosce «{name}». Se è un testo, mettilo tra virgolette: "{name}".',
    "name_blocked": "«{name}» non si usa in questa lezione.",
    "concat": 'Non puoi unire testo e numero con +. Usa la virgola: print("Anni:", 30)',
    "range_text": "Dentro range( ) serve un numero, senza virgolette. Così: range(5)",
    "type_other": "Stai usando insieme cose diverse: forse un testo e un numero?",
    "value_number": "Qui serviva un numero, ma c'è un testo.",
    "zero": "Non si può dividere per zero. Neanche il computer ci riesce! 😄",
    "index": "Nella lista non c'è un posto con quel numero. Attenzione: si conta da 0.",
    "import": "In questa lezione puoi usare solo random e math.",
    "loop": "Il programma lavora da troppo tempo: forse una ripetizione che non finisce mai. "
    "L'ho fermato.",
    "too_much": "Troppe righe! Qui mi fermo a {max} righe. Il computer ne scriverebbe milioni. 😄",
    "too_many_answers": "Troppe domande in un programma solo. Mi fermo qui.",
    "other": "Python ha trovato un problema. Leggi il messaggio in inglese qui sotto, "
    "o chiedi all'assistente.",
    # step nudges
    "step_blank": "Quasi! Cambia ___ con le tue parole.",
    "step_same_food": "Funziona! Ora cambia «pizza» con il tuo piatto preferito.",
    "step_same_count": "Funziona! Ora cambia il 3 con un altro numero.",
    "step_list_short": "Funziona! Ora aggiungi una cosa alla lista.",
    "step_same_code": "Funziona! Ora cambia il programma: aggiungi un saluto o cambia la frase.",
    "step_limit_found": "Hai trovato il limite! Il computer non si stanca mai. 🔁",
}


class _TooManySteps(BaseException):
    pass


class _TooMuchOutput(BaseException):
    pass


class _NeedInput(BaseException):
    pass


class _TooManyAnswers(BaseException):
    pass


def normalize(code: str) -> str:
    """Forgive what a keyboard or a copy-paste does to code: curly quotes,
    guillemets, non-breaking spaces and tabs."""
    lines = code.translate(_TYPOS).replace("\r\n", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines)


class _Output:
    def __init__(self) -> None:
        self.text = ""

    def write(self, s: str) -> None:
        room = MAX_CHARS - len(self.text)
        self.text += s[: max(room, 0)]
        if len(s) > room or self.text.count("\n") > MAX_LINES:
            self.text = "\n".join(self.text.split("\n")[:MAX_LINES])
            raise _TooMuchOutput()


def _say(key: str, **params: object) -> str:
    return MESSAGES[key].format(**params)


def _explain_syntax(exc: SyntaxError, line_text: str) -> str:
    msg = exc.msg or ""
    first_word = line_text.strip().split("(")[0].split(" ")[0].rstrip(":")
    if isinstance(exc, IndentationError):
        if msg.startswith("expected an indented block"):
            return _say("indent_expected")
        if msg == "unexpected indent":
            return _say("indent_unexpected")
        return _say("indent_mismatch")
    if first_word in _KEYWORDS_CAPS:
        return _say("syntax_caps", wrong=first_word, right=_KEYWORDS_CAPS[first_word])
    if msg.startswith("unterminated string"):
        return _say("syntax_quote")
    if msg.endswith("was never closed"):
        opener = msg[1]
        return _say("syntax_paren", opener=opener, closer=_CLOSERS.get(opener, ")"))
    if msg == "expected ':'":
        return _say("syntax_colon")
    if msg.startswith("Missing parentheses in call to 'print'"):
        return _say("syntax_print")
    if "'=='" in msg:
        return _say("syntax_equals")
    if "forgot a comma" in msg:
        return _say("syntax_comma")
    return _say("syntax_other")


def _explain(exc: BaseException, known_names: list[str]) -> tuple[str, str]:
    """(kind, Italian sentence) for an exception raised by her program."""
    if isinstance(exc, NameError) and not isinstance(exc, UnboundLocalError):
        name = getattr(exc, "name", "") or ""
        if name in _BLOCKED_NAMES:
            return "name", _say("name_blocked", name=name)
        close = difflib.get_close_matches(name, known_names, n=1, cutoff=0.6)
        if not close:
            close = [n for n in known_names if n.lower() == name.lower()]
        if close:
            return "name", _say("name_typo", name=name, close=close[0])
        return "name", _say("name_text", name=name)
    if isinstance(exc, ImportError):
        return "import", _say("import")
    if isinstance(exc, TypeError):
        text = str(exc)
        if "concatenate" in text or "unsupported operand" in text:
            return "type", _say("concat")
        if "cannot be interpreted as an integer" in text:
            return "type", _say("range_text")
        return "type", _say("type_other")
    if isinstance(exc, ValueError) and "invalid literal" in str(exc):
        return "value", _say("value_number")
    if isinstance(exc, ZeroDivisionError):
        return "zero", _say("zero")
    if isinstance(exc, IndexError):
        return "index", _say("index")
    if isinstance(exc, RecursionError):
        return "loop", _say("loop")
    return "other", _say("other")


def _line_of(exc: BaseException) -> int | None:
    line = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if frame.filename == FILENAME:
            line = frame.lineno
    return line


def run(code: str, answers: list[str] | None = None, seed: int = 0, step: str = "") -> dict:
    """Run one program from a clean slate. Returns a JSON-able dict:

    ok          the program finished without an error
    output      what it printed (and the input() prompts with her answers)
    need_input  the prompt of an input() still waiting for an answer, or None:
                the page asks her, then runs the whole program again with one
                more answer and the same seed
    error       None, or {kind, text (Italian), line, line_text, original}
    done, note  whether this step's goal is reached, and an Italian nudge
    """
    code = normalize(code)
    lines = code.split("\n")
    pending = list(answers or [])[:MAX_ANSWERS]
    used: list[str] = []
    out = _Output()
    state = {"steps": 0, "prompt": None, "tripped": False}

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None
        if event == "line":
            state["steps"] += 1
            if state["steps"] > MAX_STEPS:
                state["tripped"] = True
                raise _TooManySteps()
        return tracer

    def student_print(*args, sep=" ", end="\n", **_ignored):
        out.write(str(sep).join(str(a) for a in args) + str(end))

    def student_input(prompt=""):
        if len(used) >= MAX_ANSWERS:
            raise _TooManyAnswers()
        out.write(str(prompt))
        if not pending:
            state["prompt"] = str(prompt)
            raise _NeedInput()
        answer = pending.pop(0)
        used.append(answer)
        out.write(answer + "\n")
        return answer

    def student_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level != 0 or name.split(".")[0] not in ALLOWED_MODULES:
            raise ImportError(name)
        return __import__(name, globals, locals, fromlist, level)

    safe = {name: getattr(builtins, name) for name in _SAFE_BUILTINS}
    safe.update(print=student_print, input=student_input, __import__=student_import)
    namespace: dict = {"__builtins__": safe, "__name__": "__main__"}
    random.seed(seed)

    result: dict = {"ok": False, "output": "", "need_input": None, "error": None}
    old_limit = sys.getrecursionlimit()
    try:
        compiled = compile(code, FILENAME, "exec")
        depth = len(traceback.extract_stack())
        sys.setrecursionlimit(depth + RECURSION_LIMIT)
        sys.settrace(tracer)
        try:
            exec(compiled, namespace)
        finally:
            sys.settrace(None)
            sys.setrecursionlimit(old_limit)
        if state["tripped"]:  # her bare `except:` swallowed the stop
            raise _TooManySteps()
        result["ok"] = True
    except _NeedInput:
        result["need_input"] = state["prompt"]
    except _TooManySteps:
        result["error"] = _error("loop", _say("loop"), None, lines, "")
    except _TooMuchOutput:
        result["error"] = _error("too_much", _say("too_much", max=MAX_LINES), None, lines, "")
    except _TooManyAnswers:
        result["error"] = _error("other", _say("too_many_answers"), None, lines, "")
    except SyntaxError as exc:
        line_text = lines[exc.lineno - 1] if exc.lineno and exc.lineno <= len(lines) else ""
        result["error"] = _error(
            "syntax",
            _explain_syntax(exc, line_text),
            exc.lineno,
            lines,
            f"{type(exc).__name__}: {exc.msg}",
        )
    except Exception as exc:  # her program's own error, whatever it is
        known = list(safe) + [k for k in namespace if not k.startswith("__")]
        kind, text = _explain(exc, known)
        result["error"] = _error(kind, text, _line_of(exc), lines, f"{type(exc).__name__}: {exc}")
    except BaseException as exc:  # SystemExit, KeyboardInterrupt raised by her code
        result["error"] = _error("other", _say("other"), _line_of(exc), lines, type(exc).__name__)
    result["output"] = out.text
    result["done"], result["note"] = check_step(step, code, result, namespace)
    return result


def _error(kind: str, text: str, line: int | None, lines: list[str], original: str) -> dict:
    line_text = lines[line - 1].strip() if line and 0 < line <= len(lines) else ""
    return {
        "kind": kind,
        "text": text,
        "line": line,
        "line_text": line_text,
        "original": original[:300],
    }


# ---- each step's goal ------------------------------------------------------

STARTS = {  # only what the checks need; the full content is python_lesson.json
    "s7": '# Il mio biglietto di benvenuto\nsaluti = ["Ciao", "Hello", "Bonjour", "Salam"]\n'
    'for saluto in saluti:\n    print("🌸", saluto, "🌸")\nprint("Benvenute nella nostra classe!")',
}


def _out_lines(result: dict) -> list[str]:
    return [line for line in result["output"].split("\n") if line.strip()]


def check_step(step: str, code: str, result: dict, ns: dict) -> tuple[bool, str | None]:
    error = result["error"]
    if step == "s4" and error and error["kind"] == "too_much":
        return True, _say("step_limit_found")
    if not result["ok"]:
        return False, None
    out = _out_lines(result)
    if step == "s1":
        return bool(out), None
    if step == "s2":
        if "___" in result["output"]:
            return False, _say("step_blank")
        return bool(out), None
    if step == "s3":
        food = ns.get("piatto")
        if isinstance(food, str) and food.strip().lower() == "pizza":
            return False, _say("step_same_food")
        return len(out) >= 2, None
    if step == "s4":
        if len(out) == 3:
            return False, _say("step_same_count")
        return len(out) >= 1, None
    if step == "s5":
        items = ns.get("spesa")
        if isinstance(items, list) and len(items) <= 3:
            return False, _say("step_list_short")
        return len(out) >= 4, None
    if step == "s6":
        return "\n" in result["output"] and ns.get("risposta") is not None, None
    if step == "s7":
        if normalize(code).strip() == normalize(STARTS["s7"]).strip():
            return False, _say("step_same_code")
        return len(out) >= 3, None
    return False, None


def run_json(code: str, answers_json: str, seed: int, step: str) -> str:
    """The worker's entry point: JSON in, JSON out, no proxies to manage."""
    answers = [str(a) for a in json.loads(answers_json or "[]")]
    return json.dumps(run(code, answers, int(seed), step), ensure_ascii=False)
