from pydantic import BaseModel


class AIAnalysis(BaseModel):
    summary: str
    why_it_matters: str
    evidence_summary: str
    priority_explanation: str
    investigation_questions: list[str]
    recommended_remediation: list[str]
    confidence_notes: list[str]
    limitations: list[str]
    model: str
    generated_at: str
    grounded_on: list[str]
