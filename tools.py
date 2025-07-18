from typing import List
from models import WebFAQResult
import pubmed


def _search_pubmed(query: str, max_results: int = 3) -> List[WebFAQResult]:
    """
    Internal function to search PubMed for medical information.
    
    Args:
        query: The medical question or topic to search for
        max_results: Maximum number of results to return (default: 3)
        
    Returns:
        List of WebFAQResult objects containing title, snippet, and URL
    """
    try:
        results = pubmed.search_and_fetch(query, max_results)
        return results
    except Exception as e:
        # Return empty list if search fails
        print(f"Error in PubMed search: {e}")
        return []


def get_medical_faq(question: str) -> str:
    """
    Get medical FAQ information for a specific health question.
    
    This function searches PubMed for reliable medical information and formats
    the results as a comprehensive FAQ-style response with sources.
    
    Args:
        question: The medical question to answer
        
    Returns:
        Formatted FAQ response with medical information and sources
    """
    try:
        results = _search_pubmed(question, max_results=3)
        
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


# Export the main function
__all__ = ["get_medical_faq"] 