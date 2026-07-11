import json
import re
from pathlib import Path
from collections import Counter


ASSETS_DIR = Path("reverse/apk_unzipped/assets")
OUT_DIR = Path("data/final")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_COP_EN = OUT_DIR / "bible_bohairic_to_english.jsonl"
OUT_EN_COP = OUT_DIR / "bible_english_to_bohairic.jsonl"

DIALECT_KEY = "Bohairic"
DIALECT_LABEL = "bohairic"


def has_coptic(text):
    return any(
        ("\u2c80" <= ch <= "\u2cff") or ("\u03e2" <= ch <= "\u03ef")
        for ch in text
    )


def clean_text(text):
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\u200f", "")
    text = text.replace("\u200e", "")
    text = text.replace("\ufeff", "")
    text = text.strip()

    # Remove repeated whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading footnote/segment markers like "(1)", "(2)", "(ⲁ)", "(B)"
    text = re.sub(r"^\([^)]+\)\s*", "", text).strip()

    # Remove extra spaces before punctuation
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    return text


def safe_reference(book_name, section, verse_obj, fallback_index):
    verse_number = clean_text(verse_obj.get("verseNumber", ""))

    if verse_number:
        return verse_number

    chapter = clean_text(section.get("sectionNameEnglish", ""))
    if chapter:
        return f"{book_name} {chapter}:{fallback_index}"

    return f"{book_name} unknown:{fallback_index}"


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    coptic_to_english = []
    english_to_coptic = []
    counts_by_book = Counter()

    json_files = sorted(ASSETS_DIR.glob("*.json"))

    for json_path in json_files:
        # Skip source metadata files
        if json_path.name.endswith("_Sources.json"):
            continue

        book_name = json_path.stem

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Skipping {json_path.name}: could not parse JSON: {e}")
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

                coptic = clean_text(verse.get(DIALECT_KEY, ""))
                english = clean_text(verse.get("English", ""))

                if not coptic or not english:
                    continue

                # Make sure we are not accidentally training on blank/non-Coptic data
                if not has_coptic(coptic):
                    continue

                reference = safe_reference(book_name, section, verse, i)

                coptic_to_english.append({
                    "source": coptic,
                    "target": english,
                    "dialect": DIALECT_LABEL,
                    "type": "bible",
                    "book": book_name,
                    "reference": reference,
                    "quality": "apk_extracted"
                })

                english_to_coptic.append({
                    "source": f"<{DIALECT_LABEL}> {english}",
                    "target": coptic,
                    "dialect": DIALECT_LABEL,
                    "type": "bible",
                    "book": book_name,
                    "reference": reference,
                    "quality": "apk_extracted"
                })

                counts_by_book[book_name] += 1

    write_jsonl(OUT_COP_EN, coptic_to_english)
    write_jsonl(OUT_EN_COP, english_to_coptic)

    print("Extraction complete.")
    print(f"Wrote: {OUT_COP_EN}")
    print(f"Pairs: {len(coptic_to_english)}")
    print(f"Wrote: {OUT_EN_COP}")
    print(f"Pairs: {len(english_to_coptic)}")

    print("\nTop books by extracted Bohairic/English pairs:")
    for book, count in counts_by_book.most_common(20):
        print(f"{book}: {count}")


if __name__ == "__main__":
    main()