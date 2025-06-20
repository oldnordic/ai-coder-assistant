"""Integration tests for Task Management Service."""

import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from backend.services.task_management import (
    DatabaseConnectionPool,
    TaskManagementService,
    TaskPriority,
    TaskStatus,
)
from src.backend.utils.constants import (
    TEST_DELAY_MS,
    TEST_INVALID_TASK_ID,
    TEST_ITERATION_COUNT,
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def task_service(temp_data_dir):
    """Create a TaskManagementService instance for testing."""
    service = TaskManagementService(str(temp_data_dir), "test_tasks.db")
    yield service
    # Cleanup
    if hasattr(service, 'connection_pool'):
        service.connection_pool.close_all()


class TestDatabaseConnectionPool:
    """Test the database connection pool functionality."""

    def test_connection_pool_initialization(self, temp_data_dir):
        """Test connection pool initialization."""
        db_path = temp_data_dir / "test.db"
        pool = DatabaseConnectionPool(db_path, max_connections=5)

        assert pool.max_connections == 5
        assert pool._connections.qsize() == 5

        # Test getting connections
        with pool.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

        pool.close_all()

    def test_connection_pool_concurrency(self, temp_data_dir):
        """Test connection pool under concurrent access."""
        db_path = temp_data_dir / "test.db"
        pool = DatabaseConnectionPool(db_path, max_connections=3)

        def worker(worker_id):
            with pool.get_connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
                conn.execute("INSERT INTO test (id) VALUES (?)", (worker_id,))
                conn.commit()
                time.sleep(0.1)  # Simulate work
                return worker_id

        # Run multiple workers concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]

        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}

        pool.close_all()


class TestTaskManagementServiceIntegration:
    """Integration tests for TaskManagementService."""

    def test_task_creation_and_retrieval(self, task_service):
        """Test creating and retrieving tasks."""
        # Create a task
        task = task_service.create_task(
            title="Test Task",
            description="Test Description",
            assignee="Test User",
            priority=TaskPriority.HIGH,
            tags=["test", "integration"]
        )

        assert task.id > 0
        assert task.title == "Test Task"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.HIGH

        # Retrieve the task
        retrieved_task = task_service.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.title == "Test Task"
        assert retrieved_task.tags == ["test", "integration"]

    def test_task_filtering(self, task_service):
        """Test task filtering functionality."""
        # Create tasks with different attributes
        task1 = task_service.create_task(
            title="High Priority Task",
            description="High priority task",
            assignee="Alice",
            priority=TaskPriority.HIGH,
            project="Project A"
        )

        task2 = task_service.create_task(
            title="Medium Priority Task",
            description="Medium priority task",
            assignee="Bob",
            priority=TaskPriority.MEDIUM,
            project="Project B"
        )

        # Test filtering by priority
        high_priority_tasks = task_service.get_all_tasks(priority=TaskPriority.HIGH)
        assert len(high_priority_tasks) >= 1
        assert all(task.priority == TaskPriority.HIGH for task in high_priority_tasks)

        # Test filtering by assignee
        alice_tasks = task_service.get_all_tasks(assignee="Alice")
        assert len(alice_tasks) >= 1
        assert all(task.assignee == "Alice" for task in alice_tasks)

        # Test filtering by project
        project_a_tasks = task_service.get_all_tasks(project="Project A")
        assert len(project_a_tasks) >= 1
        assert all(task.project == "Project A" for task in project_a_tasks)

    def test_task_scheduling(self, task_service):
        """Test task scheduling functionality."""
        # Create tasks with different priorities
        low_task = task_service.create_task(
            title="Low Priority",
            description="Low priority task",
            assignee="User1",
            priority=TaskPriority.LOW
        )

        high_task = task_service.create_task(
            title="High Priority",
            description="High priority task",
            assignee="User2",
            priority=TaskPriority.HIGH
        )

        # Schedule tasks
        task_service.schedule_tasks()

        # Run next task (should be high priority)
        next_task = task_service.run_next_task()
        assert next_task is not None
        assert next_task.priority == TaskPriority.HIGH

        # Verify task status changed
        updated_task = task_service.get_task(high_task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS

    def test_task_dependencies(self, task_service):
        """Test task dependency resolution."""
        # Create dependent tasks
        parent_task = task_service.create_task(
            title="Parent Task",
            description="Parent task",
            assignee="User1",
            priority=TaskPriority.MEDIUM
        )

        child_task = task_service.create_task(
            title="Child Task",
            description="Child task",
            assignee="User2",
            priority=TaskPriority.HIGH
        )

        # Add dependency
        task_service.update_task(child_task.id, dependencies=[parent_task.id])

        # Schedule tasks
        task_service.schedule_tasks()

        # Child task should not be scheduled until parent is complete
        child_task_updated = task_service.get_task(child_task.id)
        assert child_task_updated.status == TaskStatus.TODO

        # Complete parent task
        task_service.complete_task(parent_task.id)

        # Reschedule tasks
        task_service.schedule_tasks()

        # Now child task should be schedulable
        next_task = task_service.run_next_task()
        assert next_task is not None
        assert next_task.id == child_task.id

    def test_concurrent_task_operations(self, task_service):
        """Test concurrent task operations."""
        def create_task(worker_id):
            return task_service.create_task(
                title=f"Task {worker_id}",
                description=f"Task created by worker {worker_id}",
                assignee=f"Worker{worker_id}",
                priority=TaskPriority.MEDIUM
            )

        # Create tasks concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_task, i) for i in range(10)]
            tasks = [future.result() for future in as_completed(futures)]

        assert len(tasks) == 10

        # Verify all tasks were created
        all_tasks = task_service.get_all_tasks()
        assert len(all_tasks) >= 10

        # Test concurrent updates
        def update_task(task_id):
            return task_service.update_task(
                task_id,
                status=TaskStatus.IN_PROGRESS,
                description="Updated concurrently"
            )

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(update_task, task.id) for task in tasks[:3]]
            updated_tasks = [future.result() for future in as_completed(futures)]

        assert len(updated_tasks) == 3
        assert all(task.status == TaskStatus.IN_PROGRESS for task in updated_tasks)

    def test_task_analytics(self, task_service):
        """Test task analytics functionality."""
        # Create tasks with different statuses
        task_service.create_task(
            title="Completed Task",
            description="A completed task",
            assignee="User1",
            priority=TaskPriority.MEDIUM
        )

        task_service.create_task(
            title="In Progress Task",
            description="A task in progress",
            assignee="User2",
            priority=TaskPriority.HIGH
        )

        # Complete the first task
        all_tasks = task_service.get_all_tasks()
        if all_tasks:
            task_service.complete_task(all_tasks[0].id)

        # Get analytics
        analytics = task_service.get_analytics()

        assert analytics.total_tasks >= 2
        assert analytics.completed_tasks >= 1
        assert analytics.in_progress_tasks >= 0
        assert analytics.completion_rate >= 0.0
        assert analytics.completion_rate <= 1.0

    def test_error_handling_and_recovery(self, task_service):
        """Test error handling and recovery mechanisms."""
        # Test with invalid task ID
        invalid_task = task_service.get_task(TEST_INVALID_TASK_ID)
        assert invalid_task is None

        # Test updating non-existent task
        result = task_service.update_task(TEST_INVALID_TASK_ID, title="New Title")
        assert result is None

        # Test completing non-existent task
        result = task_service.complete_task(TEST_INVALID_TASK_ID)
        assert result is None

        # Test deleting non-existent task
        result = task_service.delete_task(TEST_INVALID_TASK_ID)
        assert result is False

    def test_task_history_logging(self, task_service):
        """Test task history logging functionality."""
        # Create a task
        task = task_service.create_task(
            title="Test Task",
            description="Test Description",
            assignee="Test User",
            priority=TaskPriority.MEDIUM
        )

        # Update the task
        updated_task = task_service.update_task(
            task.id,
            title="Updated Title",
            status=TaskStatus.IN_PROGRESS
        )

        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.status == TaskStatus.IN_PROGRESS

        # Complete the task
        completed_task = task_service.complete_task(task.id)
        assert completed_task is not None
        assert completed_task.status == TaskStatus.DONE


