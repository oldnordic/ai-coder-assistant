# Specialized Code Reviewer System Guide

## Overview

The AI Coder Assistant now includes a specialized, locally-trained model for code review that elevates the tool to professional-grade standards. This system provides significant advantages in speed, privacy, and most importantly, the quality and relevance of its suggestions.

## Architecture

### Two-Stage Analysis Approach

1. **Quick Scan**: Immediate local analysis using static rules and patterns
2. **AI Enhancement**: On-demand AI analysis using specialized local models

### Core Components

- **LocalCodeReviewer**: Specialized service for fine-tuned model analysis
- **Enhanced Trainer**: Advanced training system for code-specific models
- **Model Manager**: Comprehensive model management and training interface
- **AI Tab Widgets**: Improved UI for the two-stage analysis workflow

## Key Features

### 1. Specialized Local Models

The system prioritizes fine-tuned models specifically trained for code review:

- **Fine-tuned Model**: `code-reviewer-v1` (specialized for code analysis)
- **Default Model**: `codellama:7b` (general code model)
- **Fallback Model**: `llama2:7b` (general purpose)

### 2. Enhanced Prompt Engineering

The system uses sophisticated prompt engineering for better code analysis:

- **System Prompts**: Expert-level code reviewer persona
- **Structured Analysis**: Comprehensive evaluation criteria
- **JSON Output**: Structured, parseable responses
- **Context Awareness**: Surrounding code context for better analysis

### 3. Multiple Enhancement Types

The system supports specialized analysis for different aspects:

- **Code Improvement**: General quality and maintainability
- **Security Analysis**: Vulnerability detection and mitigation
- **Performance Optimization**: Efficiency and optimization suggestions
- **Best Practices**: Coding standards and conventions
- **Documentation**: Documentation and comment improvements
- **Architectural Review**: Design patterns and architecture

### 4. Advanced Training System

The training system supports:

- **Dataset Creation**: Tools for creating training datasets
- **Fine-tuning**: Efficient LoRA-based fine-tuning
- **Model Evaluation**: Performance assessment tools
- **Continuous Learning**: Feedback loop for model improvement

## Usage Guide

### Setting Up the System

1. **Install Dependencies**:
   ```bash
   pip install transformers torch datasets peft
   ```

2. **Configure Models**:
   - Edit `config/local_code_reviewer_config.json`
   - Set your preferred model priorities
   - Configure training parameters

3. **Prepare Training Data**:
   - Use the sample dataset in `data/sample_code_review_dataset.json`
   - Create your own datasets using the Dataset Creation Dialog
   - Format: JSON with `code`, `issue`, `analysis`, `suggestion` fields

### Using the AI Analysis Tab

1. **Model Configuration**:
   - Select "Fine-tuned Local Model" for specialized analysis
   - Select "Ollama" for general models
   - Load your fine-tuned model using the "Load Fine-tuned Model" button

2. **Quick Scan**:
   - Select your project directory
   - Configure include/exclude patterns
   - Click "Run Quick Scan" for immediate analysis

3. **AI Enhancement**:
   - Double-click any issue for detailed AI analysis
   - Use "Enhance All Issues" for comprehensive analysis
   - Review detailed suggestions and code changes

### Training Your Own Model

1. **Create Dataset**:
   - Use the Model Manager Tab → Training Tab
   - Click "Create Dataset" to build training data
   - Include diverse code examples with issues and solutions

2. **Start Training**:
   - Select your dataset
   - Choose base model (recommended: `microsoft/DialoGPT-medium`)
   - Configure training parameters
   - Click "Start Training"

3. **Monitor Progress**:
   - Watch training progress in real-time
   - Review training logs
   - Evaluate model performance

4. **Deploy Model**:
   - Training automatically saves to `models/` directory
   - Model becomes available in the AI Analysis Tab
   - Set as active model for immediate use

## Configuration

### Model Configuration

Edit `config/local_code_reviewer_config.json`:

```json
{
  "model_configuration": {
    "fine_tuned_model": "code-reviewer-v1",
    "default_model": "codellama:7b",
    "fallback_model": "llama2:7b"
  }
}
```

