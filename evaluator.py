#!/usr/bin/env python3
"""
Evaluation Agent for WebFAQMCP

This module provides an evaluation agent that assesses telehealth responses
based on medical accuracy, precision, language clarity, and empathy.
"""

import re
from typing import Dict, List
from models import EvaluationRequest, EvaluationResponse


class EvaluationAgent:
    """AI Evaluation Agent for assessing telehealth responses"""
    
    def __init__(self):
        # Weights for different evaluation criteria
        self.weights = {
            "medical_accuracy": 0.40,
            "precision": 0.25,
            "language_clarity": 0.20,
            "empathy_score": 0.15
        }
    
    def evaluate_response(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Evaluate a telehealth response based on multiple criteria
        
        Args:
            request: EvaluationRequest containing response, context, and profile
            
        Returns:
            EvaluationResponse with scores and feedback
        """
        response = request.response
        context = request.context
        profile = request.profile
        
        # Evaluate each criterion
        medical_accuracy = self._evaluate_medical_accuracy(response, context)
        precision = self._evaluate_precision(response, context)
        language_clarity = self._evaluate_language_clarity(response, profile)
        empathy_score = self._evaluate_empathy(response, profile)
        
        # Calculate overall weighted score
        overall_score = (
            medical_accuracy * self.weights["medical_accuracy"] +
            precision * self.weights["precision"] +
            language_clarity * self.weights["language_clarity"] +
            empathy_score * self.weights["empathy_score"]
        )
        
        # Generate detailed feedback
        feedback = self._generate_feedback(
            medical_accuracy, precision, language_clarity, empathy_score, response
        )
        
        return EvaluationResponse(
            medical_accuracy=medical_accuracy,
            precision=precision,
            language_clarity=language_clarity,
            empathy_score=empathy_score,
            overall_score=overall_score,
            feedback=feedback
        )
    
    def _evaluate_medical_accuracy(self, response: str, context: str) -> float:
        """Evaluate medical accuracy of the response (0-100)"""
        score = 70.0  # Base score
        
        # Positive indicators
        positive_indicators = [
            "consult with your healthcare provider",
            "medical research",
            "evidence-based",
            "scientific",
            "clinical",
            "professional medical advice",
            "healthcare professional"
        ]
        
        for indicator in positive_indicators:
            if indicator.lower() in response.lower():
                score += 5
        
        # Negative indicators
        negative_indicators = [
            "definitely",
            "always",
            "never",
            "guaranteed",
            "cure",
            "miracle",
            "alternative medicine",
            "natural cure"
        ]
        
        for indicator in negative_indicators:
            if indicator.lower() in response.lower():
                score -= 10
        
        # Check for disclaimer
        if "educational purposes only" in response.lower():
            score += 10
        
        # Check for safety warnings
        if "consult" in response.lower() or "healthcare provider" in response.lower():
            score += 5
        
        return min(100.0, max(0.0, score))
    
    def _evaluate_precision(self, response: str, context: str) -> float:
        """Evaluate precision of the response (0-100)"""
        score = 60.0  # Base score
        
        # Check if response addresses the specific question
        context_lower = context.lower()
        response_lower = response.lower()
        
        # Look for specific medical terms in context
        medical_terms = ["pregnancy", "nutrition", "symptom", "medication", "exercise"]
        relevant_terms = [term for term in medical_terms if term in context_lower]
        
        # Check if response addresses relevant terms
        addressed_terms = 0
        for term in relevant_terms:
            if term in response_lower:
                addressed_terms += 1
        
        if relevant_terms:
            precision_ratio = addressed_terms / len(relevant_terms)
            score += precision_ratio * 30
        
        # Check for specific, actionable information
        if any(word in response_lower for word in ["important", "essential", "recommended", "guidelines"]):
            score += 10
        
        # Penalize overly generic responses
        generic_phrases = [
            "it depends",
            "maybe",
            "possibly",
            "could be",
            "might be"
        ]
        
        for phrase in generic_phrases:
            if phrase in response_lower:
                score -= 5
        
        return min(100.0, max(0.0, score))
    
    def _evaluate_language_clarity(self, response: str, profile: str) -> float:
        """Evaluate language clarity of the response (0-100)"""
        score = 70.0  # Base score
        
        # Check sentence structure
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len(sentences)
        
        # Prefer medium-length sentences (10-20 words)
        if 10 <= avg_sentence_length <= 20:
            score += 15
        elif avg_sentence_length < 10:
            score += 10
        elif avg_sentence_length > 30:
            score -= 10
        
        # Check for medical jargon
        medical_jargon = [
            "pathophysiology", "etiology", "prognosis", "differential diagnosis",
            "contraindications", "pharmacokinetics", "metabolic"
        ]
        
        jargon_count = sum(1 for jargon in medical_jargon if jargon.lower() in response.lower())
        score -= jargon_count * 5
        
        # Check for clear structure
        if any(word in response.lower() for word in ["first", "second", "finally", "additionally"]):
            score += 10
        
        # Check for appropriate language based on profile
        profile_lower = profile.lower()
        if "hindi" in profile_lower and any(char in response for char in "अआइईउऊएऐओऔ"):
            score += 10  # Bonus for using Hindi when appropriate
        
        # Penalize overly complex language
        complex_words = len([word for word in response.split() if len(word) > 12])
        score -= complex_words * 2
        
        return min(100.0, max(0.0, score))
    
    def _evaluate_empathy(self, response: str, profile: str) -> float:
        """Evaluate empathy score of the response (0-100)"""
        score = 60.0  # Base score
        
        # Extract name from profile
        name_match = re.search(r"Name:\s*(.+)", profile)
        patient_name = name_match.group(1).strip() if name_match else None
        
        # Personalization
        if patient_name and patient_name.lower() in response.lower():
            score += 15
        
        # Empathetic language
        empathetic_phrases = [
            "i understand",
            "i'm here to help",
            "i know this can be",
            "it's normal to feel",
            "don't worry",
            "you're not alone",
            "i'm here for you"
        ]
        
        for phrase in empathetic_phrases:
            if phrase.lower() in response.lower():
                score += 5
        
        # Supportive language
        supportive_words = [
            "support", "help", "assist", "guide", "care", "comfort"
        ]
        
        for word in supportive_words:
            if word.lower() in response.lower():
                score += 3
        
        # Cultural sensitivity
        profile_lower = profile.lower()
        if "india" in profile_lower or "hindi" in profile_lower:
            if any(char in response for char in "अआइईउऊएऐओऔ"):
                score += 10  # Bonus for cultural sensitivity
        
        # Avoid dismissive language
        dismissive_phrases = [
            "just",
            "simply",
            "obviously",
            "clearly",
            "of course"
        ]
        
        for phrase in dismissive_phrases:
            if phrase.lower() in response.lower():
                score -= 5
        
        return min(100.0, max(0.0, score))
    
    def _generate_feedback(self, medical_accuracy: float, precision: float, 
                          language_clarity: float, empathy_score: float, response: str) -> str:
        """Generate detailed feedback based on evaluation scores"""
        feedback_parts = []
        
        # Overall assessment
        overall_score = (
            medical_accuracy * self.weights["medical_accuracy"] +
            precision * self.weights["precision"] +
            language_clarity * self.weights["language_clarity"] +
            empathy_score * self.weights["empathy_score"]
        )
        
        if overall_score >= 85:
            feedback_parts.append("Excellent response! This is a high-quality telehealth interaction.")
        elif overall_score >= 70:
            feedback_parts.append("Good response with room for improvement.")
        elif overall_score >= 50:
            feedback_parts.append("Adequate response that needs enhancement.")
        else:
            feedback_parts.append("This response needs significant improvement.")
        
        # Specific feedback for each criterion
        if medical_accuracy < 70:
            feedback_parts.append("Medical accuracy could be improved by including more evidence-based information and appropriate disclaimers.")
        elif medical_accuracy >= 85:
            feedback_parts.append("Excellent medical accuracy with appropriate safety warnings.")
        
        if precision < 60:
            feedback_parts.append("Response could be more precise in addressing the specific patient concerns.")
        elif precision >= 80:
            feedback_parts.append("Response precisely addresses the patient's specific questions.")
        
        if language_clarity < 65:
            feedback_parts.append("Language could be clearer and more accessible to patients.")
        elif language_clarity >= 85:
            feedback_parts.append("Clear, accessible language that patients can easily understand.")
        
        if empathy_score < 60:
            feedback_parts.append("Response could be more empathetic and personalized.")
        elif empathy_score >= 80:
            feedback_parts.append("Excellent empathy and personalization in the response.")
        
        # Suggestions for improvement
        suggestions = []
        if medical_accuracy < 80:
            suggestions.append("Include more specific medical references and safety disclaimers")
        if precision < 70:
            suggestions.append("Address the patient's specific question more directly")
        if language_clarity < 75:
            suggestions.append("Use simpler language and avoid medical jargon")
        if empathy_score < 70:
            suggestions.append("Add more personalized and supportive language")
        
        if suggestions:
            feedback_parts.append(f"Suggestions for improvement: {', '.join(suggestions)}.")
        
        return " ".join(feedback_parts)


# Global evaluation agent instance
evaluation_agent = EvaluationAgent()


def evaluate_telehealth_response(request: EvaluationRequest) -> EvaluationResponse:
    """Convenience function to evaluate telehealth responses"""
    return evaluation_agent.evaluate_response(request) 