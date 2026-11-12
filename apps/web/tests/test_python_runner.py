"""Lesson 7's runner, loaded by path and run under CPython 3.14 (the same Python
Pyodide 314 gives the students). Invented code only."""

import importlib.util
import json
import re
import sys
import time
from pathlib import Path

import pytest
from rev_babel_web import python_helper

RUNNER_PATH = Path(__file__).parents[1] / "static/lessons/lezione-7/python/runner.py"
_spec = importlib.util.spec_from_file_location("lesson7_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

STEPS = python_helper.STEPS


def run(code, answers=None, seed=0, step=""):
    return runner.run(code, answers, seed, step)


def test_hello() -> None:
    r = run('print("Ciao!")')
    assert r["ok"] and r["output"] == "Ciao!\n" and r["error"] is None


def test_typos_are_normalised() -> None:
    assert run("print(“Ciao”)")["output"] == "Ciao\n"
    assert run("print(«Ciao»)")["output"] == "Ciao\n"
    assert run('print("a b")')["ok"]
    r = run('\tprint("x")')
    assert r["error"]["kind"] == "syntax" and "non deve" in r["error"]["text"]


ERRORS = [
    ('Print("a")', "name", "«print»", 1),
    ('prnt("a")', "name", "«print»", 1),
    ('piatto = "x"\nprint(piato)', "name", "«piatto»", 2),
    ("print(ciao)", "name", "tra virgolette", 1),
    ('print("ciao)', "syntax", "virgoletta", 1),
    ('print("ciao"', "syntax", "parentesi )", 1),
    ('x = ["a", "b"', "syntax", "parentesi ]", 1),
    ("for i in range(3)\n    print(i)", "syntax", "due punti", 1),
    ("for i in range(3):\nprint(i)", "syntax", "4 spazi", 2),
    ("  print(1)", "syntax", "non deve", 1),
    ('print "ciao"', "syntax", "parentesi", 1),
    ("if x = 1:\n    pass", "syntax", "==", 1),
    ("For i in range(3):\n    print(i)", "syntax", "«for»", 1),
    ('print("a" + 3)', "type", "virgola", 1),
    ('for i in range("3"):\n    pass', "type", "range", 1),
    ('int("ciao")', "value", "numero", 1),
    ("print(1/0)", "zero", "zero", 1),
    ("l = [1]\nprint(l[5])", "index", "da 0", 2),
    ("import os", "import", "random e math", 1),
    ("import js", "import", "random e math", 1),
    ("import pyodide", "import", "random e math", 1),
    ('__import__("os")', "import", "random e math", 1),
    ('open("f")', "name", "non si usa", 1),
    ('eval("1")', "name", "non si usa", 1),
]


@pytest.mark.parametrize(("code", "kind", "fragment", "line"), ERRORS)
def test_error_table(code, kind, fragment, line) -> None:
    r = run(code)
    err = r["error"]
    assert err is not None and not r["ok"], code
    assert err["kind"] == kind, (code, err)
    assert fragment in err["text"], (code, err)
    assert err["line"] == line, (code, err)
    # Italian text, not Python's English; the line is quoted back stripped.
    assert err["text"] and err["text"] != err["original"]
    assert err["line_text"] == code.split("\n")[line - 1].strip()


def test_random_and_math_with_seed() -> None:
    code = "import random\nimport math\nprint(random.randint(1, 10**6), math.sqrt(16))"
    assert run(code, seed=5)["output"] == run(code, seed=5)["output"]
    assert run(code, seed=5)["ok"]


@pytest.mark.parametrize(
    "code", ["while True:\n    pass", "try:\n    while True:\n        pass\nexcept:\n    pass"]
)
def test_endless_loop_is_stopped(code) -> None:
    started = time.time()
    r = run(code)
    assert time.time() - started < 5
    assert r["error"]["kind"] == "loop"
    assert sys.gettrace() is None


def test_recursion_is_stopped_and_limits_restored() -> None:
    before = sys.getrecursionlimit()
    r = run("def f():\n    f()\nf()")
    assert r["error"]["kind"] == "loop"
    assert sys.getrecursionlimit() == before and sys.gettrace() is None


def test_output_flood() -> None:
    r = run("for i in range(100000):\n    print(i)")
    assert r["error"]["kind"] == "too_much"
    assert len([x for x in r["output"].split("\n") if x]) <= runner.MAX_LINES
    r = run('print("x" * 100000)')
    assert r["error"]["kind"] == "too_much" and len(r["output"]) <= runner.MAX_CHARS


ASK = (
    'risposta = input("Hai fame? ")\nif risposta == "si":\n'
    '    print("Allora mangiamo!")\nelse:\n    print("Dopo.")'
)


def test_input_round_trip() -> None:
    r = run(ASK)
    assert r["need_input"] == "Hai fame? " and not r["ok"] and r["error"] is None
    assert r["output"].endswith("Hai fame? ")
    r = run(ASK, ["si"])
    assert r["ok"] and "Hai fame? si" in r["output"] and "Allora mangiamo!" in r["output"]
    assert "Dopo." in run(ASK, ["Si"])["output"]
    many = run("while True:\n    input('?')", ["a"] * 30)
    assert "Troppe domande" in many["error"]["text"]


def test_state_does_not_leak() -> None:
    run("x = 1")
    assert run("print(x)")["error"]["kind"] == "name"


def test_exit_escapes_do_not_propagate() -> None:
    assert run("raise SystemExit")["error"] is not None
    assert run("raise KeyboardInterrupt")["error"] is not None


def test_run_json_shape() -> None:
    out = json.loads(runner.run_json('print("a")', "[]", 1, "s1"))
    assert {"ok", "output", "need_input", "error", "done", "note"} <= set(out)


def test_every_message_formats() -> None:
    params = dict(closer=")", opener="(", right="for", wrong="For", name="x", close="y", max=1)
    for key, text in runner.MESSAGES.items():
        assert text.strip()
        text.format(**params)
    # And the table above reaches the main branches.
    for code, *_ in ERRORS:
        assert run(code)["error"]["text"].strip()


def test_runner_is_pure_python() -> None:
    source = RUNNER_PATH.read_text()
    for forbidden in (
        r"import js\b",
        r"from js\b",
        r"import pyodide",
        r"pyodide\.",
        "urllib",
        "socket",
    ):
        assert not re.search(forbidden, source), forbidden


# ---- each step's goal ---------------------------------------------------------


def _start(step):
    return STEPS[step]["start"]


@pytest.mark.parametrize("step", list(STEPS))
def test_starts_run_clean(step) -> None:
    r = run(_start(step), step=step)
    assert r["error"] is None
    if step == "s6":
        assert r["need_input"]
    else:
        assert r["ok"]


def test_step_goals() -> None:
    assert run(_start("s1"), step="s1")["done"]
    assert run(_start("s6"), ["si"], step="s6")["done"]
    for step in ("s2", "s3", "s4", "s5", "s7"):
        r = run(_start(step), step=step)
        assert not r["done"], step
    assert run(_start("s2"), step="s2")["note"] == runner.MESSAGES["step_blank"]
    assert run(_start("s3"), step="s3")["note"] == runner.MESSAGES["step_same_food"]
    assert run(_start("s4"), step="s4")["note"] == runner.MESSAGES["step_same_count"]
    assert run(_start("s5"), step="s5")["note"] == runner.MESSAGES["step_list_short"]
    assert run(_start("s7"), step="s7")["note"] == runner.MESSAGES["step_same_code"]
    changed = {
        "s2": _start("s2").replace("___", "Bologna"),
        "s3": _start("s3").replace("pizza", "cuscus"),
        "s4": _start("s4").replace("3", "10"),
        "s5": _start("s5").replace('"mele"', '"mele", "riso"'),
        "s7": _start("s7").replace('"Salam"', '"Salam", "Silav"'),
    }
    for step, code in changed.items():
        assert run(code, step=step)["done"], step
    flood = run(_start("s4").replace("3", "100000"), step="s4")
    assert flood["done"] and flood["note"] == runner.MESSAGES["step_limit_found"]


def test_step_ids_match() -> None:
    assert runner.STARTS["s7"] == STEPS["s7"]["start"]
    # Every id in the lesson is handled by check_step (it never falls through
    # to the unknown-step default for a program that clearly succeeds).
    for step in STEPS:
        src = RUNNER_PATH.read_text()
        assert f'step == "{step}"' in src
    assert 'step == "s8"' not in RUNNER_PATH.read_text()
