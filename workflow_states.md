# LangGraph Workflow: State Evolution Trace

This document traces how the `PipelineState` dictionary evolves as it passes through each node in the LangGraph "Diamond" architecture.

---

## 1️⃣ Initial Entry State
**Input:** Provided by the FastAPI `/api/medClaim` endpoint.

```json
{
  "claim_id": "TEST-CLAIM-001",
  "gen_ai_api_key": "gsk_xxxx...",
  "pages": [
    {"page_num": 0, "image_bytes": "<bytes>", "text": "..."},
    {"page_num": 1, "image_bytes": "<bytes>", "text": "..."},
    "... up to 18 pages"
  ],
  "page_classifications": {},
  "classification_confidence": {},
  "id_data": [],
  "discharge_data": [],
  "bill_data": [],
  "agent_errors": [],
  "final_output": {}
}
```

---

## 2️⃣ After `segregator_node`
**Transformation:** All pages are analyzed by Gemini 2.0 Flash. The `page_classifications` mapping is populated.

```json
{
  "page_classifications": {
    "0": "claim_forms",
    "2": "identity_document",
    "3": "discharge_summary",
    "8": "itemized_bill",
    "...": "..."
  },
  "classification_confidence": {
    "0": 0.98,
    "2": 1.0,
    "3": 0.95,
    "8": 0.99
  }
}
```

---

## 3️⃣ After Parallel Specialist Agents (The "Fan-Out")
**Transformation:** The 3 extraction nodes run concurrently. Each appends its structured JSON to the respective list in the state.

### Identity Agent (`id_data`)
```json
"id_data": [
  {
    "patient_name": "JOHN MICHAEL SMITH",
    "date_of_birth": "15-MAR-1985",
    "id_number": "ID-987-654-321"
  }
]
```

### Discharge Agent (`discharge_data`)
```json
"discharge_data": [
  {
    "diagnosis": "Community Acquired Pneumonia (CAP)",
    "admit_date": "January 20, 2025",
    "discharge_date": "January 25, 2025",
    "physician_name": "Dr. Sarah Johnson, MD"
  }
]
```

### Bill Agent (`bill_data`)
**Note:** This node triggers the `@model_validator` for math verification.
```json
"bill_data": [
  {
    "items": [... 20 items ...],
    "extracted_total": 6113.0,
    "calculated_total": 6113.0,
    "math_verified": true
  }
]
```

---

## 4️⃣ Final `aggregator_node` (The "Fan-In")
**Transformation:** The aggregator takes the accumulated lists and collapses them into a single, clean JSON object for the API response.

```json
{
  "final_output": {
    "claim_id": "TEST-CLAIM-001",
    "identity": { ... },
    "discharge_summary": { ... },
    "bill": {
      "items": [...],
      "math_verified": true,
      "total": 6113.0
    },
    "page_classifications": { ... },
    "errors": []
  }
}
```

---

## 💡 Key Architectural Note
Because we use **`Annotated[list, operator.add]`** in our `PipelineState` definition, each parallel agent "adds" its results to the global list without overwriting the others. This is what makes the LangGraph parallel fan-out thread-safe and reliable.
