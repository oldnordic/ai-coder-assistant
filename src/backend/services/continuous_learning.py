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
Enhanced with Unified KnowledgeBase and specialized data adapters for autonomous learning.
"""

from .trainer import train_model
from .llm_manager import LLMManager
from src.backend.utils.settings import MODEL_SAVE_PATH
from src.backend.utils import constants
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import asdict, dataclass
from collections import deque
import time
import threading
import sqlite3
import os
import json
import logging
import re
import yaml
from abc import ABC, abstractmethod


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
        data["timestamp"] = self.timestamp.isoformat()
        data["feedback_type"] = self.feedback_type.value
        if self.quality_level:
            data["quality_level"] = self.quality_level.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackData":
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data_copy["feedback_type"] = FeedbackType(data["feedback_type"])
        if data.get("quality_level"):
            data_copy["quality_level"] = DataQuality(data["quality_level"])
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
        data["timestamp"] = self.timestamp.isoformat()
        return data


class ReplayBuffer:
    """Replay buffer for preventing catastrophic forgetting."""

    def __init__(self, max_size: int = 10000, min_size: int = 1000):
        self.max_size = max_size
        self.min_size = min_size
        self.buffer: deque[FeedbackData] = deque(maxlen=max_size)
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
                len(self.buffer), size=min(batch_size, len(self.buffer)), replace=False
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

    def validate_feedback(
        self, feedback: FeedbackData
    ) -> Tuple[bool, float, List[str]]:
        """
        Validate feedback data quality.

        Returns:
            Tuple of (is_valid, quality_score, validation_errors)
        """
        errors = []
        quality_score = 0.0

        # Basic validation
        if not feedback.original_input.strip():
            errors.append("Empty original input")
            quality_score -= 0.3

        if not feedback.original_output.strip():
            errors.append("Empty original output")
            quality_score -= 0.3

        # Content quality checks
        if len(feedback.original_input) < 10:
            errors.append("Input too short")
            quality_score -= 0.2

        if len(feedback.original_output) < 10:
            errors.append("Output too short")
            quality_score -= 0.2

        # User feedback quality
        if feedback.user_rating is not None:
            if feedback.user_rating < 3:
                quality_score -= 0.2
            elif feedback.user_rating >= 4:
                quality_score += 0.2

        # Correction quality
        if feedback.feedback_type == FeedbackType.CORRECTION:
            if not feedback.corrected_output:
                errors.append("Missing corrected output for correction feedback")
                quality_score -= 0.4
            elif feedback.corrected_output == feedback.original_output:
                errors.append("Corrected output identical to original")
                quality_score -= 0.3

        # Calculate final quality score
        quality_score = max(0.0, min(1.0, quality_score + 0.5))  # Base score 0.5

        is_valid = quality_score >= self.quality_threshold and len(errors) == 0

        return is_valid, quality_score, errors

    def update_proxy_model(self, new_data: List[FeedbackData]) -> None:
        """Update the proxy model with new data."""
        # This would implement a lightweight model for validation
        # For now, we'll use simple heuristics
        pass


class KnowledgeUnit:
    """Represents a standardized unit of knowledge for the learning system."""
    
    def __init__(
        self,
        source_type: str,
        content: str,
        metadata: Dict[str, Any],
        quality_score: float = 0.5,
        timestamp: Optional[datetime] = None
    ):
        self.id = f"{source_type}_{int(time.time())}_{hash(content) % 10000}"
        self.source_type = source_type
        self.content = content
        self.metadata = metadata
        self.quality_score = quality_score
        self.timestamp = timestamp or datetime.now()
        self.usage_count = 0
        self.last_used = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "content": self.content,
            "metadata": self.metadata,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp.isoformat(),
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeUnit":
        """Create from dictionary."""
        unit = cls(
            source_type=data["source_type"],
            content=data["content"],
            metadata=data["metadata"],
            quality_score=data["quality_score"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
        unit.id = data["id"]
        unit.usage_count = data.get("usage_count", 0)
        if data.get("last_used"):
            unit.last_used = datetime.fromisoformat(data["last_used"])
        return unit


class DataAdapter(ABC):
    """Abstract base class for data adapters that process different knowledge sources."""
    
    @abstractmethod
    def can_process(self, source: Any) -> bool:
        """Check if this adapter can process the given source."""
        pass
    
    @abstractmethod
    def process(self, source: Any) -> List[KnowledgeUnit]:
        """Process the source and return knowledge units."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Return the type of source this adapter handles."""
        pass


