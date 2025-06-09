AI Coder Assistant
The Philosophy: An Assistant, Not an Oracle

In 2025, AI-generated content is more persuasive than ever, yet it is prone to "hallucinations"—confidently stating things that simply aren't true. A generative AI might fabricate a scientific citation that looks perfect in format but links to a non-existent paper. It masters the appearance of correctness without understanding the underlying substance.

This project operates on a similar principle, applied to coding.

Just as an AI can hallucinate a citation, a code-assisting AI can "hallucinate" an error. The model you train in this application learns the statistical patterns of vast amounts of code from sources like the Python Standard Library and GitHub. When it scans your code, it doesn't understand the logic or intent. Instead, it identifies lines of code that are statistically improbable based on the patterns it has learned.

An unconventional but perfectly valid line of code might be flagged as an "error" simply because it's rare. This tool is therefore not an auto-fixer; it is an assistant. Its purpose is to bring these statistical anomalies to your attention, presenting them with a justification in an interactive dialog. You, the developer, are the final authority. You are the one who verifies the suggestion and decides whether it's a genuine mistake or simply a unique solution.
How It Works

    Data Acquisition: The assistant builds its knowledge base by acquiring source code and documentation from the web and GitHub. You can provide a search query to download real-world Python code, or add your own local folders of text files to the training corpus.
    Model Training: It trains a Transformer-based language model on this corpus. The model's sole objective is to get very good at predicting the next "word" (or token) in a sequence, learning the common grammar and style of Python code.
    Code Analysis: When scanning your project, the model calculates a "probability score" (or "loss") for each line of code. Lines that are highly improbable—meaning they deviate significantly from the patterns the model has learned—are flagged as potential issues.
    Justified Suggestions: The assistant presents these flagged lines to you in a diff view, explaining why the line was flagged (i.e., its improbability score). It is then your decision to Apply or Ignore the suggestion, ensuring a human is always in the loop.

Features

    Web & GitHub Data Acquisition: Crawls specified online documentation and uses the GitHub API to download real-world Python code, building a rich local corpus for training.
    Custom Corpus Integration: Allows you to add your own local folders of .txt or .py files to the training data.
    AI Language Model Training: Trains a transformer-based language model on the preprocessed documentation and code.
    Interactive Code Suggestions: Presents potential statistical anomalies with detailed justifications and proposed changes through an interactive dialog, empowering the developer to Apply or Ignore the suggestion.
    Learning Data Collection: Records your decisions (accepted/ignored proposals) to a log file (learning_data.jsonl). This data can be used in the future to manually train even smarter models.

Project Structure

    main.py: The entry point of the PyQt5 application.
    main_window.py: Manages the main application window, tab setup, logging, and worker thread orchestration.
    config.py: Centralized configuration settings for directories, model parameters, and preprocessing.
    worker_threads.py: Provides a generic worker class for running tasks in separate QThreads to maintain UI responsiveness.
    README.md: This file.
    application.log: Logs runtime information and errors from the application.
    Data Pipeline:
        acquire_docs.py: Contains logic for web crawling and extracting documentation.
        preprocess_docs.py: Handles text cleaning, chunking, and vocabulary creation for all acquired data.
        train_language_model.py: Defines the language model architecture and the training pipeline.
    UI Modules:
        data_tab_widgets.py: Defines the UI components for the "Data & Training" tab.
        ai_tab_widgets.py: Defines the UI components for the "Code Analysis" tab.
    Core AI Logic:
        ai_coder_scanner.py: Implements the logic for scanning Python code and using the trained model to find statistical anomalies.

Usage

    Run the application:
    Bash

    python main.py

    Data & Training Tab:
        Use the "Acquire" buttons to download documentation and GitHub code.
        Optionally, add a local folder of your own text/code files.
        Run "Pre-process All Docs for AI" to prepare the data.
        Run "Train AI Language Model" to train your model on the prepared data.

    Code Analysis Tab:
        Select a directory containing Python files you want to analyze.
        Click "Scan Python Files". The AI model will scan the files and present proposals for any statistically unusual lines of code for your review.

License

This project is open-sourced. (A license like MIT or Apache 2.0 is recommended.)
