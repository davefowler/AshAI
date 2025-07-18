from pydantic import BaseModel, Field
from typing import List, Optional


class Source(BaseModel):
    """Source information for a medical article"""
    title: str = Field(..., description="Title of the medical research article")
    pmid: str = Field(..., description="PubMed ID for the article")
    url: str = Field(..., description="PubMed URL for the full article")
    content: str = Field(..., description="Content snippet extracted from the source")


class WebFAQResult(BaseModel):
    """A single FAQ result from PubMed search"""
    question: str = Field(..., description="The medical question")
    answer: str = Field(..., description="The answer to the question")
    publication_date: Optional[str] = Field(None, description="Publication date (YYYY-MM-DD)")
    sources: List[Source] = Field(..., description="List of source articles used")
    population: Optional[str] = Field(None, description="Target population (e.g., 'Pregnant women', 'Cardiac patients')")


class FAQQuery(BaseModel):
    """Input query for the FAQ search"""
    query: str = Field(..., description="Medical question to search for", min_length=1)
    max_results: Optional[int] = Field(3, description="Maximum number of results to return", ge=1, le=10)
    population_filter: Optional[str] = Field(None, description="Filter by population (e.g., 'pregnancy', 'cardiac')")


class FAQResponse(BaseModel):
    """Response containing multiple FAQ results"""
    results: List[WebFAQResult] = Field(..., description="List of FAQ results")
    query: str = Field(..., description="Original query that was searched")
    total_results: int = Field(..., description="Total number of results found")


class SourcesResponse(BaseModel):
    """Response containing raw source data"""
    sources: List[Source] = Field(..., description="List of raw source data with content snippets")
    query: str = Field(..., description="Original query that was searched")
    total_results: int = Field(..., description="Total number of sources found")


class Message(BaseModel):
    """Chat message for telehealth agent"""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")


class TelehealthRequest(BaseModel):
    """Request for telehealth agent"""
    messages: List[Message] = Field(..., description="List of chat messages")
    profile: str = Field(..., description="Patient profile information")


class TelehealthResponse(BaseModel):
    """Response from telehealth agent"""
    response: str = Field(..., description="The AI telehealth agent's response")
    sources: List[Source] = Field(..., description="List of sources used in making the response")
    faqs: List[WebFAQResult] = Field(..., description="FAQs used to create the response")
    evaluation: Optional[dict] = Field(None, description="Evaluation score from another agent")


class EvaluationRequest(BaseModel):
    """Request for evaluation agent"""
    response: str = Field(..., description="The response to evaluate")
    messages: List[Message] = Field(..., description="Full chat history for context")
    profile: str = Field(..., description="Patient profile information")


class EvaluationResponse(BaseModel):
    """Response from evaluation agent"""
    medical_accuracy: float = Field(..., description="Medical accuracy score (0-100)", ge=0, le=100)
    precision: float = Field(..., description="Precision score (0-100)", ge=0, le=100)
    language_clarity: float = Field(..., description="Language clarity score (0-100)", ge=0, le=100)
    empathy_score: float = Field(..., description="Empathy score (0-100)", ge=0, le=100)
    overall_score: float = Field(..., description="Overall weighted score (0-100)", ge=0, le=100)
    feedback: str = Field(..., description="Detailed feedback on the response") 