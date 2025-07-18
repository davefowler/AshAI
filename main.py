from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pubmed
from models import (
    FAQQuery, FAQResponse, WebFAQResult, Source,
    TelehealthRequest, TelehealthResponse,
    EvaluationRequest, EvaluationResponse
)
from telehealth import process_telehealth_request
from evaluator import evaluate_telehealth_response

# Create FastAPI app
app = FastAPI(
    title="WebFAQMCP",
    description="Medical FAQ tool using PubMed research",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "WebFAQMCP: Medical FAQ API",
        "description": "Search PubMed for medical literature and get structured FAQ-style answers",
        "endpoint": "/faq"
    }


# note this is like /sources but combines multiple sources/snippets into 
# questiontion/anser pairs and returns that.  
# more closely simulating what we're intending to build for our internal RAG
@app.post("/faq", response_model=FAQResponse)
async def search_medical_faq(query: FAQQuery) -> FAQResponse:
    """
    Search PubMed for medical literature and return synthesized FAQ results.
    
    This endpoint searches the PubMed database and combines information from
    multiple sources to create comprehensive question/answer pairs.
    
    - **query**: The medical question to search for
    - **max_results**: Maximum number of results (1-10, default: 3)
    
    Returns synthesized FAQ responses combining multiple sources.
    """
    try:
        # Search PubMed using the pubmed module
        raw_results = pubmed.search_and_fetch(query.query, max_results=query.max_results or 3)
        
        if not raw_results:
            # Return empty results if no articles found
            return FAQResponse(
                results=[],
                query=query.query,
                total_results=0
            )
        
        # Synthesize FAQ responses from multiple sources
        faq_results = _synthesize_faq_results(query.query, raw_results)
        
        return FAQResponse(
            results=faq_results,
            query=query.query,
            total_results=len(faq_results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching medical literature: {str(e)}"
        )


def _synthesize_faq_results(query: str, raw_results: List[WebFAQResult]) -> List[WebFAQResult]:
    """Synthesize FAQ responses from multiple PubMed sources"""
    if not raw_results:
        return []
    
    # Extract key information from all sources
    all_snippets = [result.answer for result in raw_results]
    all_titles = [result.question for result in raw_results]
    
    # Create sources list
    sources = []
    for result in raw_results:
        # Get pmid and url from the first source in each result
        if result.sources:
            first_source = result.sources[0]
            sources.append(Source(
                title=result.question,
                pmid=first_source.pmid,
                url=first_source.url
            ))
    
    # Create synthesized FAQ responses
    faq_results = []
    
    # FAQ 1: What is it? (Definition/Overview)
    if raw_results:
        overview_snippet = f"Based on {len(raw_results)} medical studies: " + " ".join(all_snippets[:2])
        overview_snippet = overview_snippet[:300] + "..." if len(overview_snippet) > 300 else overview_snippet
        
        faq_results.append(WebFAQResult(
            question=f"What is {query.split()[0]}?",
            answer=overview_snippet,
            publication_date=raw_results[0].publication_date,
            sources=sources,
            population=raw_results[0].population
        ))
    
    # FAQ 2: Symptoms/Signs (if applicable)
    if len(raw_results) > 1:
        symptoms_snippet = f"Common symptoms and signs include: " + " ".join(all_snippets[1:3])
        symptoms_snippet = symptoms_snippet[:300] + "..." if len(symptoms_snippet) > 300 else symptoms_snippet
        
        faq_results.append(WebFAQResult(
            question=f"What are the symptoms of {query.split()[0]}?",
            answer=symptoms_snippet,
            publication_date=raw_results[1].publication_date,
            sources=sources,
            population=raw_results[1].population
        ))
    
    # FAQ 3: Treatment/Management (if applicable)
    if len(raw_results) > 2:
        treatment_snippet = f"Treatment and management approaches: " + " ".join(all_snippets[2:])
        treatment_snippet = treatment_snippet[:300] + "..." if len(treatment_snippet) > 300 else treatment_snippet
        
        faq_results.append(WebFAQResult(
            question=f"How is {query.split()[0]} treated?",
            answer=treatment_snippet,
            publication_date=raw_results[2].publication_date,
            sources=sources,
            population=raw_results[2].population
        ))
    
    return faq_results


@app.post("/sources", response_model=FAQResponse)
async def get_raw_sources(query: FAQQuery) -> FAQResponse:
    """
    Get raw source snippets directly from PubMed abstracts.
    
    This endpoint returns the actual text snippets from medical literature
    without any interpretation or summarization.
    
    - **query**: The medical question to search for
    - **max_results**: Maximum number of results (1-10, default: 3)
    
    Returns raw source material from PubMed abstracts.
    """
    try:
        # Search PubMed using the pubmed module
        results = pubmed.search_and_fetch(query.query, max_results=query.max_results or 3)
        
        if not results:
            # Return empty results if no articles found
            return FAQResponse(
                results=[],
                query=query.query,
                total_results=0
            )
        
        return FAQResponse(
            results=results,
            query=query.query,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching medical literature: {str(e)}"
        )


@app.post("/ashai", response_model=TelehealthResponse)
async def telehealth_agent(request: TelehealthRequest) -> TelehealthResponse:
    """
    AI Telehealth Agent for patient interactions.
    
    This endpoint provides a higher-level telehealth agent that responds to user input
    based on PubMed research and patient profile information.
    
    - **messages**: List of chat messages with role and content
    - **profile**: Patient profile information (name, location, language, category, history)
    
    Returns a personalized response with sources and FAQs used.
    """
    try:
        response = process_telehealth_request(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing telehealth request: {str(e)}"
        )


@app.post("/evaluator", response_model=EvaluationResponse)
async def evaluate_response(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate telehealth responses based on multiple criteria.
    
    This endpoint evaluates telehealth responses based on:
    - Medical Accuracy (40% weight)
    - Precision (25% weight) 
    - Language Clarity (20% weight)
    - Empathy Score (15% weight)
    
    - **response**: The telehealth response to evaluate
    - **context**: Context of the conversation
    - **profile**: Patient profile information
    
    Returns detailed evaluation scores and feedback.
    """
    try:
        evaluation = evaluate_telehealth_response(request)
        return evaluation
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating response: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "WebFAQMCP"}


# For direct usage/testing
def get_medical_faq(question: str) -> str:
    """
    Get medical FAQ information for a specific health question.
    
    This function searches PubMed for reliable medical information and formats
    the results as a comprehensive FAQ-style response.
    
    Args:
        question: The medical question to answer
        
    Returns:
        Formatted FAQ response with medical information and sources
    """
    try:
        results = pubmed.search_and_fetch(question, max_results=3)
        
        if not results:
            return f"I couldn't find any medical literature specifically about '{question}'. Please try rephrasing your question or using different medical terms."
        
        # Format the response
        response = f"## Medical Information: {question}\n\n"
        response += "**Disclaimer:** This information is for educational purposes only and should not replace professional medical advice.\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"### {i}. {result.question}\n"
            response += f"{result.answer}\n"
            if result.sources:
                source_url = result.sources[0].url
                response += f"**Source:** [{source_url}]({source_url})\n\n"
        
        response += "---\n"
        response += "**Important:** Please consult with a healthcare professional for personalized medical advice and treatment options."
        
        return response
        
    except Exception as e:
        return f"An error occurred while searching for medical information: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 