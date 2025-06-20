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
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import time

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


def get_best_device(log_callback: Callable[[str], None]) -> torch.device:
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


def create_code_review_dataset(
    code_examples: List[Dict[str, str]], 
    output_path: str,
    log_callback: Optional[Callable[[str], None]] = None
) -> str:
    """
    Create a training dataset for code review tasks.
    
    Args:
        code_examples: List of dictionaries with 'code', 'issue', 'analysis', 'suggestion' keys
        output_path: Path to save the dataset
        log_callback: Optional callback for logging
        
    Returns:
        Path to the created dataset
    """
    _log: Callable[[str], None] = log_callback or print
    
    try:
        _log(f"Creating code review dataset with {len(code_examples)} examples...")
        
        # Format examples for training
        training_data: List[Dict[str, str]] = []
        for example in code_examples:
            # Create structured prompt-response pairs
            prompt = f"""Code: {example.get('code', '')}
Issue: {example.get('issue', '')}"""
            
            response = f"""Analysis: {example.get('analysis', '')}
Suggestion: {example.get('suggestion', '')}
<|endoftext|>"""
            
            training_data.append({
                "prompt": prompt,
                "response": response,
                "full_text": prompt + "\n" + response
            })
        
        # Save dataset
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        _log(f"Dataset saved to: {output_path}")
        return output_path
        
    except Exception as e:
        error_msg = f"Failed to create dataset: {e}"
        _log(error_msg)
        raise Exception(error_msg)


