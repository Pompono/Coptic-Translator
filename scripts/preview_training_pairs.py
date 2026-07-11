import json
import random
from pathlib import Path

INPUT_FILE = Path("data/final/mixed_coptic_to_english_train.jsonl")
OUTPUT_FILE = Path("data/final/preview_coptic_to_english.txt")

random.seed(42)

rows = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            rows.append(json.loads(line))

sample = random.sample(rows, min(100, len(rows)))

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for i, row in enumerate(sample, start=1):
        f.write("=" * 100 + "\n")
        f.write(f"PAIR {i}\n")
        f.write(f"REFERENCE: {row.get('reference', '')}\n")
        f.write(f"TYPE: {row.get('type', '')}\n")
        f.write(f"DIALECT: {row.get('dialect', '')}\n")
        f.write(f"QUALITY: {row.get('quality', '')}\n\n")

        f.write("SOURCE COPTIC:\n")
        f.write(row.get("source", "") + "\n\n")

        f.write("TARGET ENGLISH:\n")
        f.write(row.get("target", "") + "\n\n")

print(f"Wrote preview file: {OUTPUT_FILE}")
print(f"Total rows in input: {len(rows)}")
print(f"Sample rows written: {len(sample)}")
