# Video Presentation Script: Medical Document Processing Pipeline

This document is designed to act as your script and structural guide for your video explanation (e.g., Loom). It breaks down the architecture and specific requirements of the assignment in a clear, easy-to-explain format.

---

## 🎙️ Introduction
"Hi, I'm Atharva. In this video, I'll be walking you through my implementation of the Medical Document Processing Pipeline. I built this system using FastAPI, LangGraph, and Gemini 2.0 Flash to process complex, multi-modal medical datasets."

---

## 1️⃣ The LangGraph Workflow (Architecture Overview)
"Let's start with the overall architecture. For this pipeline, I implemented a **LangGraph 'Diamond' Pattern**, which is essentially a fan-out / fan-in architecture.

*   **State Management:** I used a typed `StateGraph` that carries a shared state across all nodes. This state holds the PDF pages (converted to images), classifications, and the extracted data arrays.
*   **The Diamond Structure:** 
    1.  The workflow begins at a single entry point: the **Segregator Node**.
    2.  From there, it *fans out*. Using LangGraph's conditional edges, the execution splits into multiple parallel paths.
    3.  Three specialist nodes (Identity, Discharge, and Bill agents) run concurrently.
    4.  Finally, the graph *fans in*, merging the results back into a final **Aggregator Node** before returning the response.
*   **Why this approach?** This architecture allows for highly efficient **parallel execution**. Instead of processing a 20-page document sequentially, all extraction agents run side-by-side on their respective pages simultaneously."

---

## 2️⃣ How the Segregator Agent Works
"The first step in the pipeline is the Segregator. Its job is to figure out exactly what every page in the uploaded PDF is.

*   **Image-Based Processing:** Since the assignment involves documents without text layers, I convert the PDF pages into base64 images right at the start.
*   **Classification Strategy:** The Segregator agent uses the Gemini Vision model. It takes all the page images and classifies each one into predefined categories like `identity_document`, `itemized_bill`, `discharge_summary`, `prescription`, etc.
*   **Output:** It updates the LangGraph state with a mapping of page numbers to their classified document types. This classification is crucial because it dictates which pages are sent to which downstream specialist agent."

---

## 3️⃣ How Extraction Agents Process Their Assigned Pages
"Once the pages are classified, the workflow branches out to the specialist Extraction Agents. I have three main agents: **Identity**, **Discharge Summary**, and **Bill Extraction**.

Here is how each agent processes its assignment:
1.  **Targeted Execution:** Each agent only looks at the pages classified for its specific domain. The Identity agent ignores bills; the Bill agent ignores discharge summaries.
2.  **Chronological Sorting:** Before doing any extraction, the agents explicitly sort their assigned pages by page number. This ensures that context isn't lost if a bill or summary spans across multiple pages.
3.  **Structured AI Extraction:** I use Pydantic models paired with LangChain's `with_structured_output()` method. This forces the Gemini model to return data in the exact JSON schema required by the assignment.
4.  **Mathematical Verification (The Bill Agent):** For the itemized bills, there is a strict requirement for financial accuracy. I implemented a Pydantic `@model_validator` in the Bill agent's schema. When Gemini extracts the line items and the total amount, the validator automatically calculates the sum of all line items and compares it against the stated total. If it matches, a `math_verified: true` flag is added to the output.
5.  **Fault Tolerance:** Every agent execution is wrapped in a `try-except` block. If an agent fails to parse a page, it logs the error to the state's `agent_errors` list but allows the rest of the pipeline to continue running."

---

## 4️⃣ The Complete Process Flow
"To summarize, here is the end-to-end lifecycle of a single API request:

1.  **Ingestion:** The user hits the FastAPI `/api/process` POST endpoint with a `claim_id` and a PDF upload.
2.  **Preprocessing:** The FastAPI server extracts the PDF pages and converts them directly into high-quality images.
3.  **Segregation Matrix:** The LangGraph pipeline starts. The Segregator node analyzes the images using Gemini 2.0 Flash and assigns a document type to each page.
4.  **Parallel Fan-Out:** The pipeline triggers the specialized extraction agents concurrently.
    *   The ID agent extracts patient demographics.
    *   The Discharge agent extracts diagnosis and treatment dates.
    *   The Bill agent extracts 20+ line items and mathematically verifies the total.
5.  **Aggregation (Fan-In):** The aggregator node waits for all agents to finish, collects their structured Pydantic outputs, and formats them into a single, cohesive JSON object.
6.  **Response:** FastAPI returns this clean, strictly typed JSON response to the client within seconds."

---

## 🎬 Tips for the Video Recording
*   **Show the Code:** While explaining the Diamond pattern, show `graph/workflow.py`.
*   **Show the Validator:** When explaining the Math Verification, show the `@model_validator` inside `graph/state.py`.
*   **Demo the Result:** Show a brief clip of hitting the FastAPI endpoint (using Postman or cURL) and scrolling through the final JSON response, highlighting the `math_verified: true` field.
