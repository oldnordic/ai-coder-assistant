# AI Coder Assistant

## Overview

The AI Coder Assistant is a desktop application built with **PyQt6** designed to be a powerful and flexible tool for software developers. It leverages both local and remote AI models to provide intelligent code analysis, suggestions, and corrections. The assistant learns from a curated corpus of documentation and source code, allowing it to provide context‑aware help tailored to your projects.

## Features

- **Data Acquisition**:
  - **Local Files**: Import documentation from your own folders.
  - **Web Crawler**: Crawl and ingest technical documentation from specified URLs.
  - **GitHub Scraper**: Download Python code from GitHub based on search queries.

- **Custom Corpus and Training**:
  - **Preprocessing**: Documents are cleaned and aggregated into a single text corpus for direct LLM training.
  - **Local Language Model**: Train and finetune a GPT‑based model on the acquired data and user feedback.

- **Hybrid AI Analysis**:
  - **Code Scanning**: Uses `flake8` for static analysis to find syntax errors, style issues and potential bugs.
  - **Intelligent Suggestions**: Generates fixes using either a locally running Ollama model or your own trained model.
  - **Interactive Review**: Shows a side‑by‑side diff so you can accept or reject each change.
  - **Report Generation**: Creates a Markdown report and JSONL file from the review, useful for further model training.

- **Integrated Tools**:
  - **Web Browser**: An embedded browser for quick access to online resources.
  - **YouTube Transcriber**: Uses `yt-dlp` and Whisper to transcribe videos for learning from tutorials.
  - **.ai_coder_ignore Editor**: Button in the main window to open and edit the `.ai_coder_ignore` file in a dialog, making it easy to update ignore patterns for code scanning.
  - **Export Local Model to Ollama**: Tab or button to export/convert your locally trained model and feed it back to the running Ollama instance. This enables seamless integration of your feedback and custom training into the Ollama model for private, on-device inference.

## Setup and Installation

### 1. Clone the repository
```bash
git clone https://github.com/oldnordic/ai-coder-assistant.git
cd ai-coder-assistant
```

### 2. Clone `llama.cpp` (Required for Model Export)
For the "Export Local Model to Ollama" feature to work, you *must* clone the `llama.cpp` repository directly into your `ai_coder_assistant` project folder.

```bash
# Navigate to your ai_coder_assistant project directory
cd /path/to/your/ai_coder_assistant

git clone https://github.com/ggerganov/llama.cpp.git
```
After this step, you should have a `llama.cpp` directory at the same level as your `main.py` file, e.g., `/home/feanor/ai_coder_assistant/llama.cpp`.

### 3. Set up Python 3.11
- **Linux/Windows:** Install Python 3.11 from [python.org](https://www.python.org/downloads/) or use `pyenv` (Linux/macOS).

### 4. Create and activate a virtual environment
#### **Linux (bash/zsh):**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```
#### **Linux (fish):**
```fish
python3.11 -m venv .venv
source .venv/bin/activate.fish
```
#### **Windows (cmd):**
```bat
python -m venv .venv
.venv\Scripts\activate
```
#### **Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Run the application
```bash
python main.py
```

> **Note**
> To make use of the machine learning capabilities, install a PyTorch build that matches your GPU (CUDA for NVIDIA or ROCm for AMD). Otherwise the application will fall back to CPU execution, which can be noticeably slower.

> **Ollama**
> To use the built-in Ollama integration you must have Ollama installed and the service running before launching the app.

> **For detailed training steps, refer to: [docs/training_workflow.md](docs/training_workflow.md)**