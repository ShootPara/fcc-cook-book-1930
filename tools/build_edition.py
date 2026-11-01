#!/usr/bin/env python3
"""Build the public Mayflower cookbook edition from the immutable V8 source."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "mayflower-recipes-v8-edited.json"
OUTPUT = ROOT / "dist" / "data"
DEFAULT_REGISTRY = Path(r"D:\Projects\Online\recipes\generated\backups\live-20261027-r5-descriptions.sqlite")
EXTENSIONS = ROOT / "config" / "mayflower-ingredient-extensions.json"

# Historical cookbook terms whose meanings are unambiguous in this culinary context.
# Values are normalized R5 registry aliases; additions remain visible in the report.
HISTORICAL_ALIASES = {
    "soda": "baking-soda",
    "gelatine": "gelatina",
    "knox-gelatine": "gelatina",
    "knox-gelatin": "gelatina",
    "alspice": "allspice",
    "cream-tartar": "cream-of-tartar",
    "whites": "egg-whites",
    "yolks": "egg-yolks",
    "toast": "bread",
    "swift-s-premium-ham": "ham",
    "swifts-premium-ham": "ham",
}

BRANDED_REFERENCE = re.compile(r"\b(?:argo|kingsford|india relish|liquid life|white rock|swift'?s|savor-tite|show you|chop suey)\b", re.IGNORECASE)
GENERIC_INGREDIENT = re.compile(r"\b(?:fat|flavoring|seasonings?|pastry|fruit|meat|vegetables?|crumbs|berries|fish|juice|stock|dressing|sauce|icing|coloring|brine|batter|dough|gravy|pickle|beans|steak)\b", re.IGNORECASE)
TEXTUAL_FRAGMENT = re.compile(r"^(?:\([^)]*\)|but\b|but not strained|chopped\.?|finely\.?|ground\.?|melted\.?|thin on board\.?|skewers\.?|bud\.?|cheese is mushy\)?|\d.*\b(?:cooked shredded|finely minced,? uncooked)\b|butter (?:a|casserole|two)\b.*)$", re.IGNORECASE)
PREPARED_COMPONENT = re.compile(r"\b(?:pan drippings|reserved beet-cooking liquid)\b", re.IGNORECASE)


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def slug(value: str) -> str:
    return normalized(value) or "recipe"


def ingredient_candidates(line: str) -> list[str]:
    """Produce conservative identity candidates without altering display text."""
    value = line.lower()
    has_measured_lead = bool(re.match(r"^\s*(?:\d+(?:[–-]\d+)?(?:[./]\d+|[½¼¾⅓⅔⅛⅜⅝⅞�])?|[½¼¾⅓⅔⅛⅜⅝⅞]+|(?:one|two|three)\b)", value))
    value = re.sub(r"\bcups?(?=flour\b)", lambda match: f"{match.group()} ", value)
    value = re.sub(r"^\s*(?:\d+(?:[–-]\d+)?(?:[./]\d+|[½¼¾⅓⅔⅛⅜⅝⅞�])?|[½¼¾⅓⅔⅛⅜⅝⅞]+|one|two|three)\s*", "", value)
    value = re.sub(r"\b(?:cups?|c\.?|tablespoons?|tbsp\.?|teaspoons?|tsp\.?|pounds?|lbs?\.?|ounces?|oz\.?|quarts?|qts?\.?|pints?|pt\.?|gallons?|cans?|packages?|pkg\.?|slices?|jars?|bottles?|box(?:es)?|dozens?|ears?|stalks?|loaves?|tins?|squares?|sq\.?|heads?|sprigs?)\b", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"^enough\s+", "", value)
    value = re.sub(r"\bcut up\b", "", value)
    value = re.sub(r"^rind\s+\d+\s+(?:large\s+)?water\s+melon$", "water melon rind", value)
    identity_value = value
    value = re.sub(r"\b(?:scalded|melted|softened|beaten|sifted|chopped|diced|minced|ground|grated|cooked|cold|hot|fresh|small|large|medium|optional|optionally|if desired|to taste|for garnish|stiff|separated|well|heaping|level|scant|thin|thinly|light|rounding|fine|finely|cut|cubed|whipped|creamed|sliced|added|dissolved|crumbled|drained|blanched|shelled|tinted|sweetened|canned|ripe|prepared|unbeaten|whole|times|crushed|shredded|peeled|quartered|halved|skinned|seeded|buttered|rolled|stuffed|freshly|carefully|uncooked|hard-boiled|boiled|flaked|pieces|rings|sections|segments|strips|split|tips|rounds|lengthwise|membranes|removed|dressed|jointed|rather|tart|coarsely|very|about)\b", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ,;.-")
    value = re.sub(r",?\s*\d+(?:[½¼¾⅓⅔⅛⅜⅝⅞])?(?:[–-]\d+(?:[½¼¾⅓⅔⅛⅜⅝⅞])?)?\s*(?:lbs?|pounds?)\.?\s*$", "", value)
    value = re.sub(r",?\s*(?:\d+(?:[½¼¾⅓⅔⅛⅜⅝⅞])?|[½¼¾⅓⅔⅛⅜⅝⅞]+)(?:[–-](?:\d+(?:[½¼¾⅓⅔⅛⅜⅝⅞])?|[½¼¾⅓⅔⅛⅜⅝⅞]+))?\s*$", "", value)
    value = re.sub(r"[,;]\s*\d+\s*$", "", value)
    value = re.split(r"\b(?:enough|for|as needed|to make|to mix|to cover|to bind|to serve|to season|to moisten|to coat|to garnish|to finish|to loosen|to roll|to right|equal in volume to|into|if available|may be added|may be|all about|all the same|per)\b", value, maxsplit=1)[0].strip(" ,;.-")
    value = re.sub(r",?\s*(?:\d+(?:[½¼¾⅓⅔⅛⅜⅝⅞])?|[½¼¾⅓⅔⅛⅜⅝⅞]+)(?:[–-](?:\d+(?:[½¼¾⅓⅔⅛⅜⅝⅞])?|[½¼¾⅓⅔⅛⅜⅝⅞]+))?\s*$", "", value)
    value = re.sub(r"\bgarnish\s*$", "", value).strip(" ,;.-")
    value = re.sub(r"\b(?:and|or)\s*$", "", value).strip(" ,;.-")
    value = re.sub(r"^(butter),?\s+and\s+in$", r"\1", value)
    candidates = [normalized(identity_value), normalized(value)]
    if " of " in value:
        candidates.append(normalized(value.rsplit(" of ", 1)[-1]))
    if " or " in value:
        candidates.extend(normalized(part) for part in value.split(" or "))
    for candidate_value in (identity_value, value):
        words = normalized(candidate_value).split("-")
        for width in (3, 2, 1):
            if len(words) >= width:
                if has_measured_lead:
                    candidates.append(normalized(" ".join(words[:width])))
                candidates.append(normalized(" ".join(words[-width:])))
    return [candidate for candidate in dict.fromkeys(candidates) if candidate]


def load_registry(path: Path) -> tuple[dict[str, dict], dict[int, int]]:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    entries: dict[str, dict] = {}
    redirects = {row["duplicate_id"]: row["canonical_id"] for row in connection.execute(
        "SELECT duplicate_id, canonical_id FROM ingredient_canonical_redirects"
    )}
    for row in connection.execute(
        "SELECT ingredient_id, canonical_name, canonical_name_normalized, display_name_en, display_name_pt FROM ingredients_canonical WHERE is_active = 1"
    ):
        entries[normalized(row["canonical_name_normalized"])] = dict(row, match_kind="canonical")
    for row in connection.execute(
        "SELECT a.alias_normalized, a.ingredient_id, c.canonical_name, c.canonical_name_normalized, c.display_name_en, c.display_name_pt FROM ingredient_aliases a JOIN ingredients_canonical c ON c.ingredient_id = a.ingredient_id"
    ):
        entries[normalized(row["alias_normalized"])] = dict(row, match_kind="alias")
    extensions = json.loads(EXTENSIONS.read_text(encoding="utf-8"))["ingredients"]
    for extension in extensions:
        entry = {
            "ingredient_id": extension["ingredient_id"],
            "canonical_name": extension["canonical_name"],
            "canonical_name_normalized": normalized(extension["canonical_name"]),
            "display_name_en": extension["display_name_en"],
            "display_name_pt": extension["display_name_pt"],
            "match_kind": "extension",
            "registry": "mayflower-extension",
        }
        entries.setdefault(entry["canonical_name_normalized"], entry)
        for alias in extension["aliases"]:
            entries.setdefault(normalized(alias), entry)
    return entries, redirects


def resolve_ingredient(line: str, registry: dict[str, dict], redirects: dict[int, int]) -> dict:
    text = line.strip()
    if re.fullmatch(r"\[[^\]]+\]", text) or re.fullmatch(r"[A-Za-z][A-Za-z ,'-]+:", text):
        return {"match_kind": "unmatched", "review_class": "structural_heading"}
    if re.fullmatch(r"\d+", text):
        return {"match_kind": "unmatched", "review_class": "stray_number"}
    for candidate in ingredient_candidates(line):
        target = HISTORICAL_ALIASES.get(candidate, candidate)
        if target not in registry:
            continue
        result = dict(registry[target])
        ingredient_id = result["ingredient_id"]
        if ingredient_id in redirects:
            result["redirected_from"] = ingredient_id
            result["ingredient_id"] = redirects[ingredient_id]
            result["match_kind"] = "redirect"
        result["matched_term"] = candidate
        if candidate != target:
            result["match_kind"] = "historical_alias"
        return result
    if TEXTUAL_FRAGMENT.fullmatch(text):
        review_class = "textual_fragment"
    elif BRANDED_REFERENCE.search(text):
        review_class = "branded_or_proprietary_reference"
    elif PREPARED_COMPONENT.search(text):
        review_class = "prepared_component"
    elif GENERIC_INGREDIENT.search(text):
        review_class = "underspecified_ingredient"
    else:
        review_class = "unresolved_food_identity"
    return {"match_kind": "unmatched", "review_class": review_class}


def make_recipe(source: dict, numeric_id: int, registry: dict[str, dict], redirects: dict[int, int]) -> tuple[dict, list[dict]]:
    title = source["title"].strip()
    chapter = source["chapter"].strip()
    matches = [resolve_ingredient(line, registry, redirects) for line in source["ingredients"]]
    search_terms = set(source["ingredients"])
    canonical_ids = []
    for match in matches:
        if match["match_kind"] == "unmatched":
            continue
        canonical_ids.append(match["ingredient_id"])
        search_terms.update(filter(None, [match.get("canonical_name"), match.get("display_name_en"), match.get("display_name_pt"), match.get("matched_term")]))
    description = f"A {chapter.lower()} recipe from the 1930 Mayflower Guild cookbook."
    original_locator = "; ".join(filter(None, [f"PDF page {source['page']}" if source.get("page") else None, f"printed page {source['printed_page']}" if source.get("printed_page") else None]))
    record = {
        "id": numeric_id,
        "slug": f"{numeric_id:03d}-{slug(title)}",
        "title": title,
        "collection": {"slug": "mayflower-guild-cookbook-1930", "name": "Mayflower Guild Cookbook (1930)"},
        "language_code": "en",
        "content_kind": "recipe",
        "description": description,
        "translations": {},
        "ingredient_search_terms": sorted(normalized(term).replace("-", " ") for term in search_terms if term),
        "yield": None,
        "prep_time": None,
        "cook_time": None,
        "total_time": None,
        "servings": None,
        "ingredients": source["ingredients"],
        "steps": source["directions"],
        "categories": [chapter],
        "instructions": "\n".join(source["directions"]),
        "notes": f"Edited Version 8. Source ID: {source['id']}. {original_locator}.",
        "originals": [],
        "photos": [],
        "source_id": source["id"],
        "source": {
            "publication": "Cook Book",
            "compiler": "Mayflower Guild of First Congregational Church, Kalamazoo, Michigan",
            "year": 1930,
            "pdf_page": source.get("page"),
            "printed_page": source.get("printed_page"),
            "contributors": source.get("contributors", []),
        },
        "canonical_ingredient_ids": sorted(set(canonical_ids)),
    }
    report_rows = [
        {"recipe_id": source["id"], "recipe_title": title, "display_text": line, **match}
        for line, match in zip(source["ingredients"], matches)
    ]
    return record, report_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--edition", default="20261101-v8-01")
    args = parser.parse_args()

    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(source["recipes"]) != 708:
        raise ValueError("Version 8 source must contain exactly 708 recipes")
    registry, redirects = load_registry(args.registry)
    records, report = zip(*(make_recipe(recipe, index, registry, redirects) for index, recipe in enumerate(source["recipes"], start=1)))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    public = {"schema_version": 3, "created_at": datetime.now(timezone.utc).isoformat(), "recipes": list(records)}
    recipes_path = OUTPUT / "recipes.json"
    recipes_path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(recipes_path.read_bytes()).hexdigest()
    matches = [row for recipe_rows in report for row in recipe_rows]
    counts = Counter(row["match_kind"] for row in matches)
    review_summary = Counter(row.get("review_class", "") for row in matches if row["match_kind"] == "unmatched")
    report_path = ROOT / "reports" / "canonical-ingredient-matches.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps({"source": SOURCE.name, "registry": str(args.registry), "summary": dict(counts), "review_summary": dict(review_summary), "matches": matches}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    queue: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in matches:
        if row["match_kind"] == "unmatched":
            queue[(row["review_class"], row["display_text"])].append(row)
    queue_path = ROOT / "reports" / "ingredient-review-queue.csv"
    with queue_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["review_class", "display_text", "occurrences", "recipe_ids", "recipe_titles"])
        writer.writeheader()
        for (review_class, display_text), rows in sorted(queue.items(), key=lambda item: (-len(item[1]), item[0][1].casefold())):
            writer.writerow({
                "review_class": review_class,
                "display_text": display_text,
                "occurrences": len(rows),
                "recipe_ids": "; ".join(row["recipe_id"] for row in rows),
                "recipe_titles": "; ".join(row["recipe_title"] for row in rows),
            })
    edition = {"schema_version": 3, "edition": args.edition, "created_at": public["created_at"], "recipes": len(records), "recipes_with_captured_originals": 0, "files": {"recipes.json": digest}}
    (OUTPUT / "edition.json").write_text(json.dumps(edition, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(records)} recipes; ingredient matching: {dict(counts)}")


if __name__ == "__main__":
    main()
