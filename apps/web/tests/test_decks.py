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


def test_list_decks_finds_the_scams_deck() -> None:
    found = {d["slug"]: d for d in decks.list_decks()}
    assert "lezione-2-truffe-online" in found
    assert found["lezione-2-truffe-online"]["slide_count"] == 5


def test_scams_deck_preserves_protected_terms_and_emoji() -> None:
    slide3 = decks.get_slide("lezione-2-truffe-online", 3, "ar")
    assert "SPID" in slide3["it"]
    assert "SPID" in slide3["translated"]

    slide4 = decks.get_slide("lezione-2-truffe-online", 4, "ckb")
    assert "commissariatodips.it" in slide4["translated"]

    slide1 = decks.get_slide("lezione-2-truffe-online", 1, "en")
    assert "🎣" in slide1["translated"]


def test_list_decks_finds_the_quiz_deck() -> None:
    found = {d["slug"]: d for d in decks.list_decks()}
    assert "lezione-2-truffe-quiz" in found
    assert found["lezione-2-truffe-quiz"]["slide_count"] == 24


def test_quiz_deck_reveal_slides_preserve_protected_terms_and_emoji() -> None:
    # Slide 1 is the bare question; slide 2 is the same message revealed
    # with a verdict - this "duplicate the slide" trick fakes an
    # animation within Slide Sync Lite's plain index-sync model.
    bare = decks.get_slide("lezione-2-truffe-quiz", 1, "fr")
    assert "❓" in bare["it"]
    assert "verdict-badge" not in bare["it"]

    revealed = decks.get_slide("lezione-2-truffe-quiz", 2, "fr")
    assert "🚨" in revealed["translated"]
    assert "Poste Italiane" in revealed["translated"]
    assert "bit.ly/pacco-it" in revealed["translated"]
    assert '<div class="verdict-badge scam">' in revealed["translated"]

    email_slide = decks.get_slide("lezione-2-truffe-quiz", 15, "ar")
    assert "agenziaentrate-rimborso@gmail.com" in email_slide["translated"]
