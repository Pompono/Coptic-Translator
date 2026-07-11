from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments
)

MODEL_NAME = "megalaa/coptic-english-translator"
OUTPUT_DIR = "models/mixed_coptic_to_english_finetuned"

SPECIAL_TOKENS = [
    "<bohairic>",
    "<sahidic>",
    "<fayyumic>",
    "<akhmimic>",
]

dataset = load_dataset(
    "json",
    data_files={
        "train": "data/final/mixed_coptic_to_english_train.jsonl",
        "validation": "data/final/mixed_coptic_to_english_valid.jsonl"
    }
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)

# Add dialect tags as special tokens so the model learns them cleanly.
num_added = tokenizer.add_special_tokens({
    "additional_special_tokens": SPECIAL_TOKENS
})

if num_added > 0:
    model.resize_token_embeddings(len(tokenizer))

print(f"Added {num_added} special tokens.")
print("Special tokens:", SPECIAL_TOKENS)


def preprocess(batch):
    model_inputs = tokenizer(
        batch["source"],
        max_length=256,
        truncation=True
    )

    labels = tokenizer(
        text_target=batch["target"],
        max_length=256,
        truncation=True
    )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


tokenized = dataset.map(
    preprocess,
    batched=True,
    remove_columns=dataset["train"].column_names
)

data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model
)

training_args = Seq2SeqTrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=1e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    weight_decay=0.01,
    save_total_limit=2,
    num_train_epochs=2,
    predict_with_generate=True,
    logging_steps=100,
    fp16=False
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator
)

trainer.train()

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"Saved fine-tuned model to {OUTPUT_DIR}")