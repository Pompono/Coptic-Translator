import json
from pathlib import Path

FILE = Path("reverse/apk_unzipped/assets/Gospel of St. John.json")

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print("File:", FILE)
print("Top-level type:", type(data).__name__)

if isinstance(data, dict):
    print("Top-level keys:")
    for key in data.keys():
        print(" ", repr(key))

    print("\nSample values:")
    for key, value in list(data.items())[:5]:
        print("\nKEY:", repr(key))
        print("TYPE:", type(value).__name__)
        print("VALUE SAMPLE:", str(value)[:1000])

elif isinstance(data, list):
    print("List length:", len(data))

    for i, item in enumerate(data[:5]):
        print("\nITEM", i)
        print("TYPE:", type(item).__name__)
        print("SAMPLE:", str(item)[:1500])

        if isinstance(item, dict):
            print("KEYS:", list(item.keys()))