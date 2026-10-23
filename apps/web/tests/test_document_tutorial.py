import json
import re
from pathlib import Path

from fastapi.testclient import TestClient
from rev_babel_web import i18n
from rev_babel_web.main import DOC_TUTORIAL_STRINGS, app

LANGS = ["it", *i18n.LANGUAGES]
WEB = Path(__file__).resolve().parent.parent


def _student(name: str) -> TestClient:
    c = TestClient(app)
    c.post("/welcome", data={"name": name}, follow_redirects=True)
    return c


def test_lesson_5_links_to_the_tutorial_in_a_new_tab() -> None:
    c = _student("Amina")
    response = c.get("/course/lezione-5")
    assert response.status_code == 200
    assert 'href="/games/documento"' in response.text
    assert 'target="_blank"' in response.text
    redirect = c.get("/course/lezione-5/documento", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == "/games/documento"


def test_lesson_5_is_in_the_course_menu() -> None:
    page = _student("Bushra").get("/course")
    assert "/course/lezione-5" in page.text


def test_tutorial_page_needs_a_name() -> None:
    anonymous = TestClient(app).get("/games/documento", follow_redirects=False)
    assert anonymous.status_code == 303


def test_tutorial_page_has_the_editor_the_pane_and_the_vendored_editor() -> None:
    c = _student("Chiara")
    page = c.get("/games/documento")
    assert page.status_code == 200
    for needle in ('id="editor"', 'id="toolbar"', 'id="step-body"', 'id="arrow"'):
        assert needle in page.text
    assert "</script><script" not in page.text.split('id="doc-strings"')[1][:50]
    for path in (
        "/static/vendor/quill/quill.js",
        "/static/vendor/quill/quill.snow.css",
        "/static/lessons/lezione-5/documento/tutorial.js",
    ):
        assert c.get(path).status_code == 200


def test_every_string_is_there_in_every_language() -> None:
    for key, entry in DOC_TUTORIAL_STRINGS.items():
        for lang in LANGS:
            assert entry.get(lang, "").strip(), (key, lang)


def test_every_tutorial_step_has_a_title_a_body_and_a_hint() -> None:
    js = (WEB / "static/lessons/lezione-5/documento/tutorial.js").read_text(encoding="utf-8")
    steps = len(re.findall(r"^\s*\{ // \d+", js, flags=re.M))
    assert steps >= 10
    for n in range(1, steps + 1):
        for part in ("t", "b", "h"):
            assert f"s{n}_{part}" in DOC_TUTORIAL_STRINGS
    assert f"s{steps + 1}_t" not in DOC_TUTORIAL_STRINGS


def test_toolbar_hover_strings_exist_for_every_button() -> None:
    html = (WEB / "templates/games/documento.html").read_text(encoding="utf-8")
    for key in re.findall(r'data-tb="(\w+)"', html):
        assert key in DOC_TUTORIAL_STRINGS


def test_strings_survive_embedding_in_a_script_tag() -> None:
    page = _student("Dilnoza").get("/games/documento")
    opening = '<script id="doc-strings" type="application/json">'
    blob = page.text.split(opening)[1].split("</script>")[0]
    assert json.loads(blob) == DOC_TUTORIAL_STRINGS
