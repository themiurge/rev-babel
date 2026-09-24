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
