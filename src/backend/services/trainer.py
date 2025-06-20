"""
trainer.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

# src/training/trainer.py
import os
from typing import Dict

import torch
from datasets import load_dataset
from transformers import (
    DataCollatorForLanguageModeling,
    GPT2LMHeadModel,
    GPT2Tokenizer,
    Trainer,
    TrainingArguments,
)

# --- FIXED: Import the new settings module from the config package ---
from src.backend.utils import settings
from src.backend.utils.constants import PROGRESS_MAX, PROGRESS_MIN


def get_best_device(log_callback):
    """
    Checks for available hardware accelerators and returns the best device.
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        log_callback("NVIDIA CUDA GPU detected. Using 'cuda' device.")
        return device
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        log_callback("Apple Metal (MPS) GPU detected. Using 'mps' device.")
        return device
    device = torch.device("cpu")
    log_callback("No compatible GPU detected. Falling back to CPU.")
    return device


def train_model(
    vocab_dir, model_save_path, finetune=False, training_data_path=None, **kwargs
):
    log_message_callback = kwargs.get("log_message_callback", print)
    progress_callback = kwargs.get("progress_callback", lambda c, t, m: None)
    _log = log_message_callback

    try:
        # --- FIXED: Reference the settings module ---
        device = get_best_device(_log)
        progress_callback(PROGRESS_MIN, PROGRESS_MAX, "Starting training...")

        base_model_name = "distilgpt2"
        _log(f"Using pre-trained model architecture: {base_model_name}")

        _log("Loading tokenizer and model...")
        tokenizer = GPT2Tokenizer.from_pretrained(base_model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = None
        if finetune and os.path.exists(os.path.join(model_save_path, "config.json")):
            _log(f"Loading existing finetuned model from {model_save_path}")
            model = GPT2LMHeadModel.from_pretrained(model_save_path)
        else:
            if finetune:
                _log(
                    f"No existing model found at {model_save_path}. Initializing new model for finetuning."
                )
            else:
                _log(f"Initializing new '{base_model_name}' model for base training.")
            model = GPT2LMHeadModel.from_pretrained(base_model_name)

        model.to(device)

        # Use provided training_data_path or fall back to settings
        if finetune:
            if training_data_path is None:
                training_data_path = settings.FINETUNING_FILE_PATH
            _log(f"Mode: Finetuning. Using feedback dataset: {training_data_path}")
        else:
            if training_data_path is None:
                training_data_path = settings.CONCAT_FILE_PATH
            _log(f"Mode: Base Training. Using general corpus: {training_data_path}")

        if (
            not os.path.exists(training_data_path)
            or os.path.getsize(training_data_path) == 0
        ):
            err_msg = f"Error: Training data file not found or is empty: {os.path.basename(training_data_path)}."
            _log(err_msg)
            return err_msg

        _log("Loading data with 🤗 Datasets library...")
        raw_datasets = load_dataset("text", data_files={"train": training_data_path})

        def tokenize_function(examples):
            # --- FIXED: Reference the settings module ---
            return tokenizer(
                examples["text"],
                truncation=True,
                max_length=settings.MAX_SEQUENCE_LENGTH,
            )

        _log("Tokenizing dataset...")
        tokenized_datasets = raw_datasets.map(
            tokenize_function, batched=True, remove_columns=["text"]
        )

        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
        _log(f"Dataset prepared with {len(tokenized_datasets['train'])} examples.")

        # --- FIXED: Reference the settings module ---
        training_args = TrainingArguments(
            output_dir=model_save_path,
            overwrite_output_dir=True,
            num_train_epochs=settings.NUM_EPOCHS,
            per_device_train_batch_size=settings.BATCH_SIZE,
            save_steps=10_000,
            save_total_limit=1,
            logging_steps=10,
            report_to="none",
            ddp_find_unused_parameters=False,
            disable_tqdm=True,
        )

        class ProgressCallbackTrainer(Trainer):
            def _log(self, logs: Dict[str, float]) -> None:
                super()._log(logs)
                if "loss" in logs and self.state.is_local_process_zero:
                    current_step = self.state.global_step
                    total_steps = self.state.max_steps
                    progress_callback(
                        current_step,
                        total_steps,
                        f"Step {current_step}/{total_steps} - Loss: {logs['loss']:.4f}",
                    )

        trainer = ProgressCallbackTrainer(
            model=model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=tokenized_datasets["train"],
        )

        # --- FIXED: Reference the settings module ---
        _log(f"Starting training for {settings.NUM_EPOCHS} epochs...")
        trainer.train()

        _log("Training complete. Saving final model and tokenizer...")
        trainer.save_model(model_save_path)
        tokenizer.save_pretrained(model_save_path)
        _log(f"Model and tokenizer saved to {model_save_path}")

        return "Success"
    except Exception as e:
        import traceback

        _log(f"An error occurred during training: {e}\n{traceback.format_exc()}")
        return f"Error: {e}"
