"""Model persistence service for AI Coder Assistant."""

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.services.performance_optimization import PersistencePerformanceMonitor
from src.backend.services.task_management import DatabaseConnectionPool
from src.core.config import Config
from src.core.error import ErrorHandler, ErrorSeverity
from src.core.events import Event, EventBus, EventType
from src.core.logging import LogManager

logger = LogManager().get_logger("model_persistence")


class ModelType(Enum):
    """Model types for persistence."""

    OLLAMA = "ollama"
    LOCAL = "local"
    CLOUD = "cloud"


class ModelState(Enum):
    """Model states for persistence."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class ModelConfig:
    """Model configuration data."""

    model_id: str
    model_type: ModelType
    name: str
    version: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModelStateRecord:
    """Model state record."""

    model_id: str
    state: ModelState
    timestamp: datetime
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class ModelPersistenceService:
    """Model persistence service with robust database operations."""

    def __init__(self, data_dir: str = "data", db_name: str = "models.db"):
        """Initialize model persistence service."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / db_name
        self._lock = threading.Lock()

        # Initialize database and connection pool
        self._init_database()
        self.connection_pool = DatabaseConnectionPool(self.db_path)

        # Initialize core services
        self.config = Config()
        self.logger = LogManager().get_logger("model_persistence")
        self.error_handler = ErrorHandler()
        self.event_bus = EventBus()

        # Initialize performance monitor
        self.performance_monitor = PersistencePerformanceMonitor()

        logger.info("Model Persistence Service initialized")

    def _init_database(self):
        """Initialize database with enhanced schema and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            # Create model configurations table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_configs (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    description TEXT,
                    parameters TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Create model states table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    error_message TEXT,
                    performance_metrics TEXT,
                    FOREIGN KEY (model_id) REFERENCES model_configs (model_id) ON DELETE CASCADE
                )
            """
            )

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_configs_type ON model_configs(model_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_configs_name ON model_configs(name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_states_model_id ON model_states(model_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_states_timestamp ON model_states(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_states_state ON model_states(state)"
            )

            conn.commit()

    def _execute_with_retry(self, operation: callable, max_retries: int = 3) -> Any:
        """Execute database operation with retry logic."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                with self.connection_pool.get_connection() as conn:
                    return operation(conn)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(0.1 * (2**attempt))  # Exponential backoff
                    last_exception = e
                    continue
                raise
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (2**attempt))
                    continue
                raise
        if last_exception:
            raise last_exception
        raise Exception("Unknown error in database operation")

    def save_model_config(self, config: ModelConfig) -> bool:
        """Save model configuration to database."""

        def save_operation(conn: sqlite3.Connection) -> bool:
            conn.execute(
                """
                INSERT OR REPLACE INTO model_configs (
                    model_id, model_type, name, version, description,
                    parameters, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    config.model_id,
                    config.model_type.value,
                    config.name,
                    config.version,
                    config.description,
                    json.dumps(config.parameters),
                    json.dumps(config.metadata),
                    config.created_at.isoformat(),
                    config.updated_at.isoformat(),
                ),
            )
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(save_operation)
            if success:
                self.event_bus.publish(
                    Event(
                        type=EventType.CONFIG_CHANGED,
                        data={"model_config_saved": config.model_id},
                    )
                )
                self.logger.info(f"Saved model config: {config.model_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to save model config {config.model_id}: {e}")
            self.error_handler.handle_error(
                f"Model config save failed: {e}", ErrorSeverity.ERROR
            )
            return False

    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration from database."""

        def get_operation(conn: sqlite3.Connection) -> Optional[ModelConfig]:
            cursor = conn.execute(
                "SELECT * FROM model_configs WHERE model_id = ?", (model_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return ModelConfig(
                model_id=row[0],
                model_type=ModelType(row[1]),
                name=row[2],
                version=row[3],
                description=row[4],
                parameters=json.loads(row[5]) if row[5] else {},
                metadata=json.loads(row[6]) if row[6] else {},
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8]),
            )

        try:
            return self._execute_with_retry(get_operation)
        except Exception as e:
            self.logger.error(f"Failed to get model config {model_id}: {e}")
            return None

    def get_all_model_configs(
        self, model_type: Optional[ModelType] = None
    ) -> List[ModelConfig]:
        """Get all model configurations with optional filtering."""

        def get_all_operation(conn: sqlite3.Connection) -> List[ModelConfig]:
            query = "SELECT * FROM model_configs"
            params = []

            if model_type:
                query += " WHERE model_type = ?"
                params.append(model_type.value)

            query += " ORDER BY updated_at DESC"

            cursor = conn.execute(query, params)
            configs = []

            for row in cursor.fetchall():
                configs.append(
                    ModelConfig(
                        model_id=row[0],
                        model_type=ModelType(row[1]),
                        name=row[2],
                        version=row[3],
                        description=row[4],
                        parameters=json.loads(row[5]) if row[5] else {},
                        metadata=json.loads(row[6]) if row[6] else {},
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                    )
                )

            return configs

        try:
            return self._execute_with_retry(get_all_operation)
        except Exception as e:
            self.logger.error(f"Failed to get model configs: {e}")
            return []

    def save_model_state(self, state_record: ModelStateRecord) -> bool:
        """Save model state record to database."""

        def save_operation(conn: sqlite3.Connection) -> bool:
            conn.execute(
                """
                INSERT INTO model_states (
                    model_id, state, timestamp, error_message, performance_metrics
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    state_record.model_id,
                    state_record.state.value,
                    state_record.timestamp.isoformat(),
                    state_record.error_message,
                    json.dumps(state_record.performance_metrics),
                ),
            )
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(save_operation)
            if success:
                self.event_bus.publish(
                    Event(
                        type=(
                            EventType.MODEL_LOADED
                            if state_record.state == ModelState.LOADED
                            else EventType.MODEL_UNLOADED
                        ),
                        data={
                            "model_id": state_record.model_id,
                            "state": state_record.state.value,
                        },
                    )
                )
                self.logger.info(
                    f"Saved model state: {state_record.model_id} -> {state_record.state.value}"
                )
            return success
        except Exception as e:
            self.logger.error(
                f"Failed to save model state {state_record.model_id}: {e}"
            )
            return False

    def get_model_states(
        self, model_id: str, limit: int = 100
    ) -> List[ModelStateRecord]:
        """Get model state history."""

        def get_states_operation(conn: sqlite3.Connection) -> List[ModelStateRecord]:
            cursor = conn.execute(
                """
                SELECT * FROM model_states
                WHERE model_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (model_id, limit),
            )

            states = []
            for row in cursor.fetchall():
                states.append(
                    ModelStateRecord(
                        model_id=row[1],
                        state=ModelState(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        error_message=row[4],
                        performance_metrics=json.loads(row[5]) if row[5] else {},
                    )
                )

            return states

        try:
            return self._execute_with_retry(get_states_operation)
        except Exception as e:
            self.logger.error(f"Failed to get model states for {model_id}: {e}")
            return []

    def delete_model_config(self, model_id: str) -> bool:
        """Delete model configuration and all associated data."""

        def delete_operation(conn: sqlite3.Connection) -> bool:
            conn.execute("DELETE FROM model_configs WHERE model_id = ?", (model_id,))
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(delete_operation)
            if success:
                self.logger.info(f"Deleted model config: {model_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete model config {model_id}: {e}")
            return False

    def get_model_analytics(self) -> Dict[str, Any]:
        """Get model analytics and statistics."""

        def analytics_operation(conn: sqlite3.Connection) -> Dict[str, Any]:
            # Get total models
            cursor = conn.execute("SELECT COUNT(*) FROM model_configs")
            total_models = cursor.fetchone()[0]

            # Get models by type
            cursor = conn.execute(
                """
                SELECT model_type, COUNT(*)
                FROM model_configs
                GROUP BY model_type
            """
            )
            models_by_type = dict(cursor.fetchall())

            # Get recent state changes
            cursor = conn.execute(
                """
                SELECT state, COUNT(*)
                FROM model_states
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY state
            """
            )
            recent_states = dict(cursor.fetchall())

            return {
                "total_models": total_models,
                "models_by_type": models_by_type,
                "recent_states": recent_states,
                "last_updated": datetime.now().isoformat(),
            }

        try:
            return self._execute_with_retry(analytics_operation)
        except Exception as e:
            self.logger.error(f"Failed to get model analytics: {e}")
            return {}

    def __del__(self):
        """Cleanup connection pool on destruction."""
        if hasattr(self, "connection_pool"):
            self.connection_pool.close_all()


# Global instance for easy access
_model_persistence_service = None


def get_model_persistence_service() -> ModelPersistenceService:
    """Get the global model persistence service instance."""
    global _model_persistence_service
    if _model_persistence_service is None:
        _model_persistence_service = ModelPersistenceService()
    return _model_persistence_service
