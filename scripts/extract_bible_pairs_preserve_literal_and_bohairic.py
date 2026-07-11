import json
import re
from pathlib import Path
from collections import Counter

ASSETS_DIR = Path("reverse/apk_unzipped/assets")
OUT_DIR = Path("data/final")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_ALL_TO_LITERAL = OUT_DIR / "bible_all_dialects_to_literal_english.jsonl"
OUT_BOHAIRIC_TO_LITERAL = OUT_DIR / "bible_bohairic_to_literal_english.jsonl"
OUT_SAHIDIC_TO_LITERAL = OUT_DIR / "bible_sahidic_to_literal_english.jsonl"
OUT_LITERAL_TO_BOHAIRIC = OUT_DIR / "bible_literal_english_to_standard_bohairic.jsonl"

DIALECTS = {
    "Bohairic": "bohairic",
    "Sahidic": "sahidic",
    "Fayyumic": "fayyumic",
    "Akhmimic": "akhmimic",
}

STANDARD_BOHAIRIC_KEY = "Bohairic"


def has_coptic(text):
    return any(
        ("\u2c80" <= ch <= "\u2cff") or ("\u03e2" <= ch <= "\u03ef")
        for ch in str(text)
    )


def clean_text(text):
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\u200f", "")
    text = text.replace("\u200e", "")
    text = text.replace("\ufeff", "")
    text = text.strip()

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^\([^)]+\)\s*", "", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    return text


def get_reference(book_name, section, verse, fallback_index):
    verse_number = clean_text(verse.get("verseNumber", ""))

    if verse_number:
        return verse_number

    section_name = clean_text(section.get("sectionNameEnglish", ""))

    if section_name:
        return f"{book_name} {section_name}:{fallback_index}"

    return f"{book_name} unknown:{fallback_index}"


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    all_to_literal = []
    bohairic_to_literal = []
    sahidic_to_literal = []
    literal_to_bohairic = []

    counts = Counter()

    for json_path in sorted(ASSETS_DIR.glob("*.json")):
        if json_path.name.endswith("_Sources.json"):
            continue

        book_name = json_path.stem

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Skipping {json_path.name}: {e}")
            continue

        if not isinstance(data, list):
            print(f"Skipping {json_path.name}: top-level is not a list")
            continue

        for section in data:
            if not isinstance(section, dict):
                continue

            verses = section.get("data", [])

            if not isinstance(verses, list):
                continue

            for i, verse in enumerate(verses, start=1):
                if not isinstance(verse, dict):
                    continue

                literal_english = clean_text(verse.get("English", ""))

                if not literal_english:
                    continue

                reference = get_reference(book_name, section, verse, i)

                # 1. Every available Coptic dialect -> literal English
                for raw_key, dialect_label in DIALECTS.items():
                    coptic = clean_text(verse.get(raw_key, ""))

                    if not coptic:
                        continue

                    if not has_coptic(coptic):
                        continue

                    record = {
                        "source": f"<{dialect_label}> {coptic}",
                        "target": literal_english,
                        "dialect": dialect_label,
                        "source_language": "coptic",
                        "target_language": "english",
                        "target_style": "literal_english",
                        "type": "bible",
                        "book": book_name,
                        "reference": reference,
                        "quality": "apk_extracted",
                    }

                    all_to_literal.append(record)

                    if dialect_label == "bohairic":
                        bohairic_to_literal.append(record)

                    if dialect_label == "sahidic":
                        sahidic_to_literal.append(record)

                    counts[f"{dialect_label}_to_literal_english"] += 1

                # 2. Literal English -> standard Bohairic only
                standard_bohairic = clean_text(verse.get(STANDARD_BOHAIRIC_KEY, ""))

                if standard_bohairic and has_coptic(standard_bohairic):
                    literal_to_bohairic.append({
                        "source": f"<bohairic> {literal_english}",
                        "target": standard_bohairic,
                        "dialect": "bohairic",
                        "source_language": "english",
                        "target_language": "coptic",
                        "target_style": "standard_bohairic",
                        "type": "bible",
                        "book": book_name,
                        "reference": reference,
                        "quality": "apk_extracted",
                    })

                    counts["literal_english_to_standard_bohairic"] += 1

    write_jsonl(OUT_ALL_TO_LITERAL, all_to_literal)
    write_jsonl(OUT_BOHAIRIC_TO_LITERAL, bohairic_to_literal)
    write_jsonl(OUT_SAHIDIC_TO_LITERAL, sahidic_to_literal)
    write_jsonl(OUT_LITERAL_TO_BOHAIRIC, literal_to_bohairic)

    print("Extraction complete.")
    print()
    print("Wrote:", OUT_ALL_TO_LITERAL)
    print("Rows:", len(all_to_literal))
    print()
    print("Wrote:", OUT_BOHAIRIC_TO_LITERAL)
    print("Rows:", len(bohairic_to_literal))
    print()
    print("Wrote:", OUT_SAHIDIC_TO_LITERAL)
    print("Rows:", len(sahidic_to_literal))
    print()
    print("Wrote:", OUT_LITERAL_TO_BOHAIRIC)
    print("Rows:", len(literal_to_bohairic))

    print("\nCounts:")
    for key, count in counts.most_common():
        print(f"{key}: {count}")


if __name__ == "__main__":
    main()
