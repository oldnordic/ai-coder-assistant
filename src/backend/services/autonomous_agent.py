"""
Autonomous Agent - Self-Improving Code Assistant

This module implements an autonomous agent that can analyze, fix, and improve
code automatically using specialized coding models and feedback loops.
"""

import asyncio
import logging
import os
import json
import subprocess
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from src.backend.services.coding_model_manager import CodingModelManager
from src.backend.services.scanner import ScannerService
from src.backend.services.feedback_loop import FeedbackLoopSystem
from src.backend.services.learning_mechanism import LearningMechanism
from src.backend.utils.exceptions import (
    AICoderAssistantError,
    FileOperationError,
    ScanningError,
    ModelError,
)
from src.backend.utils.config import get_config

logger = logging.getLogger(__name__)


class AutonomousAgent:
    """
    Orchestrates the automate mode for self-healing and improvement of the codebase.
    Handles session management, scanning, fix generation, testing, and learning integration.
    """
    def __init__(
        self,
        coding_model_manager: CodingModelManager,
        scanner_service: ScannerService,
        feedback_loop: FeedbackLoopSystem,
        learning_mechanism: LearningMechanism
    ):
        self.coding_model_manager = coding_model_manager
        self.scanner_service = scanner_service
        self.feedback_loop = feedback_loop
        self.learning_mechanism = learning_mechanism
        self.current_session: Optional[Dict[str, Any]] = None
        self.sessions: List[Dict[str, Any]] = []
        
        # Backup and rollback configuration
        self.backup_enabled = True
        self.backup_directory = "backups"
        self.max_backups = 10
        
        # Progress reporting
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        
        # Ensure backup directory exists
        if self.backup_enabled:
            Path(self.backup_directory).mkdir(exist_ok=True)

    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set a callback function for progress reporting."""
        self.progress_callback = callback

    def _report_progress(self, message: str, percentage: float):
        """Report progress if callback is set."""
        if self.progress_callback:
            try:
                self.progress_callback(message, percentage)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def create_backup(self, target_directory: str) -> str:
        """
        Create a backup of the target directory before making changes.
        
        Args:
            target_directory: Directory to backup
            
        Returns:
            Backup path
        """
        if not self.backup_enabled:
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}_{Path(target_directory).name}"
            backup_path = os.path.join(self.backup_directory, backup_name)
            
            # Create backup
            shutil.copytree(target_directory, backup_path, dirs_exist_ok=True)
            
            # Clean up old backups if we exceed max_backups
            self._cleanup_old_backups()
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise FileOperationError(f"Backup creation failed: {e}")

    def _cleanup_old_backups(self):
        """Remove old backups if we exceed the maximum number."""
        try:
            backup_dir = Path(self.backup_directory)
            if not backup_dir.exists():
                return
            
            backups = sorted(
                [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove excess backups
            for backup in backups[self.max_backups:]:
                shutil.rmtree(backup)
                logger.info(f"Removed old backup: {backup}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    def rollback_changes(self, backup_path: str, target_directory: str) -> bool:
        """
        Rollback changes by restoring from backup.
        
        Args:
            backup_path: Path to the backup directory
            target_directory: Directory to restore to
            
        Returns:
            True if rollback successful, False otherwise
        """
        if not backup_path or not os.path.exists(backup_path):
            logger.error(f"Backup path does not exist: {backup_path}")
            return False
        
        try:
            # Remove current directory contents
            if os.path.exists(target_directory):
                shutil.rmtree(target_directory)
            
            # Restore from backup
            shutil.copytree(backup_path, target_directory)
            
            logger.info(f"Successfully rolled back changes from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get a list of available backups."""
        backups = []
        try:
            backup_dir = Path(self.backup_directory)
            if not backup_dir.exists():
                return backups
            
            for backup in backup_dir.iterdir():
                if backup.is_dir() and backup.name.startswith("backup_"):
                    stat = backup.stat()
                    backups.append({
                        "name": backup.name,
                        "path": str(backup),
                        "created": datetime.fromtimestamp(stat.st_mtime),
                        "size": stat.st_size
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups

    def start_session(self, target_directory: str, mode: str = "autonomous") -> str:
        """
        Start an autonomous agent session for a given directory.
        """
        session_id = f"agent_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = {
            "id": session_id,
            "start_time": datetime.now(),
            "target_directory": target_directory,
            "mode": mode,
            "actions": [],
            "status": "running"
        }
        logger.info(f"Started session {session_id} for {target_directory}")
        return session_id

    def stop_session(self):
        """
        Stop the current session and archive it.
        """
        if self.current_session:
            self.current_session["end_time"] = datetime.now()
            self.current_session["status"] = "stopped"
            self.sessions.append(self.current_session)
            logger.info(f"Stopped session {self.current_session['id']}")
            self.current_session = None

    def get_current_session_status(self) -> Optional[Dict[str, Any]]:
        """
        Get the status of the current session.
        """
        return self.current_session

    def scan_codebase(self) -> List[Dict[str, Any]]:
        """
        Scan the codebase for issues using the scanner and coding model.
        Uses ScannerService.start_scan to trigger the scan and get_code_issues to retrieve issues.
        Returns a list of issues found in the codebase.
        """
        if not self.current_session:
            logger.warning("No active session. Cannot scan codebase.")
            return []
        target_directory = self.current_session["target_directory"]
        scan_id = self.scanner_service.start_scan(target_directory)
        logger.info(f"Scan started with ID: {scan_id}")
        # In a real async workflow, you would use a callback or polling. Here, we just fetch the issues synchronously for demo purposes.
        issues = self.scanner_service.persistence.get_code_issues(scan_id)
        logger.info(f"Scan found {len(issues)} issues.")
        # Convert issues to dicts for downstream processing
        return [issue.__dict__ for issue in issues]

    async def generate_and_apply_fixes(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use the coding model to generate and apply fixes for the given issues.
        For each issue:
          - Read the original code from file_path
          - Use CodingModelManager to generate a fix (AI/model call)
          - If a fix is generated and different, write it back to the file
        Returns a list of applied fixes (as dicts).
        """
        applied_fixes = []
        for issue in issues:
            file_path = issue.get("file_path")
            description = issue.get("description")
            language = issue.get("category", "python")  # Fallback to python if not specified
            if not file_path or not isinstance(file_path, str):
                applied_fixes.append({
                    "file_path": file_path,
                    "issue": description,
                    "status": "invalid_file_path",
                    "error": "file_path is missing or not a string",
                })
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_code = f.read()
            except Exception as e:
                applied_fixes.append({
                    "file_path": file_path,
                    "issue": description,
                    "status": "error_reading_file",
                    "error": str(e),
                })
                continue
            try:
                fixed_code = await self.coding_model_manager.fix_code(
                    code=original_code,
                    issues=[description],
                    language=language
                )
            except Exception as e:
                applied_fixes.append({
                    "file_path": file_path,
                    "issue": description,
                    "status": "error_generating_fix",
                    "error": str(e),
                })
                continue
            if fixed_code and fixed_code.strip() != original_code.strip():
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_code)
                    applied_fixes.append({
                        "file_path": file_path,
                        "issue": description,
                        "fixed_code": fixed_code,
                        "status": "applied",
                    })
                except Exception as e:
                    applied_fixes.append({
                        "file_path": file_path,
                        "issue": description,
                        "status": "error_writing_file",
                        "error": str(e),
                    })
            else:
                applied_fixes.append({
                    "file_path": file_path,
                    "issue": description,
                    "status": "no_change",
                })
        return applied_fixes

    async def test_fixes(self, fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Test the applied fixes in a sandbox (Docker) environment.
        For each fix:
          - Use FeedbackLoopSystem to test the fix in Docker
          - Collect test results and metadata
        Returns a list of test results (as dicts).
        """
        test_results = []
        for fix in fixes:
            file_path = fix.get("file_path")
            fixed_code = fix.get("fixed_code")
            status = fix.get("status")
            
            # Skip fixes that weren't applied or had errors
            if status != "applied" or not fixed_code:
                test_results.append({
                    "file_path": file_path,
                    "status": "skipped",
                    "reason": f"Fix status was '{status}', not 'applied'",
                })
                continue
            
            if not file_path or not isinstance(file_path, str):
                test_results.append({
                    "file_path": file_path,
                    "status": "error",
                    "error": "Invalid file path",
                })
                continue
            
            try:
                # Read the original code for comparison
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_code = f.read()
                
                # Test the fix in Docker
                test_result = await self.feedback_loop.test_fix_in_docker(
                    file_path=file_path,
                    original_code=original_code,
                    modified_code=fixed_code,
                    language="python"  # Default to python, could be detected from file extension
                )
                
                # Convert test result to dict format
                test_results.append({
                    "file_path": file_path,
                    "test_id": test_result.test_id,
                    "test_output": test_result.test_output,
                    "test_error": test_result.test_error,
                    "success": test_result.success,
                    "execution_time": test_result.execution_time,
                    "test_type": test_result.test_type,
                    "status": "tested",
                })
                
            except Exception as e:
                test_results.append({
                    "file_path": file_path,
                    "status": "error",
                    "error": str(e),
                })
        
        return test_results

    async def feed_results_to_learning(self, test_results: List[Dict[str, Any]]):
        """
        Feed the results of the tests back to the learning mechanism.
        For each test result:
          - Use LearningMechanism to process feedback for continuous improvement
        """
        processed_count = 0
        error_count = 0
        
        for test_result in test_results:
            try:
                # Create feedback data from test result
                feedback_data = {
                    "test_id": test_result.get("test_id"),
                    "file_path": test_result.get("file_path"),
                    "success": test_result.get("success", False),
                    "execution_time": test_result.get("execution_time", 0.0),
                    "test_output": test_result.get("test_output", ""),
                    "test_error": test_result.get("test_error"),
                    "test_type": test_result.get("test_type", "unknown"),
                    "status": test_result.get("status", "unknown"),
                }
                
                # Process feedback for learning
                await self.learning_mechanism.process_feedback_for_learning(feedback_data)
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing feedback for test result: {e}")
        
        logger.info(f"Learning feedback processed: {processed_count} successful, {error_count} errors")

    async def run_full_automation_cycle(self, target_directory: str):
        """
        Run a full automation cycle: scan, fix, test, learn.
        Includes backup creation and rollback on failure.
        """
        backup_path = ""
        session_id = self.start_session(target_directory)
        
        try:
            # Create backup before making changes
            if self.backup_enabled:
                backup_path = self.create_backup(target_directory)
                self._report_progress("Backup created", 5.0)
            
            # Step 1: Scan codebase (10% of progress)
            self._report_progress("Scanning codebase for issues...", 10.0)
            issues = self.scan_codebase()
            self._report_progress(f"Found {len(issues)} issues", 20.0)
            
            if not issues:
                self._report_progress("No issues found, cycle complete", 100.0)
                return
            
            # Step 2: Generate and apply fixes (40% of progress)
            self._report_progress("Generating and applying fixes...", 30.0)
            fixes = await self.generate_and_apply_fixes(issues)
            applied_fixes = [f for f in fixes if f.get("status") == "applied"]
            self._report_progress(f"Applied {len(applied_fixes)} fixes", 60.0)
            
            if not applied_fixes:
                self._report_progress("No fixes applied, cycle complete", 100.0)
                return
            
            # Step 3: Test fixes (20% of progress)
            self._report_progress("Testing fixes in Docker...", 70.0)
            test_results = await self.test_fixes(applied_fixes)
            successful_tests = [t for t in test_results if t.get("success", False)]
            self._report_progress(f"Tests completed: {len(successful_tests)}/{len(test_results)} successful", 90.0)
            
            # Step 4: Feed results to learning (10% of progress)
            self._report_progress("Processing learning feedback...", 95.0)
            await self.feed_results_to_learning(test_results)
            self._report_progress("Automation cycle completed successfully", 100.0)
            
        except Exception as e:
            logger.error(f"Automation cycle failed: {e}")
            self._report_progress(f"Automation cycle failed: {e}", 100.0)
            
            # Rollback changes if backup exists
            if backup_path and self.backup_enabled:
                self._report_progress("Rolling back changes...", 100.0)
                if self.rollback_changes(backup_path, target_directory):
                    self._report_progress("Changes rolled back successfully", 100.0)
                else:
                    self._report_progress("Rollback failed - manual intervention required", 100.0)
            
            raise
        finally:
            self.stop_session()

    def get_session_statistics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a specific session."""
        for session in self.sessions:
            if session["id"] == session_id:
                return {
                    "session_id": session["id"],
                    "start_time": session["start_time"],
                    "end_time": session.get("end_time"),
                    "target_directory": session["target_directory"],
                    "mode": session["mode"],
                    "status": session["status"],
                    "actions_count": len(session.get("actions", [])),
                    "duration": (session.get("end_time", datetime.now()) - session["start_time"]).total_seconds() if session.get("end_time") else None
                }
        return None

    def export_session_report(self, session_id: str, output_path: str) -> bool:
        """Export a detailed report for a specific session."""
        try:
            session_data = self.get_session_statistics(session_id)
            if not session_data:
                return False
            
            # Add detailed session information
            for session in self.sessions:
                if session["id"] == session_id:
                    session_data["actions"] = session.get("actions", [])
                    break
            
            # Write report to file
            with open(output_path, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"Session report exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export session report: {e}")
            return False

    async def start_autonomous_session(
        self,
        target_directory: str,
        mode: str = "autonomous",
        max_iterations: Optional[int] = None
    ) -> str:
        """
        Start an autonomous session to improve the codebase.
        
        Args:
            target_directory: Directory to analyze and improve
            mode: Session mode (autonomous, supervised, learning)
            max_iterations: Maximum number of improvement iterations
            
        Returns:
            Session ID
        """
        if not os.path.exists(target_directory):
            raise FileOperationError(f"Target directory does not exist: {target_directory}")
        
        session_id = f"agent_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = {
            "id": session_id,
            "start_time": datetime.now(),
            "target_directory": target_directory,
            "mode": mode,
            "actions": [],
            "status": "running"
        }
        
        if max_iterations:
            self.max_iterations = max_iterations
        
        logger.info(f"Started autonomous session {session_id} for {target_directory}")
        
        # Start the autonomous improvement process
        asyncio.create_task(self._run_autonomous_session())
        
        return session_id
    
    async def _run_autonomous_session(self):
        """Run the autonomous improvement session."""
        if not self.current_session:
            return
        
        try:
            logger.info(f"Running autonomous session: {self.current_session['id']}")
            
            iteration = 0
            while iteration < self.max_iterations:
                logger.info(f"Starting iteration {iteration + 1}/{self.max_iterations}")
                
                # Step 1: Analyze current state
                analysis_result = await self._analyze_codebase()
                
                if not analysis_result.get("issues"):
                    logger.info("No issues found, session complete")
                    break
                
                # Step 2: Prioritize issues
                prioritized_issues = self._prioritize_issues(analysis_result["issues"])
                
                # Step 3: Generate fixes for top issues
                fixes_generated = await self._generate_fixes(prioritized_issues[:3])
                
                if not fixes_generated:
                    logger.info("No fixes generated, session complete")
                    break
                
                # Step 4: Test fixes in sandbox
                if self.test_fixes:
                    tested_fixes = await self._test_fixes(fixes_generated)
                else:
                    tested_fixes = fixes_generated
                
                # Step 5: Apply successful fixes
                applied_fixes = await self._apply_fixes(tested_fixes)
                
                # Step 6: Learn from results
                await self._learn_from_results(applied_fixes)
                
                iteration += 1
                
                # Check if we should continue
                if not applied_fixes:
                    logger.info("No fixes applied, session complete")
                    break
            
            # Final analysis
            final_analysis = await self._analyze_codebase()
            self.current_session["success_rate"] = self._calculate_success_rate()
            
            logger.info(f"Autonomous session completed. Success rate: {self.current_session['success_rate']:.2%}")
            
        except Exception as e:
            logger.error(f"Error in autonomous session: {e}")
        finally:
            if self.current_session:
                self.current_session["end_time"] = datetime.now()
                self.sessions.append(self.current_session)
                self.current_session = None
    
    async def _analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the current codebase for issues."""
        if not self.current_session:
            raise AICoderAssistantError("No active session")
        
        try:
            # Use scanner service to find issues
            scan_result = await self.scanner_service.scan_directory(
                self.current_session["target_directory"]
            )
            
            # Use AI to analyze code quality
            ai_analysis = await self._ai_analyze_codebase()
            
            # Combine results
            combined_issues = []
            
            # Add scanner issues
            for issue in scan_result.get("issues", []):
                combined_issues.append({
                    "source": "scanner",
                    "type": issue.get("type", "unknown"),
                    "severity": issue.get("severity", "medium"),
                    "file": issue.get("file", ""),
                    "line": issue.get("line", 0),
                    "description": issue.get("description", ""),
                    "suggestion": issue.get("suggestion", "")
                })
            
            # Add AI analysis issues
            for issue in ai_analysis.get("issues", []):
                combined_issues.append({
                    "source": "ai_analysis",
                    **issue
                })
            
            return {
                "issues": combined_issues,
                "total_files": scan_result.get("total_files", 0),
                "scan_time": scan_result.get("scan_time", 0),
                "ai_analysis": ai_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing codebase: {e}")
            return {"issues": [], "error": str(e)}
    
    async def _ai_analyze_codebase(self) -> Dict[str, Any]:
        """Use AI to analyze code quality and suggest improvements."""
        if not self.current_session:
            return {"issues": []}
        
        try:
            # Get Python files in the directory
            python_files = []
            for root, dirs, files in os.walk(self.current_session["target_directory"]):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
            
            all_issues = []
            
            # Analyze each Python file
            for file_path in python_files[:10]:  # Limit to first 10 files for performance
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # Use coding model to analyze
                    analysis = await self.coding_model_manager.analyze_code(
                        code=code,
                        language="python",
                        analysis_type="comprehensive"
                    )
                    
                    # Add file information to issues
                    for issue in analysis.get("issues", []):
                        issue["file"] = file_path
                        all_issues.append(issue)
                        
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")
            
            return {
                "issues": all_issues,
                "files_analyzed": len(python_files),
                "analysis_score": analysis.get("score", "N/A")
            }
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {"issues": [], "error": str(e)}
    
    def _prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize issues based on severity and impact."""
        # Define severity weights
        severity_weights = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        # Calculate priority score for each issue
        for issue in issues:
            severity = issue.get("severity", "medium")
            weight = severity_weights.get(severity, 1)
            
            # Additional factors
            if issue.get("type") == "security":
                weight *= 2
            elif issue.get("type") == "bug":
                weight *= 1.5
            
            issue["priority_score"] = weight
        
        # Sort by priority score (highest first)
        return sorted(issues, key=lambda x: x.get("priority_score", 0), reverse=True)
    
    async def _generate_fixes(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fixes for the given issues."""
        fixes = []
        
        for issue in issues:
            try:
                file_path = issue.get("file", "")
                if not file_path or not os.path.exists(file_path):
                    continue
                
                # Read the original code
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_code = f.read()
                
                # Generate fix using AI
                fixed_code = await self.coding_model_manager.fix_code(
                    code=original_code,
                    issues=[issue.get("description", "")],
                    language="python"
                )
                
                if fixed_code and fixed_code != original_code:
                    fixes.append({
                        "issue": issue,
                        "file_path": file_path,
                        "original_code": original_code,
                        "fixed_code": fixed_code,
                        "confidence": 0.8  # Default confidence
                    })
                    
                    # Record action
                    self._record_action(
                        action_type="generate_fix",
                        target_file=file_path,
                        description=f"Generated fix for {issue.get('type', 'issue')}",
                        success=True,
                        details={"issue": issue, "fix_generated": True},
                        original_code=original_code,
                        modified_code=fixed_code
                    )
                
            except Exception as e:
                logger.error(f"Error generating fix for {issue.get('file', 'unknown')}: {e}")
                
                # Record failed action
                self._record_action(
                    action_type="generate_fix",
                    target_file=issue.get('file', 'unknown'),
                    description=f"Failed to generate fix: {e}",
                    success=False,
                    details={"issue": issue, "error": str(e)}
                )
        
        return fixes
    
    async def _test_fixes(self, fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test fixes in a sandboxed environment."""
        tested_fixes = []
        
        for fix in fixes:
            try:
                # Create temporary directory for testing
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Copy the file to temp directory
                    temp_file = os.path.join(temp_dir, os.path.basename(fix["file_path"]))
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(fix["fixed_code"])
                    
                    # Test the fix
                    test_result = await self._test_file(temp_file)
                    
                    if test_result["success"]:
                        fix["test_passed"] = True
                        fix["test_output"] = test_result["output"]
                        tested_fixes.append(fix)
                        
                        # Record successful test
                        self._record_action(
                            action_type="test_fix",
                            target_file=fix["file_path"],
                            description="Fix tested successfully",
                            success=True,
                            details={"test_output": test_result["output"]}
                        )
                    else:
                        logger.warning(f"Fix failed test for {fix['file_path']}")
                        
                        # Record failed test
                        self._record_action(
                            action_type="test_fix",
                            target_file=fix["file_path"],
                            description=f"Fix failed test: {test_result['error']}",
                            success=False,
                            details={"test_error": test_result["error"]}
                        )
                        
            except Exception as e:
                logger.error(f"Error testing fix for {fix['file_path']}: {e}")
                
                # Record test error
                self._record_action(
                    action_type="test_fix",
                    target_file=fix["file_path"],
                    description=f"Test error: {e}",
                    success=False,
                    details={"error": str(e)}
                )
        
        return tested_fixes
    
    async def _test_file(self, file_path: str) -> Dict[str, Any]:
        """Test a Python file for syntax errors and basic functionality."""
        try:
            # Check syntax
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": "Syntax check passed",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Test timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _apply_fixes(self, fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply the tested fixes to the codebase."""
        applied_fixes = []
        
        for fix in fixes:
            try:
                file_path = fix["file_path"]
                
                # Create backup if enabled
                if self.backup_before_changes:
                    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(file_path, backup_path)
                
                # Apply the fix
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fix["fixed_code"])
                
                applied_fixes.append(fix)
                
                # Record successful application
                self._record_action(
                    action_type="apply_fix",
                    target_file=file_path,
                    description=f"Applied fix for {fix['issue'].get('type', 'issue')}",
                    success=True,
                    details={"backup_created": self.backup_before_changes}
                )
                
                logger.info(f"Applied fix to {file_path}")
                
            except Exception as e:
                logger.error(f"Error applying fix to {fix['file_path']}: {e}")
                
                # Record failed application
                self._record_action(
                    action_type="apply_fix",
                    target_file=fix["file_path"],
                    description=f"Failed to apply fix: {e}",
                    success=False,
                    details={"error": str(e)}
                )
        
        return applied_fixes
    
    async def _learn_from_results(self, applied_fixes: List[Dict[str, Any]]):
        """Learn from the results of applied fixes."""
        for fix in applied_fixes:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "issue_type": fix["issue"].get("type", "unknown"),
                "severity": fix["issue"].get("severity", "medium"),
                "file_type": os.path.splitext(fix["file_path"])[1],
                "fix_applied": True,
                "test_passed": fix.get("test_passed", False),
                "confidence": fix.get("confidence", 0.0),
                "success": True
            }
            
            self.learning_data.append(learning_entry)
        
        # Save learning data
        await self._save_learning_data()
    
    async def _save_learning_data(self):
        """Save learning data to file."""
        try:
            learning_file = Path("data/agent_learning_data.json")
            learning_file.parent.mkdir(exist_ok=True)
            
            with open(learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def _record_action(self, action_type: str, target_file: str, description: str, 
                      success: bool, details: Dict[str, Any], 
                      original_code: Optional[str] = None, 
                      modified_code: Optional[str] = None):
        """Record an action taken by the agent."""
        if not self.current_session:
            return
        
        action = {
            "action_type": action_type,
            "target_file": target_file,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "details": details,
            "original_code": original_code,
            "modified_code": modified_code
        }
        
        self.current_session["actions"].append(action)
    
    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of the current session."""
        if not self.current_session or not self.current_session["actions"]:
            return 0.0
        
        successful_actions = sum(1 for action in self.current_session["actions"] if action["success"])
        total_actions = len(self.current_session["actions"])
        
        return successful_actions / total_actions if total_actions > 0 else 0.0
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific session."""
        for session in self.sessions:
            if session["id"] == session_id:
                return session
        return None
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics from learning data."""
        if not self.learning_data:
            return {"total_entries": 0}
        
        total_entries = len(self.learning_data)
        successful_fixes = sum(1 for entry in self.learning_data if entry.get("success", False))
        success_rate = successful_fixes / total_entries if total_entries > 0 else 0.0
        
        # Count by issue type
        issue_types = {}
        for entry in self.learning_data:
            issue_type = entry.get("issue_type", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        return {
            "total_entries": total_entries,
            "successful_fixes": successful_fixes,
            "success_rate": success_rate,
            "issue_types": issue_types
        }

    async def run_full_automation_cycle_yielding(self, target_directory: str):
        """
        Like run_full_automation_cycle, but yields per-fix context after each fix/test for real-time learning integration.
        """
        backup_path = ""
        session_id = self.start_session(target_directory)
        try:
            if self.backup_enabled:
                backup_path = self.create_backup(target_directory)
                self._report_progress("Backup created", 5.0)
            self._report_progress("Scanning codebase for issues...", 10.0)
            issues = self.scan_codebase()
            self._report_progress(f"Found {len(issues)} issues", 20.0)
            if not issues:
                self._report_progress("No issues found, cycle complete", 100.0)
                return
            self._report_progress("Generating and applying fixes...", 30.0)
            fixes = await self.generate_and_apply_fixes(issues)
            applied_fixes = [f for f in fixes if f.get("status") == "applied"]
            self._report_progress(f"Applied {len(applied_fixes)} fixes", 60.0)
            if not applied_fixes:
                self._report_progress("No fixes applied, cycle complete", 100.0)
                return
            self._report_progress("Testing fixes in Docker...", 70.0)
            test_results = await self.test_fixes(applied_fixes)
            self._report_progress(f"Tests completed: {len(test_results)}", 90.0)
            # Yield per-fix context for each fix/test
            for fix, test in zip(applied_fixes, test_results):
                yield {
                    "file_path": fix.get("file_path", ""),
                    "original_code": fix.get("original_code", ""),
                    "fixed_code": fix.get("fixed_code", ""),
                    "test_result": test,
                    "success": test.get("success", False)
                }
            self._report_progress("Processing learning feedback...", 95.0)
            await self.feed_results_to_learning(test_results)
            self._report_progress("Automation cycle completed successfully", 100.0)
        except Exception as e:
            logger.error(f"Automation cycle failed: {e}")
            self._report_progress(f"Automation cycle failed: {e}", 100.0)
            if backup_path and self.backup_enabled:
                self._report_progress("Rolling back changes...", 100.0)
                if self.rollback_changes(backup_path, target_directory):
                    self._report_progress("Changes rolled back successfully", 100.0)
                else:
                    self._report_progress("Rollback failed - manual intervention required", 100.0)
            raise
        finally:
            self.stop_session() 