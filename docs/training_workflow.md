# AI Coder Assistant: Training and Ollama Integration Workflow

This document provides a comprehensive guide to the training and Ollama integration workflow for the AI Coder Assistant. It covers data preparation, model training, and the process of feeding your custom knowledge back into Ollama for on-device inference with **intelligent analysis capabilities**. The system now uses an organized file structure with configuration and data files stored in dedicated directories.

## Project Structure

The training workflow uses the organized file structure:

```
ai_coder_assistant/
├── config/                     # Configuration files
│   ├── llm_studio_config.json  # Training configuration
│   └── ...                     # Other configuration files
├── data/                       # Data storage files
│   ├── security_training_data.json  # Security training data
│   └── ...                     # Other data files
├── src/                        # Source code
│   ├── backend/services/
│   │   ├── trainer.py          # Model training service
│   │   ├── preprocess.py       # Data preprocessing
│   │   └── ...                 # Other services
│   └── ...
├── continuous_learning_data/   # Continuous learning database
└── ...
```

## Configuration

The training system uses configuration files in the `config/` directory:

```bash
# View training configuration
cat config/llm_studio_config.json

# Edit training settings
vim config/llm_studio_config.json
```

## Overview: Intelligent Analysis Integration

The AI Coder Assistant now features **intelligent code analysis** that goes beyond simple linter errors. This enhanced analysis capability significantly improves the training process by:

- **Richer Training Data**: Intelligent analysis provides more comprehensive issue detection, creating better training examples
- **Context-Aware Learning**: The system learns from complex code patterns, security vulnerabilities, and performance issues
- **Multi-Dimensional Feedback**: Training data includes issue types, severity levels, and contextual information
- **Enhanced Model Capabilities**: Trained models can detect and suggest fixes for sophisticated code problems

## 1. Data Acquisition and Preparation

The first step is to gather and prepare the data that your model will learn from. This can include documentation, code, or any other text-based information relevant to your domain.

### 1.1 Acquiring Data

The AI Coder Assistant provides several ways to acquire data:

*   **Local Files**: Import text-based documentation from your local file system.
*   **Web Crawler**: Ingest technical documentation from specified URLs.
*   **GitHub Scraper**: Download Python code from GitHub repositories.
*   **YouTube Transcriber**: Transcribe YouTube video tutorials into text.

**UI Actions:**
*   **Data Management Tab**: Use buttons like "Add Local Files", "Acquire Docs from URLs", and "Transcribe YouTube Video" to gather data.

### 1.2 Preprocessing Data

After acquisition, the raw data needs to be preprocessed. This involves cleaning, normalizing, and consolidating all acquired text into a single, cohesive corpus that your language model can be trained on.

**UI Actions:**
*   **Data Management Tab**: Click "Pre-process All Docs & Feedback" to clean and aggregate your data. The processed data will be saved in `src/data/processed_data/preprocessed_corpus.txt`.

## 2. Model Training

Once your data is prepared, you can train or finetune your own GPT-based language model with intelligent analysis capabilities.

### 2.1 Training a Base Model

This step involves training a new language model from scratch on your processed corpus.

**UI Actions:**
*   **Data Management Tab**: Click "Train Base Model from Corpus". This will train a base GPT-based model on your `preprocessed_corpus.txt`. The trained model will be saved to `src/data/processed_data/ai_coder_model`.

**Intelligent Analysis Benefits**:
- The model learns from comprehensive code analysis patterns
- Training data includes security, performance, and maintainability examples
- Enhanced understanding of code smells and anti-patterns

### 2.2 Finetuning with User Feedback

Finetuning allows your model to learn from specific user interactions and corrections, improving its ability to provide relevant suggestions. User feedback is generated when you review code suggestions in the "AI Code Review" tab and accept or reject them.

**UI Actions:**
*   **Data Management Tab**: Click "Finetune Model with Feedback". This will finetune your existing model using the feedback data collected during interactive code reviews. Feedback data is saved in `src/data/feedback/user_feedback.jsonl`.
    *   **Note**: You must have reviewed suggestions and provided feedback for finetuning to work. The application will notify you if no feedback data is found.

**Enhanced Feedback Learning**:
- **Issue Type Classification**: Model learns to categorize issues by type (security, performance, code smell, etc.)
- **Severity Assessment**: Training includes severity level understanding
- **Contextual Suggestions**: Model learns to provide context-aware recommendations
- **Multi-Language Patterns**: Feedback includes language-specific analysis patterns

## 3. Exporting Your Model to Ollama (GGUF Conversion & Integration)

This is a crucial step to make your custom-trained knowledge available within your local Ollama instance for efficient, on-device inference with intelligent analysis capabilities.

### 3.1 Prerequisites: `llama.cpp`

The conversion of your HuggingFace model to the GGUF format requires the `convert_hf_to_gguf.py` script from the `llama.cpp` repository.

**Action Required: Clone `llama.cpp`**

You *must* clone the `llama.cpp` repository directly into your `ai_coder_assistant` project folder.

```bash
# Navigate to your ai_coder_assistant project directory
cd /path/to/your/ai_coder_assistant

# Clone llama.cpp into the project folder
git clone https://github.com/ggerganov/llama.cpp.git
```
After this step, you should have a `llama.cpp` directory at the same level as your `main.py` file, e.g., `/home/feanor/ai_coder_assistant/llama.cpp`.

### 3.2 Exporting and Sending to Ollama

The application automates the process of converting your trained model to GGUF and importing it into Ollama.

