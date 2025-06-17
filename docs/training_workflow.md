# AI Coder Assistant: Training and Ollama Integration Workflow

This document provides a comprehensive guide to the training and Ollama integration workflow for the AI Coder Assistant. It covers data preparation, model training, and the process of feeding your custom knowledge back into Ollama for on-device inference.

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

Once your data is prepared, you can train or finetune your own GPT-based language model.

### 2.1 Training a Base Model

This step involves training a new language model from scratch on your processed corpus.

**UI Actions:**
*   **Data Management Tab**: Click "Train Base Model from Corpus". This will train a base GPT-based model on your `preprocessed_corpus.txt`. The trained model will be saved to `src/data/processed_data/ai_coder_model`.

### 2.2 Finetuning with User Feedback

Finetuning allows your model to learn from specific user interactions and corrections, improving its ability to provide relevant suggestions. User feedback is generated when you review code suggestions in the "AI Code Review" tab and accept or reject them.

**UI Actions:**
*   **Data Management Tab**: Click "Finetune Model with Feedback". This will finetune your existing model using the feedback data collected during interactive code reviews. Feedback data is saved in `src/data/feedback/user_feedback.jsonl`.
    *   **Note**: You must have reviewed suggestions and provided feedback for finetuning to work. The application will notify you if no feedback data is found.

## 3. Exporting Your Model to Ollama (GGUF Conversion & Integration)

This is a crucial step to make your custom-trained knowledge available within your local Ollama instance for efficient, on-device inference.

### 3.1 Prerequisites: `llama.cpp`

The conversion of your HuggingFace model to the GGUF format requires the `convert.py` script from the `llama.cpp` repository.

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
2.  **Converts to GGUF**: It runs `python llama.cpp/convert.py` to convert your `src/data/processed_data/ai_coder_model` to GGUF. You will be prompted to save the GGUF file.
3.  **Uploads to Ollama**: It uses the Ollama API's `/api/import` endpoint to upload the generated GGUF file to your running Ollama instance, associating it with the model name you selected.
4.  **Reloads Ollama**: After successful upload, it sends a request to Ollama's `/api/reload` endpoint to ensure the newly imported model is immediately available.

## 4. Using Your Integrated Ollama Model

Once the model is integrated into Ollama, you can use it for various tasks, including code scanning within the AI Coder Assistant itself, or directly from your terminal.

### 4.1 In the AI Coder Assistant

**UI Actions:**
*   **AI Code Review Tab**:
    1.  In the "AI Model Configuration" section, ensure "Ollama" is selected as the "Model Source".
    2.  In the "Ollama Model" dropdown, select the model name you used during the export (e.g., `qwen2.5-coder:1.5b-base`).
    3.  Proceed with code scanning as usual. The AI suggestions will now come from your custom-fed Ollama model.

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
ollama run <your_ollama_model_name> "Provide a quick refactor for this Python function: def add(a,b): return a+b"
```

### Key Considerations for Ollama Integration:

*   **Model Naming**: When exporting, you associate your GGUF with an *existing* Ollama model name. If you want a brand new name, you'd typically define it in a Modelfile first (though the application currently bypasses explicit Modelfile creation for existing names).
*   **Quantization**: The `llama.cpp/convert.py` script can generate various quantization types (e.g., `q4_0`, `q8_0`). The application currently uses the default. Quantization reduces model size and improves speed but can slightly impact quality. Future versions might allow specifying this in the UI.
*   **Ollama Service**: Ensure your Ollama service is running before attempting to export or use models via the application or CLI. 