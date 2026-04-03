import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from graph.state import (
    PipelineState, PageClassification, 
    IdentityData, DischargeData, BillData
)
from utils.pdf_processing import to_base64

load_dotenv(override=True)

def get_llm(api_key: str):
    # Depending on the key prefix or user choice, you can easily swap this!
    # E.g., if api_key.startswith('sk-'): return ChatOpenAI(api_key=api_key, model="gpt-4o")
    # For now, we continue using Gemini for the pipeline logic
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

SEGREGATOR_PROMPT = """Classify this medical claim document page into exactly ONE of these types:
- claim_forms: Insurance claim application or request forms
- cheque_or_bank_details: Bank cheques, account details, NEFT/IFSC info
- identity_document: Photo ID, Aadhaar, PAN, passport, driving license
- itemized_bill: Hospital/pharmacy bills listing items with costs
- discharge_summary: Hospital discharge summary with diagnosis, dates, physician
- prescription: Doctor's handwritten or printed prescription for medicines
- investigation_report: Lab test results, radiology, blood work, pathology
- cash_receipt: Payment receipts, cash memos, transaction acknowledgments
- other: Anything not matching above categories

Return the document_type and your confidence (0.0 to 1.0)."""

# Limit concurrent LLM calls to prevent rate-limiting on large PDFs
sem = asyncio.Semaphore(5)

async def classify_single_page(page: dict, api_key: str) -> tuple[int, PageClassification, str]:
    async with sem:
        llm = get_llm(api_key)
        structured_llm = llm.with_structured_output(PageClassification)
        content = [{"type": "text", "text": SEGREGATOR_PROMPT}]
        if page["text"]:
            content.append({"type": "text", "text": f"Page text content:\n{page['text']}"})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{to_base64(page['image_bytes'])}"}
        })
        try:
            result = await structured_llm.ainvoke([HumanMessage(content=content)])
            return (page["page_num"], result, None)
        except Exception as e:
            # Fallback for errors to ensure pipeline doesn't break
            return (page["page_num"], PageClassification(document_type="other", confidence=0.0), str(e))

async def segregator_node(state: PipelineState) -> dict:
    tasks = [classify_single_page(p, state["gen_ai_api_key"]) for p in state["pages"]]
    results = await asyncio.gather(*tasks)
    
    classifications = {p_num: r.document_type for p_num, r, _ in results}
    confidence = {p_num: r.confidence for p_num, r, _ in results}
    
    # Collect any errors that happened during page classification
    errors = [f"Page {p_num} classification failed: {err}" for p_num, _, err in results if err is not None]
    
    return {
        "page_classifications": classifications,
        "classification_confidence": confidence,
        "agent_errors": errors
    }

async def id_agent_node(state: PipelineState) -> dict:
    try:
        relevant_pages = [
            p for p in state["pages"]
            if state["page_classifications"].get(p["page_num"]) == "identity_document"
        ]
        # Explicitly sort by page number to prevent the "sorting problem"
        relevant_pages = sorted(relevant_pages, key=lambda x: x["page_num"])
        if not relevant_pages:
            return {"id_data": []}
        
        content = [{"type": "text", "text": "Extract identity details from these pages."}]
        for page in relevant_pages:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{to_base64(page['image_bytes'])}"}
            })
        
        llm = get_llm(state["gen_ai_api_key"])
        structured_llm = llm.with_structured_output(IdentityData)
        result = await structured_llm.ainvoke([HumanMessage(content=content)])
        return {"id_data": [result.model_dump()]}
    except Exception as e:
        return {"id_data": [], "agent_errors": [f"id_agent failed: {str(e)}"]}

async def discharge_agent_node(state: PipelineState) -> dict:
    try:
        relevant_pages = [
            p for p in state["pages"]
            if state["page_classifications"].get(p["page_num"]) == "discharge_summary"
        ]
        # Explicitly sort by page number to prevent the "sorting problem"
        relevant_pages = sorted(relevant_pages, key=lambda x: x["page_num"])
        if not relevant_pages:
            return {"discharge_data": []}
        
        content = [{"type": "text", "text": "Extract discharge summary details."}]
        for page in relevant_pages:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{to_base64(page['image_bytes'])}"}
            })
        
        llm = get_llm(state["gen_ai_api_key"])
        structured_llm = llm.with_structured_output(DischargeData)
        result = await structured_llm.ainvoke([HumanMessage(content=content)])
        return {"discharge_data": [result.model_dump()]}
    except Exception as e:
        return {"discharge_data": [], "agent_errors": [f"discharge_agent failed: {str(e)}"]}

async def bill_agent_node(state: PipelineState) -> dict:
    try:
        relevant_pages = [
            p for p in state["pages"]
            if state["page_classifications"].get(p["page_num"]) == "itemized_bill"
        ]
        # Explicitly sort by page number to prevent the "sorting problem"
        relevant_pages = sorted(relevant_pages, key=lambda x: x["page_num"])
        if not relevant_pages:
            return {"bill_data": []}
        
        content = [{"type": "text", "text": "Extract all line items and the stated total amount."}]
        for page in relevant_pages:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{to_base64(page['image_bytes'])}"}
            })
        
        llm = get_llm(state["gen_ai_api_key"])
        structured_llm = llm.with_structured_output(BillData)
        result = await structured_llm.ainvoke([HumanMessage(content=content)])
        return {"bill_data": [result.model_dump()]}
    except Exception as e:
        return {"bill_data": [], "agent_errors": [f"bill_agent failed: {str(e)}"]}

async def aggregator_node(state: PipelineState) -> dict:
    return {"final_output": {
        "claim_id": state["claim_id"],
        "page_classifications": state["page_classifications"],
        "classification_confidence": state["classification_confidence"],
        "identity": state["id_data"][0] if state["id_data"] else None,
        "discharge_summary": state["discharge_data"][0] if state["discharge_data"] else None,
        "bill": state["bill_data"][0] if state["bill_data"] else None,
        "errors": state.get("agent_errors", []),
    }}
