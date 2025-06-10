# AI Coder Assistant

The AI Coder Assistant is a desktop application built with PyQt5 that provides a suite of tools to assist software developers. Its primary functions include acquiring and processing technical documentation and code, training a custom language model, and then using both the local model and powerful open-source LLMs to analyze Python code for potential improvements and generate justified code suggestions.

## Features

* **Web Documentation Acquisition**: Crawls specified online documentation sources (e.g., Python Standard Library, Requests library) to build a local corpus.
* **GitHub Code Acquisition**: Expands the training corpus by downloading real-world Python code from GitHub via its API based on a user-defined search query.
* **Custom Local Corpus**: Allows users to add their own local folders of text and Python files to the training data.
* **Documentation Preprocessing**: Cleans, chunks, and tokenizes all acquired documentation and code, and builds a vocabulary for language model training.
* **AI Language Model Training**: Trains a transformer-based language model on the preprocessed data.
* **Hybrid AI Analysis**:
    * **Local AI Scanner**: Scans a specified directory of Python files to identify potential code issues or statistically unusual lines based on the locally-trained model.
    * **Ollama Integration**: Offers optional, on-demand enhanced analysis for any code suggestion. It uses a locally running Ollama model (e.g., Llama 3, Code Llama) to provide in-depth explanations and refactoring ideas.
* **Interactive Code Suggestions**: Presents detected code issues with detailed justifications and proposed code changes through an interactive dialog, allowing users to apply or ignore suggestions.
* **Configuration & Persistence**: Securely saves the GitHub API token between sessions and allows for performance tuning by limiting the number of CPU cores used during scanning.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone (https://github.com/oldnordic/ai-coder-assistant.git)
    cd ai-coder-assistant
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # On Windows: .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    Install all required dependencies using the provided `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    Ensure your virtual environment is activated, then run the `main.py` script from the project root:
    ```bash
    python main.py
    ```

2.  **Application Tabs:**

    * **Data & Training Tab:**
        * **Acquire Documentation/Code**: Use the buttons to download documentation from the web or code from GitHub. A GitHub Personal Access Token is required for the GitHub feature.
        * **Add Local Folder**: Optionally, add a folder of your own `.txt` or `.py` files to the training corpus.
        * **Pre-process Docs for AI**: Processes all acquired raw text and code, preparing it for model training.
        * **Train AI Language Model**: Starts the training process for the local AI language model using the preprocessed data.

    * **Code Analysis Tab:**
        * **Configure Ollama (Optional)**: If you have Ollama running locally, click "Refresh Models" to select which powerful model (e.g., `llama3`, `codellama`) you want to use for enhanced analysis.
        * **Scan Code**: Select a directory containing Python files. The local AI model will scan these files for statistically unusual code.
        * **Review Suggestions**: When a suggestion dialog appears, you can optionally check the "Get enhanced analysis from Ollama" box to receive a detailed explanation and refactoring ideas from your selected Ollama model.

## Project Structure

* `main.py`: The entry point of the PyQt5 application.
* `main_window.py`: Manages the main application window, tab setup, logging, and worker thread orchestration.
* `config.py`: Centralized configuration settings for directories, model parameters, and performance tuning.
* `worker_threads.py`: Provides a generic worker class for running tasks in separate QThreads.
* `ollama_client.py`: Handles API communication with a locally running Ollama service.
* **Data Pipeline:**
    * `acquire_docs.py`: Logic for web crawling documentation.
    * `acquire_github.py`: Logic for downloading code from GitHub.
    * `preprocess_docs.py`: Handles text cleaning, chunking, and vocabulary creation.
    * `train_language_model.py`: Defines the language model architecture and the training pipeline.
* **UI Modules & AI Logic:**
    * `data_tab_widgets.py` & `ai_tab_widgets.py`: Defines the UI components for the main tabs.
    * `ai_coder_scanner.py`: Implements the core logic for scanning Python code.
* **Supporting Files:** `README.md`, `application.log`, `.gitignore`, `requirements.txt`.

## Known Issues / Troubleshooting

* **Ollama Integration Fails**: The enhanced analysis feature requires the [Ollama desktop application](https://ollama.com/) to be installed and running in the background. If you get a connection error, please ensure the Ollama service is active.
* For any other runtime errors or unexpected behavior, always check the `application.log` file in the project's root directory for detailed traceback information.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## Testing a change
## License

This project is open-sourced. *(A license like MIT or Apache 2.0 is recommended.)*
