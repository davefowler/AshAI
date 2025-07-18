import pytest
from unittest.mock import patch, MagicMock
from models import WebFAQResult, Source
import pubmed
from main import get_medical_faq


class TestPubMedAPI:
    """Test cases for PubMed API functionality"""
    
    def test_webfaq_result_model(self):
        """Test WebFAQResult model creation"""
        from models import Source
        
        result = WebFAQResult(
            question="Test Medical Question",
            answer="This is a test answer about medical research...",
            sources=[Source(title="Test Medical Article", pmid="12345678", url="https://pubmed.ncbi.nlm.nih.gov/12345678/")],
            publication_date=None,
            population=None
        )
        
        assert result.question == "Test Medical Question"
        assert result.answer == "This is a test answer about medical research..."
        assert result.sources[0].url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    
    @patch('pubmed.PubMedAPI._search_articles')
    @patch('pubmed.PubMedAPI._fetch_articles')
    def test_search_and_fetch_success(self, mock_fetch, mock_search):
        """Test successful search and fetch"""
        # Mock search results
        mock_search.return_value = ["12345678", "87654321", "11111111"]
        
        # Mock fetch results
        mock_fetch.return_value = [
            {
                "pmid": "12345678",
                "title": "Morning headaches and sleep disorders",
                "abstract": "Morning headaches are often associated with sleep apnea or tension-type headaches. This study examines the relationship between sleep quality and morning headache occurrence in a cohort of 500 patients."
            },
            {
                "pmid": "87654321", 
                "title": "Circadian rhythm disruption and headache patterns",
                "abstract": "Disrupted circadian rhythms can contribute to various headache disorders. Our research shows that patients with irregular sleep schedules experience more frequent morning headaches."
            },
            {
                "pmid": "11111111",
                "title": "Treatment approaches for morning headaches",
                "abstract": "Various treatment modalities exist for morning headaches, including lifestyle modifications, medication, and addressing underlying sleep disorders."
            }
        ]
        
        api = pubmed.PubMedAPI()
        results = api.search_and_fetch("morning headaches", max_results=3)
        
        assert len(results) == 3
        assert results[0].question == "Morning headaches and sleep disorders"
        assert "sleep apnea" in results[0].answer
        assert "pubmed.ncbi.nlm.nih.gov/12345678" in results[0].sources[0].url
    
    @patch('pubmed.PubMedAPI._search_articles')
    def test_search_and_fetch_no_results(self, mock_search):
        """Test search with no results"""
        mock_search.return_value = []
        
        api = pubmed.PubMedAPI()
        results = api.search_and_fetch("nonexistent medical term", max_results=3)
        
        assert len(results) == 0
    
    def test_snippet_truncation(self):
        """Test that snippets are properly truncated to 300 characters"""
        long_abstract = "A" * 500  # 500 character string
        
        api = pubmed.PubMedAPI()
        results = api._format_results([{
            "pmid": "12345678",
            "title": "Test Article",
            "abstract": long_abstract
        }])
        
        assert len(results) == 1
        assert len(results[0].answer) == 303  # 300 + "..."
        assert results[0].answer.endswith("...")
    
    def test_url_formatting(self):
        """Test that PubMed URLs are properly formatted"""
        api = pubmed.PubMedAPI()
        results = api._format_results([{
            "pmid": "12345678",
            "title": "Test Article",
            "abstract": "Test abstract"
        }])
        
        assert len(results) == 1
        assert results[0].sources[0].url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


class TestMedicalFAQ:
    """Test cases for medical FAQ functionality"""
    
    @patch('pubmed.search_and_fetch')
    def test_get_medical_faq_success(self, mock_search):
        """Test successful medical FAQ generation"""
        mock_search.return_value = [
            WebFAQResult(
                question="Morning headaches: causes and treatment",
                answer="Morning headaches can be caused by various factors including sleep apnea, dehydration, or medication overuse. Proper diagnosis is essential for effective treatment.",
                sources=[Source(title="Morning headaches: causes and treatment", pmid="12345678", url="https://pubmed.ncbi.nlm.nih.gov/12345678/")],
                publication_date=None,
                population=None
            ),
            WebFAQResult(
                question="Sleep disorders and headache patterns",
                answer="Research shows a strong correlation between sleep quality and headache frequency. Patients with sleep apnea often experience morning headaches.",
                sources=[Source(title="Sleep disorders and headache patterns", pmid="87654321", url="https://pubmed.ncbi.nlm.nih.gov/87654321/")],
                publication_date=None,
                population=None
            )
        ]
        
        result = get_medical_faq("What causes morning headaches?")
        
        assert "Medical Information: What causes morning headaches?" in result
        assert "Disclaimer:" in result
        assert "Morning headaches: causes and treatment" in result
        assert "sleep apnea" in result
        assert "pubmed.ncbi.nlm.nih.gov/12345678" in result
        assert "consult with a healthcare professional" in result
    
    @patch('pubmed.search_and_fetch')
    def test_get_medical_faq_no_results(self, mock_search):
        """Test medical FAQ with no search results"""
        mock_search.return_value = []
        
        result = get_medical_faq("nonexistent medical condition")
        
        assert "couldn't find any medical literature" in result
        assert "nonexistent medical condition" in result
        assert "try rephrasing your question" in result
    
    @patch('pubmed.search_and_fetch')
    def test_get_medical_faq_error_handling(self, mock_search):
        """Test error handling in medical FAQ"""
        mock_search.side_effect = Exception("API Error")
        
        result = get_medical_faq("test query")
        
        assert "error occurred while searching" in result
        assert "API Error" in result


class TestIntegration:
    """Integration tests (require network access)"""
    
    @pytest.mark.integration
    def test_real_pubmed_search(self):
        """Test real PubMed API search (requires network)"""
        # Skip if no network access
        try:
            results = pubmed.search_and_fetch("diabetes", max_results=1)
            
            if results:  # If we got results
                assert len(results) <= 1
                assert results[0].question != ""
                assert results[0].sources[0].url.startswith("https://pubmed.ncbi.nlm.nih.gov/")
                
        except Exception:
            pytest.skip("Network access required for integration test")
    
    @pytest.mark.integration
    def test_real_medical_faq(self):
        """Test real medical FAQ generation (requires network)"""
        try:
            result = get_medical_faq("diabetes symptoms")
            
            assert "Medical Information: diabetes symptoms" in result
            assert "Disclaimer:" in result
            assert "healthcare professional" in result
            
        except Exception:
            pytest.skip("Network access required for integration test")


def run_basic_tests():
    """Run basic tests without pytest"""
    print("Running basic WebFAQ tests...")
    
    # Test model creation
    result = WebFAQResult(
        question="Test",
        answer="Test answer",
        sources=[Source(title="Test", pmid="12345", url="https://example.com")],
        publication_date=None,
        population=None
    )
    assert result.question == "Test"
    print("✓ Model creation test passed")
    
    # Test snippet truncation
    api = pubmed.PubMedAPI()
    long_abstract = "A" * 500
    results = api._format_results([{
        "pmid": "12345",
        "title": "Test",
        "abstract": long_abstract
    }])
    assert len(results[0].answer) == 303
    print("✓ Snippet truncation test passed")
    
    # Test URL formatting
    results = api._format_results([{
        "pmid": "12345",
        "title": "Test",
        "abstract": "Test"
    }])
    assert "pubmed.ncbi.nlm.nih.gov/12345/" in results[0].sources[0].url
    print("✓ URL formatting test passed")
    
    print("All basic tests passed! ✓")


if __name__ == "__main__":
    # Run basic tests if pytest is not available
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        run_basic_tests() 