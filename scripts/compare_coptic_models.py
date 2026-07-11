import json
import random
from pathlib import Path
from transformers import pipeline

random.seed(123)

EVAL_FILE = Path("data/final/mixed_coptic_to_english_valid.jsonl")

OLD_MODEL = "models/dict_coptic_to_english_finetuned"
NEW_MODEL = "models/mixed_coptic_to_english_finetuned"

rows = []

with open(EVAL_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            rows.append(json.loads(line))

sample = random.sample(rows, min(20, len(rows)))

print("Loading old dictionary model...")
old_pipe = pipeline(
    "text2text-generation",
    model=OLD_MODEL,
    trust_remote_code=True
)

print("Loading new mixed Bible model...")
new_pipe = pipeline(
    "text2text-generation",
    model=NEW_MODEL,
    trust_remote_code=True
)

for i, row in enumerate(sample, start=1):
    source = row["source"]
    expected = row["target"]
    reference = row.get("reference", "")
    dialect = row.get("dialect", "")

    old_out = old_pipe(source, max_new_tokens=120)[0]["generated_text"]
    new_out = new_pipe(source, max_new_tokens=120)[0]["generated_text"]

    print("=" * 100)
    print(f"EXAMPLE {i}")
    print("REFERENCE:", reference)
    print("DIALECT:", dialect)

    print("\nCOPTIC SOURCE:")
    print(source)

    print("\nEXPECTED LITERAL ENGLISH:")
    print(expected)

    print("\nOLD DICTIONARY MODEL:")
    print(old_out)

    print("\nNEW MIXED MODEL:")
    print(new_out)