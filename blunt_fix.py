import sys, os, re, argparse
import litellm
from blunt import lint

try:
    import tomllib
except ImportError:
    import tomli as tomllib

MODEL = "claude-haiku-4-5"
_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".blunt", "config.toml")

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_PATH = os.path.join(_HERE, "skills", "writing", "SKILL.md")

_FALLBACK_SYSTEM = """\
You are a technical editor. Fix only the flagged prose violations. Change nothing else.
Preserve all markdown formatting, code blocks, headings, lists, and structure exactly.
Output only the corrected text, with no explanation, preamble, or commentary.
Do not change text that is a literal example of a violation — words appearing after \
"like", "including", "e.g.", or inside parentheses or quotation marks in a list item. \
Preserve those words exactly.\
"""


def _load_config():
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, "rb") as fh:
        return tomllib.load(fh).get("litellm", {})


def _load_skill():
    if not os.path.exists(_SKILL_PATH):
        return _FALLBACK_SYSTEM
    with open(_SKILL_PATH, encoding="utf-8") as fh:
        text = fh.read()
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"^.*blunt.*\n?", "", text, flags=re.M)
    return text.strip()


SYSTEM = _load_skill()


def _format_violations(result):
    return "\n".join(
        f"  line {ln}: [{rule}] {text}"
        for ln, rule, text in result["violations"]
    )


def fix(text):
    result = lint(text)
    if result["total"] == 0:
        return text

    cfg = _load_config()
    api_key = os.environ.get("LITELLM_API_KEY") or cfg.get("api_key")
    if not api_key:
        print(f"blunt-fix: no API key found. Set LITELLM_API_KEY or run 'blunt install' to configure {_CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get("LITELLM_BASE_URL") or cfg.get("base_url")
    if not base_url:
        print(f"blunt-fix: no base URL found. Set LITELLM_BASE_URL or run 'blunt install --url <url>'", file=sys.stderr)
        sys.exit(1)

    user_message = (
        f"Violations to fix:\n{_format_violations(result)}\n\n"
        f"Original text:\n{text}"
    )

    response = litellm.completion(
        model=MODEL,
        api_base=base_url,
        api_key=api_key,
        max_tokens=64000,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content


def main():
    ap = argparse.ArgumentParser(description="Fix prose violations detected by blunt")
    ap.add_argument("file", nargs="?", help="File to fix (default: stdin)")
    ap.add_argument("--in-place", "-i", action="store_true", help="Overwrite the input file")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    fixed = fix(text)

    if args.in_place and args.file:
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write(fixed)
    else:
        sys.stdout.buffer.write(fixed.encode("utf-8"))


if __name__ == "__main__":
    main()
