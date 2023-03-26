import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, GPT2Config, TextDataset, DataCollatorForLanguageModeling, Trainer, TrainingArguments

def fine_tune(dataset_path, model_name="gpt2", output_dir="fine_tuned_model"):
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    config = GPT2Config.from_pretrained(model_name)
    model = GPT2LMHeadModel.from_pretrained(model_name, config=config)

    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=dataset_path,
        block_size=128
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        save_steps=10_000,
        save_total_limit=2
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset
    )

    trainer.train()

if __name__ == "__main__":
    fine_tune("fine_tuning_dataset/train.text")
