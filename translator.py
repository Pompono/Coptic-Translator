import json
import re
from pathlib import Path
from transformers import pipeline


DICTIONARY_FILE = Path("bohairic_dictionary.json")


CHAR_TO_COPTIC = str.maketrans({
    "Α": "ⲁ", "Β": "ⲃ", "Γ": "ⲅ", "Δ": "ⲇ", "Ε": "ⲉ", "Ζ": "ⲍ",
    "Η": "ⲏ", "Θ": "ⲑ", "Ι": "ⲓ", "Κ": "ⲕ", "Λ": "ⲗ", "Μ": "ⲙ",
    "Ν": "ⲛ", "Ξ": "ⲝ", "Ο": "ⲟ", "Π": "ⲡ", "Ρ": "ⲣ", "Σ": "ⲥ",
    "Τ": "ⲧ", "Υ": "ⲩ", "Φ": "ⲫ", "Χ": "ⲭ", "Ψ": "ⲯ", "Ω": "ⲱ",

    "α": "ⲁ", "β": "ⲃ", "γ": "ⲅ", "δ": "ⲇ", "ε": "ⲉ", "ζ": "ⲍ",
    "η": "ⲏ", "θ": "ⲑ", "ι": "ⲓ", "κ": "ⲕ", "λ": "ⲗ", "μ": "ⲙ",
    "ν": "ⲛ", "ξ": "ⲝ", "ο": "ⲟ", "π": "ⲡ", "ρ": "ⲣ", "σ": "ⲥ",
    "ς": "ⲥ", "τ": "ⲧ", "υ": "ⲩ", "φ": "ⲫ", "χ": "ⲭ", "ψ": "ⲯ",
    "ω": "ⲱ",

    "A": "ⲁ", "B": "ⲃ", "G": "ⲅ", "D": "ⲇ", "E": "ⲉ", "Z": "ⲍ",
    "H": "ⲏ", "Q": "ⲑ", "I": "ⲓ", "K": "ⲕ", "L": "ⲗ", "M": "ⲙ",
    "N": "ⲛ", "O": "ⲟ", "P": "ⲡ", "R": "ⲣ", "S": "ⲥ", "C": "ⲥ",
    "T": "ⲧ", "U": "ⲩ", "Y": "ⲩ", "F": "ⲫ", "X": "ⲭ", "W": "ⲱ",

    "a": "ⲁ", "b": "ⲃ", "g": "ⲅ", "d": "ⲇ", "e": "ⲉ", "z": "ⲍ",
    "h": "ⲏ", "q": "ⲑ", "i": "ⲓ", "k": "ⲕ", "l": "ⲗ", "m": "ⲙ",
    "n": "ⲛ", "o": "ⲟ", "p": "ⲡ", "r": "ⲣ", "s": "ⲥ", "c": "ⲥ",
    "t": "ⲧ", "u": "ⲩ", "y": "ⲩ", "f": "ⲫ", "x": "ⲭ", "w": "ⲱ",
})


