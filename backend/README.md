# OncoMind-AI

## Overview

OncoMind-AI is an LLM-based AI assistant designed for cancer patients and researchers. It provides up-to-date and relevant information by leveraging various sources, including the web, scientific publications, and online communities.

## Features

- **Multi-Source Information Retrieval:** Fetches data from diverse sources like the PLOS (Public Library of Science) for research papers and Reddit for community discussions.
- **Web Search:** Integrates with web search to find the latest information.
- **Summarization:** Condenses lengthy documents and articles into concise summaries.
- **Extensible Agent Tools:** The system is designed to be modular, allowing for the addition of new tools and data sources.

## Project Structure

```
OncoMind-AI/
├── .gitignore
├── .python-version
├── import_tests.py
├── main.py                 # Main entry point for the application
├── pyproject.toml          # Project metadata
├── README.md
├── requirements.txt        # Project dependencies
├── uv.lock
├── AgentTools/             # Contains tools for the AI agent
│   ├── PLOS.py
│   ├── Reddit.py
│   └── Summarizer.py
├── CustomTools/            # Directory for custom user-defined tools
├── Databases/              # For data storage
└── Prompts/                # Prompts for the LLM
```

## Getting Started

### Prerequisites

- Python 3.12 or higher
- `uv` package manager

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd OncoMind-AI
    ```

2.  **Install dependencies using uv:**
    ```bash
    uv pip install -r requirements.txt
    ```

## Usage

To run the application, execute the `main.py` script:

```bash
python main.py
```

## Dependencies

This project uses a number of Python libraries, which are listed in the `requirements.txt` file. Key dependencies include:

All dependencies are managed via `uv` and the `requirements.txt` file.
