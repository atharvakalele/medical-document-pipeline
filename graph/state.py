import operator
from typing import Annotated, Literal, TypedDict
from pydantic import BaseModel, Field, model_validator

# Document types from assignment
DOC_TYPES = Literal[
    "claim_forms", "cheque_or_bank_details", "identity_document",
    "itemized_bill", "discharge_summary", "prescription",
    "investigation_report", "cash_receipt", "other"
]

class PageClassification(BaseModel):
    document_type: DOC_TYPES
    confidence: float = Field(ge=0.0, le=1.0)

class IdentityData(BaseModel):
    patient_name: str = ""
    date_of_birth: str = ""
    id_number: str = ""
    policy_number: str = ""
    insurer_name: str = ""

class DischargeData(BaseModel):
    diagnosis: str = ""
    admit_date: str = ""
    discharge_date: str = ""
    physician_name: str = ""
    procedures: list[str] = Field(default_factory=list)

class BillItem(BaseModel):
    description: str
    amount: float

class BillData(BaseModel):
    items: list[BillItem] = Field(default_factory=list)
    extracted_total: float = 0.0
    calculated_total: float = 0.0
    math_verified: bool = False

    @model_validator(mode='after')
    def check_math(self) -> 'BillData':
        self.calculated_total = round(sum(item.amount for item in self.items), 2)
        self.math_verified = abs(self.calculated_total - self.extracted_total) < 0.01
        return self

class PipelineState(TypedDict):
    claim_id: str
    pages: list[dict]                                    # [{page_num, image_bytes, text}]
    page_classifications: dict[int, str]                 # {page_idx: doc_type}
    classification_confidence: dict[int, float]          # {page_idx: confidence}
    id_data: Annotated[list[dict], operator.add]
    discharge_data: Annotated[list[dict], operator.add]
    bill_data: Annotated[list[dict], operator.add]
    agent_errors: Annotated[list[str], operator.add]
    final_output: dict
