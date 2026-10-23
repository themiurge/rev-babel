import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from rev_babel_web import i18n
from rev_babel_web.main import CV_TUTORIAL_STRINGS, DOC_TUTORIAL_STRINGS, app

LANGS = ["it", *i18n.LANGUAGES]
WEB = Path(__file__).resolve().parent.parent

# (route slug, page template, steps file, strings)
TUTORIALS = {
    "documento": ("games/documento.html", "lezione-5/documento/tutorial.js", DOC_TUTORIAL_STRINGS),
    "cv": ("games/cv.html", "lezione-5/cv/tutorial.js", CV_TUTORIAL_STRINGS),
}


def _student(name: str) -> TestClient:
    c = TestClient(app)
    c.post("/welcome", data={"name": name}, follow_redirects=True)
    return c


@pytest.mark.parametrize("slug", TUTORIALS)
def test_lesson_5_links_to_each_tutorial_in_a_new_tab(slug: str) -> None:
    c = _student("Amina")
    response = c.get("/course/lezione-5")
    assert response.status_code == 200
    assert f'href="/games/{slug}"' in response.text
    assert 'target="_blank"' in response.text
    redirect = c.get(f"/course/lezione-5/{slug}", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == f"/games/{slug}"


def test_lesson_5_is_in_the_course_menu() -> None:
    page = _student("Bushra").get("/course")
    assert "/course/lezione-5" in page.text


@pytest.mark.parametrize("slug", TUTORIALS)
def test_tutorial_page_needs_a_name(slug: str) -> None:
    anonymous = TestClient(app).get(f"/games/{slug}", follow_redirects=False)
    assert anonymous.status_code == 303


@pytest.mark.parametrize("slug", TUTORIALS)
def test_tutorial_page_has_the_editor_the_pane_and_the_vendored_editor(slug: str) -> None:
    c = _student("Chiara")
    page = c.get(f"/games/{slug}")
    assert page.status_code == 200
    for needle in ('id="editor"', 'id="toolbar"', 'id="step-body"', 'id="arrow"'):
        assert needle in page.text
    steps_file = TUTORIALS[slug][1]
    for path in (
        "/static/vendor/quill/quill.js",
        "/static/vendor/quill/quill.snow.css",
        "/static/lessons/guided-editor.js",
        f"/static/lessons/{steps_file}",
    ):
        assert c.get(path).status_code == 200


def test_cv_page_has_the_print_button() -> None:
    page = _student("Dilnoza").get("/games/cv")
    assert 'id="print-btn"' in page.text
    assert "@media print" in page.text


@pytest.mark.parametrize("slug", TUTORIALS)
def test_every_string_is_there_in_every_language(slug: str) -> None:
    for key, entry in TUTORIALS[slug][2].items():
        for lang in LANGS:
            assert entry.get(lang, "").strip(), (key, lang)


@pytest.mark.parametrize("slug", TUTORIALS)
def test_every_tutorial_step_has_a_title_a_body_and_a_hint(slug: str) -> None:
    strings = TUTORIALS[slug][2]
    js = (WEB / "static/lessons" / TUTORIALS[slug][1]).read_text(encoding="utf-8")
    numbers = [int(n) for n in re.findall(r"//\s*(\d+)(?:\s|$)", js)]
    steps = max(numbers)
    assert steps >= 10
    assert sorted(set(numbers)) == list(range(1, steps + 1))
    for n in range(1, steps + 1):
        for part in ("t", "b", "h"):
            assert f"s{n}_{part}" in strings
    assert f"s{steps + 1}_t" not in strings


@pytest.mark.parametrize("slug", TUTORIALS)
def test_toolbar_hover_strings_exist_for_every_button(slug: str) -> None:
    html = (WEB / "templates/games/_guided_editor.html").read_text(encoding="utf-8")
    html += (WEB / "templates" / TUTORIALS[slug][0]).read_text(encoding="utf-8")
    for key in re.findall(r'data-tb="(\w+)"', html):
        assert key in TUTORIALS[slug][2]


@pytest.mark.parametrize("slug", TUTORIALS)
def test_strings_survive_embedding_in_a_script_tag(slug: str) -> None:
    page = _student("Eli").get(f"/games/{slug}")
    opening = '<script id="doc-strings" type="application/json">'
    blob = page.text.split(opening)[1].split("</script>")[0]
    assert json.loads(blob) == TUTORIALS[slug][2]
