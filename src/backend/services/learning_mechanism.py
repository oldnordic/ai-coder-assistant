"""
Learning Mechanism - Continuous Model Improvement

This module implements a learning mechanism that processes feedback data
from the feedback loop system to continuously improve the AI coding models.
"""

import asyncio
import logging
import json
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import numpy as np
from collections import defaultdict

from src.backend.utils.exceptions import (
    AICoderAssistantError,
    LearningError,
    ModelError,
)
from src.backend.utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class LearningExample:
    """Represents a learning example for model training."""
    example_id: str
    original_code: str
    modified_code: str
    feedback_score: float
    test_results: Dict[str, Any]
    language: str
    issue_type: str
    timestamp: datetime
    applied: bool


@dataclass
class ModelPerformance:
    """Represents model performance metrics."""
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    improvement_rate: float
    total_examples: int
    successful_fixes: int
    timestamp: datetime


class LearningMechanism:
    """
    Learning mechanism for continuous model improvement.
    
    This system:
    1. Processes feedback data from the feedback loop
    2. Creates learning examples for model training
    3. Tracks model performance over time
    4. Provides insights for model improvement
    5. Manages training data and model versions
    """
    
    def __init__(self):
        """Initialize the learning mechanism."""
        self.config = get_config()
        self.learning_examples: List[LearningExample] = []
        self.model_performance: List[ModelPerformance] = []
        self.current_model_id = "base_model"
        
        # Learning parameters
        self.min_feedback_score = 0.3
        self.max_examples_per_type = 1000
        self.performance_window_days = 30
        
        # Data storage paths
        self.data_dir = Path("data/learning")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_learning_data()
        
        logger.info("Learning mechanism initialized")
    
    def _load_learning_data(self):
        """Load existing learning data from files."""
        try:
            # Load learning examples
            examples_file = self.data_dir / "learning_examples.json"
            if examples_file.exists():
                with open(examples_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                        self.learning_examples.append(LearningExample(**item))
            
            # Load model performance
            performance_file = self.data_dir / "model_performance.json"
            if performance_file.exists():
                with open(performance_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                        self.model_performance.append(ModelPerformance(**item))
            
            logger.info(f"Loaded {len(self.learning_examples)} learning examples and {len(self.model_performance)} performance records")
            
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
    
    async def process_feedback_data(self, feedback_data: List[Dict[str, Any]]) -> int:
        """
        Process feedback data and create learning examples.
        
        Args:
            feedback_data: List of feedback data from the feedback loop
            
        Returns:
            Number of learning examples created
        """
        created_examples = 0
        
        try:
            for feedback in feedback_data:
                # Extract test result
                test_result = feedback.get("test_result", {})
                
                # Check if feedback score meets minimum threshold
                feedback_score = feedback.get("improvement_score", 0.0)
                if feedback_score < self.min_feedback_score:
                    continue
                
                # Create learning example
                example = LearningExample(
                    example_id=f"example_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    original_code=test_result.get("original_code", ""),
                    modified_code=test_result.get("modified_code", ""),
                    feedback_score=feedback_score,
                    test_results=test_result,
                    language=self._detect_language(test_result.get("file_path", "")),
                    issue_type=self._classify_issue_type(test_result),
                    timestamp=datetime.now(),
                    applied=feedback.get("applied", False)
                )
                
                # Add to learning examples
                self.learning_examples.append(example)
                created_examples += 1
            
            # Save updated data
            await self._save_learning_data()
            
            logger.info(f"Created {created_examples} learning examples from feedback data")
            
        except Exception as e:
            logger.error(f"Error processing feedback data: {e}")
            raise LearningError(f"Failed to process feedback data: {e}")
        
        return created_examples
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        if not file_path:
            return "unknown"
        
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby"
        }
        
        return language_map.get(ext, "unknown")
    
    def _classify_issue_type(self, test_result: Dict[str, Any]) -> str:
        """Classify the type of issue based on test results."""
        test_error = test_result.get("test_error", "")
        test_output = test_result.get("test_output", "")
        
        # Simple classification based on error patterns
        if "syntax" in test_error.lower() or "SyntaxError" in test_error:
            return "syntax_error"
        elif "indent" in test_error.lower() or "IndentationError" in test_error:
            return "indentation_error"
        elif "import" in test_error.lower() or "ImportError" in test_error:
            return "import_error"
        elif "name" in test_error.lower() or "NameError" in test_error:
            return "name_error"
        elif "type" in test_error.lower() or "TypeError" in test_error:
            return "type_error"
        elif "attribute" in test_error.lower() or "AttributeError" in test_error:
            return "attribute_error"
        else:
            return "general_error"
    
    async def update_model_performance(self, model_id: str, test_results: List[Dict[str, Any]]):
        """
        Update model performance metrics based on test results.
        
        Args:
            model_id: ID of the model being evaluated
            test_results: List of test results
        """
        try:
            if not test_results:
                return
            
            # Calculate metrics
            total_tests = len(test_results)
            successful_tests = sum(1 for result in test_results if result.get("success", False))
            
            # Calculate accuracy
            accuracy = successful_tests / total_tests if total_tests > 0 else 0.0
            
            # Calculate precision, recall, and F1 score
            true_positives = successful_tests
            false_positives = 0  # TODO: Implement more sophisticated metrics
            false_negatives = 0
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            # Calculate improvement rate
            improvement_rate = self._calculate_improvement_rate(model_id)
            
            # Create performance record
            performance = ModelPerformance(
                model_id=model_id,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                improvement_rate=improvement_rate,
                total_examples=total_tests,
                successful_fixes=successful_tests,
                timestamp=datetime.now()
            )
            
            self.model_performance.append(performance)
            
            # Save updated data
            await self._save_learning_data()
            
            logger.info(f"Updated performance for model {model_id}: accuracy={accuracy:.3f}, f1={f1_score:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating model performance: {e}")
            raise LearningError(f"Failed to update model performance: {e}")
    
    def _calculate_improvement_rate(self, model_id: str) -> float:
        """Calculate improvement rate based on historical performance."""
        try:
            # Get recent performance records for this model
            cutoff_date = datetime.now() - timedelta(days=self.performance_window_days)
            recent_performance = [
                p for p in self.model_performance 
                if p.model_id == model_id and p.timestamp > cutoff_date
            ]
            
            if len(recent_performance) < 2:
                return 0.0
            
            # Sort by timestamp
            recent_performance.sort(key=lambda x: x.timestamp)
            
            # Calculate improvement rate
            first_accuracy = recent_performance[0].accuracy
            last_accuracy = recent_performance[-1].accuracy
            
            if first_accuracy > 0:
                improvement_rate = (last_accuracy - first_accuracy) / first_accuracy
            else:
                improvement_rate = 0.0
            
            return improvement_rate
            
        except Exception as e:
            logger.error(f"Error calculating improvement rate: {e}")
            return 0.0
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        try:
            total_examples = len(self.learning_examples)
            
            if total_examples == 0:
                return {"total_examples": 0}
            
            # Calculate average feedback score
            avg_feedback_score = sum(ex.feedback_score for ex in self.learning_examples) / total_examples
            
            # Count by language
            language_counts = defaultdict(int)
            for example in self.learning_examples:
                language_counts[example.language] += 1
            
            # Count by issue type
            issue_type_counts = defaultdict(int)
            for example in self.learning_examples:
                issue_type_counts[example.issue_type] += 1
            
            # Calculate success rate
            successful_examples = sum(1 for ex in self.learning_examples if ex.applied)
            success_rate = successful_examples / total_examples if total_examples > 0 else 0.0
            
            # Get recent performance
            recent_performance = self._get_recent_performance()
            
            return {
                "total_examples": total_examples,
                "average_feedback_score": avg_feedback_score,
                "success_rate": success_rate,
                "language_distribution": dict(language_counts),
                "issue_type_distribution": dict(issue_type_counts),
                "recent_performance": recent_performance
            }
            
        except Exception as e:
            logger.error(f"Error getting learning statistics: {e}")
            return {"error": str(e)}
    
    def _get_recent_performance(self) -> Dict[str, Any]:
        """Get recent model performance data."""
        try:
            if not self.model_performance:
                return {}
            
            # Get most recent performance for each model
            latest_performance = {}
            for performance in self.model_performance:
                if (performance.model_id not in latest_performance or 
                    performance.timestamp > latest_performance[performance.model_id].timestamp):
                    latest_performance[performance.model_id] = performance
            
            # Convert to serializable format
            return {
                model_id: {
                    "accuracy": perf.accuracy,
                    "f1_score": perf.f1_score,
                    "improvement_rate": perf.improvement_rate,
                    "total_examples": perf.total_examples,
                    "timestamp": perf.timestamp.isoformat()
                }
                for model_id, perf in latest_performance.items()
            }
            
        except Exception as e:
            logger.error(f"Error getting recent performance: {e}")
            return {}
    
    def get_training_data(self, language: Optional[str] = None, issue_type: Optional[str] = None) -> List[LearningExample]:
        """
        Get training data filtered by language and issue type.
        
        Args:
            language: Filter by programming language
            issue_type: Filter by issue type
            
        Returns:
            List of learning examples
        """
        filtered_examples = self.learning_examples
        
        if language:
            filtered_examples = [ex for ex in filtered_examples if ex.language == language]
        
        if issue_type:
            filtered_examples = [ex for ex in filtered_examples if ex.issue_type == issue_type]
        
        # Limit examples per type to prevent overfitting
        if issue_type:
            filtered_examples = filtered_examples[:self.max_examples_per_type]
        
        return filtered_examples
    
    async def _save_learning_data(self):
        """Save learning data to files."""
        try:
            # Save learning examples
            examples_file = self.data_dir / "learning_examples.json"
            serializable_examples = [asdict(ex) for ex in self.learning_examples]
            for ex in serializable_examples:
                ex["timestamp"] = ex["timestamp"].isoformat()
            
            with open(examples_file, 'w') as f:
                json.dump(serializable_examples, f, indent=2)
            
            # Save model performance
            performance_file = self.data_dir / "model_performance.json"
            serializable_performance = [asdict(perf) for perf in self.model_performance]
            for perf in serializable_performance:
                perf["timestamp"] = perf["timestamp"].isoformat()
            
            with open(performance_file, 'w') as f:
                json.dump(serializable_performance, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
            raise LearningError(f"Failed to save learning data: {e}")
    
    def export_learning_data(self, file_path: str):
        """Export learning data to file."""
        try:
            data = {
                "learning_examples": [asdict(ex) for ex in self.learning_examples],
                "model_performance": [asdict(perf) for perf in self.model_performance],
                "statistics": self.get_learning_statistics()
            }
            
            # Convert timestamps to strings
            for ex in data["learning_examples"]:
                ex["timestamp"] = ex["timestamp"].isoformat()
            for perf in data["model_performance"]:
                perf["timestamp"] = perf["timestamp"].isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Learning data exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting learning data: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old learning data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Remove old learning examples
            original_count = len(self.learning_examples)
            self.learning_examples = [
                ex for ex in self.learning_examples 
                if ex.timestamp > cutoff_date
            ]
            removed_examples = original_count - len(self.learning_examples)
            
            # Remove old performance records
            original_perf_count = len(self.model_performance)
            self.model_performance = [
                perf for perf in self.model_performance 
                if perf.timestamp > cutoff_date
            ]
            removed_perf = original_perf_count - len(self.model_performance)
            
            # Save updated data
            asyncio.create_task(self._save_learning_data())
            
            logger.info(f"Cleaned up {removed_examples} old examples and {removed_perf} old performance records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    def should_trigger_finetune(self, min_examples: int = 100) -> bool:
        """Return True if enough learning examples are collected for fine-tuning."""
        return len(self.learning_examples) >= min_examples

    def get_finetune_status(self, min_examples: int = 100) -> Dict[str, Any]:
        """Get fine-tuning status and requirements."""
        total_examples = len(self.learning_examples)
        ready = total_examples >= min_examples
        
        return {
            "ready": ready,
            "total_examples": total_examples,
            "min_required": min_examples,
            "examples_needed": max(0, min_examples - total_examples)
        }

    # Additional methods for UI integration

    def get_total_examples(self) -> int:
        """Get total number of learning examples."""
        return len(self.learning_examples)

    def get_successful_examples(self) -> int:
        """Get number of successful learning examples."""
        return len([ex for ex in self.learning_examples if ex.applied and ex.feedback_score >= 0.7])

    def get_failed_examples(self) -> int:
        """Get number of failed learning examples."""
        return len([ex for ex in self.learning_examples if not ex.applied or ex.feedback_score < 0.3])

    def get_success_rate(self) -> float:
        """Get success rate of learning examples."""
        total = len(self.learning_examples)
        if total == 0:
            return 0.0
        successful = self.get_successful_examples()
        return successful / total

    def get_last_session_time(self) -> Optional[datetime]:
        """Get timestamp of the last learning session."""
        if not self.learning_examples:
            return None
        return max(ex.timestamp for ex in self.learning_examples)

    def get_model_performance(self) -> Dict[str, Any]:
        """Get current model performance metrics."""
        if not self.model_performance:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "improvement_rate": 0.0
            }
        
        # Get the most recent performance record
        latest = max(self.model_performance, key=lambda x: x.timestamp)
        return {
            "accuracy": latest.accuracy,
            "precision": latest.precision,
            "recall": latest.recall,
            "f1_score": latest.f1_score,
            "improvement_rate": latest.improvement_rate
        }

    def get_last_finetune_time(self) -> Optional[datetime]:
        """Get timestamp of the last fine-tuning session."""
        # This would typically be stored separately, but for now we'll use the latest model performance
        if not self.model_performance:
            return None
        return max(perf.timestamp for perf in self.model_performance) 