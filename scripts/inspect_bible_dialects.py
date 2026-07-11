import json
from pathlib import Path
from collections import Counter, defaultdict

ASSETS_DIR = Path("reverse/apk_unzipped/assets")

POSSIBLE_DIALECT_KEYS = [
    "Bohairic",
    "OldBohairic",
    "Sahidic",
    "Akhmimic",
    "Fayyumic",
    "Lycopolitan",
    "SubAkhmimic",
    "Greek",
    "English",
]

def has_coptic(text):
    if not text:
        return False
    return any(
        ("\u2c80" <= ch <= "\u2cff") or ("\u03e2" <= ch <= "\u03ef")
        for ch in str(text)
    )

def clean_text(text):
    if text is None:
        return ""
    return str(text).strip()

def main():
    total_files = 0
    total_verse_records = 0

    key_counts = Counter()
    coptic_counts = Counter()
    book_dialect_counts = defaultdict(Counter)

    json_files = sorted(ASSETS_DIR.glob("*.json"))

    for json_path in json_files:
        if json_path.name.endswith("_Sources.json"):
            continue

        total_files += 1
        book = json_path.stem

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Could not parse {json_path.name}: {e}")
            continue

        if not isinstance(data, list):
            print(f"Skipping {json_path.name}: top-level is not list")
            continue

        for section in data:
            if not isinstance(section, dict):
                continue

            verses = section.get("data", [])
            if not isinstance(verses, list):
                continue

            for verse in verses:
                if not isinstance(verse, dict):
                    continue

                total_verse_records += 1

                for key in verse.keys():
                    key_counts[key] += 1

                for key in POSSIBLE_DIALECT_KEYS:
                    value = clean_text(verse.get(key, ""))

                    if value:
                        book_dialect_counts[book][key] += 1

                    if key != "English" and key != "Greek" and has_coptic(value):
                        coptic_counts[key] += 1

    print("=" * 80)
    print("BIBLE JSON INSPECTION SUMMARY")
    print("=" * 80)
    print("Bible JSON files inspected:", total_files)
    print("Total verse records inspected:", total_verse_records)

    print("\nTop keys found in verse objects:")
    for key, count in key_counts.most_common(40):
        print(f"{key}: {count}")

    print("\nCoptic-containing counts by dialect key:")
    for key, count in coptic_counts.most_common():
        print(f"{key}: {count}")

    print("\nBooks with dialect availability:")
    for book in sorted(book_dialect_counts.keys()):
        counts = book_dialect_counts[book]
        found = []
        for key in POSSIBLE_DIALECT_KEYS:
            if counts.get(key, 0):
                found.append(f"{key}={counts[key]}")
        print(f"{book}: " + ", ".join(found))

if __name__ == "__main__":
    main()