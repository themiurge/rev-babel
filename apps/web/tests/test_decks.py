from rev_babel_web import decks


def test_list_decks_finds_the_sample_deck() -> None:
    found = {d["slug"]: d for d in decks.list_decks()}
    assert "lezione-2-account-demo" in found
    assert found["lezione-2-account-demo"]["slide_count"] == 3


def test_get_slide_returns_italian_and_translation() -> None:
    slide = decks.get_slide("lezione-2-account-demo", 1, "ar")
    assert slide is not None
    assert "Il tuo account" in slide["it"]
    assert "حسابك" in slide["translated"]


def test_get_slide_out_of_range_is_none() -> None:
    assert decks.get_slide("lezione-2-account-demo", 99, "en") is None
    assert decks.get_slide("lezione-2-account-demo", 0, "en") is None


def test_get_deck_unknown_slug_is_none() -> None:
    assert decks.get_deck("nope") is None
    assert decks.get_slide("nope", 1, "en") is None


def test_list_decks_finds_the_password_deck() -> None:
    found = {d["slug"]: d for d in decks.list_decks()}
    assert "lezione-2-password-sicura" in found
    assert found["lezione-2-password-sicura"]["slide_count"] == 3


def test_password_deck_translates_the_word_but_not_the_examples() -> None:
    """Regression test for a real translation bug: an overly broad
    "never translate 'password'" instruction to the agy CLI initially left
    the Italian word untranslated even in ordinary prose, not just inside
    the literal weak-password example. Slide 1 uses "password" as a normal
    word (must be translated); slide 2's weak-password example literally
    contains the string "password" (must stay untouched, in every language,
    since it's one of the illustrative weak passwords itself)."""
    slide1 = decks.get_slide("lezione-2-password-sicura", 1, "fr")
    assert "password" not in slide1["translated"]
    assert "mot de passe" in slide1["translated"]

    slide2 = decks.get_slide("lezione-2-password-sicura", 2, "fr")
    assert '<div class="pw-example">password</div>' in slide2["translated"]
