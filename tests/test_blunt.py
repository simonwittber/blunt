import pytest
from blunt import lint, strip_code, sentences, wc


def rules(text):
    return {v[1] for v in lint(text)["violations"]}


def count(text, rule):
    return sum(1 for v in lint(text)["violations"] if v[1] == rule)


# ── strip_code ────────────────────────────────────────────────────────────────

def test_strip_code_block():
    result = strip_code("before\n```python\ncode here\n```\nafter")
    assert "code" not in result
    assert "before" in result
    assert "after" in result


def test_strip_inline_code():
    result = strip_code("Use `leverage` carefully.")
    assert "leverage" not in result


# ── wc ───────────────────────────────────────────────────────────────────────

def test_wc_basic():
    assert wc("one two three") == 3

def test_wc_empty():
    assert wc("") == 0

def test_wc_contractions():
    assert wc("don't") == 1


# ── sentences ─────────────────────────────────────────────────────────────────

def test_sentences_splits_on_period():
    result = sentences("First sentence. Second sentence.")
    assert len(result) == 2

def test_sentences_strips_heading():
    result = sentences("## My Heading")
    assert result[0][1] == "My Heading"

def test_sentences_strips_list_marker():
    result = sentences("- List item here.")
    assert result[0][1] == "List item here."


# ── long_sentence ─────────────────────────────────────────────────────────────

def test_long_sentence_triggers():
    long = "This is a very long sentence that has way more than twenty words in it and should therefore trigger a violation."
    assert "long_sentence" in rules(long)

def test_short_sentence_clean():
    assert "long_sentence" not in rules("This is a short sentence.")


# ── semicolon ────────────────────────────────────────────────────────────────

def test_semicolon_triggers():
    assert "semicolon" in rules("First part; second part.")

def test_no_semicolon_clean():
    assert "semicolon" not in rules("First part. Second part.")


# ── contraction ───────────────────────────────────────────────────────────────

def test_contraction_triggers():
    assert "contraction" in rules("It doesn't work.")

def test_no_contraction_clean():
    assert "contraction" not in rules("It does not work.")


# ── passive_voice ─────────────────────────────────────────────────────────────

def test_passive_voice_triggers():
    assert "passive_voice" in rules("The file is read by the parser.")

def test_active_voice_clean():
    assert "passive_voice" not in rules("The parser reads the file.")


# ── ing_main_verb ─────────────────────────────────────────────────────────────

def test_ing_main_verb_triggers():
    assert "ing_main_verb" in rules("The process is running.")

def test_simple_tense_clean():
    assert "ing_main_verb" not in rules("The process runs.")


# ── em_dash ───────────────────────────────────────────────────────────────────

def test_em_dash_triggers():
    assert "em_dash" in rules("This is good \u2014 or is it?")

def test_en_dash_triggers():
    assert "em_dash" in rules("Pages 10\u20132 cover this.")

def test_no_em_dash_clean():
    assert "em_dash" not in rules("This is good, or is it?")


# ── marketing_word ────────────────────────────────────────────────────────────

def test_marketing_word_triggers():
    assert "marketing_word" in rules("This is a seamless solution.")

def test_no_marketing_word_clean():
    assert "marketing_word" not in rules("This is a simple solution.")


# ── banned_word ───────────────────────────────────────────────────────────────

def test_banned_word_triggers():
    assert "banned_word" in rules("We utilize this approach.")

def test_banned_word_clean():
    assert "banned_word" not in rules("We use this approach.")


# ── cliche ────────────────────────────────────────────────────────────────────

def test_cliche_triggers():
    assert "cliche" in rules("This is low-hanging fruit.")

def test_no_cliche_clean():
    assert "cliche" not in rules("This is an easy task.")


# ── weak_opener ───────────────────────────────────────────────────────────────

def test_weak_opener_this():
    assert "weak_opener" in rules("This is the main point.")

def test_weak_opener_it_is():
    assert "weak_opener" in rules("It is worth noting that errors occur.")

def test_weak_opener_there_is():
    assert "weak_opener" in rules("There is a problem with the config.")

def test_no_weak_opener_clean():
    assert "weak_opener" not in rules("The config has a problem.")


# ── modal_hedge ───────────────────────────────────────────────────────────────

def test_modal_hedge_triggers():
    assert "modal_hedge" in rules("It is important to note that this works.")

def test_no_modal_hedge_clean():
    assert "modal_hedge" not in rules("This works.")


# ── intensifier ───────────────────────────────────────────────────────────────

def test_intensifier_triggers():
    assert "intensifier" in rules("This is very useful.")

def test_no_intensifier_clean():
    assert "intensifier" not in rules("This is useful.")


# ── long_paragraph ────────────────────────────────────────────────────────────

def test_long_paragraph_triggers():
    para = " ".join(f"Sentence {i}." for i in range(7))
    assert "long_paragraph" in rules(para)

def test_short_paragraph_clean():
    para = " ".join(f"Sentence {i}." for i in range(4))
    assert "long_paragraph" not in rules(para)


# ── code blocks not linted ───────────────────────────────────────────────────

def test_banned_word_in_code_block_ignored():
    text = "Normal sentence here.\n```\nutilize leverage\n```"
    assert "banned_word" not in rules(text)

def test_banned_word_in_inline_code_ignored():
    text = "Call `utilize()` to start."
    assert "banned_word" not in rules(text)


# ── total / counts ────────────────────────────────────────────────────────────

def test_clean_text_zero_violations():
    result = lint("The parser reads the file.")
    assert result["total"] == 0

def test_result_shape():
    result = lint("The parser reads the file.")
    assert "words" in result
    assert "sentences" in result
    assert "total" in result
    assert "total_per100w" in result
    assert "counts" in result
    assert "violations" in result
