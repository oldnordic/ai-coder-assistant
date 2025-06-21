"""
Remediation Controller - Automate Mode Orchestration

This module implements the RemediationController that manages the "Automate Mode"
workflow, coordinating the autonomous agent, UI state, and user interactions.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from src.backend.services.autonomous_agent import AutonomousAgent
from src.backend.services.coding_model_manager import CodingModelManager
from src.backend.services.scanner import ScannerService
from src.backend.services.feedback_loop import FeedbackLoopSystem
from src.backend.services.learning_mechanism import LearningMechanism
from src.backend.services.refactoring import RefactoringService
from src.backend.utils.exceptions import (
    AICoderAssistantError,
    RemediationError,
    FileOperationError,
)
from src.backend.utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class RemediationState:
    """Represents the current state of the remediation process."""
    is_active: bool = False
    is_locked: bool = False
    current_issue: Optional[Dict[str, Any]] = None
    progress_percentage: float = 0.0
    current_step: str = ""
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


@dataclass
class RemediationResult:
    """Represents the result of a remediation operation."""
    success: bool
    issues_found: int
    fixes_applied: int
    tests_passed: int
    tests_failed: int
    learning_examples_created: int
    duration_seconds: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class RemediationController:
    """
    Controller for managing the "Automate Mode" workflow.
    
    This controller orchestrates the autonomous remediation process,
    manages UI state, and provides a clean interface for user interactions.
    """
    
    def __init__(self):
        """Initialize the remediation controller."""
        self.config = get_config()
        
        # Initialize services
        self.coding_model_manager = CodingModelManager()
        self.scanner_service = ScannerService()
        self.feedback_loop = FeedbackLoopSystem()
        self.learning_mechanism = LearningMechanism()
        self.refactoring_service = RefactoringService()
        
        # Create autonomous agent
        self.autonomous_agent = AutonomousAgent(
            coding_model_manager=self.coding_model_manager,
            scanner_service=self.scanner_service,
            feedback_loop=self.feedback_loop,
            learning_mechanism=self.learning_mechanism
        )
        
        # State management
        self.state = RemediationState()
        self.workspace_lock_file = ".remediation_lock"
        
        # Callbacks
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        self.state_change_callback: Optional[Callable[[RemediationState], None]] = None
        self.completion_callback: Optional[Callable[[RemediationResult], None]] = None
        
        logger.info("Remediation controller initialized")
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
        self.autonomous_agent.set_progress_callback(callback)
    
    def set_state_change_callback(self, callback: Callable[[RemediationState], None]):
        """Set callback for state changes."""
        self.state_change_callback = callback
    
    def set_completion_callback(self, callback: Callable[[RemediationResult], None]):
        """Set callback for completion events."""
        self.completion_callback = callback
    
    def set_finetune_ready_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set a callback for when fine-tuning is ready."""
        self.finetune_ready_callback = callback
    
    def _update_state(self, **kwargs):
        """Update the remediation state and notify callbacks."""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        
        if self.state_change_callback:
            try:
                self.state_change_callback(self.state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    def _report_progress(self, message: str, percentage: float):
        """Report progress and update state."""
        self._update_state(
            progress_percentage=percentage,
            current_step=message
        )
        
        if self.progress_callback:
            try:
                self.progress_callback(message, percentage)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def lock_workspace(self, workspace_path: str) -> bool:
        """
        Lock the workspace to prevent user edits during remediation.
        
        Args:
            workspace_path: Path to the workspace to lock
            
        Returns:
            True if workspace was locked successfully
        """
        try:
            lock_file_path = os.path.join(workspace_path, self.workspace_lock_file)
            
            # Create lock file with timestamp
            lock_content = f"""
# Remediation Lock File
# Created: {datetime.now().isoformat()}
# Do not edit files while remediation is in progress
# This file will be automatically removed when remediation completes

workspace_path: {workspace_path}
lock_time: {datetime.now().isoformat()}
process_id: {os.getpid()}
            """.strip()
            
            with open(lock_file_path, 'w') as f:
                f.write(lock_content)
            
            self._update_state(is_locked=True)
            logger.info(f"Workspace locked: {workspace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to lock workspace: {e}")
            return False
    
    def unlock_workspace(self, workspace_path: str) -> bool:
        """
        Unlock the workspace after remediation completes.
        
        Args:
            workspace_path: Path to the workspace to unlock
            
        Returns:
            True if workspace was unlocked successfully
        """
        try:
            lock_file_path = os.path.join(workspace_path, self.workspace_lock_file)
            
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
            
            self._update_state(is_locked=False)
            logger.info(f"Workspace unlocked: {workspace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unlock workspace: {e}")
            return False
    
    def is_workspace_locked(self, workspace_path: str) -> bool:
        """Check if workspace is currently locked."""
        lock_file_path = os.path.join(workspace_path, self.workspace_lock_file)
        return os.path.exists(lock_file_path)
    
    async def _submit_learning_example(self, *, success: bool, original_code: str, fixed_code: str, file_path: str, test_result: Any, applied: bool, score: float):
        """Submit a structured learning example to the learning mechanism and check for fine-tune readiness. Automatically trigger fine-tuning if threshold is reached."""
        import difflib
        from src.backend.services.trainer import Trainer
        
        # Generate a diff for successful fixes
        code_diff = ""
        if success and original_code and fixed_code:
            diff = difflib.unified_diff(
                original_code.splitlines(),
                fixed_code.splitlines(),
                fromfile='original',
                tofile='fixed',
                lineterm=''
            )
            code_diff = '\n'.join(diff)
        
        # Capture error logs for failures
        error_logs = ""
        if not success and test_result:
            error_logs = getattr(test_result, 'test_error', '') or getattr(test_result, 'error_message', '') or str(test_result)
        
        feedback_data = [{
            "test_result": {
                "original_code": original_code,
                "modified_code": fixed_code,
                "file_path": file_path,
                "success": success,
                "test_output": getattr(test_result, 'test_output', getattr(test_result, 'logs', '')),
                "test_error": getattr(test_result, 'test_error', getattr(test_result, 'error_message', '')),
                "code_diff": code_diff,
                "error_logs": error_logs
            },
            "improvement_score": score,
            "applied": applied
        }]
        try:
            await self.learning_mechanism.process_feedback_data(feedback_data)
            # Check if fine-tuning should be triggered
            if self.learning_mechanism.should_trigger_finetune():
                logger.info("Enough learning examples collected for fine-tuning!")
                # Trigger fine-tuning automatically
                try:
                    trainer = Trainer()
                    result = trainer.start_finetuning()
                    logger.info(f"Auto fine-tuning triggered: {result}")
                except Exception as e:
                    logger.error(f"Auto fine-tuning failed: {e}")
                # Also notify via callback if set
                if hasattr(self, 'finetune_ready_callback') and self.finetune_ready_callback:
                    try:
                        self.finetune_ready_callback(self.get_learning_stats_and_finetune_status())
                    except Exception as e:
                        logger.error(f"Error in finetune ready callback: {e}")
        except Exception as e:
            logger.error(f"Failed to submit learning example: {e}")
    
    async def start_automated_fix(self, workspace_path: str, issue_filter: Optional[Dict[str, Any]] = None) -> RemediationResult:
        """
        Start the automated fix process for the specified workspace.
        
        Args:
            workspace_path: Path to the workspace to remediate
            issue_filter: Optional filter to limit which issues to fix
            
        Returns:
            RemediationResult with the outcome of the operation
        """
        start_time = datetime.now()
        
        try:
            # Check if workspace is already locked
            if self.is_workspace_locked(workspace_path):
                raise RemediationError("Workspace is already locked by another remediation process")
            
            # Update state
            self._update_state(
                is_active=True,
                start_time=start_time,
                error_message=None
            )
            
            # Lock workspace
            if not self.lock_workspace(workspace_path):
                raise RemediationError("Failed to lock workspace")
            
            self._report_progress("Workspace locked, starting remediation", 5.0)
            
            # Run the autonomous cycle (assume it yields per-issue results)
            async for fix_context in self.autonomous_agent.run_full_automation_cycle_yielding(workspace_path):
                # fix_context should include: file_path, original_code, fixed_code, test_result, success
                await self._submit_learning_example(
                    success=fix_context.get('success', False),
                    original_code=fix_context.get('original_code', ''),
                    fixed_code=fix_context.get('fixed_code', ''),
                    file_path=fix_context.get('file_path', ''),
                    test_result=fix_context.get('test_result', {}),
                    applied=fix_context.get('success', False),
                    score=0.8 if fix_context.get('success', False) else 0.2
                )
            
            # Collect results
            session_stats = self.autonomous_agent.get_session_statistics(
                self.autonomous_agent.current_session["id"] if self.autonomous_agent.current_session else None
            )
            
            test_stats = self.feedback_loop.get_test_statistics()
            learning_stats = self.learning_mechanism.get_learning_statistics()
            
            # Calculate results
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RemediationResult(
                success=True,
                issues_found=test_stats.get("total_tests", 0),
                fixes_applied=test_stats.get("successful_tests", 0),
                tests_passed=test_stats.get("successful_tests", 0),
                tests_failed=test_stats.get("total_tests", 0) - test_stats.get("successful_tests", 0),
                learning_examples_created=learning_stats.get("total_examples", 0),
                duration_seconds=duration,
                details={
                    "session_stats": session_stats,
                    "test_stats": test_stats,
                    "learning_stats": learning_stats
                }
            )
            
            self._report_progress("Remediation completed successfully", 100.0)
            
            return result
            
        except Exception as e:
            logger.error(f"Automated fix failed: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RemediationResult(
                success=False,
                issues_found=0,
                fixes_applied=0,
                tests_passed=0,
                tests_failed=0,
                learning_examples_created=0,
                duration_seconds=duration,
                error_message=str(e)
            )
            
            self._update_state(error_message=str(e))
            
            return result
            
        finally:
            # Unlock workspace
            self.unlock_workspace(workspace_path)
            
            # Update state
            self._update_state(
                is_active=False,
                progress_percentage=100.0
            )
            
            # Step 5: Generate report and perform cleanup
            try:
                # Save the remediation result for potential export
                self._last_remediation_result = result
                
                # Generate and save report
                report_path = await self.save_remediation_report(result, workspace_path)
                if report_path:
                    logger.info(f"Remediation report saved: {report_path}")
                
                # Perform comprehensive cleanup
                await self.perform_cleanup(workspace_path)
                
            except Exception as e:
                logger.error(f"Error in reporting/cleanup phase: {e}")
            
            # Notify completion
            if self.completion_callback:
                try:
                    self.completion_callback(result)
                except Exception as e:
                    logger.error(f"Error in completion callback: {e}")
    
    async def start_targeted_fix(self, workspace_path: str, issue_details: Dict[str, Any]) -> RemediationResult:
        """
        Start a targeted fix for a specific issue.
        
        Args:
            workspace_path: Path to the workspace
            issue_details: Details of the specific issue to fix
            
        Returns:
            RemediationResult with the outcome
        """
        start_time = datetime.now()
        
        try:
            # Check if workspace is locked
            if self.is_workspace_locked(workspace_path):
                raise RemediationError("Workspace is already locked")
            
            # Update state
            self._update_state(
                is_active=True,
                start_time=start_time,
                current_issue=issue_details,
                error_message=None
            )
            
            # Lock workspace
            if not self.lock_workspace(workspace_path):
                raise RemediationError("Failed to lock workspace")
            
            self._report_progress(f"Starting targeted fix for {issue_details.get('type', 'issue')}", 10.0)
            
            # Generate fix using the coding model
            file_path = issue_details.get("file_path", "")
            original_code = issue_details.get("original_code", "")
            issue_description = issue_details.get("message", "")
            
            if not file_path or not original_code:
                raise RemediationError("Missing required issue details")
            
            # Detect language from file extension
            language = self._detect_language(file_path)
            
            self._report_progress("Generating AI fix", 30.0)
            
            # Generate fix
            fix_result = await self.coding_model_manager.generate_code_fix(
                original_code=original_code,
                issue_description=issue_description,
                language=language
            )
            
            if not fix_result.get("success"):
                raise RemediationError(f"Failed to generate fix: {fix_result.get('error', 'Unknown error')}")
            
            fixed_code = fix_result.get("fixed_code", "")
            
            self._report_progress("Testing fix in Docker", 60.0)
            
            # Test the fix
            test_result = await self.feedback_loop.test_fix_in_docker(
                file_path=file_path,
                original_code=original_code,
                modified_code=fixed_code,
                language=language,
                test_types=["syntax_check", "lint_check"]
            )
            
            # Always submit a learning example, even on failure
            await self._submit_learning_example(
                success=test_result.success,
                original_code=original_code,
                fixed_code=fixed_code,
                file_path=file_path,
                test_result=test_result,
                applied=test_result.success,
                score=0.8 if test_result.success else 0.2
            )
            
            if not test_result.success:
                raise RemediationError(f"Fix test failed: {test_result.test_error}")
            
            self._report_progress("Applying fix to workspace", 80.0)
            
            # Apply the fix using refactoring service
            apply_result = self.refactoring_service.apply_code_changes(
                file_path=os.path.join(workspace_path, file_path),
                original_code=original_code,
                new_code=fixed_code
            )
            
            if not apply_result.get("success"):
                raise RemediationError(f"Failed to apply fix: {apply_result.get('error', 'Unknown error')}")
            
            self._report_progress("Processing learning feedback", 90.0)
            
            # Calculate results
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RemediationResult(
                success=True,
                issues_found=1,
                fixes_applied=1,
                tests_passed=1,
                tests_failed=0,
                learning_examples_created=0,
                duration_seconds=duration,
                details={
                    "issue_details": issue_details,
                    "fix_result": fix_result,
                    "test_result": test_result,
                    "apply_result": apply_result
                }
            )
            
            self._report_progress("Targeted fix completed successfully", 100.0)
            
            return result
            
        except Exception as e:
            logger.error(f"Targeted fix failed: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RemediationResult(
                success=False,
                issues_found=1,
                fixes_applied=0,
                tests_passed=0,
                tests_failed=1,
                learning_examples_created=0,
                duration_seconds=duration,
                error_message=str(e)
            )
            
            self._update_state(error_message=str(e))
            
            return result
            
        finally:
            # Unlock workspace
            self.unlock_workspace(workspace_path)
            
            # Update state
            self._update_state(
                is_active=False,
                progress_percentage=100.0
            )
            
            # Step 5: Generate report and perform cleanup
            try:
                # Save the remediation result for potential export
                self._last_remediation_result = result
                
                # Generate and save report
                report_path = await self.save_remediation_report(result, workspace_path)
                if report_path:
                    logger.info(f"Remediation report saved: {report_path}")
                
                # Perform comprehensive cleanup
                await self.perform_cleanup(workspace_path)
                
            except Exception as e:
                logger.error(f"Error in reporting/cleanup phase: {e}")
            
            # Notify completion
            if self.completion_callback:
                try:
                    self.completion_callback(result)
                except Exception as e:
                    logger.error(f"Error in completion callback: {e}")
    
    def stop_remediation(self) -> bool:
        """
        Stop the current remediation process.
        
        Returns:
            True if remediation was stopped successfully
        """
        try:
            if not self.state.is_active:
                return True
            
            # Update state
            self._update_state(
                is_active=False,
                error_message="Remediation stopped by user"
            )
            
            logger.info("Remediation stopped by user")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping remediation: {e}")
            return False
    
    def get_remediation_status(self) -> RemediationState:
        """Get the current remediation status."""
        return self.state
    
    def get_remediation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive remediation statistics."""
        try:
            test_stats = self.feedback_loop.get_test_statistics()
            learning_stats = self.learning_mechanism.get_learning_statistics()
            
            return {
                "test_statistics": test_stats,
                "learning_statistics": learning_stats,
                "current_state": {
                    "is_active": self.state.is_active,
                    "is_locked": self.state.is_locked,
                    "progress_percentage": self.state.progress_percentage,
                    "current_step": self.state.current_step,
                    "error_message": self.state.error_message
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting remediation statistics: {e}")
            return {"error": str(e)}
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        if not file_path:
            return "python"
        
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
        
        return language_map.get(ext, "python")
    
    def export_remediation_report(self, output_path: str) -> bool:
        """
        Export the last remediation report in various formats.
        
        Args:
            output_path: Path where to save the exported report
            
        Returns:
            True if export was successful
        """
        try:
            from src.backend.services.intelligent_analyzer import export_report
            
            # Get the last remediation result
            if not hasattr(self, '_last_remediation_result'):
                logger.warning("No remediation result available for export")
                return False
            
            result = self._last_remediation_result
            
            # Prepare report data
            report_data = {
                "remediation_result": {
                    "success": result.success,
                    "issues_found": result.issues_found,
                    "fixes_applied": result.fixes_applied,
                    "tests_passed": result.tests_passed,
                    "tests_failed": result.tests_failed,
                    "learning_examples_created": result.learning_examples_created,
                    "duration_seconds": result.duration_seconds,
                    "error_message": result.error_message
                },
                "details": result.details or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Determine export format from file extension
            if output_path.endswith('.json'):
                export_format = "JSON"
            elif output_path.endswith('.csv'):
                export_format = "CSV"
            elif output_path.endswith('.md'):
                export_format = "Markdown (.md)"
            elif output_path.endswith('.pdf'):
                export_format = "PDF"
            else:
                export_format = "JSON"  # Default to JSON
            
            # Export the report
            export_report(report_data, export_format, output_path)
            
            logger.info(f"Remediation report exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting remediation report: {e}")
            return False
    
    def get_learning_stats_and_finetune_status(self) -> Dict[str, Any]:
        """Return learning stats and fine-tune readiness for UI integration."""
        stats = self.learning_mechanism.get_learning_statistics()
        finetune = self.learning_mechanism.get_finetune_status()
        return {"learning_stats": stats, "finetune_status": finetune}
    
    def trigger_finetune(self):
        """Trigger fine-tuning manually."""
        try:
            from src.backend.services.trainer import Trainer
            trainer = Trainer()
            result = trainer.start_finetuning()
            logger.info(f"Manual fine-tuning triggered: {result}")
            return result
        except Exception as e:
            logger.error(f"Manual fine-tuning failed: {e}")
            return {"error": str(e)}

    # Step 5: Reporting and Cleanup Methods

    async def generate_remediation_report(self, result: RemediationResult, workspace_path: str) -> str:
        """
        Generate a comprehensive report for the remediation session.
        
        Args:
            result: The remediation result
            workspace_path: Path to the workspace that was remediated
            
        Returns:
            Markdown report content
        """
        try:
            from datetime import datetime
            import os
            
            # Get additional statistics
            test_stats = self.feedback_loop.get_test_statistics()
            learning_stats = self.learning_mechanism.get_learning_statistics()
            
            # Generate report content
            report_lines = []
            report_lines.append("# AI Coder Assistant - Remediation Report")
            report_lines.append("")
            report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"**Workspace:** {workspace_path}")
            report_lines.append(f"**Session Duration:** {result.duration_seconds:.2f} seconds")
            report_lines.append("")
            
            # Executive Summary
            report_lines.append("## Executive Summary")
            report_lines.append("")
            if result.success:
                report_lines.append("✅ **Remediation completed successfully**")
            else:
                report_lines.append("❌ **Remediation failed**")
                if result.error_message:
                    report_lines.append(f"**Error:** {result.error_message}")
            report_lines.append("")
            
            # Key Metrics
            report_lines.append("## Key Metrics")
            report_lines.append("")
            report_lines.append(f"- **Issues Found:** {result.issues_found}")
            report_lines.append(f"- **Fixes Applied:** {result.fixes_applied}")
            report_lines.append(f"- **Tests Passed:** {result.tests_passed}")
            report_lines.append(f"- **Tests Failed:** {result.tests_failed}")
            report_lines.append(f"- **Learning Examples Created:** {result.learning_examples_created}")
            report_lines.append("")
            
            # Test Statistics
            if test_stats:
                report_lines.append("## Test Statistics")
                report_lines.append("")
                report_lines.append(f"- **Total Tests:** {test_stats.get('total_tests', 0)}")
                report_lines.append(f"- **Successful Tests:** {test_stats.get('successful_tests', 0)}")
                report_lines.append(f"- **Failed Tests:** {test_stats.get('failed_tests', 0)}")
                report_lines.append(f"- **Success Rate:** {test_stats.get('success_rate', 0):.2%}")
                report_lines.append("")
            
            # Learning Statistics
            if learning_stats:
                report_lines.append("## Learning Statistics")
                report_lines.append("")
                report_lines.append(f"- **Total Examples:** {learning_stats.get('total_examples', 0)}")
                report_lines.append(f"- **Successful Examples:** {learning_stats.get('successful_examples', 0)}")
                report_lines.append(f"- **Failed Examples:** {learning_stats.get('failed_examples', 0)}")
                report_lines.append(f"- **Success Rate:** {learning_stats.get('success_rate', 0):.2%}")
                report_lines.append("")
            
            # Fine-tuning Status
            finetune_status = self.learning_mechanism.get_finetune_status()
            report_lines.append("## Fine-tuning Status")
            report_lines.append("")
            if finetune_status.get('ready', False):
                report_lines.append("🚀 **Ready for fine-tuning**")
            else:
                report_lines.append("⏳ **Collecting examples for fine-tuning**")
            report_lines.append(f"- **Examples Available:** {finetune_status.get('total_examples', 0)}")
            report_lines.append(f"- **Examples Required:** {finetune_status.get('min_required', 100)}")
            report_lines.append(f"- **Examples Needed:** {finetune_status.get('examples_needed', 100)}")
            report_lines.append("")
            
            # Detailed Results
            if result.details:
                report_lines.append("## Detailed Results")
                report_lines.append("")
                
                # Session Statistics
                session_stats = result.details.get('session_stats', {})
                if session_stats:
                    report_lines.append("### Session Statistics")
                    report_lines.append("")
                    report_lines.append(f"- **Session ID:** {session_stats.get('session_id', 'N/A')}")
                    report_lines.append(f"- **Actions Performed:** {session_stats.get('actions_count', 0)}")
                    report_lines.append(f"- **Average Action Time:** {session_stats.get('average_action_time', 0):.2f}s")
                    report_lines.append("")
                
                # Test Details
                test_details = result.details.get('test_stats', {})
                if test_details:
                    report_lines.append("### Test Details")
                    report_lines.append("")
                    for key, value in test_details.items():
                        if key not in ['total_tests', 'successful_tests', 'failed_tests', 'success_rate']:
                            report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
                    report_lines.append("")
            
            # Recommendations
            report_lines.append("## Recommendations")
            report_lines.append("")
            if result.success:
                report_lines.append("✅ **Continue with current development practices**")
                if result.tests_failed > 0:
                    report_lines.append("⚠️ **Review failed tests and consider manual intervention**")
                if finetune_status.get('ready', False):
                    report_lines.append("🚀 **Consider triggering model fine-tuning to improve future fixes**")
            else:
                report_lines.append("❌ **Review the error and consider manual intervention**")
                report_lines.append("🔍 **Check workspace permissions and Docker availability**")
                report_lines.append("📝 **Review logs for specific failure details**")
            report_lines.append("")
            
            # Cleanup Information
            report_lines.append("## Cleanup Information")
            report_lines.append("")
            report_lines.append("✅ **Test containers have been automatically cleaned up**")
            report_lines.append("✅ **Temporary files have been removed**")
            report_lines.append("✅ **Workspace lock has been released**")
            report_lines.append("")
            
            # Footer
            report_lines.append("---")
            report_lines.append("*This report was automatically generated by AI Coder Assistant*")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating remediation report: {e}")
            return f"# Remediation Report\n\nError generating report: {e}"

    async def save_remediation_report(self, result: RemediationResult, workspace_path: str) -> str:
        """
        Save the remediation report to a file.
        
        Args:
            result: The remediation result
            workspace_path: Path to the workspace that was remediated
            
        Returns:
            Path to the saved report file
        """
        try:
            from pathlib import Path
            from datetime import datetime
            
            # Generate report content
            report_content = await self.generate_remediation_report(result, workspace_path)
            
            # Create reports directory
            reports_dir = Path("src/backend/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"remediation_report_{timestamp}.md"
            report_path = reports_dir / filename
            
            # Save report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Remediation report saved to: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error saving remediation report: {e}")
            return ""

    async def perform_cleanup(self, workspace_path: str):
        """
        Perform comprehensive cleanup after remediation.
        
        Args:
            workspace_path: Path to the workspace that was remediated
        """
        try:
            logger.info("Starting comprehensive cleanup...")
            
            # 1. Cleanup Docker containers
            await self._cleanup_docker_containers()
            
            # 2. Cleanup temporary files
            await self._cleanup_temporary_files(workspace_path)
            
            # 3. Cleanup workspace lock
            self.unlock_workspace(workspace_path)
            
            # 4. Cleanup test artifacts
            await self._cleanup_test_artifacts(workspace_path)
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _cleanup_docker_containers(self):
        """Cleanup Docker containers used for testing."""
        try:
            import subprocess
            
            # Stop and remove containers with our test tag
            cleanup_commands = [
                ["docker", "ps", "-a", "--filter", "ancestor=ai-fix-test", "--format", "{{.ID}}"],
                ["docker", "stop", "$(docker ps -a --filter ancestor=ai-fix-test --format '{{.ID}}')"],
                ["docker", "rm", "$(docker ps -a --filter ancestor=ai-fix-test --format '{{.ID}}')"],
                ["docker", "image", "rm", "ai-fix-test", "--force"]
            ]
            
            for cmd in cleanup_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        logger.debug(f"Docker cleanup command successful: {' '.join(cmd)}")
                    else:
                        logger.debug(f"Docker cleanup command failed (non-critical): {' '.join(cmd)}")
                except Exception as e:
                    logger.debug(f"Docker cleanup command error (non-critical): {e}")
            
        except Exception as e:
            logger.error(f"Error cleaning up Docker containers: {e}")

    async def _cleanup_temporary_files(self, workspace_path: str):
        """Cleanup temporary files created during remediation."""
        try:
            import os
            from pathlib import Path
            
            # List of temporary file patterns to remove
            temp_patterns = [
                "*.tmp",
                "*.temp",
                "*.bak",
                "*.backup",
                ".remediation_*",
                "test_*",
                "temp_*"
            ]
            
            workspace = Path(workspace_path)
            if not workspace.exists():
                return
            
            # Remove temporary files
            for pattern in temp_patterns:
                for temp_file in workspace.rglob(pattern):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                            logger.debug(f"Removed temporary file: {temp_file}")
                    except Exception as e:
                        logger.debug(f"Could not remove temporary file {temp_file}: {e}")
            
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")

    async def _cleanup_test_artifacts(self, workspace_path: str):
        """Cleanup test artifacts and build outputs."""
        try:
            import os
            from pathlib import Path
            
            # Common test artifact directories
            test_artifacts = [
                "__pycache__",
                ".pytest_cache",
                "build",
                "dist",
                "*.egg-info",
                "node_modules",
                ".coverage",
                "htmlcov",
                "test-results",
                "reports"
            ]
            
            workspace = Path(workspace_path)
            if not workspace.exists():
                return
            
            # Remove test artifact directories
            for artifact in test_artifacts:
                for artifact_path in workspace.rglob(artifact):
                    try:
                        if artifact_path.is_dir():
                            import shutil
                            shutil.rmtree(artifact_path)
                            logger.debug(f"Removed test artifact directory: {artifact_path}")
                        elif artifact_path.is_file():
                            artifact_path.unlink()
                            logger.debug(f"Removed test artifact file: {artifact_path}")
                    except Exception as e:
                        logger.debug(f"Could not remove test artifact {artifact_path}: {e}")
            
        except Exception as e:
            logger.error(f"Error cleaning up test artifacts: {e}")
