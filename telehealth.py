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
        response = self._generate_response(latest_message.content, faqs, request.profile, request.messages)
        
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
        
        # Get the latest user message to focus on their specific question
        latest_message = self._get_latest_user_message(messages)
        if not latest_message:
            return ["general health guidelines"]
        
        content = latest_message.content.lower()
        
        # Build very specific queries based on the user's exact question
        # Combine pregnancy status with specific concerns
        is_pregnant = any(word in content for word in ["pregnant", "pregnancy", "baby", "fetus"])
        
        if is_pregnant:
            # For pregnancy-related queries, be very specific
            if any(word in content for word in ["eat", "food", "diet", "nutrition", "banana", "fruit", "vegetable"]):
                queries.append("pregnancy nutrition diet food safety")
            elif any(word in content for word in ["headache", "head ache", "migraine", "head pain"]):
                queries.append("pregnancy headache management")
            elif any(word in content for word in ["pain", "ache", "discomfort", "hurt"]):
                queries.append("pregnancy pain management")
            elif any(word in content for word in ["medicine", "medication", "drug", "pill", "treatment"]):
                queries.append("pregnancy medication safety")
            elif any(word in content for word in ["exercise", "activity", "work", "movement"]):
                queries.append("pregnancy exercise safety")
            elif any(word in content for word in ["sleep", "rest", "tired", "fatigue"]):
                queries.append("pregnancy sleep rest")
            else:
                # General pregnancy query
                queries.append("pregnancy health care")
        else:
            # For non-pregnancy queries, be specific about the symptom/concern
            if any(word in content for word in ["headache", "head ache", "migraine", "head pain"]):
                queries.append("headache treatment management")
            elif any(word in content for word in ["fever", "temperature", "hot"]):
                queries.append("fever management treatment")
            elif any(word in content for word in ["cough", "cold", "flu", "sick"]):
                queries.append("respiratory symptoms treatment")
            elif any(word in content for word in ["pain", "ache", "discomfort", "hurt"]):
                queries.append("pain management treatment")
            elif any(word in content for word in ["eat", "food", "diet", "nutrition"]):
                queries.append("nutrition diet guidelines")
            else:
                # Use the user's actual words for the query
                # Clean up the message to create a focused medical query
                query_words = [word for word in content.split() if len(word) > 2 and word not in ["hello", "hi", "can", "you", "help", "please", "thank", "thanks"]]
                if query_words:
                    queries.append(" ".join(query_words[:5]))  # Use first 5 meaningful words
                else:
                    queries.append("general health guidelines")
        
        # Extract from profile for additional context
        profile_lower = profile.lower()
        if "itching" in profile_lower and is_pregnant:
            queries.append("pregnancy itching causes treatment")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:2]  # Limit to 2 most relevant queries to reduce noise
    
    def _generate_response(self, user_message: str, faqs: List[WebFAQResult], profile: str, messages: Optional[List[Message]] = None) -> str:
        """Generate a personalized response based on FAQs and profile"""
        
        # Extract key information from profile
        profile_info = self._parse_profile(profile)
        
        # Check for system messages with evaluation feedback
        evaluation_feedback = None
        if messages:
            for message in messages:
                if message.role.lower() == "system" and "evaluation score" in message.content.lower():
                    evaluation_feedback = message.content
                    break
        
        # Build response based on user message and available FAQs
        response_parts = []
        
        # If we have evaluation feedback, acknowledge it
        if evaluation_feedback:
            response_parts.append("I understand the previous response needed improvement. Let me provide a better answer:")
        
        # Greeting based on profile
        if profile_info.get("name"):
            response_parts.append(f"Hello {profile_info['name']}! I'm here to help you with your health questions.")
        else:
            response_parts.append("Hello! I'm here to help you with your health questions.")
        
        # Directly address the user's specific question
        response_parts.append(f"Regarding your question: \"{user_message}\"")
        response_parts.append("Let me provide you with specific medical information:")
        
        # Address the specific question
        user_lower = user_message.lower()
        
        # Pregnancy-specific queries
        if any(word in user_lower for word in ["pregnant", "pregnancy", "baby", "fetus"]):
            response_parts.append("Regarding your pregnancy-related question:")
            
            if any(word in user_lower for word in ["eat", "food", "diet", "nutrition"]):
                response_parts.append("Regarding your question about food and nutrition during pregnancy:")
                
                # Find relevant FAQ about nutrition
                nutrition_faq = next((faq for faq in faqs if "nutrition" in faq.question.lower() or "diet" in faq.question.lower()), None)
                if nutrition_faq:
                    response_parts.append(f"Based on medical research: {nutrition_faq.answer}")
                else:
                    response_parts.append("It's important to maintain a balanced diet during pregnancy. Consult with your healthcare provider for personalized nutrition advice.")
            
            elif any(word in user_lower for word in ["symptom", "pain", "discomfort", "problem"]):
                response_parts.append("Regarding your pregnancy symptoms:")
                
                # Find relevant FAQ about symptoms
                symptom_faq = next((faq for faq in faqs if "symptom" in faq.question.lower() or "complication" in faq.question.lower()), None)
                if symptom_faq:
                    response_parts.append(f"Based on medical research: {symptom_faq.answer}")
                else:
                    response_parts.append("Some symptoms are normal during pregnancy, but it's important to discuss any concerns with your healthcare provider.")
            
            else:
                # General pregnancy information
                relevant_faq = self._find_most_relevant_faq(user_message, faqs)
                if relevant_faq:
                    response_parts.append("Based on current medical research:")
                    response_parts.append(relevant_faq.answer)
                else:
                    response_parts.append("I understand you have pregnancy-related questions. Please consult with your healthcare provider for personalized prenatal care advice.")
        
        # General medical queries
        elif any(word in user_lower for word in ["headache", "head ache", "migraine", "head pain"]):
            response_parts.append("Regarding your headache:")
            
            # Find relevant FAQ about headaches
            headache_faq = next((faq for faq in faqs if "headache" in faq.question.lower() or "pain" in faq.question.lower()), None)
            if headache_faq:
                response_parts.append(f"Based on medical research: {headache_faq.answer}")
            else:
                response_parts.append("Headaches can have various causes. If your headache is severe, persistent, or accompanied by other symptoms, please consult with your healthcare provider.")
        
        elif any(word in user_lower for word in ["fever", "temperature", "hot"]):
            response_parts.append("Regarding your fever:")
            
            fever_faq = next((faq for faq in faqs if "fever" in faq.question.lower() or "temperature" in faq.question.lower()), None)
            if fever_faq:
                response_parts.append(f"Based on medical research: {fever_faq.answer}")
            else:
                response_parts.append("Fever is often a sign of infection. Monitor your temperature and consult with your healthcare provider if it persists or is accompanied by other symptoms.")
        
        elif any(word in user_lower for word in ["cough", "cold", "flu", "sick"]):
            response_parts.append("Regarding your respiratory symptoms:")
            
            respiratory_faq = next((faq for faq in faqs if "cough" in faq.question.lower() or "respiratory" in faq.question.lower()), None)
            if respiratory_faq:
                response_parts.append(f"Based on medical research: {respiratory_faq.answer}")
            else:
                response_parts.append("Respiratory symptoms can be caused by various conditions. Rest, hydration, and monitoring your symptoms are important. Consult with your healthcare provider if symptoms worsen.")
        
        else:
            # Try to find the most relevant FAQ based on user message keywords
            relevant_faq = self._find_most_relevant_faq(user_message, faqs)
            if relevant_faq:
                response_parts.append("Based on current medical research:")
                response_parts.append(relevant_faq.answer)
            else:
                response_parts.append("I understand you have health concerns. It's important to discuss your specific symptoms with your healthcare provider for personalized medical advice.")
        
        # Add personalized advice based on profile
        if profile_info.get("language") == "Hindi":
            response_parts.append("मैं आपकी मदद के लिए यहाँ हूँ। कृपया अपने डॉक्टर से भी सलाह लें।")
        
        # Add safety disclaimer
        response_parts.append("Remember: This information is for educational purposes only. Always consult with your healthcare provider for personalized medical advice.")
        
        return " ".join(response_parts)
    
    def _find_most_relevant_faq(self, user_message: str, faqs: List[WebFAQResult]) -> Optional[WebFAQResult]:
        """Find the most relevant FAQ based on user message keywords"""
        if not faqs:
            return None
        
        user_lower = user_message.lower()
        user_words = set(user_lower.split())
        
        best_faq = None
        best_score = 0
        
        for faq in faqs:
            score = 0
            faq_text = (faq.question + " " + faq.answer).lower()
            faq_words = set(faq_text.split())
            
            # Calculate relevance score based on word overlap
            common_words = user_words.intersection(faq_words)
            score = len(common_words)
            
            # Boost score for important medical terms
            important_terms = ['pregnancy', 'pregnant', 'baby', 'nutrition', 'diet', 'headache', 'pain', 'symptom', 'treatment', 'health']
            for term in important_terms:
                if term in user_lower and term in faq_text:
                    score += 3
            
            # Penalize completely unrelated topics
            unrelated_terms = ['microplastic', 'plastic', 'adolescent', 'thyroid', 'spina bifida']
            for term in unrelated_terms:
                if term in faq_text and term not in user_lower:
                    score -= 5
            
            if score > best_score:
                best_score = score
                best_faq = faq
        
        # Only return if we have a reasonable relevance score
        return best_faq if best_score > 2 else None
    
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