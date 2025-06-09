# AI Coder Assistant

The AI Coder Assistant is a desktop application built with PyQt5 that provides a suite of tools to assist software developers. Its primary functions include acquiring and processing technical documentation, training a custom language model on this documentation, and then using the trained model to analyze Python code for potential improvements and generating justified code suggestions.

## Features

* **Web Documentation Acquisition**: Crawls specified online documentation sources (e.g., Python Standard Library, Requests library) to build a local corpus.
* **Documentation Preprocessing**: Cleans, chunks, and tokenizes acquired documentation, and builds a vocabulary for language model training.
* **AI Language Model Training**: Trains a transformer-based language model on the preprocessed documentation.
* **Python Code Scanning**: Scans a specified directory of Python files to identify potential code issues or areas for improvement.
* **Interactive Code Suggestions**: Presents detected code issues with detailed justifications and proposed code changes through an interactive dialog, allowing users to apply or ignore suggestions.
* **Learning from User Decisions**: Records user decisions (accepting or ignoring proposals) to potentially improve future suggestions.
* **User-Friendly GUI**: Provides a graphical user interface for managing data acquisition, model training, and code analysis workflows.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/ai-coder-assistant.git](https://github.com/your-username/ai-coder-assistant.git)
    cd ai-coder-assistant
    ```
    *(Note: Replace `https://github.com/your-username/ai-coder-assistant.git` with the actual repository URL if it's hosted.)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # On Windows:
    # .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    The core dependencies for the AI Coder Assistant include PyQt5, requests, beautifulsoup4, lxml, tqdm, and torch.
    A `requirements.txt` file is recommended for a complete list of dependencies. If one is not provided, you may need to install them individually:
    ```bash
    pip install PyQt5 requests beautifulsoup4 lxml tqdm torch
    ```
    *(Note: Additional dependencies like `pymatgen`, `mp_api`, `pandas`, `sqlite3`, and `python-dotenv` are present in `data_acquisition.py` but are currently for a separate Materials Project data acquisition feature not integrated with the main GUI workflow.)*

## Usage

1.  **Run the application:**
    Ensure your virtual environment is activated, then run the `main.py` script from the project root:
    ```bash
    python main.py
    ```

2.  **Application Tabs:**
    The application features two main tabs:

    * **Data & Training Tab:**
        * **Acquire Documentation from Web**: Initiates the crawling process to download documentation from predefined sources.
        * **Pre-process Docs for AI**: Processes the acquired raw text documentation into chunks, cleans it, and builds a vocabulary, preparing it for model training.
        * **Train AI Language Model**: Starts the training process for the AI language model using the preprocessed data.

    * **Code Analysis Tab:**
        * **Scan Code for Errors & Justification**: Allows you to select a directory containing Python files. The AI model will scan these files and generate proposals for code changes, presenting them in an interactive dialog for review.

## Project Structure

* `.gitignore`: Specifies files and directories to be ignored by Git (e.g., virtual environments, generated data, logs).
* `README.md`: This file, providing an overview of the project.
* `acquire_docs.py`: Contains logic for web crawling and extracting documentation.
* `ai_coder_scanner.py`: Implements the core logic for scanning Python code and generating AI-driven proposals.
* `ai_tab_widgets.py`: Defines the UI components for the "Code Analysis" tab.
* `application.log`: Logs runtime information and errors from the application.
* `config.py`: Centralized configuration settings for directories, model parameters, and preprocessing.
* `data_acquisition.py`: Contains functions for Materials Project data acquisition, though currently not part of the main GUI workflow.
* `data_tab_widgets.py`: Defines the UI components for the "Data & Training" tab.
* `main.py`: The entry point of the PyQt5 application.
* `main_window.py`: Manages the main application window, tab setup, logging, and worker thread orchestration.
* `preprocess_docs.py`: Handles text cleaning, chunking, and vocabulary creation for documentation.
* `train_language_model.py`: Defines the language model architecture and the training pipeline.
* `worker_threads.py`: Provides a generic worker class for running tasks in separate QThreads to maintain UI responsiveness.

## Known Issues / Troubleshooting

* **`ImportError: cannot import name 'ai_coder_scanner' from 'ai_coder_assistant'`**: This error, as seen in `application.log`, indicates a potential issue with Python's module import resolution within the application's environment. While `main.py` attempts to set the `sys.path` correctly, ensure that the project is run from its root directory and that the package structure (`ai_coder_assistant` as a package with its modules) is correctly recognized by your Python interpreter.
* For any runtime errors or unexpected behavior, always check the `application.log` file in the project's root directory for detailed traceback information.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is open-sourced. *(Please specify a license, e.g., MIT, Apache 2.0, etc.)*