class CodeScannerAdapter(DataAdapter):
    """Adapter for processing code scanner results (SAST, linter outputs)."""
    
    def __init__(self):
        self.source_type = "code_scanner"
    
    def can_process(self, source: Any) -> bool:
        """Check if source is a code scanner result."""
        if isinstance(source, dict):
            return any(key in source for key in ["issues", "vulnerabilities", "warnings", "errors"])
        elif isinstance(source, str):
            return any(keyword in source.lower() for keyword in ["error:", "warning:", "issue:", "vulnerability:"])
        return False
    
    def process(self, source: Any) -> List[KnowledgeUnit]:
        """Process code scanner results into knowledge units."""
        units = []
        
        if isinstance(source, dict):
            # Process structured scanner results
            for issue_type, issues in source.items():
                if isinstance(issues, list):
                    for issue in issues:
                        content = self._format_issue(issue)
                        metadata = {
                            "issue_type": issue_type,
                            "severity": issue.get("severity", "unknown"),
                            "file": issue.get("file", ""),
                            "line": issue.get("line", ""),
                            "rule": issue.get("rule", "")
                        }
                        units.append(KnowledgeUnit(
                            source_type=self.source_type,
                            content=content,
                            metadata=metadata,
                            quality_score=0.8
                        ))
        elif isinstance(source, str):
            # Process text-based scanner output
            lines = source.split('\n')
            current_issue = []
            
            for line in lines:
                if re.match(r'^[A-Z][a-z]+:', line) or re.match(r'^[A-Z]+:', line):
                    # New issue starts
                    if current_issue:
                        content = '\n'.join(current_issue)
                        units.append(KnowledgeUnit(
                            source_type=self.source_type,
                            content=content,
                            metadata={"format": "text_output"},
                            quality_score=0.6
                        ))
                    current_issue = [line]
                else:
                    current_issue.append(line)
            
            # Add last issue
            if current_issue:
                content = '\n'.join(current_issue)
                units.append(KnowledgeUnit(
                    source_type=self.source_type,
                    content=content,
                    metadata={"format": "text_output"},
                    quality_score=0.6
                ))
        
        return units
    
    def _format_issue(self, issue: Dict[str, Any]) -> str:
        """Format an issue into a standardized string."""
        parts = []
        if "file" in issue:
            parts.append(f"File: {issue['file']}")
        if "line" in issue:
            parts.append(f"Line: {issue['line']}")
        if "message" in issue:
            parts.append(f"Message: {issue['message']}")
        if "code" in issue:
            parts.append(f"Code: {issue['code']}")
        if "suggestion" in issue:
            parts.append(f"Suggestion: {issue['suggestion']}")
        
        return '\n'.join(parts)
    
    def get_source_type(self) -> str:
        return self.source_type


