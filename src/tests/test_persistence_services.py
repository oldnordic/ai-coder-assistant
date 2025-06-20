"""Unit and integration tests for persistence services."""

import pytest
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.services.model_persistence import (
    ModelPersistenceService, ModelConfig, ModelStateRecord,
    ModelType, ModelState
)
from backend.services.scanner_persistence import (
    ScannerPersistenceService, ScanResult, CodeIssue, FileAnalysis,
    ScanStatus, IssueSeverity
)
from src.backend.utils.constants import (
    TEST_MAX_TOKENS, TEST_FILE_SIZE, TEST_SCAN_DURATION, 
    TEST_ITERATION_COUNT, TEST_BATCH_SIZE
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def model_persistence(temp_data_dir):
    """Create a ModelPersistenceService instance for testing."""
    service = ModelPersistenceService(str(temp_data_dir), "test_models.db")
    yield service
    if hasattr(service, 'connection_pool'):
        service.connection_pool.close_all()

@pytest.fixture
def scanner_persistence(temp_data_dir):
    """Create a ScannerPersistenceService instance for testing."""
    service = ScannerPersistenceService(str(temp_data_dir), "test_scanner.db")
    yield service
    if hasattr(service, 'connection_pool'):
        service.connection_pool.close_all()

class TestModelPersistenceService:
    """Test ModelPersistenceService functionality."""

    def test_save_and_get_model_config(self, model_persistence):
        """Test saving and retrieving model configuration."""
        config = ModelConfig(
            model_id="test-model-1",
            model_type=ModelType.OLLAMA,
            name="Test Model",
            version="1.0.0",
            description="A test model",
            parameters={"temperature": 0.7, "max_tokens": TEST_MAX_TOKENS},
            metadata={"author": "Test Author"}
        )
        
        # Save config
        success = model_persistence.save_model_config(config)
        assert success
        
        # Retrieve config
        retrieved_config = model_persistence.get_model_config("test-model-1")
        assert retrieved_config is not None
        assert retrieved_config.model_id == "test-model-1"
        assert retrieved_config.model_type == ModelType.OLLAMA
        assert retrieved_config.name == "Test Model"
        assert retrieved_config.parameters["temperature"] == 0.7
        assert retrieved_config.metadata["author"] == "Test Author"

    def test_get_all_model_configs(self, model_persistence):
        """Test retrieving all model configurations."""
        # Create multiple configs
        configs = [
            ModelConfig(model_id="model-1", model_type=ModelType.OLLAMA, name="Model 1", version="1.0"),
            ModelConfig(model_id="model-2", model_type=ModelType.LOCAL, name="Model 2", version="2.0"),
            ModelConfig(model_id="model-3", model_type=ModelType.CLOUD, name="Model 3", version="3.0")
        ]
        
        for config in configs:
            model_persistence.save_model_config(config)
        
        # Get all configs
        all_configs = model_persistence.get_all_model_configs()
        assert len(all_configs) >= 3
        
        # Filter by type
        ollama_configs = model_persistence.get_all_model_configs(ModelType.OLLAMA)
        assert len(ollama_configs) >= 1
        assert all(config.model_type == ModelType.OLLAMA for config in ollama_configs)

    def test_save_and_get_model_state(self, model_persistence):
        """Test saving and retrieving model state records."""
        # First save a model config
        config = ModelConfig(
            model_id="test-model",
            model_type=ModelType.OLLAMA,
            name="Test Model",
            version="1.0.0"
        )
        model_persistence.save_model_config(config)
        
        # Save state records
        states = [
            ModelStateRecord(
                model_id="test-model",
                state=ModelState.LOADING,
                timestamp=datetime.now() - timedelta(minutes=2)
            ),
            ModelStateRecord(
                model_id="test-model",
                state=ModelState.LOADED,
                timestamp=datetime.now() - timedelta(minutes=1)
            ),
            ModelStateRecord(
                model_id="test-model",
                state=ModelState.ERROR,
                timestamp=datetime.now(),
                error_message="Test error"
            )
        ]
        
        for state in states:
            success = model_persistence.save_model_state(state)
            assert success
        
        # Get state history
        state_history = model_persistence.get_model_states("test-model")
        assert len(state_history) >= 3
        assert state_history[0].state == ModelState.ERROR  # Most recent first

    def test_delete_model_config(self, model_persistence):
        """Test deleting model configuration."""
        config = ModelConfig(
            model_id="delete-test",
            model_type=ModelType.OLLAMA,
            name="Delete Test",
            version="1.0.0"
        )
        
        # Save and verify
        model_persistence.save_model_config(config)
        retrieved = model_persistence.get_model_config("delete-test")
        assert retrieved is not None
        
        # Delete and verify
        success = model_persistence.delete_model_config("delete-test")
        assert success
        
        retrieved = model_persistence.get_model_config("delete-test")
        assert retrieved is None

    def test_model_analytics(self, model_persistence):
        """Test model analytics functionality."""
        # Create some test data
        configs = [
            ModelConfig(model_id="model-1", model_type=ModelType.OLLAMA, name="Model 1", version="1.0"),
            ModelConfig(model_id="model-2", model_type=ModelType.OLLAMA, name="Model 2", version="1.0"),
            ModelConfig(model_id="model-3", model_type=ModelType.LOCAL, name="Model 3", version="1.0")
        ]
        
        for config in configs:
            model_persistence.save_model_config(config)
        
        # Get analytics
        analytics = model_persistence.get_model_analytics()
        assert analytics["total_models"] >= 3
        assert "models_by_type" in analytics
        assert "recent_states" in analytics

    def test_error_handling(self, model_persistence):
        """Test error handling scenarios."""
        # Test getting non-existent config
        config = model_persistence.get_model_config("non-existent")
        assert config is None
        
        # Test getting states for non-existent model
        states = model_persistence.get_model_states("non-existent")
        assert states == []

class TestScannerPersistenceService:
    """Test ScannerPersistenceService functionality."""

    def test_save_and_get_scan_result(self, scanner_persistence):
        """Test saving and retrieving scan results."""
        scan_result = ScanResult(
            scan_id="test-scan-1",
            scan_type="security",
            target_path="/test/path",
            model_used="test-model",
            status=ScanStatus.COMPLETED,
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now(),
            total_files=TEST_ITERATION_COUNT,
            processed_files=TEST_ITERATION_COUNT,
            issues_found=5,
            metadata={"scan_duration": TEST_SCAN_DURATION}
        )
        
        # Save scan result
        success = scanner_persistence.save_scan_result(scan_result)
        assert success
        
        # Retrieve scan result
        retrieved = scanner_persistence.get_scan_result("test-scan-1")
        assert retrieved is not None
        assert retrieved.scan_id == "test-scan-1"
        assert retrieved.scan_type == "security"
        assert retrieved.status == ScanStatus.COMPLETED
        assert retrieved.issues_found == 5
        assert retrieved.metadata["scan_duration"] == TEST_SCAN_DURATION

    def test_get_all_scan_results(self, scanner_persistence):
        """Test retrieving all scan results."""
        # Create multiple scan results
        scans = [
            ScanResult(
                scan_id="scan-1",
                scan_type="security",
                target_path="/path1",
                model_used="model1",
                status=ScanStatus.COMPLETED,
                start_time=datetime.now() - timedelta(hours=2)
            ),
            ScanResult(
                scan_id="scan-2",
                scan_type="quality",
                target_path="/path2",
                model_used="model2",
                status=ScanStatus.IN_PROGRESS,
                start_time=datetime.now() - timedelta(hours=1)
            ),
            ScanResult(
                scan_id="scan-3",
                scan_type="security",
                target_path="/path3",
                model_used="model3",
                status=ScanStatus.FAILED,
                start_time=datetime.now()
            )
        ]
        
        for scan in scans:
            scanner_persistence.save_scan_result(scan)
        
        # Get all scan results
        all_scans = scanner_persistence.get_all_scan_results()
        assert len(all_scans) >= 3
        
        # Filter by status
        completed_scans = scanner_persistence.get_all_scan_results(ScanStatus.COMPLETED)
        assert len(completed_scans) >= 1
        assert all(scan.status == ScanStatus.COMPLETED for scan in completed_scans)

    def test_save_and_get_code_issues(self, scanner_persistence):
        """Test saving and retrieving code issues."""
        # First save a scan result
        scan_result = ScanResult(
            scan_id="test-scan",
            scan_type="security",
            target_path="/test/path",
            model_used="test-model",
            status=ScanStatus.COMPLETED,
            start_time=datetime.now()
        )
        scanner_persistence.save_scan_result(scan_result)
        
        # Save code issues
        issues = [
            CodeIssue(
                issue_id="issue-1",
                scan_id="test-scan",
                file_path="/test/file1.py",
                line_number=10,
                severity=IssueSeverity.HIGH,
                category="security",
                description="SQL injection vulnerability",
                suggestion="Use parameterized queries"
            ),
            CodeIssue(
                issue_id="issue-2",
                scan_id="test-scan",
                file_path="/test/file2.py",
                line_number=25,
                severity=IssueSeverity.MEDIUM,
                category="quality",
                description="Unused variable",
                suggestion="Remove unused variable"
            )
        ]
        
        for issue in issues:
            success = scanner_persistence.save_code_issue(issue)
            assert success
        
        # Get all issues for scan
        all_issues = scanner_persistence.get_code_issues("test-scan")
        assert len(all_issues) == 2
        
        # Filter by severity
        high_issues = scanner_persistence.get_code_issues("test-scan", IssueSeverity.HIGH)
        assert len(high_issues) == 1
        assert high_issues[0].severity == IssueSeverity.HIGH

    def test_save_and_get_file_analysis(self, scanner_persistence):
        """Test saving and retrieving file analysis."""
        # First save a scan result
        scan_result = ScanResult(
            scan_id="test-scan",
            scan_type="quality",
            target_path="/test/path",
            model_used="test-model",
            status=ScanStatus.COMPLETED,
            start_time=datetime.now()
        )
        scanner_persistence.save_scan_result(scan_result)
        
        # Save file analysis
        analysis = FileAnalysis(
            file_id="file-1",
            scan_id="test-scan",
            file_path="/test/file.py",
            file_size=TEST_FILE_SIZE,
            lines_of_code=50,
            language="python",
            complexity_score=3.5,
            issues_count=2,
            analysis_data={"cyclomatic_complexity": 3, "maintainability_index": 85}
        )
        
        success = scanner_persistence.save_file_analysis(analysis)
        assert success
        
        # Get file analysis
        analyses = scanner_persistence.get_file_analysis("test-scan")
        assert len(analyses) == 1
        assert analyses[0].file_path == "/test/file.py"
        assert analyses[0].language == "python"
        assert analyses[0].complexity_score == 3.5
        assert analyses[0].analysis_data["cyclomatic_complexity"] == 3

    def test_scanner_analytics(self, scanner_persistence):
        """Test scanner analytics functionality."""
        # Create some test data
        scan_result = ScanResult(
            scan_id="test-scan",
            scan_type="security",
            target_path="/test/path",
            model_used="test-model",
            status=ScanStatus.COMPLETED,
            start_time=datetime.now(),
            issues_found=3
        )
        scanner_persistence.save_scan_result(scan_result)
        
        # Add some issues
        issues = [
            CodeIssue(
                issue_id="issue-1",
                scan_id="test-scan",
                file_path="/test/file.py",
                line_number=10,
                severity=IssueSeverity.HIGH,
                category="security",
                description="Test issue 1"
            ),
            CodeIssue(
                issue_id="issue-2",
                scan_id="test-scan",
                file_path="/test/file.py",
                line_number=20,
                severity=IssueSeverity.MEDIUM,
                category="quality",
                description="Test issue 2"
            )
        ]
        
        for issue in issues:
            scanner_persistence.save_code_issue(issue)
        
        # Get analytics
        analytics = scanner_persistence.get_scanner_analytics()
        assert analytics["total_scans"] >= 1
        assert analytics["total_issues"] >= 2
        assert "scans_by_status" in analytics
        assert "issues_by_severity" in analytics

    def test_delete_scan_result(self, scanner_persistence):
        """Test deleting scan result and cascading deletes."""
        # Create scan result with issues
        scan_result = ScanResult(
            scan_id="delete-test",
            scan_type="security",
            target_path="/test/path",
            model_used="test-model",
            status=ScanStatus.COMPLETED,
            start_time=datetime.now()
        )
        scanner_persistence.save_scan_result(scan_result)
        
        # Add an issue
        issue = CodeIssue(
            issue_id="issue-1",
            scan_id="delete-test",
            file_path="/test/file.py",
            line_number=10,
            severity=IssueSeverity.HIGH,
            category="security",
            description="Test issue"
        )
        scanner_persistence.save_code_issue(issue)
        
        # Verify data exists
        retrieved_scan = scanner_persistence.get_scan_result("delete-test")
        assert retrieved_scan is not None
        
        retrieved_issues = scanner_persistence.get_code_issues("delete-test")
        assert len(retrieved_issues) == 1
        
        # Delete scan result
        success = scanner_persistence.delete_scan_result("delete-test")
        assert success
        
        # Verify cascading delete
        retrieved_scan = scanner_persistence.get_scan_result("delete-test")
        assert retrieved_scan is None
        
        retrieved_issues = scanner_persistence.get_code_issues("delete-test")
        assert len(retrieved_issues) == 0

    def test_error_handling(self, scanner_persistence):
        """Test error handling scenarios."""
        # Test getting non-existent scan result
        scan = scanner_persistence.get_scan_result("non-existent")
        assert scan is None
        
        # Test getting issues for non-existent scan
        issues = scanner_persistence.get_code_issues("non-existent")
        assert issues == []
        
        # Test getting file analysis for non-existent scan
        analyses = scanner_persistence.get_file_analysis("non-existent")
        assert analyses == []

class TestPersistenceServicesIntegration:
    """Integration tests for persistence services."""

    def test_concurrent_operations(self, model_persistence, scanner_persistence):
        """Test concurrent operations on persistence services."""
        import threading
        import time
        
        results = []
        
        def model_operation(operation_id):
            config = ModelConfig(
                model_id=f"concurrent-model-{operation_id}",
                model_type=ModelType.OLLAMA,
                name=f"Concurrent Model {operation_id}",
                version="1.0.0"
            )
            success = model_persistence.save_model_config(config)
            results.append(("model", operation_id, success))
        
        def scanner_operation(operation_id):
            scan_result = ScanResult(
                scan_id=f"concurrent-scan-{operation_id}",
                scan_type="security",
                target_path=f"/test/path/{operation_id}",
                model_used="test-model",
                status=ScanStatus.COMPLETED,
                start_time=datetime.now()
            )
            success = scanner_persistence.save_scan_result(scan_result)
            results.append(("scanner", operation_id, success))
        
        # Run operations concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=model_operation, args=(i,))
            threads.append(thread)
            thread = threading.Thread(target=scanner_operation, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all operations completed successfully
        assert len(results) == 20
        assert all(result[2] for result in results)  # All operations successful

    def test_data_integrity(self, model_persistence, scanner_persistence):
        """Test data integrity across persistence operations."""
        # Create model config
        config = ModelConfig(
            model_id="integrity-test",
            model_type=ModelType.OLLAMA,
            name="Integrity Test Model",
            version="1.0.0",
            parameters={"temperature": 0.7}
        )
        model_persistence.save_model_config(config)
        
        # Create scan result using the model
        scan_result = ScanResult(
            scan_id="integrity-test-scan",
            scan_type="security",
            target_path="/test/path",
            model_used="integrity-test",
            status=ScanStatus.COMPLETED,
            start_time=datetime.now()
        )
        scanner_persistence.save_scan_result(scan_result)
        
        # Verify data integrity
        retrieved_config = model_persistence.get_model_config("integrity-test")
        retrieved_scan = scanner_persistence.get_scan_result("integrity-test-scan")
        
        assert retrieved_config is not None
        assert retrieved_scan is not None
        assert retrieved_scan.model_used == retrieved_config.model_id
        assert retrieved_config.parameters["temperature"] == 0.7 