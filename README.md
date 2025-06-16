# AI Coder Assistant

## Overview

The AI Coder Assistant is a desktop application built with **PyQt6** designed to be a powerful and flexible tool for software developers. It leverages both local and remote AI models to provide intelligent code analysis, suggestions, and corrections. The application is designed to learn from a curated corpus of technical documentation and source code, allowing it to provide context-aware assistance tailored to the user's needs.

## Features

- **Data Acquisition**:
  - **Web Crawler**: Crawls and ingests technical documentation from specified URLs.
  - **GitHub Scraper**: Downloads Python code from GitHub based on search queries.

- **Custom Corpus and Training**:
  - **Preprocessing**: Acquired documents are chunked, and a searchable FAISS vector database is created for Relevance-Augmented Generation (RAG).
  - **Local Language Model**: Train a custom Transformer-based language model on the acquired data to create a specialized, locally-runnable model.

- **Hybrid AI Analysis**:
  - **Code Scanning**: Uses `flake8` for initial static analysis to find syntax errors, style issues, and potential bugs.
  - **Intelligent Suggestions**: For each identified issue, the application generates a suggested fix using one of two modes:
    1. **Ollama Integration**: Connects to a locally-running Ollama instance to leverage powerful open-source models like Llama 3, CodeLlama, etc.
    2. **Own Trained Model**: Uses the custom-trained language model for generating suggestions.
  - **Interactive Review**: Presents suggestions in a user-friendly "diff" format, allowing developers to review, accept, or reject changes.

- **Integrated Tools**:
  - **Web Browser**: An embedded browser for quick access to online resources.
  - **YouTube Transcriber**: A tool to transcribe YouTube videos, useful for learning from tutorials.

## Architecture

The application is built using a modular architecture with a PyQt6 frontend that runs long-running tasks (data acquisition, model training, code analysis) in separate worker threads to keep the UI responsive.

- **`main_window.py`**: The main application window and orchestration logic.
- **`worker_threads.py`**: Handles background processing.
- **`data_tab_widgets.py` / `ai_tab_widgets.py`**: UI components for the respective tabs.
- **`acquire_docs.py` / `acquire_github.py`**: Logic for data acquisition.
- **`preprocess_docs.py`**: Handles text processing and FAISS database creation.
- **`train_language_model.py`**: Contains the PyTorch code for the custom language model and training loop.
- **`ai_coder_scanner.py`**: Implements the code scanning and suggestion generation logic.
- **`ollama_client.py`**: Manages communication with the Ollama API.
- **`ai_tools.py`**: Contains helper tools like the YouTube transcriber.

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/your-repo/ai-coder-assistant.git](https://github.com/your-repo/ai-coder-assistant.git)
    cd ai-coder-assistant
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    python main.py
    ```