import json
import re
from itertools import permutations

COLOR_MAPPINGS = {
    "Black": {
        "convention": "K",
        "aliases": ["k", "black", "bk", "noir", "schwarz", "negro", "zwart"],
    },
    "Black - Photo": {
        "convention": "PHK",
        "aliases": ["phk", "photo black", "photo bk"],
    },
    "Black - UV": {
        "convention": "KUV",
        "aliases": ["kuv", "black uv"],
    },
    "Black - Dye": {
        "convention": "K DYE",
        "aliases": ["k dye", "black dye"],
    },
    "Black - Matte": {
        "convention": "MK",
        "aliases": ["mk", "matte black", "mat black"],
    },
    "Black - Pigment": {
        "convention": "K PIGMENT",
        "aliases": ["k pigment", "pigment black"],
    },
    "Blue": {
        "convention": "BL",
        "aliases": ["bl", "blue", "bleu", "blau", "azul", "blauw"],
    },
    "Color": {
        "convention": "COL",
        "aliases": [
            "col", "colour", "color",
            *["".join(p) for p in permutations("cmy")],
        ],
    },
    "Color - Tri": {
        "convention": "TRI-COL",
        "aliases": ["tri-col", "tri color", "tri colour", "tricolor", "tricolour"],
    },
    "Color - Full": {
        "convention": "FC-COL",
        "aliases": [
            "fc", "full color", "full colour",
            *["".join(p) for p in permutations("cmyk")],
        ],
    },
    "Cyan": {
        "convention": "C",
        "aliases": ["c", "cyan"],
    },
    "Cyan - Light": {
        "convention": "LTC",
        "aliases": ["ltc", "light cyan", "lc"],
    },
    "Cyan - Photo": {
        "convention": "PHC",
        "aliases": ["phc", "photo cyan"],
    },
    "Cyan - UV": {
        "convention": "CUV",
        "aliases": ["cuv", "cyan uv"],
    },
    "Cyan - Light - UV": {
        "convention": "LTC UV",
        "aliases": ["ltc uv", "light cyan uv"],
    },
    "Cyan - Dye": {
        "convention": "C DYE",
        "aliases": ["c dye", "cyan dye"],
    },
    "Drum": {
        "convention": "DRUM",
        "aliases": ["drum", "drumcartridge"],
    },
    "Gold": {
        "convention": "GD",
        "aliases": ["gd", "gold", "or", "oro"],
    },
    "Gray": {
        "convention": "GY",
        "aliases": ["gy", "gray", "grey", "grau", "gris"],
    },
    "Gray - Light": {
        "convention": "LTGY",
        "aliases": ["ltgy", "light gray", "light grey", "lg"],
    },
    "Gray - Photo": {
        "convention": "PHGY",
        "aliases": ["phgy", "photo gray", "photo grey"],
    },
    "Green": {
        "convention": "GN",
        "aliases": ["gn", "green", "vert", "grün", "verde", "groen"],
    },
    "Magenta": {
        "convention": "M",
        "aliases": ["m", "ma", "magenta"],
    },
    "Magenta - Light": {
        "convention": "LTMA",
        "aliases": ["ltma", "light magenta", "lm"],
    },
    "Magenta - Photo": {
        "convention": "PHMA",
        "aliases": ["phma", "photo magenta"],
    },
    "Magenta - UV": {
        "convention": "MA UV",
        "aliases": ["ma uv", "magenta uv"],
    },
    "Magenta - Light - UV": {
        "convention": "LTMA UV",
        "aliases": ["ltma uv", "light magenta uv"],
    },
    "Magenta - Dye": {
        "convention": "MA DYE",
        "aliases": ["ma dye", "magenta dye"],
    },
    "Mono": {
        "convention": "MONO",
        "aliases": ["mono"],
    },
    "Red": {
        "convention": "R",
        "aliases": ["r", "red", "rouge", "rot", "rojo", "rood"],
    },
    "Silver": {
        "convention": "SV",
        "aliases": ["sv", "silver", "argent", "silber", "plata"],
    },
    "Transparent": {
        "convention": "T",
        "aliases": ["t", "transparent", "clear", "transparant"],
    },
    "White": {
        "convention": "W",
        "aliases": ["w", "white", "blanc", "weiß", "blanco", "wit"],
    },
    "Yellow": {
        "convention": "Y",
        "aliases": ["y", "yellow", "jaune", "gelb", "amarillo", "geel"],
    },
    "Yellow - UV": {
        "convention": "Y UV",
        "aliases": ["y uv", "yellow uv"],
    },
    "Yellow - Dye": {
        "convention": "Y DYE",
        "aliases": ["y dye", "yellow dye"],
    },
}

# Build flat lookup: lowercased alias/key/convention → convention
_LOOKUP: dict[str, str] = {}
for full_name, entry in COLOR_MAPPINGS.items():
    _LOOKUP[full_name.lower()] = entry["convention"]
    _LOOKUP[entry["convention"].lower()] = entry["convention"]
    for alias in entry["aliases"]:
        _LOOKUP[alias.lower()] = entry["convention"]


def normalize_color(raw: str) -> tuple[str, bool]:
    if not raw:
        return raw, False

    key = re.sub(r"\s+", " ", raw.strip().lower())

    if key in _LOOKUP:
        normalized = _LOOKUP[key]
        return normalized, normalized != raw

    print(f"  WARNING: could not map color '{raw}'")
    return raw, False


def fix_colors(records: list[dict]) -> tuple[list[dict], int]:
    changed = 0
    for record in records:
        raw = record.get("color", "")
        normalized, was_changed = normalize_color(raw)
        if was_changed:
            print(f"  [{record.get('part_number', '?')}] color: '{raw}' → '{normalized}'")
            record["color"] = normalized
            changed += 1
    return records, changed


if __name__ == "__main__":
    import sys

    input_file  = sys.argv[1] if len(sys.argv) > 1 else "consumables.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    single = isinstance(data, dict)
    records = [data] if single else data

    print(f"Processing {len(records)} record(s) from '{input_file}'...")
    records, changed = fix_colors(records)
    print(f"Done — {changed} record(s) updated.")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records[0] if single else records, f, indent=2, ensure_ascii=False)

    print(f"Written to '{output_file}'.")