### Training Configuration

```json
{
  "training_configuration": {
    "default_training_params": {
      "epochs": 3,
      "batch_size": 4,
      "learning_rate": 2e-4
    }
  }
}
```

### Performance Settings

```json
{
  "performance_settings": {
    "max_concurrent_analyses": 3,
    "timeout_seconds": 30,
    "max_context_lines": 10
  }
}
```

## Advanced Features

### Custom Enhancement Types

You can define custom enhancement types in the configuration:

```json
{
  "enhancement_types": {
    "custom_analysis": {
      "description": "Your custom analysis type",
      "priority": 7
    }
  }
}
```

### Prompt Customization

Customize the system prompts for your specific needs:

```json
{
  "prompt_templates": {
    "system_prompt": "Your custom system prompt...",
    "analysis_guidelines": [
      "Your custom guideline 1",
      "Your custom guideline 2"
    ]
  }
}
```

### Model Evaluation

Evaluate your trained models:

```python
from src.backend.services.trainer import evaluate_model_performance

results = evaluate_model_performance(
    model_path="models/code-reviewer-v1",
    test_dataset_path="data/test_dataset.json"
)
print(f"Model accuracy: {results['accuracy']:.2%}")
```

## Best Practices

### Training Data Quality

1. **Diverse Examples**: Include various code patterns and languages
2. **Real Issues**: Use actual code problems from your projects
3. **Quality Solutions**: Ensure suggestions are correct and actionable
4. **Balanced Dataset**: Include both simple and complex issues

### Model Training

1. **Start Small**: Begin with a small dataset and iterate
2. **Monitor Overfitting**: Watch for decreasing validation accuracy
3. **Regular Evaluation**: Test models on unseen data
4. **Incremental Training**: Add new data and retrain periodically

### Performance Optimization

1. **Batch Processing**: Use batch enhancement for multiple issues
2. **Context Limits**: Set appropriate context line limits
3. **Concurrent Processing**: Adjust max concurrent analyses
4. **Model Selection**: Choose appropriate model size for your hardware

## Troubleshooting

### Common Issues

1. **Model Not Loading**:
   - Check if Ollama is running
   - Verify model names in configuration
   - Check model file paths

2. **Training Failures**:
   - Ensure sufficient disk space
   - Check GPU memory availability
   - Verify dataset format

3. **Poor Analysis Quality**:
   - Improve training data quality
   - Increase training epochs
   - Try different base models

4. **Performance Issues**:
   - Reduce batch size
   - Use smaller models
   - Adjust timeout settings

### Debug Mode

Enable debug logging in configuration:

```json
{
  "logging": {
    "level": "DEBUG",
    "log_enhancement_requests": true,
    "log_model_performance": true
  }
}
```

## Integration with Existing Workflow

### Continuous Learning

1. **Collect Feedback**: Save user feedback on suggestions
2. **Update Dataset**: Add new examples to training data
3. **Retrain Model**: Periodically retrain with new data
4. **Deploy Updates**: Replace old models with improved versions

### Team Integration

1. **Shared Models**: Store models in shared repository
2. **Configuration Management**: Version control configuration files
3. **Training Pipeline**: Automated training and deployment
4. **Quality Gates**: Automated model evaluation before deployment

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Enhanced support for more programming languages
2. **Project-specific Models**: Models trained on specific project patterns
3. **Real-time Learning**: Continuous model updates from user feedback
4. **Advanced Evaluation**: More sophisticated model performance metrics
5. **Cloud Integration**: Remote model training and deployment

### Contributing

To contribute to the specialized code reviewer system:

1. **Improve Training Data**: Submit high-quality training examples
2. **Enhance Prompts**: Suggest better prompt engineering
3. **Add Features**: Implement new enhancement types
4. **Optimize Performance**: Improve training and inference efficiency

## Conclusion

The specialized code reviewer system represents a significant advancement in automated code analysis. By leveraging fine-tuned local models, it provides professional-grade code review capabilities while maintaining privacy and performance. The system's modular architecture allows for continuous improvement and customization to meet specific project needs.

For support and questions, refer to the main documentation or create an issue in the project repository. 