class DocumentationAdapter(DataAdapter):
    """Adapter for processing documentation files (.md, .rst, etc.)."""
    
    def __init__(self, docs_dir: str = "docs"):
        self.source_type = "documentation"
        self.docs_dir = Path(docs_dir)
    
    def can_process(self, source: Any) -> bool:
        """Check if source is a documentation file."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.suffix.lower() in ['.md', '.rst', '.txt', '.yaml', '.yml']
        return False
    
    def process(self, source: Any) -> List[KnowledgeUnit]:
        """Process documentation files into knowledge units."""
        units = []
        
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding='utf-8')
                    units.extend(self._process_content(content, str(path)))
                except Exception as e:
                    logger.warning(f"Failed to process documentation file {path}: {e}")
        
        return units
    
    def _process_content(self, content: str, file_path: str) -> List[KnowledgeUnit]:
        """Process documentation content into knowledge units."""
        units = []
        
        # Split by headers for markdown files
        if file_path.endswith('.md'):
            sections = self._split_markdown_sections(content)
            for section in sections:
                if len(section.strip()) > 50:  # Minimum content threshold
                    units.append(KnowledgeUnit(
                        source_type=self.source_type,
                        content=section,
                        metadata={
                            "file": file_path,
                            "format": "markdown",
                            "section_length": len(section)
                        },
                        quality_score=0.9
                    ))
        else:
            # For other formats, treat as single unit
            if len(content.strip()) > 50:
                units.append(KnowledgeUnit(
                    source_type=self.source_type,
                    content=content,
                    metadata={
                        "file": file_path,
                        "format": Path(file_path).suffix[1:],
                        "content_length": len(content)
                    },
                    quality_score=0.8
                ))
        
        return units
    
    def _split_markdown_sections(self, content: str) -> List[str]:
        """Split markdown content into sections based on headers."""
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.startswith('#'):
                # New header found
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def get_source_type(self) -> str:
        return self.source_type


class UserInteractionAdapter(DataAdapter):
    """Adapter for processing user interactions and manual fixes."""
    
    def __init__(self):
        self.source_type = "user_interaction"
    
    def can_process(self, source: Any) -> bool:
        """Check if source is a user interaction."""
        if isinstance(source, dict):
            return any(key in source for key in ["user_action", "manual_fix", "correction", "feedback"])
        return False
    
    def process(self, source: Any) -> List[KnowledgeUnit]:
        """Process user interactions into knowledge units."""
        units = []
        
        if isinstance(source, dict):
            # Process structured user interaction
            action_type = source.get("user_action", "unknown")
            original_code = source.get("original_code", "")
            corrected_code = source.get("corrected_code", "")
            explanation = source.get("explanation", "")
            
            if original_code and corrected_code:
                content = f"Original Code:\n{original_code}\n\nCorrected Code:\n{corrected_code}"
                if explanation:
                    content += f"\n\nExplanation:\n{explanation}"
                
                metadata = {
                    "action_type": action_type,
                    "has_explanation": bool(explanation),
                    "code_length": len(original_code)
                }
                
                units.append(KnowledgeUnit(
                    source_type=self.source_type,
                    content=content,
                    metadata=metadata,
                    quality_score=0.95  # High quality as it's user-verified
                ))
        
        return units
    
    def get_source_type(self) -> str:
        return self.source_type


class WebContentAdapter(DataAdapter):
    """Adapter for processing web content and YouTube tutorials."""
    
    def __init__(self):
        self.source_type = "web_content"
    
    def can_process(self, source: Any) -> bool:
        """Check if source is web content."""
        if isinstance(source, dict):
            return any(key in source for key in ["url", "web_content", "youtube_transcript"])
        elif isinstance(source, str):
            return source.startswith(('http://', 'https://')) or 'youtube.com' in source
        return False
    
    def process(self, source: Any) -> List[KnowledgeUnit]:
        """Process web content into knowledge units."""
        units = []
        
        if isinstance(source, dict):
            content = source.get("content", "")
            url = source.get("url", "")
            title = source.get("title", "")
            
            if content:
                # Split content into manageable chunks
                chunks = self._split_content(content)
                for i, chunk in enumerate(chunks):
                    if len(chunk.strip()) > 100:  # Minimum content threshold
                        units.append(KnowledgeUnit(
                            source_type=self.source_type,
                            content=chunk,
                            metadata={
                                "url": url,
                                "title": title,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "content_type": "web_page"
                            },
                            quality_score=0.7
                        ))
        
        return units
    
    def _split_content(self, content: str, max_chunk_size: int = 2000) -> List[str]:
        """Split content into manageable chunks."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in content.split('\n\n'):
            if current_size + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_size += len(paragraph)
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def get_source_type(self) -> str:
        return self.source_type


