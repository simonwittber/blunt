import os
import pytest
import tempfile
import textwrap


# ── _load_config ──────────────────────────────────────────────────────────────

def test_load_config_missing(monkeypatch, tmp_path):
    import blunt_fix
    monkeypatch.setattr(blunt_fix, "_CONFIG_PATH", str(tmp_path / "config.toml"))
    assert blunt_fix._load_config() == {}


def test_load_config_reads_litellm_section(monkeypatch, tmp_path):
    import blunt_fix
    cfg = tmp_path / "config.toml"
    cfg.write_text('[litellm]\napi_key = "test-key"\nbase_url = "http://example.com"\n')
    monkeypatch.setattr(blunt_fix, "_CONFIG_PATH", str(cfg))
    result = blunt_fix._load_config()
    assert result["api_key"] == "test-key"
    assert result["base_url"] == "http://example.com"


def test_load_config_missing_litellm_section(monkeypatch, tmp_path):
    import blunt_fix
    cfg = tmp_path / "config.toml"
    cfg.write_text('[other]\nkey = "value"\n')
    monkeypatch.setattr(blunt_fix, "_CONFIG_PATH", str(cfg))
    assert blunt_fix._load_config() == {}


# ── _load_skill ───────────────────────────────────────────────────────────────

def test_load_skill_returns_fallback_when_missing(monkeypatch):
    import blunt_fix
    monkeypatch.setattr(blunt_fix, "_SKILL_PATH", "/nonexistent/path/SKILL.md")
    result = blunt_fix._load_skill()
    assert result == blunt_fix._FALLBACK_SYSTEM


def test_load_skill_strips_frontmatter(tmp_path, monkeypatch):
    import blunt_fix
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: test\n---\n\nActual content here.\n")
    monkeypatch.setattr(blunt_fix, "_SKILL_PATH", str(skill))
    result = blunt_fix._load_skill()
    assert "---" not in result
    assert "Actual content here." in result


def test_load_skill_removes_blunt_pipe_line(tmp_path, monkeypatch):
    import blunt_fix
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: test\n---\n\nGood line.\nRun: echo ... | blunt\nAnother good line.\n")
    monkeypatch.setattr(blunt_fix, "_SKILL_PATH", str(skill))
    result = blunt_fix._load_skill()
    assert "blunt" not in result
    assert "Good line." in result
    assert "Another good line." in result


# ── _format_violations ────────────────────────────────────────────────────────

def test_format_violations_output():
    import blunt_fix
    result = {"violations": [(3, "banned_word", '"utilize"'), (5, "contraction", '"don\'t"')]}
    output = blunt_fix._format_violations(result)
    assert "line 3" in output
    assert "banned_word" in output
    assert "line 5" in output
    assert "contraction" in output


def test_format_violations_empty():
    import blunt_fix
    assert blunt_fix._format_violations({"violations": []}) == ""


# ── fix — no API call when clean ──────────────────────────────────────────────

def test_fix_returns_original_when_no_violations():
    import blunt_fix
    text = "The parser reads the file."
    result = blunt_fix.fix(text)
    assert result == text


def test_fix_no_api_key_needed_for_clean_text(monkeypatch):
    import blunt_fix
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.setattr(blunt_fix, "_load_config", lambda: {})
    text = "The parser reads the file."
    result = blunt_fix.fix(text)
    assert result == text
