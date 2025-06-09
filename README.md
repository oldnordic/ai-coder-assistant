# AI Coder Assistant

## The Philosophy: An Assistant, Not an Oracle

In 2025, AI-generated content is more persuasive than ever, yet it is prone to "hallucinations"—confidently stating things that simply aren't true. A generative AI might fabricate a scientific citation that looks perfect in format but links to a non-existent paper. It masters the *appearance* of correctness without understanding the underlying substance.

This project operates on a similar principle, applied to coding.

Just as an AI can hallucinate a citation, a code-assisting AI can "hallucinate" an error. The model you train in this application learns the statistical patterns of vast amounts of code from sources like the Python Standard Library and GitHub. When it scans your code, it doesn't *understand* the logic or intent. Instead, it identifies lines of code that are **statistically improbable** based on the patterns it has learned.

An unconventional but perfectly valid line of code might be flagged as an "error" simply because it's rare. This tool is therefore not an auto-fixer; it is an **assistant**. Its purpose is to bring these statistical anomalies to your attention, presenting them with a justification in an interactive dialog. **You, the developer, are the final authority.** You are the one who verifies the suggestion and decides whether it's a genuine mistake or simply a unique solution.

## How It Works

1.  **Data Acquisition:** The assistant builds its knowledge base by acquiring source code and documentation from the web and GitHub. You can provide a search query to download real-world Python code, or add your own local folders of text files to the training corpus.

2.  **Model Training:** It trains a Transformer-based language model on this corpus. The model's sole objective is to get very good at predicting the next "word" (or token) in a sequence, learning the common grammar and style of Python code.

3.  **Code Analysis:** When scanning your project, the model calculates a "probability score" (or "loss") for each line of code. Lines that are highly improbable—meaning they deviate significantly from the patterns the model has learned—are flagged as potential issues.

4.  **Justified Suggestions:** The assistant presents these flagged lines to you in a `diff` view, explaining *why* the line was flagged (i.e., its improbability score). It is then your decision to **Apply** or **Ignore** the suggestion, ensuring a human is always in the loop.

## Features

* **Web & GitHub Data Acquisition**: Crawls specified online documentation and uses the GitHub API to download real-world Python code, building a rich local corpus for training.
* **Custom Corpus Integration**: Allows you to add your own local folders of `.txt` or `.py` files to the training data.
* **AI Language Model Training**: Trains a transformer-based language model on the preprocessed documentation and code.
* **Interactive Code Suggestions**: Presents potential statistical anomalies with detailed justifications and proposed changes through an interactive dialog, empowering the developer to **Apply** or **Ignore** the suggestion.
* **Learning Data Collection**: Records your decisions (accepted/ignored proposals) to a log file (`learning_data.jsonl`). This data can be used in the future to manually train even smarter models.

## Project Structure

The project is organized into several key areas:

* **Core Application:** `main.py`, `main_window.py`, `config.py`, `worker_threads.py`
* **Data Pipeline:** `acquire_docs.py`, `acquire_github.py`, `preprocess_docs.py`, `train_language_model.py`
* **UI Modules:** `data_tab_widgets.py`, `ai_tab_widgets.py`
* **AI Scanning Logic:** `ai_coder_scanner.py`
* **Supporting Files:** `README.md`, `application.log`, `.gitignore`

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Data & Training Tab:**
    * Use the "Acquire" buttons to download documentation and GitHub code. You will need a GitHub Personal Access Token for this step.
    * Optionally, add a local folder of your own text/code files.
    * Run "Pre-process All Docs for AI" to prepare the data.
    * Run "Train AI Language Model" to train your model on the prepared data.

3.  **Code Analysis Tab:**
    * Select a directory containing Python files you want to analyze.
    * Click "Scan Python Files". The AI model will scan the files and present proposals for any statistically unusual lines of code for your review.

## License

This project is open-sourced. *(A license like MIT or Apache 2.0 is recommended.)*
