import re, sys, glob, os, argparse, json, shutil

_HERE = os.path.dirname(os.path.abspath(__file__))
_LISTS_DIR = os.path.join(_HERE, "lists")


def _load_list(name):
    path = os.path.join(_LISTS_DIR, name)
    if not os.path.exists(path):
        print(f"blunt: warning: missing list file: {path}", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def _compile(phrases):
    if not phrases:
        return None
    phrases = sorted(set(phrases), key=len, reverse=True)
    pat = "|".join(re.escape(p) for p in phrases)
    return re.compile(r"(?<![a-z])(" + pat + r")(?![a-z])", re.I)


def _compile_anchored(phrases):
    if not phrases:
        return None
    phrases = sorted(set(phrases), key=len, reverse=True)
    pat = "|".join(re.escape(p) for p in phrases)
    return re.compile(r"^(" + pat + r")", re.I)


def _load_banned_re():
    path = os.path.join(_LISTS_DIR, "banned.txt")
    if not os.path.exists(path):
        print("blunt: warning: missing lists/banned.txt", file=sys.stderr)
        return None
    terms = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if not w or w.startswith("---"):
                continue
            m = re.match(r"^[a-z][\w\- ]*\(([^)]+)\)$", w)
            terms.append(m.group(1).strip() if m else w)
    return _compile(terms)


# Compiled list patterns — loaded once at import.
MARKETING_RE    = _compile(_load_list("marketing.txt"))
PHRASAL_RE      = _compile(_load_list("phrasal.txt"))
MODAL_HEDGE_RE  = _compile(_load_list("modal_hedge.txt"))
WEASEL_RE       = _compile(_load_list("weasel.txt"))
FILLER_RE       = _compile_anchored(_load_list("filler_opener.txt"))
REDUNDANT_RE    = _compile(_load_list("redundant.txt"))
CLICHE_RE       = _compile(_load_list("cliche.txt"))
HEDGE_VERB_RE   = _compile(_load_list("hedge_verb.txt"))
BUREAUCRATIC_RE = _compile(_load_list("bureaucratic.txt"))
INTENSIFIER_RE  = _compile(_load_list("intensifiers.txt"))
ADVERB_EXCLUDE  = set(_load_list("adverb_exclude.txt"))
BANNED_RE       = _load_banned_re()

# Precompiled structural patterns.
_BE       = r"(?:am|is|are|was|were|be|been|being)"
_PP_IRREG = r"(?:done|made|sent|read|built|kept|held|set|put|run|written|shown|given|taken|found|got|gotten|seen|known|thrown|drawn)"
PASSIVE_RE     = re.compile(rf"\b{_BE}\s+(?:being\s+)?(?:\w+ed|{_PP_IRREG})\b", re.I)
ING_RE         = re.compile(rf"\b{_BE}\s+\w+ing\b", re.I)
NOM_RE         = re.compile(
    r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|provide(?:s|d)?|carry out|carries out"
    r"|make use of|makes use of)\b|\b\w{{4,}}(?:tion|ment|ance|ence)\s+of\b", re.I
)
CONTRACTION_RE = re.compile(r"\b\w+[''](t|re|ve|ll|d|s|m)\b")
ADVERB_RE      = re.compile(r"\b(\w+ly)\b", re.I)
EM_DASH_RE     = re.compile(r"[\u2014\u2013]")

WEAK_OPENERS = ("this ", "it is ", "there is ", "there are ")


def strip_code(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t


def sentences(text):
    out = []
    for lineno, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if not s:
            continue
        s = re.sub(r"^\s*#{1,6}\s*", "", s)
        s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", s)
        if not s:
            continue
        for p in re.split(r"(?<=[.!?:])\s+(?=[A-Z0-9\"'\-])", s):
            p = p.strip()
            if p:
                out.append((lineno, p))
    return out


def wc(s):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", s))


def trunc(s, n=80):
    return s[:n] + "..." if len(s) > n else s


def _hits(pat, text):
    if not pat:
        return []
    return [m.group(1) for m in pat.finditer(text)]


def _check_sentence(lineno, s, v):
    sl = s.lower()

    if wc(s) > 20:
        v("long_sentence", lineno, trunc(s))
    if ";" in s:
        v("semicolon", lineno, trunc(s))
    for m in CONTRACTION_RE.finditer(s):
        v("contraction", lineno, f'"{m.group()}"')

    if PASSIVE_RE.search(s):
        v("passive_voice", lineno, trunc(s))
    if ING_RE.search(s):
        v("ing_main_verb", lineno, trunc(s))
    if NOM_RE.search(s):
        v("nominalization", lineno, trunc(s))

    for ph in _hits(PHRASAL_RE, sl):
        v("phrasal_verb", lineno, f'"{ph}"')
    for ph in _hits(MARKETING_RE, sl):
        v("marketing_word", lineno, f'"{ph}"')
    for ph in _hits(MODAL_HEDGE_RE, sl):
        v("modal_hedge", lineno, f'"{ph}"')
    for ph in _hits(WEASEL_RE, sl):
        v("weasel_word", lineno, f'"{ph}"')
    for ph in _hits(REDUNDANT_RE, sl):
        v("redundant_phrase", lineno, f'"{ph}"')
    for ph in _hits(CLICHE_RE, sl):
        v("cliche", lineno, f'"{ph}"')
    for ph in _hits(HEDGE_VERB_RE, sl):
        v("hedge_verb", lineno, f'"{ph}"')
    for ph in _hits(BUREAUCRATIC_RE, sl):
        v("bureaucratic", lineno, f'"{ph}"')
    for ph in _hits(INTENSIFIER_RE, sl):
        v("intensifier", lineno, f'"{ph}"')

    if FILLER_RE:
        fm = FILLER_RE.match(sl)
        if fm:
            v("filler_opener", lineno, f'"{fm.group(1)}"')

    for opener in WEAK_OPENERS:
        if sl.startswith(opener):
            v("weak_opener", lineno, trunc(s))
            break

    for m in ADVERB_RE.finditer(s):
        if m.group(1).lower() not in ADVERB_EXCLUDE:
            v("adverb", lineno, f'"{m.group(1)}"')

    if BANNED_RE:
        for m in BANNED_RE.finditer(s):
            v("banned_word", lineno, f'"{m.group(1)}"')


def lint(text):
    raw = text
    text = strip_code(text)
    sents = sentences(text)
    words = sum(wc(s) for _, s in sents) or 1
    violations = []

    def v(rule, lineno, display):
        violations.append((lineno, rule, display))

    for lineno, s in sents:
        _check_sentence(lineno, s, v)

    for lineno, line in enumerate(raw.split("\n"), 1):
        count = len(EM_DASH_RE.findall(line))
        for _ in range(count):
            v("em_dash", lineno, trunc(line.strip()))

    for para in re.split(r"\n\s*\n", raw):
        if not para.strip():
            continue
        ps = sentences(strip_code(para))
        if len(ps) > 6:
            v("long_paragraph", ps[0][0], trunc(ps[0][1]) + " ...")

    counts = {}
    for _, rule, _ in violations:
        counts[rule] = counts.get(rule, 0) + 1

    return {
        "words": words,
        "sentences": len(sents),
        "total": len(violations),
        "total_per100w": round(len(violations) * 100.0 / words, 2),
        "counts": counts,
        "violations": violations,
    }


def _to_json_result(result):
    return {
        "words": result["words"],
        "sentences": result["sentences"],
        "total": result["total"],
        "per_100_words": result["total_per100w"],
        "counts": result["counts"],
        "violations": [
            {"line": ln, "rule": rule, "text": display}
            for ln, rule, display in result["violations"]
        ],
    }


def print_json(label_results):
    if len(label_results) == 1:
        label, result = next(iter(label_results.items()))
        print(json.dumps(_to_json_result(result), indent=2))
    else:
        print(json.dumps({k: _to_json_result(v) for k, v in label_results.items()}, indent=2))


def print_human(label, result):
    for lineno, rule, display in result["violations"]:
        loc = f"{label}:{lineno}" if label else str(lineno)
        print(f"  {loc:<28} {rule:<22} {display}")
    r = result
    name = label or "(stdin)"
    print(f"\n  {name}  words={r['words']} sentences={r['sentences']} total={r['total']} per100w={r['total_per100w']}\n")


def _write_config(config_path, url, key):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as fh:
        fh.write(f'[litellm]\nbase_url = "{url}"\napi_key = "{key}"\n')
    print(f"blunt: config written to {config_path}")


def install(url=None):
    src = os.path.join(_HERE, "skills")
    dst = os.path.join(os.path.expanduser("~"), ".claude", "skills")
    if not os.path.isdir(src):
        print("blunt: skills/ directory not found", file=sys.stderr)
        sys.exit(1)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
            print(f"blunt: installed skill {item!r} to {d}")
        else:
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(s, d)
            print(f"blunt: installed {item!r} to {d}")

    config_path = os.path.join(os.path.expanduser("~"), ".blunt", "config.toml")
    print()
    if not url:
        url = input("LiteLLM base URL: ").strip()
    key = input("LiteLLM API key: ").strip()
    if url and key:
        _write_config(config_path, url, key)
    else:
        print("blunt: no URL or API key provided, skipping config")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        ap = argparse.ArgumentParser(prog="blunt install")
        ap.add_argument("--url", help="LiteLLM base URL")
        args = ap.parse_args(sys.argv[2:])
        install(url=args.url)
        return

    ap = argparse.ArgumentParser(description="Prose linter for technical English")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--human", action="store_true", help="Human-readable output")
    args = ap.parse_args()

    if not args.files:
        result = lint(sys.stdin.read())
        if args.human:
            print_human("", result)
        else:
            print_json({"": result})
        return

    expanded = []
    for f in args.files:
        expanded += sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]

    if args.human:
        for f in expanded:
            with open(f) as fh:
                print_human(f, lint(fh.read()))
    else:
        results = {}
        for f in expanded:
            with open(f) as fh:
                results[f] = lint(fh.read())
        print_json(results)


if __name__ == "__main__":
    main()
