# WebFAQMCP: Medical FAQ Tool using PubMed

A Python tool that searches PubMed for medical literature and returns structured FAQ-style answers to health questions. Perfect for integration with AI assistants, chatbots, or standalone medical information systems.

## 🔍 What It Does

- Takes natural language medical questions (e.g., "What causes morning headaches?")
- Searches the **NCBI PubMed database** using E-utilities API
- Returns structured results with:
  - Article titles
  - Abstract snippets (first 300 characters)
  - Direct PubMed URLs
  - Medical disclaimers

## 🧠 Tech Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI |
| Data Validation | Pydantic |
| Medical Data | PubMed E-utilities |
| HTTP Client | Requests |
| Language | Python 3.10+ |

## 📁 Project Structure

```
pubMedFAQ/
├── main.py                  # FastAPI entrypoint
├── tools.py                 # Core tool logic
├── models.py                # Pydantic data models
├── pubmed.py                # PubMed API interaction
├── test_webfaq.py           # Tests
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd pubMedFAQ

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the API Server

```bash
./run.sh
```

The API will be available at `http://localhost:8000`

### 3. Test the API

**FAQ Endpoint (structured results):**
```bash
curl -X POST http://localhost:8000/faq \
  -H "Content-Type: application/json" \
  -d '{"query": "pregnancy morning sickness"}'
```

**Sources Endpoint (raw snippets):**
```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{"query": "postpartum depression symptoms"}'
```

**With custom result count:**
```bash
curl -X POST http://localhost:8000/faq \
  -H "Content-Type: application/json" \
  -d '{"query": "cardiac rehabilitation", "max_results": 5}'
```

**Telehealth Agent Endpoint:**
```bash
curl -X POST http://localhost:8000/ashai \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "hello, i am pregnant"},
      {"role": "user", "content": "can i eat banana?"}
    ],
    "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
  }'
```

**Evaluation Endpoint:**
```bash
curl -X POST http://localhost:8000/evaluator \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Hello Ann! I am here to help you with your pregnancy-related questions. Regarding your question about food and nutrition during pregnancy: Based on medical research, bananas are generally safe and nutritious during pregnancy...",
    "context": "Patient asked about eating bananas during pregnancy",
    "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
  }'
```

## 📖 Usage Examples

### API Endpoints

**POST** `/faq` - Medical FAQ Search

```json
{
  "query": "What are the symptoms of diabetes?"
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "Type 2 diabetes mellitus: clinical manifestations and diagnosis",
      "snippet": "Type 2 diabetes mellitus is characterized by hyperglycemia, insulin resistance, and relative insulin deficiency. Common symptoms include polyuria, polydipsia, polyphagia, weight loss, and fatigue...",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ],
  "query": "What are the symptoms of diabetes?",
  "total_results": 3
}
```

### Python Usage

```python
from pubmed import search_and_fetch

# Search PubMed directly
results = search_and_fetch("morning headaches", max_results=3)

for result in results:
    print(f"Title: {result.title}")
    print(f"Snippet: {result.snippet}")
    print(f"URL: {result.url}")
    print("-" * 50)
```

### Jupyter Notebook Usage

```python
import pubmed

# Quick search
results = pubmed.search_and_fetch("sleep apnea treatment")

# Display results
for i, result in enumerate(results, 1):
    print(f"{i}. {result.question}")
    print(f"   {result.answer}")
    print(f"   🔗 {result.sources[0].url}\n")
```

**POST** `/ashai` - AI Telehealth Agent

```json
{
  "messages": [
    {"role": "user", "content": "hello, i am pregnant"},
    {"role": "user", "content": "can i eat banana?"}
  ],
  "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
}
```

**Response:**
```json
{
  "response": "Hello Ann! I'm here to help you with your pregnancy-related questions. Regarding your question about food and nutrition during pregnancy: Based on medical research, bananas are generally safe and nutritious during pregnancy...",
  "sources": [
    {
      "title": "Nutrition during pregnancy",
      "pmid": "12345678",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ],
  "faqs": [
    {
      "question": "What foods are safe during pregnancy?",
      "answer": "Based on medical research...",
      "sources": [...],
      "publication_date": "2023-01-01",
      "population": "Pregnant women"
    }
  ],
  "evaluation": null
}
```

**POST** `/evaluator` - Response Evaluation

```json
{
  "response": "Hello Ann! I am here to help you with your pregnancy-related questions...",
  "context": "Patient asked about eating bananas during pregnancy",
  "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
}
```

**Response:**
```json
{
  "medical_accuracy": 85.0,
  "precision": 78.0,
  "language_clarity": 82.0,
  "empathy_score": 88.0,
  "overall_score": 83.7,
  "feedback": "Excellent response! This is a high-quality telehealth interaction. Excellent medical accuracy with appropriate safety warnings..."
}
```

## 🔧 Configuration

### Email Configuration (Recommended)

NCBI recommends providing your email when using their APIs:

```python
from pubmed import PubMedAPI

api = PubMedAPI(email="your-email@example.com")
results = api.search_and_fetch("your query")
```

### Environment Variables

You can set these environment variables:

```bash
export PUBMED_EMAIL="your-email@example.com"
export PUBMED_TOOL="your-tool-name"
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest test_webfaq.py -v
```

Or run individual tests:

```bash
python test_webfaq.py
```

## 📊 API Documentation

Once the server is running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## 🔒 Medical Disclaimer

**Important:** This tool provides information for educational purposes only and should not replace professional medical advice. All responses include appropriate medical disclaimers.

The tool retrieves information from:
- **PubMed**: Public domain medical literature from NCBI
- **No PHI**: No personal health information is processed
- **Peer-reviewed**: Only accesses peer-reviewed medical literature

## 🛡️ Rate Limiting & Best Practices

- **NCBI Guidelines**: Respects NCBI's usage guidelines
- **Rate Limiting**: Built-in request throttling
- **Caching**: Consider implementing caching for production use
- **Error Handling**: Graceful fallbacks for API failures

## 🔧 Development

### Adding New Features

1. **New search filters**: Extend `PubMedAPI._search_articles()`
2. **Response formatting**: Modify `_format_results()`
3. **Additional metadata**: Update `WebFAQResult` model

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📋 Dependencies

- `fastapi>=0.104.1`: Web framework
- `uvicorn>=0.24.0`: ASGI server
- `requests>=2.31.0`: HTTP client
- `pydantic>=2.5.0`: Data validation
- `python-multipart>=0.0.6`: Form data parsing
- `pytest>=7.4.0`: Testing framework

## 🚀 Deployment

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

- Use environment variables for configuration
- Implement proper logging
- Add rate limiting middleware
- Consider database caching for frequent queries
- Set up monitoring and health checks

## 📈 Roadmap

- [ ] Add metadata fields (publication date, authors, journal)
- [ ] Implement caching layer
- [ ] Add batch query support
- [ ] Integration with other medical databases
- [ ] Voice interface support
- [ ] Full-text search capabilities

## 📞 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the API documentation
- Review the test cases for usage examples

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ for the medical AI community** 