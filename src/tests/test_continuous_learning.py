"""
test_continuous_learning.py

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
Unit tests for continuous learning service.
Comprehensive test coverage for all continuous learning functionality.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sqlite3

import numpy as np

from backend.services.continuous_learning import (
    ContinuousLearningService,
    FeedbackData,
    FeedbackType,
    DataQuality,
    ReplayBuffer,
    DataValidator,
    ModelUpdate
)
from backend.utils.constants import (
    CONTINUOUS_LEARNING_DB_PATH, CONTINUOUS_LEARNING_MIN_INPUT_LENGTH,
    CONTINUOUS_LEARNING_MIN_OUTPUT_LENGTH, CONTINUOUS_LEARNING_MAX_INPUT_LENGTH, CONTINUOUS_LEARNING_MAX_OUTPUT_LENGTH,
    CONTINUOUS_LEARNING_REPLAY_BUFFER_SIZE, CONTINUOUS_LEARNING_QUALITY_THRESHOLD, CONTINUOUS_LEARNING_BATCH_SIZE,
    CONTINUOUS_LEARNING_UPDATE_INTERVAL_HOURS
)


class TestFeedbackData(unittest.TestCase):
    """Test FeedbackData dataclass."""
    
    def test_feedback_data_creation(self):
        """Test creating FeedbackData instance."""
        feedback = FeedbackData(
            id="test_id",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="def test_function():",
            original_output="def test_function():\n    pass",
            corrected_output="def test_function():\n    return True",
            user_rating=4,
            user_comment="Good improvement"
        )
        
        self.assertEqual(feedback.id, "test_id")
        self.assertEqual(feedback.feedback_type, FeedbackType.CORRECTION)
        self.assertEqual(feedback.user_rating, 4)
        self.assertEqual(feedback.original_input, "def test_function():")
    
    def test_feedback_data_to_dict(self):
        """Test converting FeedbackData to dictionary."""
        timestamp = datetime.now()
        feedback = FeedbackData(
            id="test_id",
            timestamp=timestamp,
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="test input",
            original_output="test output",
            quality_level=DataQuality.GOOD
        )
        
        data_dict = feedback.to_dict()
        
        self.assertEqual(data_dict['id'], "test_id")
        self.assertEqual(data_dict['feedback_type'], "correction")
        self.assertEqual(data_dict['quality_level'], "good")
        self.assertEqual(data_dict['timestamp'], timestamp.isoformat())
    
    def test_feedback_data_from_dict(self):
        """Test creating FeedbackData from dictionary."""
        timestamp = datetime.now()
        data_dict = {
            'id': 'test_id',
            'timestamp': timestamp.isoformat(),
            'feedback_type': 'correction',
            'user_id': 'user123',
            'session_id': 'session456',
            'original_input': 'test input',
            'original_output': 'test output',
            'quality_level': 'good'
        }
        
        feedback = FeedbackData.from_dict(data_dict)
        
        self.assertEqual(feedback.id, "test_id")
        self.assertEqual(feedback.feedback_type, FeedbackType.CORRECTION)
        self.assertEqual(feedback.quality_level, DataQuality.GOOD)
        self.assertEqual(feedback.timestamp, timestamp)


class TestReplayBuffer(unittest.TestCase):
    """Test ReplayBuffer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.buffer = ReplayBuffer(max_size=5, min_size=2)
    
    def test_add_and_sample(self):
        """Test adding data and sampling from buffer."""
        # Add some test data
        for i in range(3):
            feedback = FeedbackData(
                id=f"test_{i}",
                timestamp=datetime.now(),
                feedback_type=FeedbackType.CORRECTION,
                user_id="user123",
                session_id="session456",
                original_input=f"input_{i}",
                original_output=f"output_{i}"
            )
            self.buffer.add(feedback)
        
        # Test sampling
        samples = self.buffer.sample(2)
        self.assertEqual(len(samples), 2)
        self.assertTrue(all(isinstance(s, FeedbackData) for s in samples))
    
    def test_buffer_size_limit(self):
        """Test that buffer respects size limit."""
        # Add more data than max_size
        for i in range(7):
            feedback = FeedbackData(
                id=f"test_{i}",
                timestamp=datetime.now(),
                feedback_type=FeedbackType.CORRECTION,
                user_id="user123",
                session_id="session456",
                original_input=f"input_{i}",
                original_output=f"output_{i}"
            )
            self.buffer.add(feedback)
        
        # Buffer should not exceed max_size
        self.assertLessEqual(self.buffer.get_size(), 5)
    
    def test_sample_with_insufficient_data(self):
        """Test sampling when buffer has insufficient data."""
        # Add only one sample
        feedback = FeedbackData(
            id="test_1",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="input_1",
            original_output="output_1"
        )
        self.buffer.add(feedback)
        
        # Should return all available data
        samples = self.buffer.sample(3)
        self.assertEqual(len(samples), 1)
    
    def test_clear_buffer(self):
        """Test clearing the buffer."""
        # Add some data
        feedback = FeedbackData(
            id="test_1",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="input_1",
            original_output="output_1"
        )
        self.buffer.add(feedback)
        
        self.assertEqual(self.buffer.get_size(), 1)
        
        # Clear buffer
        self.buffer.clear()
        self.assertEqual(self.buffer.get_size(), 0)


