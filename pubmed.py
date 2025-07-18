import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from models import WebFAQResult, Source


class PubMedAPI:
    """Wrapper for NCBI PubMed E-utilities API"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: Optional[str] = None, tool: str = "webfaqmcp"):
        """
        Initialize PubMed API client
        
        Args:
            email: Your email address (recommended by NCBI)
            tool: Tool name for API identification
        """
        self.email = email
        self.tool = tool
        self.session = requests.Session()
    
    def search_and_fetch(self, query: str, max_results: int = 3) -> List[WebFAQResult]:
        """
        Search PubMed and fetch article details
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of WebFAQResult objects
        """
        # First, search for article IDs
        pmids = self._search_articles(query, max_results)
        
        if not pmids:
            return []
        
        # Then fetch article details
        articles = self._fetch_articles(pmids)
        
        return self._format_results(articles)
    
    def _search_articles(self, query: str, max_results: int) -> List[str]:
        """Search for article PMIDs using esearch"""
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "sort": "relevance"
        }
        
        if self.email:
            params["email"] = self.email
        if self.tool:
            params["tool"] = self.tool
            
        try:
            response = self.session.get(f"{self.BASE_URL}/esearch.fcgi", params=params)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            pmids = []
            
            for id_elem in root.findall(".//Id"):
                pmids.append(id_elem.text)
                
            return pmids
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def _fetch_articles(self, pmids: List[str]) -> List[Dict]:
        """Fetch article details using efetch"""
        if not pmids:
            return []
            
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        if self.email:
            params["email"] = self.email
        if self.tool:
            params["tool"] = self.tool
            
        try:
            response = self.session.get(f"{self.BASE_URL}/efetch.fcgi", params=params)
            response.raise_for_status()
            
            return self._parse_fetch_response(response.content)
            
        except Exception as e:
            print(f"Error fetching articles: {e}")
            return []
    
    def _parse_fetch_response(self, xml_content: bytes) -> List[Dict]:
        """Parse XML response from efetch"""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//PMID")
                title_elem = article.find(".//ArticleTitle")
                abstract_elem = article.find(".//AbstractText")
                
                if pmid_elem is not None and title_elem is not None:
                    pmid = pmid_elem.text
                    title = title_elem.text or ""
                    abstract = abstract_elem.text if abstract_elem is not None else ""
                    
                    # Extract additional metadata
                    journal_elem = article.find(".//Journal/Title")
                    journal = journal_elem.text if journal_elem is not None else ""
                    
                    # Extract publication date
                    pub_date_elem = article.find(".//PubDate")
                    publication_date = None
                    if pub_date_elem is not None:
                        year_elem = pub_date_elem.find("Year")
                        month_elem = pub_date_elem.find("Month")
                        if year_elem is not None and year_elem.text is not None:
                            year = year_elem.text
                            month = month_elem.text if month_elem is not None and month_elem.text is not None else "01"
                            publication_date = f"{year}-{month.zfill(2)}-01"
                    
                    # Determine target population
                    population = self._determine_population(title, abstract or "")
                    
                    articles.append({
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "publication_date": publication_date,
                        "population": population
                    })
                    
        except Exception as e:
            print(f"Error parsing XML: {e}")
            
        return articles
    

    
    def _determine_population(self, title: str, abstract: str) -> str:
        """Determine target population based on title and abstract"""
        text_lower = (title + " " + abstract).lower()
        
        if any(word in text_lower for word in ["pregnant", "pregnancy", "gestational", "maternal", "obstetric"]):
            return "Pregnant women"
        elif any(word in text_lower for word in ["postpartum", "postnatal", "breastfeeding", "lactation"]):
            return "Postpartum women"
        elif any(word in text_lower for word in ["cardiac", "cardiovascular", "heart", "coronary"]):
            return "Cardiac patients"
        elif any(word in text_lower for word in ["pediatric", "child", "infant", "neonatal"]):
            return "Pediatric patients"
        else:
            return "General population"
    
    def _format_results(self, articles: List[Dict]) -> List[WebFAQResult]:
        """Format articles as WebFAQResult objects"""
        results = []
        
        for article in articles:
            # Create snippet from abstract (first 300 characters)
            abstract = article.get("abstract", "")
            snippet = abstract[:300] + "..." if len(abstract) > 300 else abstract
            
            # Create PubMed URL
            pmid = article.get("pmid", "")
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # Create sources list for this single article
            sources = [Source(
                title=article.get("title", ""),
                pmid=pmid,
                url=url
            )]
            
            result = WebFAQResult(
                question=article.get("title", ""),
                answer=snippet,
                publication_date=article.get("publication_date"),
                sources=sources,
                population=article.get("population")
            )
            results.append(result)
            
        return results


# Convenience function for direct usage
def search_and_fetch(query: str, max_results: int = 3, email: Optional[str] = None) -> List[WebFAQResult]:
    """
    Convenience function to search PubMed and fetch results
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        email: Your email address (recommended by NCBI)
        
    Returns:
        List of WebFAQResult objects
    """
    api = PubMedAPI(email=email)
    return api.search_and_fetch(query, max_results) 