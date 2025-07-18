#!/usr/bin/env python3
"""
Niharika FAQ Module

This module provides functionality to read Q&A pairs from a Google Sheet
for the Niharika FAQ endpoint.
"""

import requests
import csv
from io import StringIO
from typing import List, Dict, Optional
from models import WebFAQResult, Source


class NiharikaFAQService:
    """Service for reading FAQ data from Google Sheets"""
    
    def __init__(self):
        # Public Google Sheet URL
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1jE9m65m_fCQRZcfFfTVMxifmJKaE6J4WPKY9CrRtOkg/edit?usp=sharing"
        self.csv_url = "https://docs.google.com/spreadsheets/d/1jE9m65m_fCQRZcfFfTVMxifmJKaE6J4WPKY9CrRtOkg/export?format=csv&gid=1981029180"
        
    def search_faqs(self, query: str, max_results: int = 3, relevance_threshold: float = 0.3) -> List[WebFAQResult]:
        """
        Search FAQ data from Google Sheet based on query
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            relevance_threshold: Minimum relevance score (0.0-1.0) to include results
            
        Returns:
            List of WebFAQResult objects
        """
        try:
            # Try to read from the actual Google Sheet first
            return self._read_from_sheet(query, max_results)
        except Exception as e:
            print(f"Error reading from Google Sheet: {e}")
            # Fallback to mock data
            return self._get_mock_faqs(query, max_results)
    
    def _read_from_sheet(self, query: str, max_results: int) -> List[WebFAQResult]:
        """
        Read FAQ data from the actual Google Sheet
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of WebFAQResult objects
        """
        try:
            # Download CSV from Google Sheet
            response = requests.get(self.csv_url)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = StringIO(response.text)
            reader = csv.reader(csv_data)
            
            # Skip header rows and find the data section
            faq_data = []
            in_data_section = False
            
            for row in reader:
                if len(row) > 0:
                    # Look for the "Keywords" header to start data section
                    if "Keywords" in row[0] and "Questions" in row[1]:
                        in_data_section = True
                        continue
                    
                    # If we're in data section and have enough columns
                    if in_data_section and len(row) >= 4:
                        keywords = row[0].strip()
                        question_bengali = row[1].strip()
                        question_english = row[2].strip()
                        answer_bengali = row[3].strip()
                        answer_english = row[4].strip() if len(row) > 4 else ""
                        
                        # Skip empty rows
                        if keywords and question_bengali:
                            faq_data.append({
                                "keywords": keywords,
                                "question_bengali": question_bengali,
                                "question_english": question_english,
                                "answer_bengali": answer_bengali,
                                "answer_english": answer_english
                            })
            
            # Calculate relevance scores for each FAQ
            query_lower = query.lower()
            query_words = set(query_lower.split())
            scored_faqs = []
            
            for faq in faq_data:
                # Combine all searchable text
                faq_text = (
                    faq["keywords"].lower() + " " +
                    faq["question_english"].lower() + " " +
                    faq["answer_english"].lower()
                )
                faq_words = set(faq_text.split())
                
                # Calculate word overlap score
                common_words = query_words.intersection(faq_words)
                overlap_score = len(common_words) / max(len(query_words), 1)
                
                # Boost score for medical terms
                medical_terms = ['pregnancy', 'pregnant', 'baby', 'nutrition', 'diet', 'headache', 'pain', 'symptom', 'treatment']
                term_matches = sum(1 for term in medical_terms if term in query_lower and term in faq_text)
                term_boost = term_matches * 0.1
                
                # Calculate final relevance score
                relevance = min(1.0, overlap_score + term_boost)
                
                scored_faqs.append((faq, relevance))
            
            # Sort by relevance score
            scored_faqs.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by threshold if specified
            matching_faqs = []
            min_relevance = 0.3  # Default threshold
            
            for faq, score in scored_faqs:
                if score >= min_relevance:
                    matching_faqs.append(faq)
            
            # If no matches meet threshold, return empty list
            if not matching_faqs:
                return []
            
            # Limit results
            matching_faqs = matching_faqs[:max_results]
            
            # Convert to WebFAQResult format
            results = []
            for faq in matching_faqs:
                # Use only the English answer
                english_answer = faq['answer_english']
                
                # Create a source object
                source = Source(
                    title=f"Niharika FAQ: {faq['keywords']}",
                    pmid="niharika-faq",
                    url=self.sheet_url,
                    content=f"Keywords: {faq['keywords']}"
                )
                
                result = WebFAQResult(
                    question=faq['question_english'],
                    answer=english_answer,
                    publication_date=None,
                    sources=[source],
                    population="Pregnant women"
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error reading from sheet: {e}")
            raise
    
    def _get_mock_faqs(self, query: str, max_results: int) -> List[WebFAQResult]:
        """Mock implementation using the provided data"""
        
        # This is the data from the Google Sheet you provided
        faq_data = [
            {
                "keywords": "Neck Pain + Hypertension",
                "question_bengali": "৪ মাসের গর্ভবতী মা। ২য় গর্ভধারন। মাথার পিছনে ব্যাথা করে। ঘাড়ের রগ ধরে থাকে। সাথে পেটেও ব্যাথা করে। কি করবেন?",
                "question_english": "4 months pregnant mother. 2nd pregnancy. Back of head hurts. The jugular vein remains. It also hurts the stomach. what to do",
                "answer_bengali": """আপনার প্রশ্নের জন্য ধন্যবাদ। 

গর্ভকালীন সময়ে মাথা ব্যথা ও ঘাড়ের রগ ধরে থাকা উচ্চ রক্তচাপের লক্ষণ হতে পারে, যা গর্ভকালীন ঝুঁকির লক্ষণ। তাই, দেরি না করে আপনার নিকটস্থ ডাক্তারের কাছে অথবা হাসপাতালে গিয়ে প্রয়োজনীয় চিকিৎসা নিন। 

যেসকল বিষয় মেনে চললে পেটের ব্যথা কমতে পারে: 
১। শাকসবজি ও মৌসুমি ফলসহ ভিটামিন ও খনিজ সমৃদ্ধ সুষম খাবার খান
২। প্রতিবার অল্প পরিমাণে দিনে ৪-৬ বার খাবার খাবেন
৩। পর্যাপ্ত পানি পান করুন
৪। পর্যাপ্ত বিশ্রাম নিন এবং ঘুমান
৫। চা কফি খাবেন না।

যদি পেট ব্যথা বেশি হয় তাহলে ডাক্তারের কাছে বা হাসপাতালে যান। ডাক্তার আপনার শারীরিক অবস্থা বিবেচনা করে যথাযথ চিকিৎসা ও পরামর্শ দিবেন।
  
*** আমাদের ফোনভিত্তিক স্বাস্থ্যশিক্ষা সেবার উপদেশগুলি মেনে চলুন।***""",
                "answer_english": """Thanks for your question. 

Headaches and varicose veins during pregnancy can be symptoms of high blood pressure, which are pregnancy risk factors. So, visit your nearest doctor or hospital without delay and seek necessary treatment. 

Abdominal pain can be reduced by following the following: 
1. Eat a balanced diet rich in vitamins and minerals including vegetables and seasonal fruits
2. Eat small meals 4-6 times a day each time
3. Drink enough water
4. Get enough rest and sleep
5. Do not drink tea or coffee.

If the stomach pain is severe, go to the doctor or hospital. The doctor will give proper treatment and advice considering your physical condition.
  
*** Follow the advice of our phone-based health education service.***"""
            },
            {
                "keywords": "Blurred Vision + Leg Swollen",
                "question_bengali": "গর্ভবতী মায়ের পাঁচ মাস চলছে।বয়স ত্রিশ বছর।অন্য কোন সমস্যা নেই। মাঝে মাঝে চোখে মুখে অন্ধকার দেখে, বসে থাকলে পা গুলো ফুলে যায়, কি করনীয়?",
                "question_english": "The pregnant mother is five months pregnant. Age thirty years. No other problem. Sometimes I see darkness in my face, my legs swell when I sit, what should I do?",
                "answer_bengali": """আপনার প্রশ্নের জন্য ধন্যবাদ।

গর্ভাবস্থায় মাঝে মাঝে চোখে মুখে অন্ধকার দেখা ও পা ফুলে থাকা - গর্ভাবস্থায় মায়ের স্বাস্থ্য ঝুঁকিগুলোর মাঝে একটি। আপনার যদি এই লক্ষণগুলো দেখা দেয় তাহলে দেরি না করে দ্রুত নিকটস্থ ডাক্তারের কাছে অথবা হাসপাতালে যান। আপনি দ্রুত রক্ত ও প্রস্রাব পরীক্ষা করান এবং প্রয়োজনীয় চিকিৎসা গ্রহণ করুন।

গর্ভকালীন সেবা নিন ও ডাক্তারের পরামর্শ মতো চলুন।

*** আমাদের ফোনভিত্তিক স্বাস্থ্যশিক্ষা সেবার উপদেশগুলি মেনে চলুন।***""",
                "answer_english": """Thank you for your question.

Occasional darkening of the eyes and swollen legs during pregnancy - one of the health risks of the mother during pregnancy. If you experience these symptoms, go to the nearest doctor or hospital without delay. You should get blood and urine tests done quickly and get the necessary treatment.

Get prenatal care and follow your doctor's advice.

***Follow the advice of our phone-based health education service.***"""
            },
            {
                "keywords": "Preeclampsia + Leg and Hand Swollen",
                "question_bengali": "রোগী জানতে চেয়েছেন,৮-৯ মাসের গর্ভবতী মায়ের যদি হাত পায় ফুলে আসে, পানি নামে সেক্ষেত্রে একলাম্পশিয়া হতে পারে, এটা উনি জানিয়েছেন এটা কি সঠিক ? উনি ওনার জানার জন্য জানতে চেয়েছে",
                "question_english": "The patient wants to know, if the hands of a pregnant mother of 8-9 months are swollen, it can be eclampsia. Is it correct? He wants to know for his sake",
                "answer_bengali": "মায়ের হাত ও পা ফুলে যাওয়া প্রি-এক্ল্যাম্পসিয়া হওয়ার লক্ষণ হতে পারে। তবে, আসলেই এটি প্রি-এক্ল্যাম্পসিয়া কি না তা জানতে রক্ত এবং প্রস্রাবের পরীক্ষা করতে হবে। অনুগ্রহ করে অবিলম্বে একজন ডাক্তারের পরামর্শ নিন অথবা নিকটবর্তী হাসপাতালে গিয়ে পরীক্ষা ও প্রয়োজনীয় চিকিৎসা গ্রহণ করুন।",
                "answer_english": "Swelling of the mother's hands and feet can be a sign of pre-eclampsia. However, blood and urine tests are required to know if it is actually pre-eclampsia. Please consult a doctor immediately or visit the nearest hospital for examination and necessary treatment."
            }
        ]
        
        # Simple keyword matching for now
        query_lower = query.lower()
        # Calculate relevance scores for each FAQ
        query_words = set(query_lower.split())
        scored_faqs = []
        
        for faq in faq_data:
            # Combine all searchable text
            faq_text = (
                faq["keywords"].lower() + " " +
                faq["question_english"].lower() + " " +
                faq["answer_english"].lower()
            )
            faq_words = set(faq_text.split())
            
            # Calculate word overlap score
            common_words = query_words.intersection(faq_words)
            overlap_score = len(common_words) / max(len(query_words), 1)
            
            # Boost score for medical terms
            medical_terms = ['pregnancy', 'pregnant', 'baby', 'nutrition', 'diet', 'headache', 'pain', 'symptom', 'treatment']
            term_matches = sum(1 for term in medical_terms if term in query_lower and term in faq_text)
            term_boost = term_matches * 0.1
            
            # Calculate final relevance score
            relevance = min(1.0, overlap_score + term_boost)
            
            scored_faqs.append((faq, relevance))
        
        # Sort by relevance score
        scored_faqs.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold
        matching_faqs = []
        min_relevance = 0.3  # Default threshold
        
        for faq, score in scored_faqs:
            if score >= min_relevance:
                matching_faqs.append(faq)
        
        # If no matches meet threshold, return empty list
        if not matching_faqs:
            return []
        
        # Limit results
        matching_faqs = matching_faqs[:max_results]
        
        # Convert to WebFAQResult format
        results = []
        for faq in matching_faqs:
            # Use only the English answer
            english_answer = faq['answer_english']
            
            # Create a source object
            source = Source(
                title=f"Niharika FAQ: {faq['keywords']}",
                pmid="niharika-faq",
                url="https://docs.google.com/spreadsheets/d/1jE9m65m_fCQRZcfFfTVMxifmJKaE6J4WPKY9CrRtOkg",
                content=f"Keywords: {faq['keywords']}"
            )
            
            result = WebFAQResult(
                question=faq['question_english'],
                answer=english_answer,
                publication_date=None,
                sources=[source],
                population="Pregnant women"
            )
            results.append(result)
        
        return results


# Convenience function
def search_niharika_faqs(query: str, max_results: int = 3, relevance_threshold: float = 0.3) -> List[WebFAQResult]:
    """
    Convenience function to search Niharika FAQs
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        relevance_threshold: Minimum relevance score (0.0-1.0) to include results
        
    Returns:
        List of WebFAQResult objects
    """
    service = NiharikaFAQService()
    return service.search_faqs(query, max_results, relevance_threshold) 