"""
thread_monitor.py

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

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread, QThreadPool
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QHeaderView, QMessageBox
)

from frontend.ui.worker_threads import get_thread_manager

logger = logging.getLogger(__name__)

@dataclass
class WorkerInfo:
    """Information about a worker thread."""
    worker_id: str
    task_type: str
    start_time: datetime
    status: str = "running"  # running, completed, error, cancelled
    progress: Optional[tuple] = None  # (current, total, message)
    error_message: Optional[str] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None

class ThreadMonitor(QObject):
    """
    Real-time thread monitoring system for debugging and performance analysis.
    """
    
    worker_started = pyqtSignal(str)  # worker_id
    worker_finished = pyqtSignal(str)  # worker_id
    worker_error = pyqtSignal(str, str)  # worker_id, error_message
    worker_progress = pyqtSignal(str, int, int, str)  # worker_id, current, total, message
    
    def __init__(self):
        super().__init__()
        self.thread_manager = get_thread_manager()
        self.workers: Dict[str, WorkerInfo] = {}
        self.worker_history: List[WorkerInfo] = []
        self.performance_stats = defaultdict(list)
        
        # Setup monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_stats)
        self.monitor_timer.start(1000)  # Update every second
        
        logger.info("ThreadMonitor initialized")
    
    def _on_worker_started(self, worker_id: str):
        """Handle worker start event."""
        task_type = worker_id.split('_')[0] if '_' in worker_id else 'unknown'
        worker_info = WorkerInfo(
            worker_id=worker_id,
            task_type=task_type,
            start_time=datetime.now()
        )
        self.workers[worker_id] = worker_info
        self.worker_started.emit(worker_id)
        logger.info(f"Worker started: {worker_id}")
    
    def _on_worker_finished(self, worker_id: str):
        """Handle worker finish event."""
        if worker_id in self.workers:
            worker_info = self.workers[worker_id]
            worker_info.status = "completed"
            worker_info.end_time = datetime.now()
            worker_info.duration = worker_info.end_time - worker_info.start_time
            
            # Move to history
            self.worker_history.append(worker_info)
            del self.workers[worker_id]
            
            # Update performance stats
            self.performance_stats[worker_info.task_type].append(worker_info.duration.total_seconds())
            
            self.worker_finished.emit(worker_id)
            logger.info(f"Worker finished: {worker_id} (duration: {worker_info.duration})")
    
    def _on_worker_error(self, worker_id: str, error_message: str):
        """Handle worker error event."""
        if worker_id in self.workers:
            worker_info = self.workers[worker_id]
            worker_info.status = "error"
            worker_info.error_message = error_message
            worker_info.end_time = datetime.now()
            worker_info.duration = worker_info.end_time - worker_info.start_time
            
            # Move to history
            self.worker_history.append(worker_info)
            del self.workers[worker_id]
            
            self.worker_error.emit(worker_id, error_message)
            logger.error(f"Worker error: {worker_id} - {error_message}")
    
    def _on_worker_progress(self, worker_id: str, current: int, total: int, message: str):
        """Handle worker progress event."""
        if worker_id in self.workers:
            worker_info = self.workers[worker_id]
            worker_info.progress = (current, total, message)
            self.worker_progress.emit(worker_id, current, total, message)
    
    def get_thread_pool_info(self) -> Dict[str, int]:
        """Get information about the thread pool."""
        pool = QThreadPool.globalInstance()
        return {
            'active_thread_count': pool.activeThreadCount(),
            'max_thread_count': pool.maxThreadCount(),
            'active_workers': len(self.workers)
        }
    
    def get_active_workers(self) -> Dict[str, WorkerInfo]:
        """Get currently active workers."""
        return self.workers.copy()
    
    def get_worker_history(self, limit: int = 50) -> List[WorkerInfo]:
        """Get worker history, limited to the most recent entries."""
        return self.worker_history[-limit:]
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for each task type."""
        stats = {}
        for task_type, durations in self.performance_stats.items():
            if durations:
                stats[task_type] = {
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'total_tasks': len(durations)
                }
        return stats
    
    def _update_stats(self):
        """Update performance statistics."""
        # This method is called periodically to update stats
        pass

