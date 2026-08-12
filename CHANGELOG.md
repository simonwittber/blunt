# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-12

### Added

- `blunt` — prose linter that checks text against word lists for banned words, marketing language, clichés, weak sentence structure, and more.
- `blunt-fix` — companion tool that reads violations from `blunt` and rewrites the text using the Claude API via LiteLLM.
- `blunt install` — copies the writing skill to `~/.claude/skills/` and writes `~/.blunt/config.toml` with the LiteLLM base URL and API key.
- `--human` flag on `blunt` for human-readable output (default is JSON).
- `--in-place` / `-i` flag on `blunt-fix` to overwrite the input file.
- `skills/writing/SKILL.md` — plain-English writing rules for use with Claude Code.
- Word lists: `banned.txt`, `marketing.txt`, `cliche.txt`, `phrasal.txt`, `weasel.txt`, `modal_hedge.txt`, `redundant.txt`, `filler_opener.txt`, `hedge_verb.txt`, `bureaucratic.txt`, `intensifiers.txt`, `adverb_exclude.txt`.
- Unit tests covering all lint rules and fix utilities.
- GitHub Actions release workflow triggered on `v*` tags.