def fine_tune_code_model(
    dataset_path: str, 
    base_model: str = "microsoft/DialoGPT-medium",
    output_model_name: str = "code-reviewer",
    **kwargs: Any
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
    log_message_callback: Callable[[str], None] = kwargs.get("log_message_callback", print)
    progress_callback: Callable[[int, int, str], None] = kwargs.get("progress_callback", lambda c, t, m: None)
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
        
        # Prepare training data - support both old and new formats
        training_texts: List[Dict[str, str]] = []
        for item in dataset_data:
            if isinstance(item, dict):
                if 'full_text' in item:
                    # New format with structured prompt-response
                    text = item['full_text']
                else:
                    # Old format - convert to new format
                    text = f"Code: {item.get('code', '')}\n"
                    text += f"Issue: {item.get('issue', '')}\n"
                    text += f"Analysis: {item.get('analysis', '')}\n"
                    text += f"Suggestion: {item.get('suggestion', '')}\n"
                    text += f"<|endoftext|>\n"
            else:
                # Fallback for string format
                text = str(item) + "\n<|endoftext|>\n"
            
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
        def tokenize_function(examples: Dict[str, Any]) -> Dict[str, Any]:
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
            num_train_epochs=kwargs.get('epochs', 3),
            per_device_train_batch_size=kwargs.get('batch_size', 4),
            gradient_accumulation_steps=4,
            warmup_steps=100,
            learning_rate=kwargs.get('learning_rate', 2e-4),
            fp16=True,
            logging_steps=10,
            save_steps=500,
            save_total_limit=2,
            report_to="none",
            remove_unused_columns=False,
        )
        
        # Custom callback for progress
        class ProgressCallback(TrainerCallback):
            def __init__(self, progress_callback: Callable[[int, int, str], None], log_callback: Callable[[str], None]):
                self.progress_callback = progress_callback
                self.log_callback = log_callback
                self.start_time = time.time()
            
            def on_step_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
                if state.global_step % 10 == 0:  # Update every 10 steps
                    elapsed = time.time() - self.start_time
                    progress = min(state.global_step / args.max_steps, 1.0) if args.max_steps else 0.5
                    current = int(progress * PROGRESS_MAX)
                    
                    message = f"Training step {state.global_step}, Loss: {state.log_history[-1].get('loss', 'N/A'):.4f}"
                    self.progress_callback(current, PROGRESS_MAX, message)
                    self.log_callback(message)
        
        # Initialize trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            callbacks=[ProgressCallback(progress_callback, _log)]
        )
        
        # Start training
        _log("Starting training...")
        progress_callback(PROGRESS_MIN + 10, PROGRESS_MAX, "Training in progress...")
        
        trainer.train()
        
        # Save the model
        _log("Saving fine-tuned model...")
        progress_callback(PROGRESS_MAX - 20, PROGRESS_MAX, "Saving model...")
        
        # Save to models directory
        model_save_path = f"models/{output_model_name}"
        trainer.save_model(model_save_path)
        tokenizer.save_pretrained(model_save_path)
        
        # Create model info file
        model_info = {
            "model_name": output_model_name,
            "base_model": base_model,
            "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "dataset_size": len(training_texts),
            "training_parameters": {
                "epochs": kwargs.get('epochs', 3),
                "batch_size": kwargs.get('batch_size', 4),
                "learning_rate": kwargs.get('learning_rate', 2e-4)
            }
        }
        
        with open(f"{model_save_path}/model_info.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        _log(f"Fine-tuned model saved to: {model_save_path}")
        progress_callback(PROGRESS_MAX, PROGRESS_MAX, "Training completed successfully!")
        
        return "Success"
        
    except Exception as e:
        error_msg = f"Fine-tuning failed: {e}"
        _log(error_msg)
        return error_msg


def collect_training_data_from_refactoring(
    refactoring_history: List[Dict[str, Any]],
    output_path: str,
    log_callback: Optional[Callable[[str], None]] = None
) -> str:
    """
    Collect training data from refactoring history.
    
    Args:
        refactoring_history: List of refactoring operations with before/after code
        output_path: Path to save the training data
        log_callback: Optional callback for logging
        
    Returns:
        Path to the created training data file
    """
    _log: Callable[[str], None] = log_callback or print
    
    try:
        _log(f"Collecting training data from {len(refactoring_history)} refactoring operations...")
        
        training_examples: List[Dict[str, str]] = []
        for refactoring in refactoring_history:
            # Extract code before and after refactoring
            original_code = refactoring.get('original_code', '')
            refactored_code = refactoring.get('refactored_code', '')
            description = refactoring.get('description', '')
            
            if original_code and refactored_code:
                # Create training example
                example = {
                    "code": original_code,
                    "issue": f"Code needs refactoring: {description}",
                    "analysis": f"This code was refactored to improve {description.lower()}",
                    "suggestion": f"Refactored version:\n{refactored_code}"
                }
                training_examples.append(example)
        
        # Save training data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_examples, f, indent=2, ensure_ascii=False)
        
        _log(f"Training data saved to: {output_path}")
        return output_path
        
    except Exception as e:
        error_msg = f"Failed to collect training data: {e}"
        _log(error_msg)
        raise Exception(error_msg)


def evaluate_model_performance(
    model_path: str,
    test_dataset_path: str,
    log_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Evaluate the performance of a fine-tuned model.
    
    Args:
        model_path: Path to the fine-tuned model
        test_dataset_path: Path to test dataset
        log_callback: Optional callback for logging
        
    Returns:
        Dictionary with evaluation metrics
    """
    _log: Callable[[str], None] = log_callback or print
    
    try:
        _log(f"Evaluating model: {model_path}")
        
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        
        # Load test dataset
        with open(test_dataset_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Simple evaluation metrics
        total_examples = len(test_data)
        correct_predictions = 0
        
        for example in test_data[:10]:  # Evaluate first 10 examples
            # Generate response
            input_text = example.get('prompt', '')
            expected_response = example.get('response', '')
            
            inputs = tokenizer(input_text, return_tensors="pt")
            outputs = model.generate(
                **inputs,
                max_length=len(inputs['input_ids'][0]) + 100,
                temperature=0.7,
                do_sample=True
            )
            
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Simple accuracy check (can be improved)
            if expected_response.lower() in generated_text.lower():
                correct_predictions += 1
        
        accuracy = correct_predictions / min(10, total_examples)
        
        evaluation_results = {
            "model_path": model_path,
            "total_test_examples": total_examples,
            "evaluated_examples": min(10, total_examples),
            "accuracy": accuracy,
            "correct_predictions": correct_predictions
        }
        
        _log(f"Evaluation complete. Accuracy: {accuracy:.2%}")
        return evaluation_results
        
    except Exception as e:
        error_msg = f"Model evaluation failed: {e}"
        _log(error_msg)
        return {"error": error_msg}


def train_model(
    vocab_dir: str, 
    model_save_path: str, 
    finetune: bool = False, 
    training_data_path: Optional[str] = None, 
    **kwargs: Any
) -> str:
    """
    Legacy training function - kept for compatibility.
    """
    log_message_callback: Callable[[str], None] = kwargs.get("log_message_callback", print)
    progress_callback: Callable[[int, int, str], None] = kwargs.get("progress_callback", lambda c, t, m: None)
    _log = log_message_callback
    
    try:
        _log("Starting model training...")
        progress_callback(PROGRESS_MIN, PROGRESS_MAX, "Initializing training...")
        
        # Get best device
        device = get_best_device(_log)
        
        # Load training data
        if training_data_path and os.path.exists(training_data_path):
            _log(f"Loading training data from: {training_data_path}")
            with open(training_data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
        else:
            _log("No training data provided, using default dataset")
            training_data = [
                {"text": "Sample training text 1\n<|endoftext|>\n"},
                {"text": "Sample training text 2\n<|endoftext|>\n"}
            ]
        
        # Create dataset
        dataset = Dataset.from_list(training_data)
        
        # Load tokenizer and model
        _log("Loading tokenizer and model...")
        tokenizer = GPT2Tokenizer.from_pretrained(vocab_dir)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = GPT2LMHeadModel.from_pretrained(vocab_dir)
        model.to(device)
        
        # Tokenize dataset
        _log("Tokenizing dataset...")
        def tokenize_function(examples: Dict[str, Any]) -> Dict[str, Any]:
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
            output_dir=model_save_path,
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            learning_rate=5e-5,
            fp16=True,
            logging_steps=10,
            save_steps=500,
            save_total_limit=2,
            report_to="none",
            remove_unused_columns=False,
        )
        
        # Custom callback for progress
        class ProgressCallbackTrainer(Trainer):
            def _log(self, logs: Dict[str, float]) -> None:
                if self.state.global_step % 10 == 0:
                    elapsed = time.time() - self.state.epoch
                    progress = min(self.state.global_step / self.args.max_steps, 1.0) if self.args.max_steps else 0.5
                    current = int(progress * PROGRESS_MAX)
                    
                    message = f"Training step {self.state.global_step}, Loss: {logs.get('loss', 'N/A'):.4f}"
                    progress_callback(current, PROGRESS_MAX, message)
                    _log(message)
        
        # Initialize trainer
        trainer = ProgressCallbackTrainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator
        )
        
        # Start training
        _log("Starting training...")
        progress_callback(PROGRESS_MIN + 10, PROGRESS_MAX, "Training in progress...")
        
        trainer.train()
        
        # Save the model
        _log("Saving model...")
        progress_callback(PROGRESS_MAX - 20, PROGRESS_MAX, "Saving model...")
        
        trainer.save_model(model_save_path)
        tokenizer.save_pretrained(model_save_path)
        
        _log(f"Model saved to: {model_save_path}")
        progress_callback(PROGRESS_MAX, PROGRESS_MAX, "Training completed successfully!")
        
        return "Success"
        
    except Exception as e:
        error_msg = f"Training failed: {e}"
        _log(error_msg)
        return error_msg