class ThreadMonitorWidget(QWidget):
    """
    GUI widget for monitoring thread activity in real-time.
    """
    
    def __init__(self):
        super().__init__()
        self.monitor = ThreadMonitor()
        self.setup_ui()
        self.connect_signals()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)  # Update every 500ms
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Thread pool info
        pool_group = QGroupBox("Thread Pool Status")
        pool_layout = QHBoxLayout()
        
        self.active_threads_label = QLabel("Active Threads: 0")
        self.max_threads_label = QLabel("Max Threads: 0")
        self.active_workers_label = QLabel("Active Workers: 0")
        
        pool_layout.addWidget(self.active_threads_label)
        pool_layout.addWidget(self.max_threads_label)
        pool_layout.addWidget(self.active_workers_label)
        pool_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_display)
        pool_layout.addWidget(self.refresh_btn)
        
        pool_group.setLayout(pool_layout)
        layout.addWidget(pool_group)
        
        # Splitter for tables
        splitter = QSplitter()
        
        # Active workers table
        active_group = QGroupBox("Active Workers")
        active_layout = QVBoxLayout()
        
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(5)
        self.active_table.setHorizontalHeaderLabels([
            "Worker ID", "Task Type", "Status", "Duration", "Progress"
        ])
        self.active_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        active_layout.addWidget(self.active_table)
        active_group.setLayout(active_layout)
        splitter.addWidget(active_group)
        
        # Worker history table
        history_group = QGroupBox("Recent History")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Worker ID", "Task Type", "Status", "Duration", "Error", "Start Time"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        splitter.addWidget(history_group)
        
        layout.addWidget(splitter)
        
        # Performance stats
        stats_group = QGroupBox("Performance Statistics")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)
        
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect monitor signals."""
        self.monitor.worker_started.connect(self._on_worker_started)
        self.monitor.worker_finished.connect(self._on_worker_finished)
        self.monitor.worker_error.connect(self._on_worker_error)
        self.monitor.worker_progress.connect(self._on_worker_progress)
    
    def _on_worker_started(self, worker_id: str):
        """Handle worker start event."""
        self.update_display()
    
    def _on_worker_finished(self, worker_id: str):
        """Handle worker finish event."""
        self.update_display()
    
    def _on_worker_error(self, worker_id: str, error_message: str):
        """Handle worker error event."""
        self.update_display()
    
    def _on_worker_progress(self, worker_id: str, current: int, total: int, message: str):
        """Handle worker progress event."""
        self.update_display()
    
    def update_display(self):
        """Update the display with current information."""
        # Update thread pool info
        pool_info = self.monitor.get_thread_pool_info()
        self.active_threads_label.setText(f"Active Threads: {pool_info['active_thread_count']}")
        self.max_threads_label.setText(f"Max Threads: {pool_info['max_thread_count']}")
        self.active_workers_label.setText(f"Active Workers: {pool_info['active_workers']}")
        
        # Update active workers table
        active_workers = self.monitor.get_active_workers()
        self.active_table.setRowCount(len(active_workers))
        
        for row, (worker_id, worker_info) in enumerate(active_workers.items()):
            self.active_table.setItem(row, 0, QTableWidgetItem(worker_id))
            self.active_table.setItem(row, 1, QTableWidgetItem(worker_info.task_type))
            self.active_table.setItem(row, 2, QTableWidgetItem(worker_info.status))
            
            duration = datetime.now() - worker_info.start_time
            self.active_table.setItem(row, 3, QTableWidgetItem(str(duration).split('.')[0]))
            
            if worker_info.progress:
                current, total, message = worker_info.progress
                progress_text = f"{current}/{total} - {message}"
            else:
                progress_text = "No progress"
            self.active_table.setItem(row, 4, QTableWidgetItem(progress_text))
        
        # Update history table
        history = self.monitor.get_worker_history(50)  # Last 50 workers
        self.history_table.setRowCount(len(history))
        
        for row, worker_info in enumerate(reversed(history)):  # Most recent first
            self.history_table.setItem(row, 0, QTableWidgetItem(worker_info.worker_id))
            self.history_table.setItem(row, 1, QTableWidgetItem(worker_info.task_type))
            self.history_table.setItem(row, 2, QTableWidgetItem(worker_info.status))
            
            if worker_info.duration:
                duration_text = str(worker_info.duration).split('.')[0]
            else:
                duration_text = "N/A"
            self.history_table.setItem(row, 3, QTableWidgetItem(duration_text))
            
            error_text = worker_info.error_message or ""
            self.history_table.setItem(row, 4, QTableWidgetItem(error_text))
            
            start_time_text = worker_info.start_time.strftime("%H:%M:%S")
            self.history_table.setItem(row, 5, QTableWidgetItem(start_time_text))
        
        # Update performance stats
        stats = self.monitor.get_performance_stats()
        stats_text = "Performance Statistics:\n\n"
        
        for task_type, task_stats in stats.items():
            stats_text += f"{task_type}:\n"
            stats_text += f"  Count: {task_stats['total_tasks']}\n"
            stats_text += f"  Avg Duration: {task_stats['avg_duration']:.2f}s\n"
            stats_text += f"  Min Duration: {task_stats['min_duration']:.2f}s\n"
            stats_text += f"  Max Duration: {task_stats['max_duration']:.2f}s\n\n"
        
        self.stats_text.setPlainText(stats_text) 