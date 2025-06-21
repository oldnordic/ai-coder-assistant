# Autonomous Workflow Quick Start Guide

## Overview

This guide provides a quick introduction to using the autonomous workflow features of the AI Coder Assistant.

## Prerequisites

1. **Docker**: Required for testing fixes in isolated environments
2. **Python 3.8+**: Required for running the autonomous workflow
3. **Required Dependencies**: Install via `poetry install`

## Quick Start

### 1. Run the Demo

The easiest way to see the autonomous workflow in action is to run the demonstration:

```bash
python test_autonomous_workflow.py
```

This will:
- Create a test codebase with intentional bugs
- Simulate the complete autonomous cycle
- Generate detailed reports
- Save results to `test_reports/`

### 2. Basic Usage

```python
import asyncio
from src.backend.services.autonomous_agent import AutonomousAgent
from src.backend.services.coding_model_manager import CodingModelManager
from src.backend.services.scanner import ScannerService
from src.backend.services.feedback_loop import FeedbackLoopSystem
from src.backend.services.learning_mechanism import LearningMechanism

async def main():
    # Initialize components
    coding_manager = CodingModelManager()
    scanner_service = ScannerService()
    feedback_loop = FeedbackLoopSystem()
    learning_mechanism = LearningMechanism()
    
    # Create autonomous agent
    agent = AutonomousAgent(
        coding_model_manager=coding_manager,
        scanner_service=scanner_service,
        feedback_loop=feedback_loop,
        learning_mechanism=learning_mechanism
    )
    
    # Set up progress reporting
    def progress_callback(message: str, percentage: float):
        print(f"[{percentage:.1f}%] {message}")
    
    agent.set_progress_callback(progress_callback)
    
    # Run autonomous cycle
    await agent.run_full_automation_cycle("/path/to/your/codebase")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Individual Component Usage

#### Testing a Fix with Docker

```python
from src.backend.services.feedback_loop import FeedbackLoopSystem

feedback_loop = FeedbackLoopSystem()

# Test a code fix
test_result = await feedback_loop.test_fix_in_docker(
    file_path="example.py",
    original_code="def test(): pass",
    modified_code="def test():\n    return True",
    language="python",
    test_types=["syntax_check", "lint_check"]
)

print(f"Test success: {test_result.success}")
print(f"Execution time: {test_result.execution_time}s")
```

#### Processing Learning Data

```python
from src.backend.services.learning_mechanism import LearningMechanism

learning_mechanism = LearningMechanism()

# Process feedback data
feedback_data = [
    {
        "test_result": {
            "original_code": "def test(): pass",
            "modified_code": "def test():\n    return True",
            "success": True,
            "test_output": "Syntax check passed"
        },
        "improvement_score": 0.8,
        "applied": True
    }
]

examples_created = await learning_mechanism.process_feedback_data(feedback_data)
print(f"Created {examples_created} learning examples")
```

## Configuration

### Backup Settings

```python
# Configure backup behavior
agent.backup_enabled = True
agent.backup_directory = "my_backups"
agent.max_backups = 5
```

### Learning Parameters

```python
# Configure learning behavior
learning_mechanism.min_feedback_score = 0.5  # Minimum score for learning
learning_mechanism.max_examples_per_type = 500  # Max examples per issue type
learning_mechanism.performance_window_days = 14  # Performance tracking window
```

### Docker Testing

```python
# Configure Docker testing
feedback_loop.docker_images = {
    "python": "python:3.11-slim",
    "node": "node:18-slim",
    "java": "openjdk:17-slim"
}
```

## Monitoring and Reporting

### Get Statistics

```python
# Get comprehensive statistics
test_stats = feedback_loop.get_test_statistics()
learning_stats = learning_mechanism.get_learning_statistics()
session_stats = agent.get_session_statistics(session_id)

print(f"Test success rate: {test_stats['success_rate']:.2%}")
print(f"Learning examples: {learning_stats['total_examples']}")
print(f"Session duration: {session_stats['duration']} seconds")
```

### Export Reports

```python
# Export detailed reports
agent.export_session_report(session_id, "session_report.json")
feedback_loop.export_test_results("test_results.json")
learning_mechanism.export_learning_data("learning_data.json")
```

### List Backups

```python
# List available backups
backups = agent.get_backup_list()
for backup in backups:
    print(f"Backup: {backup['name']}")
    print(f"Created: {backup['created']}")
    print(f"Size: {backup['size']} bytes")
```

## Error Handling

### Automatic Rollback

The system automatically creates backups and can rollback on failure:

```python
try:
    await agent.run_full_automation_cycle("/path/to/codebase")
except Exception as e:
    print(f"Automation failed: {e}")
    # System automatically attempts rollback if backup exists
```

### Manual Rollback

```python
# Manual rollback
backup_path = "backups/backup_20250621_123456_project"
if agent.rollback_changes(backup_path, "/path/to/codebase"):
    print("Rollback successful")
else:
    print("Rollback failed")
```

## Best Practices

### 1. Start Small
- Begin with small codebases or individual files
- Test the workflow on non-critical code first
- Monitor the results and adjust parameters as needed

### 2. Monitor Progress
- Always set up progress callbacks to track automation
- Review test results and learning statistics
- Export reports for analysis

### 3. Backup Management
- Keep backups enabled for safety
- Regularly clean up old backups
- Monitor backup storage usage

### 4. Learning Optimization
- Start with higher feedback score thresholds
- Gradually lower thresholds as the system improves
- Monitor learning statistics to ensure quality

### 5. Docker Configuration
- Ensure Docker has sufficient resources
- Monitor Docker container cleanup
- Adjust timeouts based on your codebase size

## Troubleshooting

### Common Issues

1. **Docker Not Available**
   ```
   Error: Docker not found or not running
   Solution: Install Docker and ensure it's running
   ```

2. **Backup Creation Fails**
   ```
   Error: Permission denied creating backup
   Solution: Check write permissions for backup directory
   ```

3. **Test Timeout**
   ```
   Error: Test timeout after 60 seconds
   Solution: Increase timeout or optimize test code
   ```

4. **Learning Data Corruption**
   ```
   Error: Invalid learning data format
   Solution: Check data files and regenerate if needed
   ```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with detailed logging
await agent.run_full_automation_cycle("/path/to/codebase")
```

## Next Steps

1. **Read the Full Documentation**: See `docs/AUTONOMOUS_WORKFLOW_IMPLEMENTATION.md`
2. **Explore Components**: Study individual component implementations
3. **Customize Parameters**: Adjust settings for your specific use case
4. **Extend Functionality**: Add custom test types or learning algorithms
5. **Monitor Performance**: Track improvements over time

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the detailed implementation documentation
3. Examine the test reports for insights
4. Check the logs for detailed error information 