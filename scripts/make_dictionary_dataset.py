import json
import random
import re
from pathlib import Path


INPUT_FILE = Path("bohairic_dictionary.json")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

OUT_COP_EN_TRAIN = DATA_DIR / "dict_coptic_to_english_train.jsonl"
OUT_COP_EN_VALID = DATA_DIR / "dict_coptic_to_english_valid.jsonl"
OUT_EN_COP_TRAIN = DATA_DIR / "dict_english_to_coptic_train.jsonl"
OUT_EN_COP_VALID = DATA_DIR / "dict_english_to_coptic_valid.jsonl"


def clean_text(text):
    if not text:
        return ""

    text = text.strip()

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove trailing punctuation that can confuse short glosses
    text = text.strip(" .;:")

    return text


def is_bad_sense(sense):
    if not sense:
        return True

    s = sense.lower().strip()

    bad_patterns = [
        "unknown",
        "see:",
        "same meaning",
        "meaning as last",
    ]

    return any(p in s for p in bad_patterns)


def is_bad_word(word):
    if not word:
        return True

    word = word.strip()

    # Avoid weirdly long entries or explanatory entries
    if len(word) > 60:
        return True

    # Avoid obvious malformed dictionary notation
    if "See:" in word:
        return True

    return False


def split_sense_into_glosses(sense):
    """
    Converts a dictionary sense like:
    'Love, brotherly love, love of God, charity, alms'
    into cleaner glosses:
    ['love', 'brotherly love', 'love of God', 'charity', 'alms']
    """

    sense = clean_text(sense)

    # Remove common dictionary notes
    sense = re.sub(r"^\(?w/\s*[^)]*\)?\s*", "", sense, flags=re.IGNORECASE)
    sense = re.sub(r"^(m\.|f\.|adj\.|vb\.|vi\.|vt\.|nn\.|pl\.|sg\.)\s*", "", sense, flags=re.IGNORECASE)

    # Split on semicolon first, then comma
    parts = re.split(r"[;,]", sense)

    glosses = []
    for part in parts:
        part = clean_text(part)

        # Remove small dictionary labels again
        part = re.sub(r"^(m\.|f\.|adj\.|vb\.|vi\.|vt\.|nn\.|pl\.|sg\.)\s*", "", part, flags=re.IGNORECASE)
        part = clean_text(part)

        if not part:
            continue

        if is_bad_sense(part):
            continue

        # Avoid overly explanatory glosses as direct translation targets
        if len(part.split()) > 8:
            continue

        glosses.append(part)

    return glosses


def make_pairs(entry):
    pairs_cop_en = []
    pairs_en_cop = []

    word = clean_text(entry.get("word", ""))
    pos = clean_text(entry.get("pos", ""))
    tag = clean_text(entry.get("scriptorium_tag", ""))
    senses = entry.get("senses") or []
    variants = entry.get("bohairic_variants") or []

    if is_bad_word(word):
        return [], []

    # Skip cross references
    if "cross-reference" in pos.lower() or "cross-ref" in tag.lower():
        return [], []

    all_coptic_forms = [word]

    for variant in variants:
        variant = clean_text(variant)

        # Skip variants that are just grammatical notation, like "-ⲟⲛ"
        if not variant:
            continue
        if variant.startswith("-"):
            continue
        if len(variant) > 60:
            continue

        all_coptic_forms.append(variant)

    all_coptic_forms = list(dict.fromkeys(all_coptic_forms))

    all_glosses = []
    for sense in senses:
        if is_bad_sense(sense):
            continue
        all_glosses.extend(split_sense_into_glosses(sense))

    all_glosses = list(dict.fromkeys(all_glosses))

    if not all_glosses:
        return [], []

    # Limit glosses per entry so one dictionary entry does not dominate training
    all_glosses = all_glosses[:4]

    for coptic in all_coptic_forms:
        for gloss in all_glosses:
            # Coptic -> English
            pairs_cop_en.append({
                "source": coptic,
                "target": gloss,
                "dialect": "bohairic",
                "source_type": "dictionary"
            })

            # English -> Coptic
            pairs_en_cop.append({
                "source": gloss,
                "target": coptic,
                "dialect": "bohairic",
                "source_type": "dictionary"
            })

    return pairs_cop_en, pairs_en_cop


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Could not find {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    coptic_to_english = []
    english_to_coptic = []

    for entry in entries:
        pairs_cop_en, pairs_en_cop = make_pairs(entry)
        coptic_to_english.extend(pairs_cop_en)
        english_to_coptic.extend(pairs_en_cop)

    # Shuffle for training
    random.seed(42)
    random.shuffle(coptic_to_english)
    random.shuffle(english_to_coptic)

    # Split 90/10 train/validation
    split_cop_en = int(len(coptic_to_english) * 0.9)
    split_en_cop = int(len(english_to_coptic) * 0.9)

    cop_en_train = coptic_to_english[:split_cop_en]
    cop_en_valid = coptic_to_english[split_cop_en:]

    en_cop_train = english_to_coptic[:split_en_cop]
    en_cop_valid = english_to_coptic[split_en_cop:]

    write_jsonl(OUT_COP_EN_TRAIN, cop_en_train)
    write_jsonl(OUT_COP_EN_VALID, cop_en_valid)
    write_jsonl(OUT_EN_COP_TRAIN, en_cop_train)
    write_jsonl(OUT_EN_COP_VALID, en_cop_valid)

    print("Dictionary conversion complete.")
    print(f"Coptic -> English train: {len(cop_en_train)}")
    print(f"Coptic -> English valid: {len(cop_en_valid)}")
    print(f"English -> Coptic train: {len(en_cop_train)}")
    print(f"English -> Coptic valid: {len(en_cop_valid)}")


if __name__ == "__main__":
    main()