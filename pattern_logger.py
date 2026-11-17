#!/usr/bin/env python3
"""
Part-number pattern detector — quiet mode, aligned output,
known+unknown composites, with per-shape expansion trace.

Usage:
    python pattern_logger.py xerox_data.json
"""

import json
import re
import sys
import unicodedata
from collections import OrderedDict


# ---------------------------------------------------------------------------
# Atomic patterns (X = digit, A = letter A-Z)
# ---------------------------------------------------------------------------
PATTERNS = [
    ("Xerox R-code (5)",   re.compile(r"^\d{3}R\d{5}$"),        "XXXRXXXXX", "006R01237"),
    ("Xerox R-code (3)",   re.compile(r"^\d{3}R\d{3}$"),        "XXXRXXX",   "113R315"),
    ("9-digit numeric",    re.compile(r"^\d{9}$"),              "XXXXXXXXX", "016188300"),
    ("CT + 6 digits",      re.compile(r"^CT\d{6}$"),            "AAXXXXXX",  "CT350574"),
    ("CT + 5 digits",      re.compile(r"^CT\d{5}$"),            "AAXXXXX",   "CT50413"),
    ("CTI + 5 digits",     re.compile(r"^CTI\d{5}$"),           "AAIXXXXX",  "CTI50285"),
    ("Dell XXX-XXXX",      re.compile(r"^\d{3}-\d{4}$"),        "XXX-XXXX",  "330-3111"),
    ("Fujitsu AAXXXA",     re.compile(r"^[A-Z]{2}\d{3}[A-Z]$"), "AAXXXA",    "LB322B"),
]

FALLBACK = ("UNKNOWN", "?", "")