class TestDataValidator(unittest.TestCase):
    """Test DataValidator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator(quality_threshold=0.7)
    
    def test_validate_good_feedback(self):
        """Test validation of good quality feedback."""
        feedback = FeedbackData(
            id="test_id",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="def test_function():\n    return True",
            original_output="def test_function():\n    pass",
            corrected_output="def test_function():\n    return True",
            user_rating=4
        )
        
        is_valid, quality_score, errors = self.validator.validate_feedback(feedback)
        
        self.assertTrue(is_valid)
        self.assertGreater(quality_score, 0.7)
        self.assertEqual(len(errors), 0)
    
    def test_validate_poor_feedback(self):
        """Test validation of poor quality feedback."""
        feedback = FeedbackData(
            id="test_id",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="",  # Empty input
            original_output="test",
            user_rating=1  # Low rating
        )
        
        is_valid, quality_score, errors = self.validator.validate_feedback(feedback)
        
        self.assertFalse(is_valid)
        self.assertLess(quality_score, 0.7)
        self.assertGreater(len(errors), 0)
    
    def test_validate_identical_input_output(self):
        """Test validation when input and output are identical."""
        feedback = FeedbackData(
            id="test_id",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="same content",
            original_output="same content"
        )
        
        is_valid, quality_score, errors = self.validator.validate_feedback(feedback)
        
        self.assertFalse(is_valid)
        self.assertIn("Input and output are identical", errors)
    
    def test_validate_invalid_rating(self):
        """Test validation with invalid user rating."""
        feedback = FeedbackData(
            id="test_id",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.CORRECTION,
            user_id="user123",
            session_id="session456",
            original_input="test input",
            original_output="test output",
            user_rating=6  # Invalid rating
        )
        
        is_valid, quality_score, errors = self.validator.validate_feedback(feedback)
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid user rating", errors)


class TestContinuousLearningService(unittest.TestCase):
    """Test ContinuousLearningService functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ContinuousLearningService(
            data_dir=self.temp_dir,
            quality_threshold=0.7
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.quality_threshold, 0.7)
        self.assertIsInstance(self.service.replay_buffer, ReplayBuffer)
        self.assertIsInstance(self.service.validator, DataValidator)
        
        # Check that database was created
        db_path = Path(self.temp_dir) / "continuous_learning.db"
        self.assertTrue(db_path.exists())
    
    def test_collect_feedback(self):
        """Test collecting feedback."""
        feedback_id = self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="def test_function():",
            original_output="def test_function():\n    pass",
            corrected_output="def test_function():\n    return True",
            user_rating=4
        )
        
        self.assertIsInstance(feedback_id, str)
        self.assertTrue(feedback_id.startswith("feedback_"))
        
        # Check statistics
        self.assertEqual(self.service.stats['total_feedback'], 1)
        self.assertEqual(self.service.stats['accepted_feedback'], 1)
        self.assertEqual(self.service.stats['rejected_feedback'], 0)
    
    def test_collect_invalid_feedback(self):
        """Test collecting invalid feedback."""
        feedback_id = self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="",  # Empty input
            original_output="test",
            user_rating=1
        )
        
        self.assertIsInstance(feedback_id, str)
        
        # Check statistics
        self.assertEqual(self.service.stats['total_feedback'], 1)
        self.assertEqual(self.service.stats['accepted_feedback'], 0)
        self.assertEqual(self.service.stats['rejected_feedback'], 1)
    
    def test_get_feedback_stats(self):
        """Test getting feedback statistics."""
        # Add some test feedback
        for i in range(3):
            self.service.collect_feedback(
                feedback_type=FeedbackType.CORRECTION,
                original_input=f"def function_{i}(): return {i}",
                original_output=f"def function_{i}():\n    pass",
                user_rating=4
            )
        
        # Add one invalid feedback
        self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="",
            original_output="test",
            user_rating=1
        )
        
        stats = self.service.get_feedback_stats()
        
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['accepted'], 3)
        self.assertEqual(stats['rejected'], 1)
        self.assertEqual(stats['acceptance_rate'], 75.0)
        self.assertIn('correction', stats['type_distribution'])
        self.assertEqual(stats['type_distribution']['correction'], 4)
    
    def test_get_feedback_stats_with_date_filter(self):
        """Test getting feedback statistics with date filter."""
        # Add feedback
        self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="test input",
            original_output="test output",
            user_rating=4
        )
        
        # Get stats for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = self.service.get_feedback_stats(start_date=start_date, end_date=end_date)
        
        self.assertEqual(stats['total'], 1)
    
    def test_trigger_model_update_insufficient_data(self):
        """Test triggering model update with insufficient data."""
        # Try to trigger update without enough data
        update_id = self.service.trigger_model_update(batch_size=100)
        
        self.assertIsNone(update_id)
        self.assertEqual(self.service.stats['model_updates'], 0)
    
    def test_trigger_model_update_with_data(self):
        """Test triggering model update with sufficient data."""
        # Add enough feedback data
        for i in range(50):
            self.service.collect_feedback(
                feedback_type=FeedbackType.CORRECTION,
                original_input=f"def function_{i}(): return {i}",
                original_output=f"def function_{i}():\n    pass",
                user_rating=4
            )
        
        # Trigger update
        update_id = self.service.trigger_model_update(batch_size=20)
        self.assertIsNotNone(update_id)
        if update_id is not None:
            self.assertTrue(update_id.startswith("update_"))
        self.assertEqual(self.service.stats['model_updates'], 1)
    
    def test_trigger_model_update_already_in_progress(self):
        """Test triggering model update when one is already in progress."""
        # Mock the update to be in progress
        self.service._update_in_progress = True
        
        update_id = self.service.trigger_model_update(batch_size=10)
        
        self.assertIsNone(update_id)
    
    def test_force_model_update(self):
        """Test forcing model update."""
        update_id = self.service.trigger_model_update(batch_size=100, force_update=True)
        
        self.assertIsNotNone(update_id)
        self.assertEqual(self.service.stats['model_updates'], 1)
    
    def test_get_update_history(self):
        """Test getting model update history."""
        # Trigger an update
        self.service.trigger_model_update(batch_size=10, force_update=True)
        
        # Get history
        history = self.service.get_update_history(limit=5)
        
        self.assertEqual(len(history), 1)
        self.assertIsInstance(history[0], ModelUpdate)
        self.assertEqual(history[0].samples_processed, 10)
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        # Add some feedback
        self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="test input",
            original_output="test output",
            user_rating=4
        )
        
        # Clean up data older than 1 day
        deleted_count = self.service.cleanup_old_data(days_to_keep=1)
        
        # Should not delete recent data
        self.assertEqual(deleted_count, 0)
    
    def test_export_data(self):
        """Test exporting feedback data."""
        # Add some feedback
        self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="test input",
            original_output="test output",
            user_rating=4
        )
        
        # Export data
        export_path = Path(self.temp_dir) / "export.json"
        self.service.export_data(str(export_path))
        
        # Check that file was created
        self.assertTrue(export_path.exists())
        
        # Check file content
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['original_input'], "test input")
    
    def test_export_data_with_date_filter(self):
        """Test exporting data with date filter."""
        # Add feedback
        self.service.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            original_input="test input",
            original_output="test output",
            user_rating=4
        )
        
        # Export data for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        export_path = Path(self.temp_dir) / "export_filtered.json"
        
        self.service.export_data(str(export_path), start_date=start_date, end_date=end_date)
        
        # Check that file was created
        self.assertTrue(export_path.exists())
        
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)


