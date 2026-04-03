# Document Processing Pipeline (LangGraph + Gemini)

An automated medical document processing pipeline that classifies pages and extracts structured data from complex claim documents using **LangGraph** and **Gemini 2.0 Flash**.

## 🚀 Features
- **Intelligent Classification**: Automatically categorizes 18+ page PDFs into identity, billing, discharge, and clinical documents.
- **Structured Data Extraction**: Extracted high-fidelity JSON for Identity, Discharge Summaries, and Itemized Bills.
- **Mathematical Verification**: Built-in Pydantic validators cross-check billing totals against itemized costs.
- **Resilient Architecture**: Uses a LangGraph "diamond" (fan-out/fan-in) pattern for parallel specialist execution.
- **FastAPI Integration**: RESTful API endpoint for document processing.

## 🛠️ Tech Stack
- **Framework**: LangGraph, FastAPI
- **Model**: Gemini 2.0 Flash (Vision)
- **PDF Handling**: PyMuPDF
- **Validation**: Pydantic

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd document-pipeline
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

## 🖥️ Usage

1. **Start the API server**:
   ```bash
   python main.py
   ```

2. **Process a document**:
   Send a `POST` request to `http://localhost:8000/api/process` with a PDF file and `claim_id`.

## 📄 Project Structure
- `main.py`: FastAPI server entry point.
- `graph/`: LangGraph orchestration and specialist nodes.
- `utils/`: PDF processing and image conversion utilities.
- `requirements.txt`: Project dependencies.