class TestTaskManagementServicePerformance:
    """Performance tests for TaskManagementService."""

    def test_bulk_task_creation(self, task_service):
        """Test bulk task creation performance."""
        start_time = time.time()

        # Create 100 tasks
        tasks = []
        for i in range(TEST_ITERATION_COUNT):
            task = task_service.create_task(
                title=f"Bulk Task {i}",
                description=f"Bulk task description {i}",
                assignee=f"User{i % 5}",
                priority=TaskPriority.MEDIUM,
                tags=[f"tag{i}", f"bulk"]
            )
            tasks.append(task)

        end_time = time.time()
        creation_time = end_time - start_time

        assert len(tasks) == TEST_ITERATION_COUNT
        assert creation_time < 10.0  # Should complete within 10 seconds

        # Test bulk retrieval
        start_time = time.time()
        all_tasks = task_service.get_all_tasks()
        end_time = time.time()
        retrieval_time = end_time - start_time

        assert len(all_tasks) >= TEST_ITERATION_COUNT
        assert retrieval_time < 5.0  # Should complete within 5 seconds

    def test_concurrent_read_write_performance(self, task_service):
        """Test concurrent read/write performance."""
        def writer_worker(worker_id):
            for i in range(10):
                task = task_service.create_task(
                    title=f"Concurrent Task {worker_id}-{i}",
                    description=f"Task from worker {worker_id}",
                    assignee=f"Worker{worker_id}",
                    priority=TaskPriority.MEDIUM
                )
                time.sleep(TEST_DELAY_MS / 1000)  # Small delay
                return task.id

        def reader_worker(worker_id):
            for i in range(20):
                tasks = task_service.get_all_tasks()
                time.sleep(TEST_DELAY_MS / 1000)  # Small delay
                return len(tasks)

        start_time = time.time()

        # Run concurrent writers and readers
        with ThreadPoolExecutor(max_workers=10) as executor:
            writer_futures = [executor.submit(writer_worker, i) for i in range(5)]
            reader_futures = [executor.submit(reader_worker, i) for i in range(5)]

            # Wait for all to complete
            all_futures = writer_futures + reader_futures
            results = [future.result() for future in as_completed(all_futures)]

        end_time = time.time()
        total_time = end_time - start_time

        assert total_time < 30.0  # Should complete within 30 seconds
        assert len(results) == 10  # 5 writers + 5 readers
