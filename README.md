# MatrixCurator

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

An AI-powered tool to automate the extraction of morphological character data from scientific publications and generate standardized, FAIR-compliant NEXUS files for phylogenetic analysis.

| Deployment      | Link                                                                                                             | Purpose                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Primary App** | [![Tailscale Funnel](https://img.shields.io/badge/Tailscale-Funnel-blue.svg?logo=tailscale)](https://matrixcurator.tortoise-butterfly.ts.net/) | Main application link. |
| **Mirror**      | [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://matrixcurator-zkxwfebfdvwlkueytkffxj.streamlit.app/) | Backup link for redundancy. |


---

## Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Running with Streamlit](#running-with-streamlit)
  - [Running with Docker](#running-with-docker)
- [Project Structure](#project-structure)
- [Citation](#citation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

## About The Project

The curation of biological and paleontological datasets, particularly morphological matrices, is a labor-intensive and error-prone process. Data is often locked away in published literature (PDFs, DOCX files) in inconsistent formats, hindering reproducibility and compliance with FAIR (Findable, Accessible, Interoperable, and Reusable) data principles.

**MatrixCurator** addresses this challenge by leveraging Large Language Models (LLMs) to automate the entire curation workflow. Developed for the [MorphoBank](https://morphobank.org) repository, this tool transforms unstructured character descriptions from research papers into structured, machine-readable `CHARSTATELABELS` blocks within a NEXUS file.

This project aims to:
- **Accelerate research** by drastically reducing manual data entry time.
- **Improve data quality** by minimizing transcription errors and standardizing formats.
- **Enhance data reusability** by producing complete, FAIR-compliant NEXUS files.

## Key Features

- **Automated Data Extraction**: Uses Google's Gemini family of LLMs to intelligently parse and extract character names and their corresponding states from text.
- **Multi-Parser Support**: Robustly handles various document formats (`.pdf`, `.docx`, `.txt`) with multiple parsing backends, including:
  - Google's Gemini native multimodal capabilities
  - LlamaParse
  - PyMuPDF
  - python-docx
- **AI-Powered Validation**: Employs a multi-agent system where an `Evaluator` agent scores the accuracy of the extracted data, ensuring high-quality output. The system retries with corrective prompts if the quality is below a set threshold.
- **NEXUS File Generation**: Seamlessly integrates the extracted character data into an existing NEXUS file, creating or updating the `CHARSTATELABELS` block.
- **Web-Based Interface**: Built with Streamlit for an intuitive, user-friendly experience that requires no coding to use.
- **Efficient & Cost-Effective**: Utilizes LLM context caching to reduce API token consumption by over 90% for large documents, making the process both fast and affordable.

## How It Works

The MatrixCurator pipeline is a multi-step process designed for accuracy and efficiency:

1.  **User Input**: The user uploads a research article (PDF/DOCX), a base NEXUS file (typically containing only the TAXA and MATRIX blocks), and specifies parameters like the total number of characters and the relevant page range in the article.

2.  **Document Parsing**: The selected pages of the article are isolated and parsed into a machine-readable format (Markdown or raw text) using the chosen parsing engine.

3.  **AI Core - Multi-Agent Extraction & Evaluation**:
    - **Retriever Agent**: For each character number, this agent is prompted to read the parsed document and extract the character's name and its list of states as JSON object.
    - **Evaluator Agent**: The extracted data is passed to this agent, which compares it against the source text to assign an accuracy score (1-10).
    - **Self-Correction Loop**: If the score is below a threshold (e.g., 8), the process is retried with a corrective prompt. This ensures high-fidelity extraction.

4.  **NEXUS File Update**: The structured JSON data is converted into the `CHARSTATELABELS` format and inserted into the correct position within the user's original NEXUS file.

5.  **Output**: The final, complete NEXUS file is made available for download.

## Getting Started

Follow these instructions to set up and run the MatrixCurator project locally.

### Prerequisites

- [Python](https://www.python.org/) 3.12+
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) (Optional, for containerized deployment)
- API keys for required services (see [Configuration](#configuration))

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MorphoEx/morphoex.git
    cd morphoex
    ```
2.  **Install Python dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3.  **Configure API Keys:**
    See the [Configuration](#configuration) section below to set up your API keys.

## Configuration

MatrixCurator requires API keys to interact with external LLM and parsing services. You can provide these keys via a `.streamlit/secrets.toml` file.

1.  **Copy the template:**
    ```bash
    cp .streamlit/secrets_template.toml .streamlit/secrets.toml
    ```
2.  **Edit the `secrets.toml` file** and add your keys:

    ```toml
    # .streamlit/secrets.toml

    # Required for accessing Google's Gemini family of models.
    # Obtain from Google AI Studio (https://aistudio.google.com/app/apikey)
    GEMINI_API_KEY="your-gemini-api-key"

    # Required for accessing LlamaParse.
    # Obtain from your LlamaCloud account dashboard.
    LLAMACLOUD_API_KEY="your-llamacloude-api-key"

    # Required for accessing LLM Prompts.
    # Obtain from your Langfuse project settings.
    LANGFUSE_PUBLIC_KEY="pk-lf-..."
    LANGFUSE_SECRET_KEY="sk-lf-..."
    LANGFUSE_HOST="https://cloud.langfuse.com" # or your self-hosted instance

    # Optional: For error tracking with Sentry.
    SENTRY_DSN=""
    ```
3.  **Set Up Prompts in Langfuse:**

The application dynamically fetches prompts from your Langfuse project. You must create three specific prompts in the Langfuse UI.

Log into your Langfuse project, navigate to the **Prompts** section, and create the following three prompts.

> **Important:** The application fetches prompts by their unique name. You must use the exact names specified below (`system_prompt`, `extraction_prompt`, and `evaluation_prompt`).



**A. Prompt Name: `system_prompt`**

```text
You are a helpful and precise research assistant. Focus on extracting the requested character descriptions and corresponding states accurately from the provided text.
```

**B. Prompt Name: `extraction_prompt`**

```text
Here is a section of text from a phylogenetic research paper. Please extract the character descriptions and their corresponding states for character index: {character_index}

Previous attempts to extract information for this character index have yielded these incorrect results:
```

**C. Prompt Name: `evaluation_prompt`**

```text
Evaluate the generated answer based on the previously provided section of a phylogenetic research paper and the following user query.

User Query: {extraction_prompt}
Generated Answer: {extraction_reponse}

Scoring Criteria:
- 1-3: The generated answer is not relevant to the user query.
- 4-6: The generated answer is relevant to the query but contains mistakes. A score of 4 indicates more significant errors, while 6 indicates minor errors.
- 7-10: The generated answer is relevant and fully correct, accurately extracting the complete character description and all corresponding states for the requested character index. A score of 7 indicates an ok answer, while 10 indicates a perfect extraction.
```

### Running with Streamlit

Once installed and configured, you can run the web application locally.

```bash
streamlit run src/streamlit_app.py
```

Navigate to `http://localhost:8501` in your web browser. From there, you can:
1.  Upload your research article (`.pdf`, `.docx`).
2.  Select the document parsing method.
3.  Enter the total number of characters and the page range where they are described.
4.  Choose the LLMs for extraction and evaluation.
5.  Upload the base NEXUS file to be updated.
6.  Click "Generate Updated NEXUS File" and download the result.

### Running with Docker

You can run MatrixCurator using a pre-built image or by building it from source.

> **Note:** Both `docker run` commands require you to mount your secrets file from `.streamlit/secrets.toml`.

#### Using the Pre-built Image
1.  **Pull the image:**
    ```bash
    docker pull ghcr.io/morphobankorg/matrixcurator:latest
    ```
2.  **Run the container:**
    ```bash
    docker run -p 8501:80 -v "$(pwd)/.streamlit/secrets.toml:/app/.streamlit/secrets.toml" ghcr.io/morphobankorg/matrixcurator:latest
    ```

#### Building from Source
1.  **Build the image:**
    ```bash
    docker build -t matrixcurator .
    ```
2.  **Run the container:**
    ```bash
    docker run -p 8501:80 -v "$(pwd)/.streamlit/secrets.toml:/app/.streamlit/secrets.toml" matrixcurator
    ```

Once started, the application is available at **`http://localhost:8501`**.


## Project Structure

The project is organized into modular components for clarity and maintainability.

```
morphobankorg-matrixcurator/
├── src/
│   ├── streamlit_app.py        # Main Streamlit application UI and entry point
│   ├── llm/                    # Handles all LLM interactions
│   │   ├── services.py         # High-level service for extraction/evaluation cycle
│   │   └── external_service.py # Direct client for the Gemini API
│   ├── parser/                 # Manages document parsing from different formats
│   │   ├── services.py         # Main service to orchestrate different parsers
│   │   └── external_services.py# Client for LlamaParse
│   ├── nex/                    # Logic for reading and updating NEXUS files
│   │   └── services.py         # Service to build and insert CHARSTATELABELS
│   ├── config.py               # Model configurations and defaults
│   └── utils.py                # General utility functions
├── .streamlit/
│   └── secrets_template.toml   # Template for API keys
├── requirements.txt            # Python dependencies
├── Dockerfile                  # For building the Docker container
└── README.md                   # This file
```

## Citation

If you use MatrixCurator or its underlying methodology in your research, please cite the following paper:

Jariwala, S., Long-Fox, B. L., & Berardini, T. Z. (2025). *Advancing FAIR Data Management through AI-Assisted Curation of Morphological Data Matrices*. (Journal and full citation details to be updated upon publication).

**BibTeX:**
```bibtex
@article{Jariwala2025MatrixCurator,
  title   = {Advancing FAIR Data Management through AI-Assisted Curation of Morphological Data Matrices},
  author  = {Jariwala, Shreya and Long-Fox, Brooke L. and Berardini, Tanya Z.},
  year    = {2025},
  journal = {To Be Determined}
}
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

This project is distributed under the GNU GPL v3 License. See `LICENSE` for more information.

## Acknowledgments

- This work was supported by Phoenix Bioinformatics and the US National Science Foundation (NSF-DBI-2049965 and NSF-EAR-2148768).
- We thank Dr. Maureen A. O’Leary for her ongoing support.
- We acknowledge the use of Google's Gemini models, which were instrumental in the development of this tool.

## Contact

- Shreya Jariwala - [sjariwala@morphobank.org](mailto:sjariwala@morphobank.org)
- Brooke L. Long-Fox (Corresponding Author) - [blongfox@morphobank.org](mailto:blongfox@morphobank.org)

Project Link: [https://github.com/MorphoEx/morphoex](https://github.com/MorphoEx/matrixcurator)