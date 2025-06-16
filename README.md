# AI Coder Assistant

## Overview

The AI Coder Assistant is a desktop application built with **PyQt6** designed to be a powerful and flexible tool for software developers. It leverages both local and remote AI models to provide intelligent code analysis, suggestions, and corrections. The assistant learns from a curated corpus of documentation and source code, allowing it to provide context‑aware help tailored to your projects.

## Features

- **Data Acquisition**:
  - **Local Files**: Import documentation from your own folders.
  - **Web Crawler**: Crawl and ingest technical documentation from specified URLs.
  - **GitHub Scraper**: Download Python code from GitHub based on search queries.

- **Custom Corpus and Training**:
  - **Preprocessing**: Documents are cleaned, embedded with SentenceTransformers and stored in a FAISS vector database for RAG-style retrieval.
  - **Local Language Model**: Train and finetune a GPT‑based model on the acquired data and user feedback.

- **Hybrid AI Analysis**:
  - **Code Scanning**: Uses `flake8` for static analysis to find syntax errors, style issues and potential bugs.
  - **Intelligent Suggestions**: Generates fixes using either a locally running Ollama model or your own trained model.
  - **Interactive Review**: Shows a side‑by‑side diff so you can accept or reject each change.
  - **Report Generation**: Creates a Markdown report and JSONL file from the review, useful for further model training.

- **Integrated Tools**:
  - **Web Browser**: An embedded browser for quick access to online resources.
  - **YouTube Transcriber**: Uses `yt-dlp` and Whisper to transcribe videos for learning from tutorials.

## Architecture

The application is built using a modular architecture with a PyQt6 frontend that runs long-running tasks (data acquisition, model training, code analysis) in separate worker threads to keep the UI responsive.

- **`src/ui/main_window.py`**: The main application window and orchestration logic.
- **`src/ui/worker_threads.py`**: Handles background processing.
- **`src/ui/data_tab_widgets.py`** / **`src/ui/ai_tab_widgets.py`**: UI components for the respective tabs.
- **`src/processing/acquire.py`** and **`scripts/acquire_github.py`**: Document and code acquisition helpers.
- **`src/processing/preprocess.py`**: Text processing and FAISS database creation.
- **`src/training/trainer.py`**: PyTorch training code for the custom language model.
- **`src/core/scanner.py`**: Performs code scanning and suggestion generation.
- **`src/core/ollama_client.py`**: Manages communication with the Ollama API.
- **`src/core/ai_tools.py`**: Tools such as the YouTube transcriber and report generator.
- **`src/config/settings.py`**: Centralized configuration for paths and hyperparameters.

## Key Libraries

- **PyQt6** and **PyQt6-WebEngine** for the desktop interface
- **PyTorch** and **transformers** for model training
- **Sentence-Transformers** and **FAISS** for embedding and retrieval
- **requests** and **beautifulsoup4** for web scraping
- **flake8** and **pathspec** for static code analysis
- **yt-dlp**, **youtube-transcript-api** and **openai/whisper** for transcription
- **datasets** and **PyPDF2** for data handling
- **qdarkstyle** for optional dark theme styling

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/oldnordic/ai-coder-assistant.git
    cd ai-coder-assistant
    ```

2.  **Set up Python 3.11 with `pyenv`** (recommended if you have multiple
    Python versions on your machine):
    ```bash
    pyenv install 3.11.9        # install once
    pyenv local 3.11.9          # use Python 3.11 inside this project
    ```

3.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv        # create the venv with Python 3.11
    source .venv/bin/activate   # activate it
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the application**:
    ```bash
    python main.py
    ```

> **Note**
> To make use of the machine learning capabilities, install a PyTorch build that
> matches your GPU (CUDA for NVIDIA or ROCm for AMD). Otherwise the application
> will fall back to CPU execution, which can be noticeably slower.

> **Ollama**
> To use the built-in Ollama integration you must have Ollama installed and the service running before launching the app.
