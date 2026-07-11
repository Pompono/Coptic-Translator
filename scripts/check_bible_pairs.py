import json
from pathlib import Path

path = Path("data/final/bible_bohairic_to_english.jsonl")

def has_coptic(text):
    return any(
        ("\u2c80" <= ch <= "\u2cff") or ("\u03e2" <= ch <= "\u03ef")
        for ch in text
    )

def count_coptic(text):
    return sum(
        1 for ch in text
        if ("\u2c80" <= ch <= "\u2cff") or ("\u03e2" <= ch <= "\u03ef")
    )

def count_mojibake(text):
    bad_chars = ["â", "Î", "Ï", "Ã", "Â"]
    return sum(text.count(ch) for ch in bad_chars)

total = 0
with_coptic = 0
with_mojibake = 0

with open(path, "r", encoding="utf-8") as f:
    for line in f:
        total += 1
        row = json.loads(line)

        source = row["source"]
        target = row["target"]

        coptic_chars = count_coptic(source)
        mojibake_chars = count_mojibake(source)

        if coptic_chars > 0:
            with_coptic += 1

        if mojibake_chars > 0:
            with_mojibake += 1

        if total <= 3:
            print("REFERENCE:", row["reference"])
            print("SOURCE:", source)
            print("TARGET:", target)
            print("COPTIC CHAR COUNT:", coptic_chars)
            print("MOJIBAKE CHAR COUNT:", mojibake_chars)
            print("-" * 80)

print("TOTAL ROWS:", total)
print("ROWS WITH COPTIC:", with_coptic)
print("ROWS WITH MOJIBAKE:", with_mojibake)