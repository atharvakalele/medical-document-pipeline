from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import traceback

from utils.pdf_processing import extract_pages
from graph.workflow import graph

app = FastAPI(
    title="Document Processing Pipeline API",
    description="API for processing medical claims using LangGraph and Gemini 2.0 Flash",
    version="1.0.0"
)

@app.post("/api/medClaim", summary="Process a medical claim document")
async def process_claim(
    claim_id: str = Form(..., description="Unique identifier for the claim"),
    gen_ai_api_key: str = Form(..., description="API key (Gemini, OpenAI, etc.)"),
    file: UploadFile = File(..., description="The medical claim PDF document")
):
    """
    Process a medical claim PDF file.
    
    This endpoint takes a tracking 'claim_id' and a PDF 'file'. It extracts all pages,
    converts them to images, and runs them through the LangGraph AI pipeline to 
    extract structured identity, discharge, and billing information.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read the uploaded file bytes
        file_bytes = await file.read()
        
        # Extract pages into our internal representation (CPU-bound)
        pages = extract_pages(file_bytes)
        
        if not pages:
            raise HTTPException(status_code=400, detail="Could not extract any pages from the PDF")
            
        # Initialize the state for the LangGraph pipeline
        initial_state = {
            "gen_ai_api_key": gen_ai_api_key,
            "claim_id": claim_id,
            "pages": pages,
            "page_classifications": {},
            "classification_confidence": {},
            "id_data": [],
            "discharge_data": [],
            "bill_data": [],
            "agent_errors": [],
            "final_output": {},
        }
        
        # Invoke the LangGraph pipeline
        result = await graph.ainvoke(initial_state)
        
        # Return the final consolidated output
        return JSONResponse(content=result.get("final_output", {}))
        
    except Exception as e:
        error_trace = traceback.format_exc()
        # In a production environment, use a proper logger instead of print
        print(f"Error processing claim {claim_id}:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