class TestModelUpdate(unittest.TestCase):
    """Test ModelUpdate dataclass."""
    
    def test_model_update_creation(self):
        """Test creating ModelUpdate instance."""
        update = ModelUpdate(
            id="update_123",
            timestamp=datetime.now(),
            model_version="v1.2.3",
            previous_version="v1.2.2",
            samples_processed=100,
            samples_accepted=95,
            samples_rejected=5,
            quality_threshold=0.7,
            pre_update_accuracy=0.85,
            post_update_accuracy=0.87,
            performance_change=0.02
        )
        
        self.assertEqual(update.id, "update_123")
        self.assertEqual(update.model_version, "v1.2.3")
        self.assertEqual(update.samples_processed, 100)
        self.assertEqual(update.samples_accepted, 95)
        self.assertEqual(update.samples_rejected, 5)
        self.assertEqual(update.performance_change, 0.02)
    
    def test_model_update_to_dict(self):
        """Test converting ModelUpdate to dictionary."""
        timestamp = datetime.now()
        update = ModelUpdate(
            id="update_123",
            timestamp=timestamp,
            model_version="v1.2.3",
            previous_version="v1.2.2",
            samples_processed=100,
            samples_accepted=95,
            samples_rejected=5,
            quality_threshold=0.7
        )
        
        data_dict = update.to_dict()
        
        self.assertEqual(data_dict['id'], "update_123")
        self.assertEqual(data_dict['model_version'], "v1.2.3")
        self.assertEqual(data_dict['timestamp'], timestamp.isoformat())