# ---------------------------------------------------------------------------
# Width-aware display helpers
# ---------------------------------------------------------------------------
def dwidth(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def pad(s: str, width: int, align: str = "left") -> str:
    gap = max(0, width - dwidth(s))
    return (" " * gap + s) if align == "right" else (s + " " * gap)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
_TRANS = {
    "\uFF08": "(", "\uFF09": ")", "\uFF0C": ",",
    "\u3000": " ", "\u00A0": " ", "\uFF0F": "/",
}

def normalise(s: str) -> str:
    s = s.translate(_TRANS)
    s = unicodedata.normalize("NFKC", s)
    return s.strip()


# ---------------------------------------------------------------------------
# Shape helpers
# ---------------------------------------------------------------------------
def shape(s: str) -> str:
    return re.sub(r"[0-9]", "X", re.sub(r"[A-Za-z]", "A", s))


def composite_shape(s: str) -> str:
    return re.sub(r"[0-9]", "X", re.sub(r"[A-Za-z]", "A", s))


# ---------------------------------------------------------------------------
# Explode composites
# ---------------------------------------------------------------------------
_SEP = re.compile(r"[/(),;|\s]+")

def explode(pn: str):
    pn = normalise(pn)
    tokens = [t for t in _SEP.split(pn) if t]
    result, prev_full = [], None
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if prev_full is None or re.search(r"[A-Za-z]", tok):
            result.append(tok)
            prev_full = tok
        else:
            n = len(tok)
            full = (prev_full[:-n] + tok) if (prev_full and len(prev_full) > n) else tok
            result.append(full)
            prev_full = full
    return result


def classify(pn: str):
    for name, rx, pat, example in PATTERNS:
        if rx.match(pn):
            return name, pat, example
    return FALLBACK


def bar(ch="=", w=100):
    return ch * w


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(path: str) -> None:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        sys.exit("Error: JSON root must be a list of objects.")

    counts = {name: 0 for name, *_ in PATTERNS}
    counts["UNKNOWN"] = 0

    known_example: dict[str, str] = {}

    # shape -> (source example, [atoms])
    known_composites:   "OrderedDict[str, tuple]" = OrderedDict()
    unknown_composites: "OrderedDict[str, tuple]" = OrderedDict()
    unknown_atomic:     "OrderedDict[str, str]"   = OrderedDict()

    total_records = total_atomic = total_composites = 0
    total_known_composites = total_unknown_composites = 0

    for obj in data:
        if not isinstance(obj, dict):
            continue
        pn = obj.get("part_number")
        if not pn:
            continue
        total_records += 1
        original = normalise(str(pn))
        atoms = explode(original)

        if len(atoms) > 1:
            total_composites += 1
            any_unknown = False
            for a in atoms:
                total_atomic += 1
                name, _, _ = classify(a)
                counts[name] += 1
                if name == "UNKNOWN":
                    any_unknown = True
                    unknown_atomic.setdefault(shape(a), a)
                else:
                    known_example.setdefault(name, a)
            csh = composite_shape(original)
            if any_unknown:
                total_unknown_composites += 1
                unknown_composites.setdefault(csh, (original, atoms))
            else:
                total_known_composites += 1
                known_composites.setdefault(csh, (original, atoms))
        else:
            total_atomic += 1
            a = atoms[0]
            name, _, _ = classify(a)
            counts[name] += 1
            if name == "UNKNOWN":
                unknown_atomic.setdefault(shape(a), a)
            else:
                known_example.setdefault(name, a)

    # -----------------------------------------------------------------------
    # Summary rows + widths
    # -----------------------------------------------------------------------
    rows = []
    for name, _rx, pat, default_ex in PATTERNS:
        if counts[name] == 0:
            continue
        rows.append((name, pat, counts[name], known_example.get(name, default_ex)))
    if counts["UNKNOWN"]:
        rows.append(("UNKNOWN (atomic)", "?", counts["UNKNOWN"],
                     next(iter(unknown_atomic.values()), "")))

    w_name = max(dwidth("PATTERN NAME"), *(dwidth(r[0]) for r in rows)) + 2
    w_pat  = max(dwidth("PATTERN"),      *(dwidth(r[1]) for r in rows)) + 2
    w_cnt  = max(dwidth("COUNT"),        *(dwidth(str(r[2])) for r in rows)) + 2
    w_ex   = max(dwidth("EXAMPLE"),      *(dwidth(r[3]) for r in rows)) + 2
    total_w = w_name + w_pat + w_cnt + w_ex + 8

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print()
    print(bar("=", total_w))
    print("  PART-NUMBER PATTERN SUMMARY")
    print(bar("=", total_w))
    print(f"  File              : {path}")
    print(f"  JSON records      : {total_records}")
    print(f"  Atomic part nums  : {total_atomic}")
    print(f"  Composite entries : {total_composites}"
          f"  (known {total_known_composites}, unknown {total_unknown_composites})")
    print(bar("=", total_w))
    print()

    print("  " + pad("PATTERN NAME", w_name) + pad("PATTERN", w_pat)
          + pad("COUNT", w_cnt, "right") + "  " + pad("EXAMPLE", w_ex))
    print("  " + "-" * (total_w - 2))
    for name, pat, cnt, ex in rows:
        print("  " + pad(name, w_name) + pad(pat, w_pat)
              + pad(str(cnt), w_cnt, "right") + "  " + pad(ex, w_ex))
    print("  " + "-" * (total_w - 2))
    print()

    # -----------------------------------------------------------------------
    # Composite block printer — now with expansion trace
    # -----------------------------------------------------------------------
    def print_composites(title: str, mapping: "OrderedDict[str, tuple]"):
        if not mapping:
            return
        # Prepare expanded lines
        prepared = []
        for sh, (src, atoms) in mapping.items():
            expansion = ", ".join(atoms)
            prepared.append((sh, src, expansion))

        w_sh  = max(dwidth("SHAPE"),  *(dwidth(p[0]) for p in prepared)) + 2
        w_src = max(dwidth("SOURCE"), *(dwidth(p[1]) for p in prepared)) + 2
        w_exp = max(dwidth("EXPANSION"), *(dwidth(p[2]) for p in prepared)) + 2
        tw = w_sh + w_src + w_exp + 10

        print(bar("-", tw))
        print(f"  {title}")
        print(bar("-", tw))
        print(
            "  " + pad("SHAPE", w_sh)
            + pad("SOURCE", w_src)
            + "  " + pad("EXPANSION", w_exp)
        )
        print("  " + "-" * (tw - 2))
        for sh, src, exp in prepared:
            print(
                "  " + pad(sh, w_sh)
                + pad(src, w_src)
                + "  " + pad(exp, w_exp)
            )
        print()

    print_composites(
        "KNOWN COMPOSITES  (one example per distinct shape — all atoms resolve)",
        known_composites,
    )
    print_composites(
        "UNKNOWN COMPOSITES  (one example per distinct shape — >=1 unknown atom)",
        unknown_composites,
    )

    # -----------------------------------------------------------------------
    # Unknown atomic shapes (unchanged)
    # -----------------------------------------------------------------------
    if unknown_atomic:
        w1 = max(dwidth("SHAPE"), *(dwidth(k) for k in unknown_atomic)) + 2
        w2 = max(dwidth("EXAMPLE"), *(dwidth(v) for v in unknown_atomic.values())) + 2
        tw = w1 + w2 + 6
        print(bar("-", tw))
        print("  UNKNOWN ATOMIC SHAPES  (one example per distinct shape)")
        print(bar("-", tw))
        print("  " + pad("SHAPE", w1) + "  " + pad("EXAMPLE", w2))
        print("  " + "-" * (tw - 2))
        for k, v in unknown_atomic.items():
            print("  " + pad(k, w1) + "  " + pad(v, w2))
        print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pattern_logger.py <file.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])