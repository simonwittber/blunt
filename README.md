# blunt

A prose linter for technical English. blunt checks documentation for vague words, marketing language, AI slop, and weak sentence structure.

## Install

```bash
pip install -e .
blunt install
```

`blunt install` copies the writing skill to `~/.claude/skills/` and prompts for your LiteLLM API key.

## Usage

### blunt

```bash
blunt README.md          # JSON output (default)
blunt --human README.md  # human-readable output
cat README.md | blunt    # read from stdin
```

### blunt-fix

blunt-fix reads your prose, finds violations, and rewrites the text using the Claude API.

```bash
blunt-fix README.md             # output to stdout
blunt-fix -i README.md          # fix in place
cat README.md | blunt-fix       # read from stdin
```

Set `LITELLM_API_KEY` in your environment or run `blunt install` to save it to `~/.blunt/config.toml`.

## Before and After

**Before:**

> **blunt** is a powerful, robust prose linter that leverages a comprehensive set of
> curated word lists to seamlessly identify and flag writing patterns that make technical
> documentation harder to read and maintain. It's important to note that blunt doesn't
> just identify issues — it can actually fix them for you: the companion `blunt-fix` tool
> utilizes the Claude API to automatically remediate violations, facilitating the
> production of clean, actionable prose from your existing content. Prior to use, ensure
> you have Python 3.8 or higher, then simply run `pip install -e .` to get started.

**After:**

> **blunt** is a prose linter that identifies and flags writing patterns that make technical documentation harder to read and maintain. It checks your text against a comprehensive set of curated word lists. blunt does more than identify issues: the companion `blunt-fix` tool uses the Claude API to fix violations automatically, so you can produce clean prose from your existing content. You need Python 3.8 or higher. Run `pip install -e .` to get started.

## Word Lists

blunt checks against these lists in `lists/`:

- `banned.txt` — words that add length without meaning ("leverage", "utilize", "delve")
- `marketing.txt` — adjectives with no place in technical docs ("seamless", "robust", "cloud-native")
- `cliche.txt` — overused phrases from software engineering ("dogfooding", "shift left", "bikeshedding")
- `phrasal.txt` — informal phrasal verbs to replace with plain verbs
- `weasel.txt` — vague quantifiers and hedging language

## Writing Skill

`blunt install` copies `skills/writing/SKILL.md` to `~/.claude/skills/`. Claude Code uses this skill when you create or update documentation. `blunt-fix` also loads the skill at runtime, so both tools apply the same rules.
