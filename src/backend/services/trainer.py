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
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GPT2LMHeadModel,
    GPT2Tokenizer,
)
from transformers.data.data_collator import DataCollatorForLanguageModeling
from transformers.trainer import Trainer
from transformers.training_args import TrainingArguments
from transformers.utils.quantization_config import BitsAndBytesConfig
from transformers.trainer_callback import TrainerCallback
from peft import LoraConfig, get_peft_model, TaskType

# --- FIXED: Import the new settings module from the config package ---
from src.backend.utils import settings
from src.backend.utils.constants import PROGRESS_MAX, PROGRESS_MIN

logger = logging.getLogger(__name__)


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


def fine_tune_code_model(
    dataset_path: str, 
    base_model: str = "microsoft/DialoGPT-medium",
    output_model_name: str = "code-reviewer",
    **kwargs
) -> str:
    """
    Fine-tune a model specifically for code review and analysis tasks.
    
    This function implements the model specialization workflow for creating
    custom-trained local models for code analysis.
    
    Args:
        dataset_path: Path to the training dataset (JSON format with code examples)
        base_model: Base model to fine-tune (default: microsoft/DialoGPT-medium)
        output_model_name: Name for the output fine-tuned model
        **kwargs: Additional training parameters
        
    Returns:
        "Success" if training completed successfully, error message otherwise
    """
    log_message_callback = kwargs.get("log_message_callback", print)
    progress_callback = kwargs.get("progress_callback", lambda c, t, m: None)
    _log = log_message_callback
    
    try:
        _log(f"Starting code model fine-tuning with base model: {base_model}")
        progress_callback(PROGRESS_MIN, PROGRESS_MAX, "Initializing fine-tuning...")
        
        # Get best device
        device = get_best_device(_log)
        
        # Load and prepare dataset
        _log("Loading code review dataset...")
        if not os.path.exists(dataset_path):
            return f"Error: Dataset file not found: {dataset_path}"
        
        # Load dataset from JSON file
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset_data = json.load(f)
        
        # Prepare training data
        training_texts = []
        for item in dataset_data:
            # Format: "Code: {code}\nIssue: {issue}\nAnalysis: {analysis}\nSuggestion: {suggestion}"
            text = f"Code: {item.get('code', '')}\n"
            text += f"Issue: {item.get('issue', '')}\n"
            text += f"Analysis: {item.get('analysis', '')}\n"
            text += f"Suggestion: {item.get('suggestion', '')}\n"
            text += f"<|endoftext|>\n"
            training_texts.append({"text": text})
        
        _log(f"Prepared {len(training_texts)} training examples")
        
        # Create dataset
        dataset = Dataset.from_list(training_texts)
        
        # Load tokenizer and model
        _log("Loading tokenizer and model...")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with quantization for memory efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Configure LoRA for efficient fine-tuning
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=8,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
        )
        
        # Apply LoRA
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        # Tokenize dataset
        _log("Tokenizing dataset...")
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,
                padding="max_length"
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function, 
            batched=True, 
            remove_columns=["text"]
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer, 
            mlm=False
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=f"models/{output_model_name}",
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=10,
            save_steps=500,
            save_total_limit=2,
            report_to="none",
            remove_unused_columns=False,
        )
        
        # Custom callback for progress
        class ProgressCallback(TrainerCallback):
            def __init__(self, progress_callback, log_callback):
                self.progress_callback = progress_callback
                self.log_callback = log_callback
                
            def on_step_end(self, args, state, control, **kwargs):
                if state.global_step % 10 == 0:
                    progress = (state.global_step / state.max_steps) * 100
                    self.progress_callback(
                        int(progress), 
                        100, 
                        f"Step {state.global_step}/{state.max_steps}"
                    )
        
        # Initialize trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            callbacks=[ProgressCallback(progress_callback, _log)]
        )
        
        # Start training
        _log("Starting fine-tuning...")
        trainer.train()
        
        # Save the fine-tuned model
        output_path = f"models/{output_model_name}"
        trainer.save_model(output_path)
        tokenizer.save_pretrained(output_path)
        
        # Save model metadata
        metadata = {
            "model_name": output_model_name,
            "base_model": base_model,
            "fine_tuned_for": "code_review",
            "training_examples": len(training_texts),
            "training_epochs": 3,
            "lora_config": lora_config.to_dict()
        }
        
        with open(f"{output_path}/model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        _log(f"Fine-tuning completed successfully. Model saved to: {output_path}")
        return "Success"
        
    except Exception as e:
        import traceback
        error_msg = f"Error during fine-tuning: {e}\n{traceback.format_exc()}"
        _log(error_msg)
        return f"Error: {e}"


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
