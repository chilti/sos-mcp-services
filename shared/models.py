from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AuthorProfile(BaseModel):
    id: str
    display_name: str
    orcid: Optional[str] = None
    snii_level: Optional[str] = None
    works_count: int = 0
    cited_by_count: int = 0
    h_index: Optional[int] = None
    institution: Optional[str] = None

class WorkMetadata(BaseModel):
    id: str
    doi: Optional[str] = None
    title: str
    publication_year: Optional[int] = None
    cited_by_count: int = 0
    is_oa: bool = False
    oa_status: Optional[str] = None
    primary_topic: Optional[str] = None

class LawFitResult(BaseModel):
    law_name: str
    parameters: Dict[str, Any]
    r_squared: Optional[float] = None
    p_value: Optional[float] = None
    is_valid: bool = True
    summary: str
    plot_data: Optional[Dict[str, Any]] = None

class SOMResult(BaseModel):
    rows: int
    cols: int
    quantization_error: float
    topographic_error: Optional[float] = None
    u_matrix: List[List[float]]
    clusters: List[int]
    cluster_metrics: Dict[str, float]
