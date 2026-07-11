import json
import random
from pathlib import Path

random.seed(42)

DATA_DIR = Path("data")
FINAL_DIR = Path("data/final")
FINAL_DIR.mkdir(parents=True, exist_ok=True)

# Coptic -> English should use all Coptic dialects to literal English
BIBLE_COP_EN = FINAL_DIR / "bible_all_dialects_to_literal_english.jsonl"

# English -> Coptic should use literal English to STANDARD Bohairic only
BIBLE_EN_COP = FINAL_DIR / "bible_literal_english_to_standard_bohairic.jsonl"

DICT_COP_EN = DATA_DIR / "dict_coptic_to_english_train.jsonl"
DICT_EN_COP = DATA_DIR / "dict_english_to_coptic_train.jsonl"

OUT_COP_EN_TRAIN = FINAL_DIR / "mixed_coptic_to_english_train.jsonl"
OUT_COP_EN_VALID = FINAL_DIR / "mixed_coptic_to_english_valid.jsonl"
OUT_EN_COP_TRAIN = FINAL_DIR / "mixed_english_to_coptic_train.jsonl"
OUT_EN_COP_VALID = FINAL_DIR / "mixed_english_to_coptic_valid.jsonl"


def read_jsonl(path):
    if not path.exists():
        print(f"Missing file, skipping: {path}")
        return []

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_bohairic_tag(text):
    text = str(text).strip()
    if text.startswith("<"):
        return text
    return f"<bohairic> {text}"


def prepare_dictionary_cop_en(rows):
    prepared = []

    for row in rows:
        source = str(row.get("source", "")).strip()
        target = str(row.get("target", "")).strip()

        if not source or not target:
            continue

        prepared.append({
            "source": ensure_bohairic_tag(source),
            "target": target,
            "dialect": "bohairic",
            "type": "dictionary",
            "reference": "",
            "quality": row.get("quality", "dictionary_extracted")
        })

    return prepared


def prepare_dictionary_en_cop(rows):
    prepared = []

    for row in rows:
        source = str(row.get("source", "")).strip()
        target = str(row.get("target", "")).strip()

        if not source or not target:
            continue

        prepared.append({
            "source": ensure_bohairic_tag(source),
            "target": target,
            "dialect": "bohairic",
            "type": "dictionary",
            "reference": "",
            "quality": row.get("quality", "dictionary_extracted")
        })

    return prepared


def clean_rows(rows, max_source_len=700, max_target_len=700):
    cleaned = []
    seen = set()

    for row in rows:
        source = str(row.get("source", "")).strip()
        target = str(row.get("target", "")).strip()

        if not source or not target:
            continue

        if len(source) > max_source_len or len(target) > max_target_len:
            continue

        key = (source, target)
        if key in seen:
            continue

        seen.add(key)

        cleaned.append({
            "source": source,
            "target": target,
            "dialect": row.get("dialect", "unknown"),
            "type": row.get("type", "unknown"),
            "reference": row.get("reference", ""),
            "quality": row.get("quality", "")
        })

    return cleaned


def split_train_valid(rows, valid_ratio=0.08):
    random.shuffle(rows)
    split = int(len(rows) * (1 - valid_ratio))
    return rows[:split], rows[split:]


def main():
    bible_cop_en = read_jsonl(BIBLE_COP_EN)
    bible_en_cop = read_jsonl(BIBLE_EN_COP)

    dict_cop_en = prepare_dictionary_cop_en(read_jsonl(DICT_COP_EN))
    dict_en_cop = prepare_dictionary_en_cop(read_jsonl(DICT_EN_COP))

    random.shuffle(dict_cop_en)
    random.shuffle(dict_en_cop)

    # Dictionary helps vocabulary, but Bible sentence pairs should dominate.
    dict_cop_en = dict_cop_en[:3000]
    dict_en_cop = dict_en_cop[:1500]

    cop_en = clean_rows(bible_cop_en + dict_cop_en)
    en_cop = clean_rows(bible_en_cop + dict_en_cop)

    cop_en_train, cop_en_valid = split_train_valid(cop_en)
    en_cop_train, en_cop_valid = split_train_valid(en_cop)

    write_jsonl(OUT_COP_EN_TRAIN, cop_en_train)
    write_jsonl(OUT_COP_EN_VALID, cop_en_valid)
    write_jsonl(OUT_EN_COP_TRAIN, en_cop_train)
    write_jsonl(OUT_EN_COP_VALID, en_cop_valid)

    print("Mixed training data created.")
    print("Coptic -> literal English train:", len(cop_en_train))
    print("Coptic -> literal English valid:", len(cop_en_valid))
    print("Literal English -> standard Bohairic train:", len(en_cop_train))
    print("Literal English -> standard Bohairic valid:", len(en_cop_valid))


if __name__ == "__main__":
    main()