**UI Actions:**
*   **Ollama Export Tab**:
    1.  **Select Ollama Model to Feed Knowledge**: Choose an existing Ollama model from the dropdown. Your converted model will be imported under this name.
    2.  Click "Export & Send to Ollama".

**What the application does:**
1.  **Locates `llama.cpp`**: It automatically finds the `llama.cpp` directory (expecting it in the project root).
2.  **Converts to GGUF**: It runs `python llama.cpp/convert_hf_to_gguf.py` to convert your `src/data/processed_data/ai_coder_model` to GGUF. You will be prompted to save the GGUF file.
3.  **Creates Modelfile**: Generates a Modelfile with intelligent analysis system prompts
4.  **Imports to Ollama**: Uses `ollama create` to import the model with intelligent analysis capabilities
5.  **Model Ready**: The newly imported model is immediately available for use.

## 4. Using Your Integrated Ollama Model

Once the model is integrated into Ollama, you can use it for various tasks, including intelligent code scanning within the AI Coder Assistant itself, or directly from your terminal.

### 4.1 In the AI Coder Assistant

**UI Actions:**
*   **AI Code Review Tab**:
    1.  In the "AI Model Configuration" section, ensure "Ollama" is selected as the "Model Source".
    2.  In the "Ollama Model" dropdown, select the model name you used during the export (e.g., `qwen2.5-coder:1.5b-base`).
    3.  Proceed with intelligent code scanning as usual. The AI suggestions will now come from your custom-fed Ollama model with enhanced analysis capabilities.

**Intelligent Analysis Features**:
- **Comprehensive Issue Detection**: Security vulnerabilities, performance issues, code smells
- **Context-Aware Suggestions**: AI provides suggestions based on issue type and severity
- **Multi-Language Support**: Intelligent analysis across 20+ programming languages
- **Detailed Explanations**: AI explains the reasoning behind each suggestion

### 4.2 From the Terminal

You can also interact directly with your updated Ollama model via the command line.

**1. List available models (to confirm your model is there):**

```bash
ollama list
```

**2. Run your specific model with a query:**

Replace `<your_ollama_model_name>` with the exact name you used during export (e.g., `qwen2.5-coder:1.5b-base`).

```bash
# Example for Linux (Bash/Zsh/Fish) and Windows Command Prompt/PowerShell
ollama run <your_ollama_model_name> "Analyze this Python code for security vulnerabilities and performance issues: def process_data(data): return eval(data)"
```

## 5. Intelligent Analysis Training Benefits

### 5.1 Enhanced Model Capabilities

Trained models with intelligent analysis can:

- **Detect Security Vulnerabilities**: Hardcoded credentials, SQL injection, XSS attacks
- **Identify Performance Issues**: Inefficient algorithms, memory leaks, bottlenecks
- **Recognize Code Smells**: Anti-patterns, magic numbers, poor practices
- **Assess Maintainability**: Complex functions, poor documentation, architectural issues
- **Provide Context-Aware Suggestions**: Tailored recommendations based on issue type and severity

### 5.2 Training Data Quality

The intelligent analysis system provides:

- **Rich Context**: Each training example includes issue type, severity, and context
- **Multi-Dimensional Learning**: Models learn from various types of code problems
- **Language-Specific Patterns**: Training includes language-specific analysis patterns
- **Real-World Examples**: Training data comes from actual code analysis scenarios

### 5.3 Continuous Improvement

The feedback loop enables:

- **Issue Type Learning**: Models improve at categorizing different types of issues
- **Severity Assessment**: Better understanding of issue importance and urgency
- **Suggestion Quality**: More accurate and helpful code improvement suggestions
- **Context Understanding**: Better grasp of code context and project-specific patterns

## Key Considerations for Ollama Integration:

*   **Model Naming**: When exporting, you associate your GGUF with an *existing* Ollama model name. If you want a brand new name, you'd typically define it in a Modelfile first (though the application currently bypasses explicit Modelfile creation for existing names).
*   **Quantization**: The `llama.cpp/convert_hf_to_gguf.py` script can generate various quantization types (e.g., Q4_K_M, Q5_K_M) for different performance/memory trade-offs.
*   **Model Size**: Larger models provide better analysis capabilities but require more computational resources.
*   **Intelligent Analysis Integration**: The exported model includes system prompts that enable intelligent analysis capabilities.
*   **Continuous Learning**: Regular feedback collection and model retraining improves analysis accuracy over time.

## Troubleshooting

### Common Issues

1. **Model Not Found**: Ensure `llama.cpp` is cloned in the project root directory
2. **Conversion Errors**: Check that your trained model files are complete and valid
3. **Ollama Import Failures**: Verify Ollama is running and accessible
4. **Analysis Quality**: If analysis quality is poor, consider retraining with more diverse data

### Performance Optimization

- **Model Size**: Choose appropriate model size for your hardware
- **Quantization**: Use quantization for better performance on limited hardware
- **Batch Processing**: Process multiple files for better efficiency
- **Caching**: The system caches analysis results for improved performance

## Frontend/Backend Integration

- The training workflow is initiated from the frontend (UI) in `src/frontend/ui/main_window.py` and related tabs.
- All training, finetuning, and preprocessing logic is implemented in the backend (`src/backend/services/trainer.py`, `preprocess.py`, etc.).
- The frontend uses worker threads and progress dialogs to call backend training functions and display progress.
- Unit tests in `tests/frontend_backend/` verify that the frontend calls backend training logic correctly and handles results.

---

This enhanced training workflow ensures that your custom models can provide intelligent, context-aware code analysis that goes far beyond simple linter errors, helping you write better, more secure, and more maintainable code.