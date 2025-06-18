"""
continuous_learning.py

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

"""
Continuous Learning Service
Implements state-of-the-art continuous learning for AI Coder Assistant.
Handles data collection, validation, incremental updates, and performance monitoring.
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from collections import deque
import hashlib
import pickle
import sqlite3
from contextlib import contextmanager
import tempfile
import os

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from .models import LLMModel
from .llm_manager import LLMManager
from ..utils import constants
from ..utils.settings import MODEL_SAVE_PATH
from .trainer import train_model

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of user feedback for continuous learning."""
    CORRECTION = "correction"
    IMPROVEMENT = "improvement"
    REJECTION = "rejection"
    APPROVAL = "approval"
    CODE_SAMPLE = "code_sample"
    EXPLANATION_REQUEST = "explanation_request"


class DataQuality(Enum):
    """Data quality levels for validation."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REJECTED = "rejected"


@dataclass
class FeedbackData:
    """Structured feedback data for continuous learning."""
    id: str
    timestamp: datetime
    feedback_type: FeedbackType
    user_id: Optional[str]
    session_id: Optional[str]
    
    # Input data
    original_input: str
    original_output: str
    
    # Feedback data
    corrected_output: Optional[str] = None
    user_rating: Optional[int] = None  # 1-5 scale
    user_comment: Optional[str] = None
    
    # Metadata
    context: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    processing_time_ms: Optional[int] = None
    
    # Quality assessment
    quality_score: Optional[float] = None
    quality_level: Optional[DataQuality] = None
    validation_errors: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['feedback_type'] = self.feedback_type.value
        if self.quality_level:
            data['quality_level'] = self.quality_level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackData':
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data_copy['feedback_type'] = FeedbackType(data['feedback_type'])
        if data.get('quality_level'):
            data_copy['quality_level'] = DataQuality(data['quality_level'])
        return cls(**data_copy)


@dataclass
class ModelUpdate:
    """Model update information."""
    id: str
    timestamp: datetime
    model_version: str
    previous_version: Optional[str]
    
    # Update statistics
    samples_processed: int
    samples_accepted: int
    samples_rejected: int
    quality_threshold: float
    
    # Performance metrics
    pre_update_accuracy: Optional[float] = None
    post_update_accuracy: Optional[float] = None
    performance_change: Optional[float] = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, failed, rolled_back
    error_message: Optional[str] = None
    
    # Rollback
    rollback_performed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ReplayBuffer:
    """Replay buffer for preventing catastrophic forgetting."""
    
    def __init__(self, max_size: int = 10000, min_size: int = 1000):
        self.max_size = max_size
        self.min_size = min_size
        self.buffer: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        
    def add(self, data: FeedbackData) -> None:
        """Add data to replay buffer."""
        with self._lock:
            self.buffer.append(data)
    
    def sample(self, batch_size: int) -> List[FeedbackData]:
        """Sample data from replay buffer."""
        with self._lock:
            if len(self.buffer) < self.min_size:
                return list(self.buffer)
            
            indices = np.random.choice(
                len(self.buffer), 
                size=min(batch_size, len(self.buffer)), 
                replace=False
            )
            return [self.buffer[i] for i in indices]
    
    def get_size(self) -> int:
        """Get current buffer size."""
        with self._lock:
            return len(self.buffer)
    
    def clear(self) -> None:
        """Clear the replay buffer."""
        with self._lock:
            self.buffer.clear()


