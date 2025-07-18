#!/usr/bin/env python3
"""
Telehealth Agent for WebFAQMCP

This module provides a higher-level telehealth agent that can engage in
conversations with patients and provide medical information based on
PubMed research.
"""

import re
from typing import List, Dict, Tuple, Optional
from models import Message, TelehealthRequest, TelehealthResponse, WebFAQResult, Source
import pubmed


class TelehealthAgent:
    """AI Telehealth Agent for patient interactions"""
    
    def __init__(self):
        self.conversation_history: List[Message] = []
    
    def process_conversation(self, request: TelehealthRequest) -> TelehealthResponse:
        """
        Process a conversation and generate a telehealth response
        
        Args:
            request: TelehealthRequest containing messages and profile
            
        Returns:
            TelehealthResponse with AI response, sources, and FAQs
        """
        # Extract the latest user message
        latest_message = self._get_latest_user_message(request.messages)
        if not latest_message:
            return self._create_error_response("No user message found")
        
        # Extract medical queries from the conversation
        medical_queries = self._extract_medical_queries(request.messages, request.profile)
        
        if not medical_queries:
            return self._create_error_response("No medical queries identified")
        
        # Search PubMed for relevant information
        faqs = []
        all_sources = []
        
        for query in medical_queries:
            try:
                results = pubmed.search_and_fetch(query, max_results=2)
                if results:
                    faqs.extend(results)
                    # Collect all sources
                    for result in results:
                        all_sources.extend(result.sources)
            except Exception as e:
                print(f"Error searching PubMed for query '{query}': {e}")
        
        if not faqs:
            return self._create_error_response("No relevant medical information found")
        
        # Generate response based on FAQs and profile
        response = self._generate_response(latest_message.content, faqs, request.profile)
        
        # Remove duplicate sources
        unique_sources = self._deduplicate_sources(all_sources)
        
        return TelehealthResponse(
            response=response,
            sources=unique_sources,
            faqs=faqs,
            evaluation=None  # Will be filled by evaluation endpoint
        )
    
    def _get_latest_user_message(self, messages: List[Message]) -> Optional[Message]:
        """Get the most recent user message"""
        for message in reversed(messages):
            if message.role.lower() == "user":
                return message
        return None
    
    def _extract_medical_queries(self, messages: List[Message], profile: str) -> List[str]:
        """Extract medical queries from conversation and profile"""
        queries = []
        
        # Extract from user messages
        for message in messages:
            if message.role.lower() == "user":
                content = message.content.lower()
                
                # Look for medical questions and concerns
                if any(word in content for word in ["pregnant", "pregnancy", "baby", "fetus"]):
                    queries.append("pregnancy health concerns")
                
                if any(word in content for word in ["eat", "food", "diet", "nutrition"]):
                    queries.append("pregnancy nutrition guidelines")
                
                if any(word in content for word in ["symptom", "pain", "discomfort", "problem"]):
                    queries.append("pregnancy symptoms and complications")
                
                if any(word in content for word in ["medicine", "medication", "drug", "pill"]):
                    queries.append("pregnancy medication safety")
                
                if any(word in content for word in ["exercise", "workout", "activity", "fitness"]):
                    queries.append("pregnancy exercise guidelines")
        
        # Extract from profile
        profile_lower = profile.lower()
        if "prenatal" in profile_lower or "pregnant" in profile_lower:
            queries.append("prenatal care guidelines")
        
        if "itching" in profile_lower:
            queries.append("pregnancy itching causes and treatment")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:3]  # Limit to 3 most relevant queries
    
    def _generate_response(self, user_message: str, faqs: List[WebFAQResult], profile: str) -> str:
        """Generate a personalized response based on FAQs and profile"""
        
        # Extract key information from profile
        profile_info = self._parse_profile(profile)
        
        # Build response based on user message and available FAQs
        response_parts = []
        
        # Greeting based on profile
        if profile_info.get("name"):
            response_parts.append(f"Hello {profile_info['name']}! I'm here to help you with your pregnancy-related questions.")
        else:
            response_parts.append("Hello! I'm here to help you with your pregnancy-related questions.")
        
        # Address the specific question
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ["eat", "food", "diet", "nutrition"]):
            response_parts.append("Regarding your question about food and nutrition during pregnancy:")
            
            # Find relevant FAQ about nutrition
            nutrition_faq = next((faq for faq in faqs if "nutrition" in faq.question.lower() or "diet" in faq.question.lower()), None)
            if nutrition_faq:
                response_parts.append(f"Based on medical research: {nutrition_faq.answer}")
            else:
                response_parts.append("It's important to maintain a balanced diet during pregnancy. Consult with your healthcare provider for personalized nutrition advice.")
        
        elif any(word in user_lower for word in ["symptom", "pain", "discomfort", "problem"]):
            response_parts.append("Regarding your symptoms:")
            
            # Find relevant FAQ about symptoms
            symptom_faq = next((faq for faq in faqs if "symptom" in faq.question.lower() or "complication" in faq.question.lower()), None)
            if symptom_faq:
                response_parts.append(f"Based on medical research: {symptom_faq.answer}")
            else:
                response_parts.append("Some symptoms are normal during pregnancy, but it's important to discuss any concerns with your healthcare provider.")
        
        else:
            # General pregnancy information
            if faqs:
                response_parts.append("Based on current medical research:")
                response_parts.append(faqs[0].answer)
        
        # Add personalized advice based on profile
        if profile_info.get("language") == "Hindi":
            response_parts.append("मैं आपकी मदद के लिए यहाँ हूँ। कृपया अपने डॉक्टर से भी सलाह लें।")
        
        # Add safety disclaimer
        response_parts.append("Remember: This information is for educational purposes only. Always consult with your healthcare provider for personalized medical advice.")
        
        return " ".join(response_parts)
    
    def _parse_profile(self, profile: str) -> Dict[str, str]:
        """Parse patient profile information"""
        profile_info = {}
        
        # Extract name
        name_match = re.search(r"Name:\s*(.+)", profile)
        if name_match:
            profile_info["name"] = name_match.group(1).strip()
        
        # Extract location
        location_match = re.search(r"Location:\s*(.+)", profile)
        if location_match:
            profile_info["location"] = location_match.group(1).strip()
        
        # Extract language
        language_match = re.search(r"Language:\s*(.+)", profile)
        if language_match:
            profile_info["language"] = language_match.group(1).strip()
        
        # Extract category
        category_match = re.search(r"Category:\s*(.+)", profile)
        if category_match:
            profile_info["category"] = category_match.group(1).strip()
        
        return profile_info
    
    def _deduplicate_sources(self, sources: List[Source]) -> List[Source]:
        """Remove duplicate sources based on PMID"""
        seen_pmids = set()
        unique_sources = []
        
        for source in sources:
            if source.pmid not in seen_pmids:
                seen_pmids.add(source.pmid)
                unique_sources.append(source)
        
        return unique_sources
    
    def _create_error_response(self, error_message: str) -> TelehealthResponse:
        """Create an error response"""
        return TelehealthResponse(
            response=f"I apologize, but I encountered an issue: {error_message}. Please try rephrasing your question or consult with your healthcare provider.",
            sources=[],
            faqs=[],
            evaluation=None
        )


# Global telehealth agent instance
telehealth_agent = TelehealthAgent()


def process_telehealth_request(request: TelehealthRequest) -> TelehealthResponse:
    """Convenience function to process telehealth requests"""
    return telehealth_agent.process_conversation(request) 