def clean_text(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_coptic_output(text):
    text = clean_text(text)
    text = text.translate(CHAR_TO_COPTIC)

    text = text.replace("ⲓⲏⲥ ⲟⲩⲥ", "ⲓⲏⲥⲟⲩⲥ")
    text = text.replace("ⲡⲓ ⲭⲣⲓ ⲥ ⲧⲟⲥ", "ⲡⲓⲭⲣⲓⲥⲧⲟⲥ")
    text = text.replace("ⲡⲓ ⲭⲡⲓ ⲥ ⲧⲟⲥ", "ⲡⲓⲭⲣⲓⲥⲧⲟⲥ")
    text = text.replace("ⲭⲡⲓ", "ⲭⲣⲓ")

    return text


def first_good_sense(senses):
    for sense in senses:
        if not sense:
            continue

        s = clean_text(sense)
        low = s.lower()

        if "unknown" in low:
            continue
        if low.startswith("see:"):
            continue

        # Keep only the first clean gloss
        parts = re.split(r"[;,]", s)
        for part in parts:
            part = clean_text(part).strip(" .;:")
            part = re.sub(r"^(m\.|f\.|adj\.|vb\.|vi\.|vt\.|nn\.|pl\.|sg\.)\s*", "", part, flags=re.IGNORECASE)
            part = clean_text(part).strip(" .;:")

            if part and "unknown" not in part.lower() and not part.lower().startswith("see:"):
                return part

    return ""


def load_dictionary():
    coptic_to_english = {}
    english_to_coptic = {}

    if not DICTIONARY_FILE.exists():
        print("Dictionary file not found. Skipping dictionary lookup.")
        return coptic_to_english, english_to_coptic

    with open(DICTIONARY_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        word = clean_text(entry.get("word", ""))
        pos = clean_text(entry.get("pos", ""))
        tag = clean_text(entry.get("scriptorium_tag", ""))
        senses = entry.get("senses") or []

        if not word:
            continue

        if "cross-reference" in pos.lower() or "cross-ref" in tag.lower():
            continue

        gloss = first_good_sense(senses)
        if not gloss:
            continue

        coptic_to_english[word] = gloss

        # English lookup should be lowercase
        english_key = gloss.lower()
        if english_key not in english_to_coptic:
            english_to_coptic[english_key] = word

        # Add variants too
        for variant in entry.get("bohairic_variants") or []:
            variant = clean_text(variant)
            if variant and not variant.startswith("-"):
                coptic_to_english[variant] = gloss

    return coptic_to_english, english_to_coptic


class CopticTranslator:
    def __init__(self):
        print("Loading dictionary...")
        self.dict_cop_to_en, self.dict_en_to_cop = load_dictionary()
        print(f"Loaded {len(self.dict_cop_to_en)} Coptic dictionary entries.")
        print(f"Loaded {len(self.dict_en_to_cop)} English dictionary entries.")

        print("Loading Coptic -> English fine-tuned model...")
        self.cop_to_en = pipeline(
            "text2text-generation",
            model="models/mixed_coptic_to_english_finetuned",
            trust_remote_code=True
        )

        print("Loading English -> Coptic BASE model...")
        # Use the base model for now because the dictionary-fine-tuned English -> Coptic model returned empty outputs.
        self.en_to_cop = pipeline(
            "text2text-generation",
            model="megalaa/english-coptic-translator",
            trust_remote_code=True
        )

    def coptic_to_english(self, text):
        text = clean_text(text)

        # Exact dictionary lookup first
        if text in self.dict_cop_to_en:
            return self.dict_cop_to_en[text]

        result = self.cop_to_en(text, max_new_tokens=30)
        output = clean_text(result[0].get("generated_text", ""))

        if not output:
            return "[No translation produced]"

        return output

    def english_to_coptic(self, text):
        text = clean_text(text)
        key = text.lower()

        # Exact dictionary lookup first
        if key in self.dict_en_to_cop:
            return self.dict_en_to_cop[key]

        result = self.en_to_cop(text, max_new_tokens=30)
        raw_text = clean_text(result[0].get("generated_text", ""))
        output = normalize_coptic_output(raw_text)

        if not output:
            return "[No translation produced]"

        return output


if __name__ == "__main__":
    translator = CopticTranslator()

    tests = [
        ("ⲁⲅⲁⲡⲏ", "coptic_to_english"),
        ("ⲁⲅⲅⲉⲗⲟⲥ", "coptic_to_english"),
        ("ⲁⲙⲏⲛ", "coptic_to_english"),
        ("love", "english_to_coptic"),
        ("angel", "english_to_coptic"),
        ("amen", "english_to_coptic"),
    ]

    for text, direction in tests:
        print("\nInput:", text)
        print("Direction:", direction)

        if direction == "coptic_to_english":
            print("Output:", translator.coptic_to_english(text))
        else:
            print("Output:", translator.english_to_coptic(text))