class DataValidator:
    """Validates and filters feedback data for quality."""
    
    def __init__(self, quality_threshold: float = 0.7):
        self.quality_threshold = quality_threshold
        self.proxy_model: Optional[Any] = None  # Lightweight model for validation
        
    def validate_feedback(self, feedback: FeedbackData) -> Tuple[bool, float, List[str]]:
        """
        Validate feedback data quality.
        
        Returns:
            Tuple of (is_valid, quality_score, validation_errors)
        """
        errors = []
        quality_score = 0.0
        
        # Check input/output length
        if len(feedback.original_input) < 10:
            errors.append("Input too short")
            quality_score -= 0.2
        
        if len(feedback.original_input) > 10000:
            errors.append("Input too long")
            quality_score -= 0.1
        
        # Check for empty or null values
        if not feedback.original_input.strip():
            errors.append("Empty input")
            quality_score -= 0.5
        
        if not feedback.original_output.strip():
            errors.append("Empty output")
            quality_score -= 0.3
        
        # Check user rating if provided
        if feedback.user_rating is not None:
            if not 1 <= feedback.user_rating <= 5:
                errors.append("Invalid user rating")
                quality_score -= 0.2
            elif feedback.user_rating >= 4:
                quality_score += 0.2
            elif feedback.user_rating <= 2:
                quality_score -= 0.2
        
        # Check for duplicate content (basic check)
        if feedback.original_input == feedback.original_output:
            errors.append("Input and output are identical")
            quality_score -= 0.3
        
        # Check for code-like content
        code_indicators = ['def ', 'class ', 'import ', 'from ', 'if __name__', 'return ']
        has_code = any(indicator in feedback.original_input for indicator in code_indicators)
        if has_code:
            quality_score += 0.1
        
        # Normalize quality score to 0-1 range
        quality_score = max(0.0, min(1.0, quality_score + 0.5))
        
        is_valid = quality_score >= self.quality_threshold and len(errors) == 0
        
        return is_valid, quality_score, errors
    
    def update_proxy_model(self, new_data: List[FeedbackData]) -> None:
        """Update proxy model with new data for better validation."""
        # This would implement a lightweight model update
        # For now, we'll use a simple statistical approach
        pass


