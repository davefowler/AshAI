from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import pubmed
from models import (
    FAQQuery, FAQResponse, WebFAQResult, Source,
    TelehealthRequest, TelehealthResponse,
    EvaluationRequest, EvaluationResponse, Message, SourcesResponse
)
from telehealth import process_telehealth_request
from evaluator import evaluate_telehealth_response
from niharika_faq import search_niharika_faqs

# Create FastAPI app
app = FastAPI(
    title="AshAI - AI Telehealth Agent",
    description="Comprehensive telehealth platform providing evidence-based medical information with cultural sensitivity",
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
    """Root endpoint with simple web UI"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return {"error": "Template file not found. Please ensure templates/index.html exists."}


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
        raw_results = pubmed.search_and_fetch(
            query.query, 
            max_results=query.max_results or 3,
            snippet_length=query.snippet_length or 500
        )
        
        if not raw_results:
            # Return empty results if no articles found
            return FAQResponse(
                results=[],
                query=query.query,
                total_results=0
            )
        
        # Synthesize FAQ responses from multiple sources
        faq_results = _synthesize_faq_results(query.query, raw_results)
        
        # Apply relevance filtering if threshold is specified
        if query.relevance_threshold is not None:
            filtered_results = _filter_by_relevance(query.query, faq_results, query.relevance_threshold)
        else:
            filtered_results = faq_results
        
        return FAQResponse(
            results=filtered_results,
            query=query.query,
            total_results=len(filtered_results)
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
                url=first_source.url,
                content=result.answer
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


def _filter_by_relevance(query: str, faqs: List[WebFAQResult], threshold: float) -> List[WebFAQResult]:
    """Filter FAQ results by relevance score"""
    filtered = []
    query_words = set(query.lower().split())
    
    for faq in faqs:
        # Combine question and answer text
        faq_text = (faq.question + " " + faq.answer).lower()
        faq_words = set(faq_text.split())
        
        # Calculate word overlap score
        common_words = query_words.intersection(faq_words)
        overlap_score = len(common_words) / max(len(query_words), 1)  # Avoid division by zero
        
        # Boost score for medical terms
        medical_terms = ['pregnancy', 'pregnant', 'baby', 'nutrition', 'diet', 'headache', 'pain', 'symptom', 'treatment']
        term_matches = sum(1 for term in medical_terms if term in query.lower() and term in faq_text)
        term_boost = term_matches * 0.1  # Each matching term adds 0.1 to score
        
        # Calculate final relevance score
        relevance = min(1.0, overlap_score + term_boost)
        
        # Add FAQ if it meets the threshold
        if relevance >= threshold:
            filtered.append(faq)
    
    return filtered


@app.post("/sources", response_model=SourcesResponse)
async def get_raw_sources(query: FAQQuery) -> SourcesResponse:
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
        results = pubmed.search_and_fetch(
            query.query, 
            max_results=query.max_results or 3,
            snippet_length=query.snippet_length or 500
        )
        
        if not results:
            # Return empty results if no articles found
            return SourcesResponse(
                sources=[],
                query=query.query,
                total_results=0
            )
        
        # Convert to raw source format
        raw_sources = []
        for result in results:
            # Each result has sources, extract the content from the answer
            if result.sources:
                for source in result.sources:
                    raw_sources.append(Source(
                        title=source.title,
                        pmid=source.pmid,
                        url=source.url,
                        content=result.answer  # Use the answer as content snippet
                    ))
        
        return SourcesResponse(
            sources=raw_sources,
            query=query.query,
            total_results=len(raw_sources)
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
    based on PubMed research and patient profile information. The agent self-evaluates
    its responses and retries with improved instructions if the evaluation score is low.
    
    - **messages**: List of chat messages with role and content
    - **profile**: Patient profile information (name, location, language, category, history)
    
    Returns a personalized response with sources, FAQs, and self-evaluation.
    """
    try:
        # Generate initial response
        initial_response = process_telehealth_request(request)
        
        # Self-evaluate the response
        evaluation_request = EvaluationRequest(
            response=initial_response.response,
            messages=request.messages,
            profile=request.profile
        )
        
        evaluation = evaluate_telehealth_response(evaluation_request)
        
        # Check if evaluation score is low (below 7.0 out of 10)
        if evaluation.overall_score < 7.0:
            # Create improved request with evaluation feedback
            improved_messages = request.messages.copy()
            
            # Add system message with evaluation feedback
            feedback_message = Message(
                role="system",
                content=f"""Your previous response received a low evaluation score ({evaluation.overall_score:.1f}/10). 
                Please improve your response based on this feedback:
                
                Medical Accuracy ({evaluation.medical_accuracy:.1f}/10)
                Precision ({evaluation.precision:.1f}/10)
                Language Clarity ({evaluation.language_clarity:.1f}/10)
                Empathy ({evaluation.empathy_score:.1f}/10)
                
                Detailed feedback: {evaluation.feedback}
                
                Focus on being more accurate, precise, clear, and empathetic in your response."""
            )
            
            improved_messages.insert(0, feedback_message)
            
            # Generate improved response
            improved_request = TelehealthRequest(
                messages=improved_messages,
                profile=request.profile
            )
            
            improved_response = process_telehealth_request(improved_request)
            
            # Re-evaluate the improved response
            improved_evaluation_request = EvaluationRequest(
                response=improved_response.response,
                messages=request.messages,  # Use original messages for evaluation
                profile=request.profile
            )
            
            improved_evaluation = evaluate_telehealth_response(improved_evaluation_request)
            
            # Return the better response
            if improved_evaluation.overall_score > evaluation.overall_score:
                improved_response.evaluation = {
                    "medical_accuracy": improved_evaluation.medical_accuracy,
                    "precision": improved_evaluation.precision,
                    "language_clarity": improved_evaluation.language_clarity,
                    "empathy_score": improved_evaluation.empathy_score,
                    "overall_score": improved_evaluation.overall_score,
                    "feedback": improved_evaluation.feedback
                }
                return improved_response
            else:
                initial_response.evaluation = {
                    "medical_accuracy": evaluation.medical_accuracy,
                    "precision": evaluation.precision,
                    "language_clarity": evaluation.language_clarity,
                    "empathy_score": evaluation.empathy_score,
                    "overall_score": evaluation.overall_score,
                    "feedback": evaluation.feedback
                }
                return initial_response
        else:
            # Score is good enough, return initial response with evaluation
            initial_response.evaluation = {
                "medical_accuracy": evaluation.medical_accuracy,
                "precision": evaluation.precision,
                "language_clarity": evaluation.language_clarity,
                "empathy_score": evaluation.empathy_score,
                "overall_score": evaluation.overall_score,
                "feedback": evaluation.feedback
            }
            return initial_response
        
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
    - **messages**: Full chat history for context evaluation
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
    return {"status": "healthy", "service": "AshAI"}


@app.post("/turn")
async def turn_integration(request: Request):
    """
    Turn.io integration endpoint for WhatsApp chat integration.
    
    Handles both handshake and context retrieval requests from Turn.io.
    Converts WhatsApp chat messages to AshAI format and returns responses.
    """
    try:
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Handle handshake request
        if query_params.get("handshake") == "true":
            return {
                "version": "1.0.0-alpha",
                "capabilities": {
                    "actions": True,
                    "suggested_responses": True,
                    "context_objects": [
                        {
                            "title": "Patient Information",
                            "code": "patient_info",
                            "type": "table"
                        },
                        {
                            "title": "Medical Context",
                            "code": "medical_context", 
                            "type": "ordered-list"
                        }
                    ]
                }
            }
        
        # Handle context retrieval request
        body = await request.json()
        chat = body.get("chat", {})
        messages = body.get("messages", [])
        
        # Convert Turn.io messages to AshAI format
        ashai_messages = []
        for msg in messages:
            # Only process user messages (inbound)
            if msg.get("direction") == "inbound":
                ashai_messages.append({
                    "role": "user",
                    "content": msg.get("text", "")
                })
        
        # Create patient profile from chat context
        patient_profile = f"""Name: {chat.get('owner', 'Unknown')}
Location: WhatsApp User
Language: English
Category: General
Patient History: Chat-based consultation"""
        
        # Create AshAI request
        ashai_request = TelehealthRequest(
            messages=[Message(**msg) for msg in ashai_messages],
            profile=patient_profile
        )
        
        # Get AshAI response
        ashai_response = process_telehealth_request(ashai_request)
        
        # Convert to Turn.io format
        context_objects = {
            "patient_info": {
                "Phone Number": chat.get("owner", "Unknown"),
                "Chat State": chat.get("state", "Active"),
                "Response Quality": f"{ashai_response.evaluation.get('overall_score', 0):.1f}/10" if ashai_response.evaluation else "N/A"
            },
            "medical_context": [
                f"**Medical Sources**: {len(ashai_response.sources)} PubMed articles",
                f"**Response Length**: {len(ashai_response.response)} characters",
                f"**FAQs Used**: {len(ashai_response.faqs)} medical FAQs"
            ]
        }
        
        # Create suggested responses from AshAI
        suggested_responses = []
        if ashai_response.response:
            # Get evaluation score for confidence calculation
            evaluation_score = ashai_response.evaluation.get('overall_score', 75) if ashai_response.evaluation else 75
            base_confidence = evaluation_score / 100.0  # Convert to 0-1 scale
            
            # Add the complete AshAI response as the main suggested response
            suggested_responses.append({
                "type": "TEXT",
                "title": "Complete Medical Response",
                "body": ashai_response.response,
                "confidence": round(base_confidence, 2)
            })
        
        # Add individual FAQs as additional suggested responses
        if ashai_response.faqs:
            for i, faq in enumerate(ashai_response.faqs[:3]):  # Max 3 FAQ suggestions
                if faq.answer and len(faq.answer.strip()) > 20:  # Only add substantial FAQs
                    # FAQ confidence is slightly lower than main response but still high
                    faq_confidence = round(base_confidence * 0.9, 2)
                    
                    suggested_responses.append({
                        "type": "TEXT",
                        "title": f"FAQ: {faq.question[:50]}{'...' if len(faq.question) > 50 else ''}",
                        "body": faq.answer,
                        "confidence": faq_confidence
                    })
        
        # Add disclaimer as a separate suggestion with moderate confidence
        suggested_responses.append({
            "type": "TEXT",
            "title": "Medical Disclaimer",
            "body": "This information is for educational purposes only. Please consult with your healthcare provider for personalized medical advice.",
            "confidence": 0.7  # Standard confidence for disclaimers
        })
        
        return {
            "version": "1.0.0-alpha",
            "context_objects": context_objects,
            "actions": {},
            "suggested_responses": suggested_responses
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Turn.io request: {str(e)}"
        )


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


@app.post("/faq/niharika", response_model=FAQResponse)
async def search_niharika_faq(query: FAQQuery) -> FAQResponse:
    """
    Search Niharika FAQ data from Google Sheets.
    
    This endpoint searches a curated Google Sheet containing Bengali/English 
    medical Q&A pairs specifically for pregnancy and maternal health.
    
    - **query**: The medical question to search for
    - **max_results**: Maximum number of results (1-10, default: 3)
    - **snippet_length**: Length of content snippets (not used for this endpoint)
    
    Returns FAQ responses from the Niharika Google Sheet database.
    """
    try:
        # Search Niharika FAQ data
        results = search_niharika_faqs(query.query, max_results=query.max_results or 3)
        
        if not results:
            # Return empty results if no FAQs found
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
            detail=f"Error searching Niharika FAQ data: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 