from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    filename: str
    label_count: int
    total_quantity: int
    has_quantity_commands: bool


class RuntimeResponse(BaseModel):
    available: bool
    description: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    version: str
    runtime: RuntimeResponse