class ContinuousLearningService:
    """
    Main continuous learning service.
    
    Implements state-of-the-art continuous learning techniques including:
    - Data collection and validation
    - Incremental model updates
    - Catastrophic forgetting prevention
    - Performance monitoring and rollback
    """
    
    def __init__(self, 
                 data_dir: str = "continuous_learning_data",
                 model_manager: Optional[LLMManager] = None,
                 quality_threshold: float = 0.7,
                 replay_buffer_size: int = 10000):
        """
        Initialize continuous learning service.
        
        Args:
            data_dir: Directory for storing continuous learning data
            model_manager: LLM manager for model operations
            quality_threshold: Minimum quality score for data acceptance
            replay_buffer_size: Size of replay buffer for preventing forgetting
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_manager = model_manager
        self.quality_threshold = quality_threshold
        self.replay_buffer = ReplayBuffer(max_size=replay_buffer_size)
        self.validator = DataValidator(quality_threshold)
        
        # Database for persistent storage
        self.db_path = self.data_dir / "continuous_learning.db"
        self._init_database()
        
        # Threading
        self._lock = threading.Lock()
        self._update_in_progress = False
        
        # Statistics
        self.stats = {
            'total_feedback': 0,
            'accepted_feedback': 0,
            'rejected_feedback': 0,
            'model_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'rollbacks': 0
        }
        
        logger.info("Continuous Learning Service initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Create feedback_data table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_data (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        user_id TEXT,
                        session_id TEXT,
                        original_input TEXT NOT NULL,
                        original_output TEXT NOT NULL,
                        corrected_output TEXT,
                        user_rating INTEGER,
                        user_comment TEXT,
                        context TEXT,
                        model_version TEXT,
                        processing_time_ms INTEGER,
                        quality_score REAL,
                        quality_level TEXT,
                        validation_errors TEXT,
                        accepted BOOLEAN NOT NULL DEFAULT 1
                    )
                """)
                
                # Create model_updates table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS model_updates (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        previous_version TEXT,
                        samples_processed INTEGER NOT NULL,
                        samples_accepted INTEGER NOT NULL,
                        samples_rejected INTEGER NOT NULL,
                        quality_threshold REAL NOT NULL,
                        pre_update_accuracy REAL,
                        post_update_accuracy REAL,
                        performance_change REAL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        rollback_performed BOOLEAN NOT NULL DEFAULT 0
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback_data(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_accepted ON feedback_data(accepted)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_quality ON feedback_data(quality_score)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_updates_timestamp ON model_updates(timestamp)")
                
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def collect_feedback(self,
                        feedback_type: FeedbackType,
                        original_input: str,
                        original_output: str,
                        user_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        corrected_output: Optional[str] = None,
                        user_rating: Optional[int] = None,
                        user_comment: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None,
                        model_version: Optional[str] = None,
                        processing_time_ms: Optional[int] = None) -> str:
        """
        Collect and store user feedback.
        
        Args:
            feedback_type: Type of feedback
            original_input: Original user input
            original_output: Original model output
            user_id: Optional user identifier
            session_id: Optional session identifier
            corrected_output: Corrected output if applicable
            user_rating: User rating (1-5 scale)
            user_comment: User comment
            context: Additional context
            model_version: Model version used
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Feedback ID
        """
        feedback_id = self._generate_feedback_id()
        
        feedback = FeedbackData(
            id=feedback_id,
            timestamp=datetime.now(),
            feedback_type=feedback_type,
            user_id=user_id,
            session_id=session_id,
            original_input=original_input,
            original_output=original_output,
            corrected_output=corrected_output,
            user_rating=user_rating,
            user_comment=user_comment,
            context=context,
            model_version=model_version,
            processing_time_ms=processing_time_ms
        )
        
        # Validate feedback
        is_valid, quality_score, validation_errors = self.validator.validate_feedback(feedback)
        
        feedback.quality_score = quality_score
        feedback.quality_level = self._get_quality_level(quality_score)
        feedback.validation_errors = validation_errors if not is_valid else None
        
        # Store feedback
        self._store_feedback(feedback)
        
        # Add to replay buffer if valid
        if is_valid:
            self.replay_buffer.add(feedback)
            self.stats['accepted_feedback'] += 1
            logger.info(f"Feedback {feedback_id} accepted (quality: {quality_score:.3f})")
        else:
            self.stats['rejected_feedback'] += 1
            logger.warning(f"Feedback {feedback_id} rejected: {validation_errors}")
        
        self.stats['total_feedback'] += 1
        
        return feedback_id
    
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID."""
        timestamp = datetime.now().isoformat()
        random_suffix = str(int(time.time() * 1000))[-6:]
        return f"feedback_{timestamp}_{random_suffix}"
    
    def _get_quality_level(self, quality_score: float) -> DataQuality:
        """Convert quality score to quality level."""
        if quality_score >= 0.9:
            return DataQuality.EXCELLENT
        elif quality_score >= 0.8:
            return DataQuality.GOOD
        elif quality_score >= 0.7:
            return DataQuality.ACCEPTABLE
        elif quality_score >= 0.5:
            return DataQuality.POOR
        else:
            return DataQuality.REJECTED
    
    def _store_feedback(self, feedback: FeedbackData) -> None:
        """Store feedback data in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.id,
                feedback.timestamp.isoformat(),
                feedback.feedback_type.value,
                feedback.user_id,
                feedback.session_id,
                feedback.original_input,
                feedback.original_output,
                feedback.corrected_output,
                feedback.user_rating,
                feedback.user_comment,
                json.dumps(feedback.context) if feedback.context else None,
                feedback.model_version,
                feedback.processing_time_ms,
                feedback.quality_score,
                feedback.quality_level.value if feedback.quality_level else None,
                json.dumps(feedback.validation_errors) if feedback.validation_errors else None,
                1  # accepted column
            ))
    
    def get_feedback_stats(self, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get feedback statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Build date filter
            conditions = []
            params = []
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date.isoformat())
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date.isoformat())
            date_filter = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            # Get total counts
            cursor = conn.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN quality_score >= ? THEN 1 ELSE 0 END) as accepted,
                    SUM(CASE WHEN quality_score < ? THEN 1 ELSE 0 END) as rejected
                FROM feedback_data {date_filter}
            """, [self.quality_threshold, self.quality_threshold] + params)
            
            row = cursor.fetchone()
            total, accepted, rejected = row
            
            # Get feedback type distribution
            cursor = conn.execute(f"""
                SELECT feedback_type, COUNT(*) as count
                FROM feedback_data {date_filter}
                GROUP BY feedback_type
            """, params)
            
            type_distribution = dict(cursor.fetchall())
            
            # Get quality distribution
            # Combine date_filter and quality_level IS NOT NULL
            if date_filter:
                quality_where = f"{date_filter} AND quality_level IS NOT NULL"
            else:
                quality_where = "WHERE quality_level IS NOT NULL"
            cursor = conn.execute(f"""
                SELECT quality_level, COUNT(*) as count
                FROM feedback_data {quality_where}
                GROUP BY quality_level
            """, params)
            quality_distribution = dict(cursor.fetchall())
            
            return {
                'total': total or 0,
                'accepted': accepted or 0,
                'rejected': rejected or 0,
                'acceptance_rate': (accepted / total * 100) if total else 0,
                'type_distribution': type_distribution,
                'quality_distribution': quality_distribution,
                'replay_buffer_size': self.replay_buffer.get_size(),
                'model_updates': self.stats['model_updates'],
                'successful_updates': self.stats['successful_updates'],
                'failed_updates': self.stats['failed_updates'],
                'rollbacks': self.stats['rollbacks']
            }
    
    def trigger_model_update(self, batch_size: int = 100, force_update: bool = False) -> Optional[str]:
        """
        Trigger a model update with the collected feedback.
        
        Args:
            batch_size: Number of samples to use for training
            force_update: Whether to force update even if data requirements aren't met
            
        Returns:
            Update ID if successful, None otherwise
        """
        try:
            # Check if update is already in progress
            if self._update_in_progress:
                logger.warning("Model update already in progress")
                return None
            
            # Get valid feedback samples
            valid_samples = self._get_valid_samples(batch_size)
            
            if not valid_samples and not force_update:
                logger.error(f"Insufficient valid samples: {len(valid_samples)}/{batch_size}")
                return None
            
            if not valid_samples and force_update:
                logger.warning("No valid samples available, but forcing update")
                valid_samples = self._get_replay_buffer_samples(batch_size)
                
                # If still no samples, create minimal training data
                if not valid_samples:
                    logger.warning("No replay buffer samples available, creating minimal training data")
                    valid_samples = []
                    for i in range(batch_size):
                        valid_samples.append(FeedbackData(
                            id=f"minimal_sample_{i}",
                            timestamp=datetime.now(),
                            feedback_type=FeedbackType.CORRECTION,
                            user_id="system",
                            session_id="force_update",
                            original_input=f"def test_function_{i}():",
                            original_output=f"def test_function_{i}():\n    pass",
                            corrected_output=f"def test_function_{i}():\n    return True",
                            user_rating=5,
                            quality_score=1.0,
                            quality_level=DataQuality.EXCELLENT
                        ))
            
            if not valid_samples:
                logger.error("No samples available for training")
                return None
            
            # Create update record
            update_id = f"update_{datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}"
            update_record = ModelUpdate(
                id=update_id,
                timestamp=datetime.now(),
                model_version="current",
                previous_version=None,
                samples_processed=len(valid_samples),
                samples_accepted=len(valid_samples),
                samples_rejected=0,
                quality_threshold=self.quality_threshold,
                pre_update_accuracy=None,
                post_update_accuracy=None,
                performance_change=None,
                status="in_progress",
                error_message=None,
                rollback_performed=False
            )
            
            # Save current model state for potential rollback
            current_model_path = MODEL_SAVE_PATH
            backup_path = f"{current_model_path}_backup_{update_id}"
            
            if os.path.exists(current_model_path):
                import shutil
                shutil.copytree(current_model_path, backup_path)
                logger.info(f"Model backup created at: {backup_path}")
            
            # Start update process
            self._update_in_progress = True
            self._save_update_record(update_record)
            
            # Export valid feedback to temporary file
            tmpfile_path = os.path.join(constants.TMP_DIR, f"feedback_{update_id}.txt")
            os.makedirs(os.path.dirname(tmpfile_path), exist_ok=True)
            
            with open(tmpfile_path, 'w', encoding='utf-8') as f:
                for sample in valid_samples:
                    # Format for training: input + output
                    training_text = f"{sample.original_input}\n{sample.original_output}\n"
                    if sample.corrected_output:
                        training_text = f"{sample.original_input}\n{sample.corrected_output}\n"
                    f.write(training_text + "\n")
            
            logger.info(f"Exported {len(valid_samples)} samples to {tmpfile_path}")
            
            # --- INTEGRATION: Call trainer for incremental finetuning ---
            logger.info(f"Performing incremental update with {len(valid_samples)} samples using {tmpfile_path}")
            train_result = train_model(
                vocab_dir=None,  # Not used in finetune mode
                model_save_path=MODEL_SAVE_PATH,
                finetune=True,
                training_data_path=tmpfile_path,
                log_message_callback=logger.info,
                progress_callback=lambda c, t, m: logger.info(f"Progress: {c}/{t} {m}")
            )
            
            # Clean up temporary file
            try:
                os.remove(tmpfile_path)
            except OSError:
                pass
            
            # Evaluate model performance
            performance_change = self._evaluate_model_performance(update_id)
            
            # Check if rollback is needed
            if performance_change is not None and performance_change < -0.1:  # 10% degradation threshold
                logger.warning(f"Performance degradation detected: {performance_change:.3f}. Initiating rollback.")
                self._rollback_model(update_id, backup_path)
                update_record.status = "rolled_back"
                update_record.performance_change = performance_change
                update_record.rollback_performed = True
            else:
                update_record.status = "completed"
                update_record.performance_change = performance_change
                update_record.rollback_performed = False
                
                # Clean up backup if successful
                if os.path.exists(backup_path):
                    import shutil
                    shutil.rmtree(backup_path)
                    logger.info(f"Cleaned up backup: {backup_path}")
            
            self._update_in_progress = False
            self._save_update_record(update_record)
            
            # Update statistics
            self.stats['model_updates'] += 1
            if update_record.status == "completed":
                self.stats['successful_updates'] += 1
            elif update_record.status == "rolled_back":
                self.stats['rollbacks'] += 1
            else:
                self.stats['failed_updates'] += 1
            
            logger.info(f"Model update {update_id} {update_record.status}")
            return update_id
            
        except Exception as e:
            logger.error(f"Model update failed: {e}")
            self._update_in_progress = False
            
            # Update the record with failure status
            if 'update_record' in locals():
                update_record.status = "failed"
                update_record.error_message = str(e)
                self._save_update_record(update_record)
                
                # Update statistics
                self.stats['model_updates'] += 1
                self.stats['failed_updates'] += 1
            
            # Attempt rollback on error
            if 'backup_path' in locals() and os.path.exists(backup_path):
                self._rollback_model(update_id, backup_path)
            
            return None
    
    def _evaluate_model_performance(self, update_id: str) -> Optional[float]:
        """
        Evaluate model performance after update.
        
        Args:
            update_id: ID of the update to evaluate
            
        Returns:
            Performance change (positive = improvement, negative = degradation)
        """
        try:
            # Get recent feedback for evaluation
            recent_feedback = self._get_recent_feedback(days=7)
            
            if not recent_feedback:
                logger.warning("No recent feedback available for evaluation")
                return None
            
            # Calculate average user rating before and after update
            update_time = datetime.now()
            
            before_ratings = [
                f.user_rating for f in recent_feedback 
                if f.timestamp < update_time - timedelta(hours=1) and f.user_rating is not None
            ]
            
            after_ratings = [
                f.user_rating for f in recent_feedback 
                if f.timestamp >= update_time - timedelta(hours=1) and f.user_rating is not None
            ]
            
            if not before_ratings or not after_ratings:
                logger.warning("Insufficient data for performance evaluation")
                return None
            
            before_avg = sum(before_ratings) / len(before_ratings)
            after_avg = sum(after_ratings) / len(after_ratings)
            
            performance_change = after_avg - before_avg
            
            logger.info(f"Performance evaluation: {before_avg:.2f} -> {after_avg:.2f} (change: {performance_change:+.3f})")
            
            return performance_change
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return None
    
    def _rollback_model(self, update_id: str, backup_path: str) -> bool:
        """
        Rollback model to previous state.
        
        Args:
            update_id: ID of the update being rolled back
            backup_path: Path to the backup model
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            current_model_path = MODEL_SAVE_PATH
            
            # Remove current model
            if os.path.exists(current_model_path):
                import shutil
                shutil.rmtree(current_model_path)
            
            # Restore from backup
            import shutil
            shutil.copytree(backup_path, current_model_path)
            
            logger.info(f"Model rolled back successfully from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error during model rollback: {e}")
            return False
    
    def _get_recent_feedback(self, days: int = 7) -> List[FeedbackData]:
        """Get recent feedback within specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, feedback_type, original_input, original_output,
                           corrected_output, user_rating, user_comment, quality_score,
                           accepted, validation_errors
                    FROM feedback_data
                    WHERE timestamp >= ? AND accepted = 1
                    ORDER BY timestamp DESC
                """, (cutoff_date.isoformat(),))
                
                rows = cursor.fetchall()
                return [self._row_to_feedback(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting recent feedback: {e}")
            return []
    
    def _get_valid_samples(self, batch_size: int) -> List[FeedbackData]:
        """Get valid feedback samples for training."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, feedback_type, original_input, original_output,
                           corrected_output, user_rating, user_comment, quality_score,
                           accepted, validation_errors
                    FROM feedback_data
                    WHERE accepted = 1 AND quality_score >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (self.quality_threshold, batch_size))
                
                rows = cursor.fetchall()
                return [self._row_to_feedback(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting valid samples: {e}")
            return []
    
    def _get_replay_buffer_samples(self, batch_size: int) -> List[FeedbackData]:
        """Get samples from replay buffer."""
        try:
            return self.replay_buffer.sample(batch_size)
        except Exception as e:
            logger.error(f"Error getting replay buffer samples: {e}")
            return []
    
    def _row_to_feedback(self, row: tuple) -> FeedbackData:
        """Convert database row to FeedbackData object."""
        return FeedbackData(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            feedback_type=FeedbackType(row[2]),
            user_id="",  # Not stored in current schema
            session_id="",  # Not stored in current schema
            original_input=row[3],
            original_output=row[4],
            corrected_output=row[5],
            user_rating=row[6],
            user_comment=row[7],
            context=None,  # Not stored in current schema
            model_version="",  # Not stored in current schema
            processing_time_ms=0,  # Not stored in current schema
            quality_score=row[8],
            quality_level=DataQuality.EXCELLENT if row[8] and row[8] >= 0.8 else DataQuality.GOOD if row[8] and row[8] >= 0.6 else DataQuality.ACCEPTABLE,
            validation_errors=json.loads(row[10]) if row[10] else None
        )
    
    def _save_update_record(self, update_record: ModelUpdate) -> None:
        """Save model update record to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO model_updates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                update_record.id,
                update_record.timestamp.isoformat(),
                update_record.model_version,
                update_record.previous_version,
                update_record.samples_processed,
                update_record.samples_accepted,
                update_record.samples_rejected,
                update_record.quality_threshold,
                update_record.pre_update_accuracy,
                update_record.post_update_accuracy,
                update_record.performance_change,
                update_record.status,
                update_record.error_message,
                update_record.rollback_performed
            ))
    
    def get_update_history(self, limit: int = 10) -> List[ModelUpdate]:
        """Get recent model update history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, model_version, previous_version, samples_processed,
                           samples_accepted, samples_rejected, quality_threshold,
                           pre_update_accuracy, post_update_accuracy, performance_change,
                           status, error_message, rollback_performed
                    FROM model_updates
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                updates = []
                for row in rows:
                    update = ModelUpdate(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        model_version=row[2],
                        previous_version=row[3],
                        samples_processed=row[4],
                        samples_accepted=row[5],
                        samples_rejected=row[6],
                        quality_threshold=row[7],
                        pre_update_accuracy=row[8],
                        post_update_accuracy=row[9],
                        performance_change=row[10],
                        status=row[11],
                        error_message=row[12],
                        rollback_performed=bool(row[13])
                    )
                    updates.append(update)
                
                return updates
                
        except Exception as e:
            logger.error(f"Error getting update history: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old feedback data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM feedback_data 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old feedback records")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def export_data(self, output_path: str, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> None:
        """Export feedback data to JSON file."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build date filter
                date_filter = ""
                params = []
                if start_date or end_date:
                    conditions = []
                    if start_date:
                        conditions.append("timestamp >= ?")
                        params.append(start_date.isoformat())
                    if end_date:
                        conditions.append("timestamp <= ?")
                        params.append(end_date.isoformat())
                    date_filter = f"WHERE {' AND '.join(conditions)}"
                
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT id, timestamp, feedback_type, original_input, original_output,
                           corrected_output, user_rating, user_comment, quality_score,
                           validation_errors
                    FROM feedback_data {date_filter}
                    ORDER BY timestamp DESC
                """, params)
                
                data = []
                for row in cursor.fetchall():
                    feedback = FeedbackData(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        feedback_type=FeedbackType(row[2]),
                        user_id="",  # Not stored in current schema
                        session_id="",  # Not stored in current schema
                        original_input=row[3],
                        original_output=row[4],
                        corrected_output=row[5],
                        user_rating=row[6],
                        user_comment=row[7],
                        context=None,  # Not stored in current schema
                        model_version="",  # Not stored in current schema
                        processing_time_ms=0,  # Not stored in current schema
                        quality_score=row[8],
                        quality_level=DataQuality.EXCELLENT if row[8] and row[8] >= 0.8 else DataQuality.GOOD if row[8] and row[8] >= 0.6 else DataQuality.ACCEPTABLE,
                        validation_errors=json.loads(row[9]) if row[9] else None
                    )
                    data.append(feedback.to_dict())
                
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Exported {len(data)} feedback records to {output_path}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise


# Global instance for easy access
_continuous_learning_service: Optional[ContinuousLearningService] = None


def get_continuous_learning_service() -> ContinuousLearningService:
    """Get or create global continuous learning service instance."""
    global _continuous_learning_service
    if _continuous_learning_service is None:
        _continuous_learning_service = ContinuousLearningService()
    return _continuous_learning_service 