class TestIntegration(unittest.TestCase):
    """Integration tests for continuous learning workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ContinuousLearningService(
            data_dir=self.temp_dir,
            quality_threshold=0.7
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test complete continuous learning workflow."""
        # 1. Collect feedback
        feedback_ids = []
        for i in range(10):
            feedback_id = self.service.collect_feedback(
                feedback_type=FeedbackType.CORRECTION,
                original_input=f"def function_{i}():",
                original_output=f"def function_{i}():\n    pass",
                corrected_output=f"def function_{i}():\n    return True",
                user_rating=4
            )
            feedback_ids.append(feedback_id)
        
        # 2. Check statistics
        stats = self.service.get_feedback_stats()
        self.assertEqual(stats['total'], 10)
        self.assertEqual(stats['accepted'], 10)
        self.assertEqual(stats['acceptance_rate'], 100.0)
        
        # 3. Trigger model update
        update_id = self.service.trigger_model_update(batch_size=5)
        self.assertIsNotNone(update_id)
        
        # 4. Check update history
        history = self.service.get_update_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].status, "completed")
        
        # 5. Export data
        export_path = Path(self.temp_dir) / "workflow_export.json"
        self.service.export_data(str(export_path))
        self.assertTrue(export_path.exists())
    
    def test_concurrent_feedback_collection(self):
        """Test concurrent feedback collection."""
        import threading
        import time
        
        feedback_ids = []
        lock = threading.Lock()
        
        def collect_feedback(thread_id):
            for i in range(5):
                feedback_id = self.service.collect_feedback(
                    feedback_type=FeedbackType.CORRECTION,
                    original_input=f"thread_{thread_id}_input_{i}",
                    original_output=f"thread_{thread_id}_output_{i}",
                    user_rating=4
                )
                with lock:
                    feedback_ids.append(feedback_id)
                time.sleep(0.01)  # Small delay to simulate real usage
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=collect_feedback, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(feedback_ids), 15)
        self.assertEqual(self.service.stats['total_feedback'], 15)
        self.assertEqual(self.service.stats['accepted_feedback'], 15)


if __name__ == '__main__':
    unittest.main() 