class ProjectRulesAdapter(DataAdapter):
    """Adapter for processing project rules and configuration files."""
    
    def __init__(self):
        self.source_type = "project_rules"
    
    def can_process(self, source: Any) -> bool:
        """Check if source is a project rules file."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.name in ['.flake8', 'pyproject.toml', 'setup.cfg', 'code_standards_config.json']
        return False
    
    def process(self, source: Any) -> List[KnowledgeUnit]:
        """Process project rules into knowledge units."""
        units = []
        
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding='utf-8')
                    units.extend(self._process_rules_file(content, str(path)))
                except Exception as e:
                    logger.warning(f"Failed to process rules file {path}: {e}")
        
        return units
    
    def _process_rules_file(self, content: str, file_path: str) -> List[KnowledgeUnit]:
        """Process rules file content into knowledge units."""
        units = []
        
        if file_path.endswith('.json'):
            try:
                rules = json.loads(content)
                units.append(KnowledgeUnit(
                    source_type=self.source_type,
                    content=json.dumps(rules, indent=2),
                    metadata={
                        "file": file_path,
                        "format": "json",
                        "rule_count": len(rules) if isinstance(rules, dict) else 0
                    },
                    quality_score=0.9
                ))
            except json.JSONDecodeError:
                pass
        elif file_path.endswith('.toml'):
            units.append(KnowledgeUnit(
                source_type=self.source_type,
                content=content,
                metadata={
                    "file": file_path,
                    "format": "toml"
                },
                quality_score=0.9
            ))
        else:
            # Process as text
            units.append(KnowledgeUnit(
                source_type=self.source_type,
                content=content,
                metadata={
                    "file": file_path,
                    "format": "text"
                },
                quality_score=0.8
            ))
        
        return units
    
    def get_source_type(self) -> str:
        return self.source_type


class UnifiedKnowledgeBase:
    """Central knowledge aggregator that manages all learning data sources."""
    
    def __init__(self, data_dir: str = "continuous_learning_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize adapters
        self.adapters: List[DataAdapter] = [
            CodeScannerAdapter(),
            DocumentationAdapter(),
            UserInteractionAdapter(),
            WebContentAdapter(),
            ProjectRulesAdapter()
        ]
        
        # Knowledge storage
        self.knowledge_db_path = self.data_dir / "knowledge_base.db"
        self._init_knowledge_database()
        
        # Statistics
        self.stats = {
            "total_units": 0,
            "units_by_source": {},
            "last_update": None
        }
    
    def _init_knowledge_database(self):
        """Initialize the knowledge database."""
        with sqlite3.connect(self.knowledge_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_units (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT
                )
            """)
            conn.commit()
    
    def add_knowledge(self, source: Any) -> List[str]:
        """Add knowledge from a source using appropriate adapters."""
        added_ids = []
        
        for adapter in self.adapters:
            if adapter.can_process(source):
                try:
                    units = adapter.process(source)
                    for unit in units:
                        self._store_knowledge_unit(unit)
                        added_ids.append(unit.id)
                        logger.info(f"Added knowledge unit {unit.id} from {adapter.get_source_type()}")
                except Exception as e:
                    logger.error(f"Failed to process source with {adapter.get_source_type()} adapter: {e}")
        
        if added_ids:
            self._update_stats()
        
        return added_ids
    
    def _store_knowledge_unit(self, unit: KnowledgeUnit):
        """Store a knowledge unit in the database."""
        with sqlite3.connect(self.knowledge_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_units 
                (id, source_type, content, metadata, quality_score, timestamp, usage_count, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                unit.id,
                unit.source_type,
                unit.content,
                json.dumps(unit.metadata),
                unit.quality_score,
                unit.timestamp.isoformat(),
                unit.usage_count,
                unit.last_used.isoformat() if unit.last_used else None
            ))
            conn.commit()
    
    def get_knowledge_units(
        self,
        source_type: Optional[str] = None,
        min_quality: float = 0.0,
        limit: Optional[int] = None
    ) -> List[KnowledgeUnit]:
        """Retrieve knowledge units with optional filtering."""
        query = "SELECT * FROM knowledge_units WHERE quality_score >= ?"
        params = [min_quality]
        
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
        
        query += " ORDER BY quality_score DESC, usage_count DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        units = []
        with sqlite3.connect(self.knowledge_db_path) as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                unit = KnowledgeUnit(
                    source_type=row[1],
                    content=row[2],
                    metadata=json.loads(row[3]),
                    quality_score=row[4],
                    timestamp=datetime.fromisoformat(row[5])
                )
                unit.id = row[0]
                unit.usage_count = row[6]
                if row[7]:
                    unit.last_used = datetime.fromisoformat(row[7])
                units.append(unit)
        
        return units
    
    def update_usage(self, unit_id: str):
        """Update usage statistics for a knowledge unit."""
        with sqlite3.connect(self.knowledge_db_path) as conn:
            conn.execute("""
                UPDATE knowledge_units 
                SET usage_count = usage_count + 1, last_used = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), unit_id))
            conn.commit()
    
    def _update_stats(self):
        """Update knowledge base statistics."""
        with sqlite3.connect(self.knowledge_db_path) as conn:
            # Total units
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_units")
            self.stats["total_units"] = cursor.fetchone()[0]
            
            # Units by source
            cursor = conn.execute("""
                SELECT source_type, COUNT(*) 
                FROM knowledge_units 
                GROUP BY source_type
            """)
            self.stats["units_by_source"] = dict(cursor.fetchall())
            
            self.stats["last_update"] = datetime.now().isoformat()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        self._update_stats()
        return self.stats.copy()
    
    def export_knowledge(self, output_path: str, source_type: Optional[str] = None):
        """Export knowledge units to a file."""
        units = self.get_knowledge_units(source_type=source_type)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_units": len(units),
            "source_type_filter": source_type,
            "units": [unit.to_dict() for unit in units]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(units)} knowledge units to {output_path}")


class ContinuousLearningService:
    """
    Enhanced Continuous Learning Service with Unified KnowledgeBase integration.
    Implements autonomous learning capabilities with data adapters and fine-tuning support.
    """

    def __init__(
        self,
        data_dir: str = "continuous_learning_data",
        model_manager: Optional[LLMManager] = None,
        quality_threshold: float = 0.7,
        replay_buffer_size: int = 10000,
        enable_autonomous_learning: bool = True,
    ):
        """Initialize the enhanced continuous learning service."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Core components
        self.model_manager = model_manager
        self.quality_threshold = quality_threshold
        self.replay_buffer = ReplayBuffer(max_size=replay_buffer_size)
        self.validator = DataValidator(quality_threshold=quality_threshold)
        
        # Enhanced components for autonomous learning
        self.enable_autonomous_learning = enable_autonomous_learning
        self.knowledge_base = UnifiedKnowledgeBase(str(self.data_dir))
        
        # Database initialization
        self.db_path = self.data_dir / "continuous_learning.db"
        self._init_database()
        
        # Learning configuration
        self.learning_config = {
            "auto_fine_tune_interval_hours": 24,
            "min_samples_for_fine_tuning": 100,
            "preferred_model": "codeollama",
            "fine_tuning_batch_size": 50,
            "knowledge_integration_enabled": True
        }
        
        # Statistics and monitoring
        self.stats = {
            "total_feedback": 0,
            "valid_feedback": 0,
            "knowledge_units_added": 0,
            "fine_tuning_runs": 0,
            "last_fine_tuning": None
        }
        
        logger.info("Enhanced Continuous Learning Service initialized with autonomous learning capabilities")

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                # Create feedback_data table
                conn.execute(
                    """
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
                """
                )

                # Create model_updates table
                conn.execute(
                    """
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
                """
                )

                # Create indexes for better performance
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback_data(timestamp)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_feedback_accepted ON feedback_data(accepted)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_feedback_quality ON feedback_data(quality_score)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_updates_timestamp ON model_updates(timestamp)"
                )

                logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def collect_feedback(
        self,
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
        processing_time_ms: Optional[int] = None,
    ) -> str:
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
            processing_time_ms=processing_time_ms,
        )

        # Validate feedback
        is_valid, quality_score, validation_errors = self.validator.validate_feedback(
            feedback
        )

        feedback.quality_score = quality_score
        feedback.quality_level = self._get_quality_level(quality_score)
        feedback.validation_errors = validation_errors if not is_valid else None

        # Store feedback
        self._store_feedback(feedback)

        # Add to replay buffer if valid
        if is_valid:
            self.replay_buffer.add(feedback)
            self.stats["valid_feedback"] += 1
            logger.info(
                f"Feedback {feedback_id} accepted (quality: {quality_score:.3f})"
            )
        else:
            logger.warning(f"Feedback {feedback_id} rejected: {validation_errors}")

        self.stats["total_feedback"] += 1

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
            conn.execute(
                """
                INSERT INTO feedback_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
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
                    (
                        json.dumps(feedback.validation_errors)
                        if feedback.validation_errors
                        else None
                    ),
                    1,  # accepted column
                ),
            )

    def get_feedback_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
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
            if date_filter:
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN quality_score >= ? THEN 1 ELSE 0 END) as accepted,
                        SUM(CASE WHEN quality_score < ? THEN 1 ELSE 0 END) as rejected
                    FROM feedback_data WHERE timestamp >= ? AND timestamp <= ?
                """,
                    [self.quality_threshold, self.quality_threshold] + params,
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN quality_score >= ? THEN 1 ELSE 0 END) as accepted,
                        SUM(CASE WHEN quality_score < ? THEN 1 ELSE 0 END) as rejected
                    FROM feedback_data
                """,
                    [self.quality_threshold, self.quality_threshold],
                )

            row = cursor.fetchone()
            total, accepted, rejected = row

            # Get feedback type distribution
            if date_filter:
                cursor = conn.execute(
                    """
                    SELECT feedback_type, COUNT(*) as count
                    FROM feedback_data WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY feedback_type
                """,
                    params,
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT feedback_type, COUNT(*) as count
                    FROM feedback_data
                    GROUP BY feedback_type
                """
                )

            type_distribution = dict(cursor.fetchall())

            # Get quality distribution
            if date_filter:
                cursor = conn.execute(
                    """
                    SELECT quality_level, COUNT(*) as count
                    FROM feedback_data WHERE timestamp >= ? AND timestamp <= ? AND quality_level IS NOT NULL
                    GROUP BY quality_level
                """,
                    params,
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT quality_level, COUNT(*) as count
                    FROM feedback_data WHERE quality_level IS NOT NULL
                    GROUP BY quality_level
                """
                )
            quality_distribution = dict(cursor.fetchall())

            return {
                "total": total or 0,
                "accepted": accepted or 0,
                "rejected": rejected or 0,
                "acceptance_rate": (accepted / total * 100) if total else 0,
                "type_distribution": type_distribution,
                "quality_distribution": quality_distribution,
                "replay_buffer_size": self.replay_buffer.get_size(),
                "model_updates": self.stats["model_updates"],
                "successful_updates": self.stats["successful_updates"],
                "failed_updates": self.stats["failed_updates"],
                "rollbacks": self.stats["rollbacks"],
            }

    def trigger_model_update(
        self, batch_size: int = 100, force_update: bool = False
    ) -> Optional[str]:
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
                logger.error(
                    f"Insufficient valid samples: {len(valid_samples)}/{batch_size}"
                )
                return None

            if not valid_samples and force_update:
                logger.warning("No valid samples available, but forcing update")
                valid_samples = self._get_replay_buffer_samples(batch_size)

                # If still no samples, create minimal training data
                if not valid_samples:
                    logger.warning(
                        "No replay buffer samples available, creating minimal training data"
                    )
                    valid_samples = []
                    for i in range(batch_size):
                        valid_samples.append(
                            FeedbackData(
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
                                quality_level=DataQuality.EXCELLENT,
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
                rollback_performed=False,
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

            with open(tmpfile_path, "w", encoding="utf-8") as f:
                for sample in valid_samples:
                    # Format for training: input + output
                    training_text = (
                        f"{sample.original_input}\n{sample.original_output}\n"
                    )
                    if sample.corrected_output:
                        training_text = (
                            f"{sample.original_input}\n{sample.corrected_output}\n"
                        )
                    f.write(training_text + "\n")

            logger.info(f"Exported {len(valid_samples)} samples to {tmpfile_path}")

            # --- INTEGRATION: Call trainer for incremental finetuning ---
            logger.info(
                f"Performing incremental update with {len(valid_samples)} samples using {tmpfile_path}"
            )
            train_result = train_model(
                vocab_dir=None,  # Not used in finetune mode
                model_save_path=MODEL_SAVE_PATH,
                finetune=True,
                training_data_path=tmpfile_path,
                log_message_callback=logger.info,
                progress_callback=lambda c, t, m: logger.info(f"Progress: {c}/{t} {m}"),
            )

            # Clean up temporary file
            try:
                os.remove(tmpfile_path)
            except OSError:
                pass

            # Evaluate model performance
            performance_change = self._evaluate_model_performance(update_id)

            # Check if rollback is needed
            if (
                performance_change is not None and performance_change < -0.1
            ):  # 10% degradation threshold
                logger.warning(
                    f"Performance degradation detected: {performance_change:.3f}. Initiating rollback."
                )
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
            self.stats["model_updates"] += 1
            if update_record.status == "completed":
                self.stats["successful_updates"] += 1
            elif update_record.status == "rolled_back":
                self.stats["rollbacks"] += 1
            else:
                self.stats["failed_updates"] += 1

            logger.info(f"Model update {update_id} {update_record.status}")
            return update_id

        except Exception as e:
            logger.error(f"Model update failed: {e}")
            self._update_in_progress = False

            # Update the record with failure status
            if "update_record" in locals():
                update_record.status = "failed"
                update_record.error_message = str(e)
                self._save_update_record(update_record)

                # Update statistics
                self.stats["model_updates"] += 1
                self.stats["failed_updates"] += 1

            # Attempt rollback on error
            if "backup_path" in locals() and os.path.exists(backup_path):
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
                f.user_rating
                for f in recent_feedback
                if f.timestamp < update_time - timedelta(hours=1)
                and f.user_rating is not None
            ]

            after_ratings = [
                f.user_rating
                for f in recent_feedback
                if f.timestamp >= update_time - timedelta(hours=1)
                and f.user_rating is not None
            ]

            if not before_ratings or not after_ratings:
                logger.warning("Insufficient data for performance evaluation")
                return None

            before_avg = sum(before_ratings) / len(before_ratings)
            after_avg = sum(after_ratings) / len(after_ratings)

            performance_change = after_avg - before_avg

            logger.info(
                f"Performance evaluation: {before_avg:.2f} -> {after_avg:.2f} (change: {performance_change:+.3f})"
            )

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
                cursor.execute(
                    """
                    SELECT id, timestamp, feedback_type, original_input, original_output,
                           corrected_output, user_rating, user_comment, quality_score,
                           accepted, validation_errors
                    FROM feedback_data
                    WHERE timestamp >= ? AND accepted = 1
                    ORDER BY timestamp DESC
                """,
                    (cutoff_date.isoformat(),),
                )

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
                cursor.execute(
                    """
                    SELECT id, timestamp, feedback_type, original_input, original_output,
                           corrected_output, user_rating, user_comment, quality_score,
                           accepted, validation_errors
                    FROM feedback_data
                    WHERE accepted = 1 AND quality_score >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (self.quality_threshold, batch_size),
                )

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
            quality_level=(
                DataQuality.EXCELLENT
                if row[8] and row[8] >= 0.8
                else (
                    DataQuality.GOOD
                    if row[8] and row[8] >= 0.6
                    else DataQuality.ACCEPTABLE
                )
            ),
            validation_errors=json.loads(row[10]) if row[10] else None,
        )

    def _save_update_record(self, update_record: ModelUpdate) -> None:
        """Save model update record to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO model_updates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
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
                    update_record.rollback_performed,
                ),
            )

    def get_update_history(self, limit: int = 10) -> List[ModelUpdate]:
        """Get recent model update history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, timestamp, model_version, previous_version, samples_processed,
                           samples_accepted, samples_rejected, quality_threshold,
                           pre_update_accuracy, post_update_accuracy, performance_change,
                           status, error_message, rollback_performed
                    FROM model_updates
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

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
                        rollback_performed=bool(row[13]),
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
                cursor.execute(
                    """
                    DELETE FROM feedback_data
                    WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old feedback records")
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

    def export_data(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> None:
        """Export feedback data to JSON file."""
        feedback_data = self._get_feedback_in_range(start_date, end_date)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_feedback": len(feedback_data),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "feedback": [feedback.to_dict() for feedback in feedback_data],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(feedback_data)} feedback records to {output_path}")

    # New methods for autonomous learning

    def add_knowledge_source(self, source: Any) -> List[str]:
        """Add knowledge from various sources using the Unified KnowledgeBase."""
        if not self.enable_autonomous_learning:
            logger.info("Autonomous learning is disabled")
            return []
        
        try:
            added_ids = self.knowledge_base.add_knowledge(source)
            self.stats["knowledge_units_added"] += len(added_ids)
            logger.info(f"Added {len(added_ids)} knowledge units from source")
            return added_ids
        except Exception as e:
            logger.error(f"Failed to add knowledge source: {e}")
            return []

    def get_knowledge_for_context(self, context: str, limit: int = 10) -> List[KnowledgeUnit]:
        """Retrieve relevant knowledge units for a given context."""
        if not self.enable_autonomous_learning:
            return []
        
        try:
            # Simple keyword-based retrieval (can be enhanced with embeddings)
            units = self.knowledge_base.get_knowledge_units(min_quality=0.5, limit=limit * 2)
            
            # Filter by relevance (simple keyword matching for now)
            relevant_units = []
            context_lower = context.lower()
            
            for unit in units:
                if any(keyword in unit.content.lower() for keyword in context_lower.split()):
                    relevant_units.append(unit)
                    if len(relevant_units) >= limit:
                        break
            
            return relevant_units
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge for context: {e}")
            return []

    def trigger_autonomous_fine_tuning(self, force: bool = False) -> Optional[str]:
        """Trigger autonomous fine-tuning using accumulated knowledge and feedback."""
        if not self.enable_autonomous_learning:
            logger.info("Autonomous learning is disabled")
            return None
        
        try:
            # Check if we have enough data
            total_samples = self.stats["valid_feedback"] + self.stats["knowledge_units_added"]
            if total_samples < self.learning_config["min_samples_for_fine_tuning"] and not force:
                logger.info(f"Insufficient samples for fine-tuning: {total_samples}/{self.learning_config['min_samples_for_fine_tuning']}")
                return None
            
            # Check if enough time has passed since last fine-tuning
            if not force and self.stats["last_fine_tuning"]:
                last_tuning = datetime.fromisoformat(self.stats["last_fine_tuning"])
                hours_since = (datetime.now() - last_tuning).total_seconds() / 3600
                if hours_since < self.learning_config["auto_fine_tune_interval_hours"]:
                    logger.info(f"Fine-tuning interval not reached: {hours_since:.1f}h/{self.learning_config['auto_fine_tune_interval_hours']}h")
                    return None
            
            logger.info("Starting autonomous fine-tuning process...")
            
            # Prepare training data
            training_data = self._prepare_training_data_for_fine_tuning()
            
            if not training_data:
                logger.warning("No training data available for fine-tuning")
                return None
            
            # Perform fine-tuning
            result = self._perform_fine_tuning(training_data)
            
            if result:
                self.stats["fine_tuning_runs"] += 1
                self.stats["last_fine_tuning"] = datetime.now().isoformat()
                logger.info("Autonomous fine-tuning completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Autonomous fine-tuning failed: {e}")
            return None

    def _prepare_training_data_for_fine_tuning(self) -> List[Dict[str, str]]:
        """Prepare training data from feedback and knowledge base."""
        training_data = []
        
        # Get high-quality feedback
        feedback_samples = self._get_valid_samples(self.learning_config["fine_tuning_batch_size"])
        
        for feedback in feedback_samples:
            # Create training example from feedback
            if feedback.feedback_type == FeedbackType.CORRECTION and feedback.corrected_output:
                training_data.append({
                    "input": feedback.original_input,
                    "output": feedback.corrected_output,
                    "source": "user_correction",
                    "quality": feedback.quality_score or 0.5
                })
            elif feedback.user_rating and feedback.user_rating >= 4:
                training_data.append({
                    "input": feedback.original_input,
                    "output": feedback.original_output,
                    "source": "user_approval",
                    "quality": feedback.quality_score or 0.5
                })
        
        # Get high-quality knowledge units
        knowledge_units = self.knowledge_base.get_knowledge_units(
            min_quality=0.7,
            limit=self.learning_config["fine_tuning_batch_size"]
        )
        
        for unit in knowledge_units:
            if unit.source_type == "code_scanner":
                # Convert scanner results to training examples
                training_data.append({
                    "input": f"Analyze this code for issues: {unit.metadata.get('code', '')}",
                    "output": unit.content,
                    "source": "code_scanner",
                    "quality": unit.quality_score
                })
            elif unit.source_type == "documentation":
                # Convert documentation to training examples
                training_data.append({
                    "input": f"Explain this concept: {unit.metadata.get('title', '')}",
                    "output": unit.content,
                    "source": "documentation",
                    "quality": unit.quality_score
                })
        
        return training_data

    def _perform_fine_tuning(self, training_data: List[Dict[str, str]]) -> Optional[str]:
        """Perform the actual fine-tuning process."""
        try:
            # Create training dataset
            dataset_path = self.data_dir / "autonomous_training_dataset.json"
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            # Get preferred model for fine-tuning
            preferred_model = self.learning_config["preferred_model"]
            
            # Perform fine-tuning using the trainer
            result = train_model(
                vocab_dir=str(self.data_dir),
                model_save_path=str(self.data_dir / "autonomous_model"),
                finetune=True,
                training_data_path=str(dataset_path),
                base_model=preferred_model,
                log_message_callback=logger.info
            )
            
            if "Success" in result:
                logger.info(f"Fine-tuning completed: {result}")
                return result
            else:
                logger.error(f"Fine-tuning failed: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error during fine-tuning: {e}")
            return None

    def get_autonomous_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for autonomous learning."""
        stats = self.stats.copy()
        stats.update({
            "knowledge_base_stats": self.knowledge_base.get_stats(),
            "learning_config": self.learning_config,
            "autonomous_learning_enabled": self.enable_autonomous_learning
        })
        return stats

    def configure_autonomous_learning(self, config: Dict[str, Any]) -> None:
        """Configure autonomous learning parameters."""
        for key, value in config.items():
            if key in self.learning_config:
                self.learning_config[key] = value
                logger.info(f"Updated learning config: {key} = {value}")
            else:
                logger.warning(f"Unknown learning config key: {key}")

    def enable_autonomous_learning_mode(self, enabled: bool = True) -> None:
        """Enable or disable autonomous learning mode."""
        self.enable_autonomous_learning = enabled
        logger.info(f"Autonomous learning mode {'enabled' if enabled else 'disabled'}")

    def _get_feedback_in_range(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[FeedbackData]:
        """Get feedback data within a date range."""
        try:
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

                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                cursor = conn.cursor()
                if conditions:
                    cursor.execute(
                        f"""
                        SELECT id, timestamp, feedback_type, original_input, original_output,
                               corrected_output, user_rating, user_comment, quality_score,
                               validation_errors
                        FROM feedback_data {where_clause}
                        ORDER BY timestamp DESC
                    """,
                        params,
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, timestamp, feedback_type, original_input, original_output,
                               corrected_output, user_rating, user_comment, quality_score,
                               validation_errors
                        FROM feedback_data
                        ORDER BY timestamp DESC
                    """
                    )

                feedback_data = []
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
                        quality_level=(
                            DataQuality.EXCELLENT
                            if row[8] and row[8] >= 0.8
                            else (
                                DataQuality.GOOD
                                if row[8] and row[8] >= 0.6
                                else DataQuality.ACCEPTABLE
                            )
                        ),
                        validation_errors=json.loads(row[9]) if row[9] else None,
                    )
                    feedback_data.append(feedback)

                return feedback_data

        except Exception as e:
            logger.error(f"Error getting feedback in range: {e}")
            return []


# Global instance for easy access
_continuous_learning_service: Optional[ContinuousLearningService] = None


def get_continuous_learning_service() -> ContinuousLearningService:
    """Get or create global continuous learning service instance."""
    global _continuous_learning_service
    if _continuous_learning_service is None:
        _continuous_learning_service = ContinuousLearningService()
    return _continuous_learning_service
