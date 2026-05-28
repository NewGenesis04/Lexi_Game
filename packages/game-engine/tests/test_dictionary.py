from game_engine.dictionary import is_valid_word, load  # type: ignore
from game_engine.models import Dictionary  # type: ignore


def test_load_returns_frozenset():
    assert isinstance(load(Dictionary.TWL06), frozenset)


def test_load_caches_result():
    assert load(Dictionary.TWL06) is load(Dictionary.TWL06)


def test_csw21_larger_than_twl06():
    assert len(load(Dictionary.CSW21)) > len(load(Dictionary.TWL06))


def test_csw21_has_words_not_in_twl06():
    csw_only = load(Dictionary.CSW21) - load(Dictionary.TWL06)
    assert len(csw_only) > 0


def test_valid_word_twl06():
    assert is_valid_word("CAT", Dictionary.TWL06) is True


def test_valid_word_csw21():
    assert is_valid_word("CAT", Dictionary.CSW21) is True


def test_invalid_word_twl06():
    assert is_valid_word("ZZZZZ", Dictionary.TWL06) is False


def test_invalid_word_csw21():
    assert is_valid_word("ZZZZZ", Dictionary.CSW21) is False


def test_case_insensitive_lower():
    assert is_valid_word("cat", Dictionary.TWL06) is True


def test_case_insensitive_mixed():
    assert is_valid_word("cAt", Dictionary.CSW21) is True
