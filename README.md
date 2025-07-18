# AshAI - AI Telehealth Agent

> **Asha** (आशा) means "hope" in Hindi and refers to community health workers who support mothers and families. AshAI combines this concept with AI to create an intelligent telehealth agent for maternal and family health.

AshAI is a comprehensive telehealth platform that provides evidence-based medical information through multiple AI-powered endpoints. Built on PubMed research, it offers personalized health guidance with cultural sensitivity and quality evaluation.

## 🌟 Features

- **🤖 AI Telehealth Agent** - Conversational health assistant with cultural sensitivity
- **📚 Evidence-Based Responses** - All information sourced from PubMed medical literature
- **🌏 Multi-Cultural Support** - Hindi language support and cultural awareness
- **📊 Quality Evaluation** - Automated assessment of response quality
- **🔍 Medical FAQ Search** - Structured Q&A from medical research
- **📖 Raw Source Access** - Direct access to PubMed abstracts and sources
- **🖥️ Interactive Web UI** - Easy-to-use interface for testing all endpoints

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd AshAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The server will start at `http://localhost:8000`

### Web Interface

Visit `http://localhost:8000/` for an interactive web UI that allows you to:
- **Select API endpoints** from a dropdown menu
- **Auto-fill example requests** when switching endpoints
- **Send requests** and view formatted responses
- **Test all endpoints** without using curl or other tools

### API Documentation

Once running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## 📡 API Endpoints

### 1. `/ashai` - AI Telehealth Agent

**POST** `/ashai`

A higher-level telehealth agent that responds to user input based on PubMed research and patient profile information. The agent **self-evaluates** its responses and automatically retries with improved instructions if the evaluation score is low (below 7.0/10).

**Request Body:**
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
  "response": "Hello Ann! I'm here to help you with your pregnancy-related questions...",
  "sources": [
    {
      "title": "Pregnancy Nutrition Guidelines",
      "pmid": "12345678",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ],
  "faqs": [...],
  "evaluation": {
    "medical_accuracy": 85.0,
    "precision": 78.0,
    "language_clarity": 82.0,
    "empathy_score": 88.0,
    "overall_score": 83.5,
    "feedback": "Good medical accuracy and empathy, could improve precision..."
  }
}
```

**Features:**
- **Self-Evaluation**: Automatically evaluates responses using the same criteria as `/evaluator`
- **Auto-Retry**: If score < 7.0, retries with evaluation feedback as system message
- **Cultural Sensitivity**: Supports multiple languages (Hindi, English)
- **Evidence-Based**: All responses backed by PubMed research
- **Personalized**: Uses patient profile for tailored responses

**Example:**
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

### 2. `/evaluator` - Response Quality Assessment

Evaluates telehealth responses based on multiple criteria.

**Request:**
```bash
curl -X POST http://localhost:8000/evaluator \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Hello Ann! I am here to help you with your pregnancy-related questions...",
    "messages": [
      {"role": "user", "content": "hello, i am pregnant"},
      {"role": "user", "content": "can i eat banana?"}
    ],
    "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
  }'
```

**Response:**
```json
{
  "medical_accuracy": 85.0,
  "precision": 78.0,
  "language_clarity": 82.0,
  "empathy_score": 88.0,
  "overall_score": 83.7,
  "feedback": "Excellent response! This is a high-quality telehealth interaction..."
}
```

**Evaluation Criteria:**
- **Medical Accuracy (40%)** - Evidence-based information and safety warnings
- **Precision (25%)** - Addresses specific patient concerns
- **Language Clarity (20%)** - Accessible language without medical jargon
- **Empathy Score (15%)** - Personalization and cultural sensitivity

### 3. `/faq` - Medical FAQ Search

Synthesizes multiple PubMed sources into structured Q&A pairs.

**Request:**
```bash
curl -X POST http://localhost:8000/faq \
  -H "Content-Type: application/json" \
  -d '{"query": "pregnancy nutrition guidelines", "max_results": 3, "snippet_length": 500}'
```

**Response:**
```json
{
  "results": [
    {
      "question": "What is pregnancy nutrition?",
      "answer": "Based on medical research: Nutritional concerns in pregnancy are gaining increasing importance...",
      "sources": [
        {
          "title": "Nutrition during pregnancy",
          "pmid": "18760225",
          "url": "https://pubmed.ncbi.nlm.nih.gov/18760225/"
        }
      ],
      "publication_date": "2008-Sep-01",
      "population": "Pregnant women"
    }
  ],
  "query": "pregnancy nutrition guidelines",
  "total_results": 1
}
```

### 4. `/faq/niharika` - Niharika FAQ (Bengali/English)

Searches curated Google Sheet containing Bengali/English medical Q&A pairs specifically for pregnancy and maternal health.

**Request:**
```bash
curl -X POST http://localhost:8000/faq/niharika \
  -H "Content-Type: application/json" \
  -d '{"query": "neck pain headache pregnancy", "max_results": 2}'
```

**Response:**
```json
{
  "results": [
    {
      "question": "4 months pregnant mother. 2nd pregnancy. Back of head hurts. The jugular vein remains. It also hurts the stomach. what to do",
      "answer": "Thanks for your question. Headaches and varicose veins during pregnancy can be symptoms of high blood pressure, which are pregnancy risk factors. So, visit your nearest doctor or hospital without delay and seek necessary treatment. Abdominal pain can be reduced by following the following: 1. Eat a balanced diet rich in vitamins and minerals including vegetables and seasonal fruits 2. Eat small meals 4-6 times a day each time 3. Drink enough water 4. Get enough rest and sleep 5. Do not drink tea or coffee. If the stomach pain is severe, go to the doctor or hospital. The doctor will give proper treatment and advice considering your physical condition. *** Follow the advice of our phone-based health education service.***",
      "sources": [
        {
          "title": "Niharika FAQ: Neck Pain + Hypertension",
          "pmid": "niharika-faq",
          "url": "https://docs.google.com/spreadsheets/d/1jE9m65m_fCQRZcfFfTVMxifmJKaE6J4WPKY9CrRtOkg/edit?usp=sharing"
        }
      ],
      "population": "Pregnant women"
    }
  ],
  "query": "neck pain headache pregnancy",
  "total_results": 1
}
```

**Features:**
- **English Output**: Returns English translations of medical advice from Bengali healthcare experts
- **Pregnancy-Focused**: Specialized content for maternal health from Bengali medical context
- **Real-time Data**: Reads directly from live Google Sheet
- **Cultural Sensitivity**: Culturally appropriate medical advice translated to English
- **Multilingual Search**: Searches across keywords, Bengali questions, and English questions

**Example Queries:**
- `"neck pain headache pregnancy"` - Pregnancy-related pain management
- `"blurred vision swollen legs"` - Pre-eclampsia symptoms
- `"eclampsia seizures"` - Serious pregnancy complications
- `"edema leg swelling"` - Pregnancy swelling concerns

### 5. `/sources` - Raw PubMed Sources

Returns raw snippets from individual PubMed articles.

**Request:**
```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{"query": "postpartum depression symptoms", "max_results": 2, "snippet_length": 800}'
```

**Response:**
```json
{
  "results": [
    {
      "question": "Postpartum depression: A systematic review",
      "answer": "Postpartum depression affects approximately 10-15% of women...",
      "sources": [...],
      "publication_date": "2020-01-01",
      "population": "Postpartum women"
    }
  ],
  "query": "postpartum depression symptoms",
  "total_results": 1
}
```

### 6. `/turn` - Turn.io WhatsApp Integration

Integrates with [Turn.io](https://whatsapp.turn.io/docs/api/context) for WhatsApp chat-based telehealth consultations.

**Handshake Request:**
```bash
curl -X POST "http://localhost:8000/turn?handshake=true"
```

**Response:**
```json
{
  "version": "1.0.0-alpha",
  "capabilities": {
    "actions": true,
    "suggested_responses": true,
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
```

**Context Retrieval Request:**
```bash
curl -X POST http://localhost:8000/turn \
  -H "Content-Type: application/json" \
  -d '{
    "chat": {
      "owner": "+1234567890",
      "state": "active"
    },
    "messages": [
      {
        "direction": "inbound",
        "text": "hello, i have a headache",
        "timestamp": "2024-01-01T12:00:00Z"
      },
      {
        "direction": "outbound",
        "text": "Hello! I can help. Can you tell me more?",
        "timestamp": "2024-01-01T12:01:00Z"
      },
      {
        "direction": "inbound", 
        "text": "it has been going on for 2 days",
        "timestamp": "2024-01-01T12:02:00Z"
      }
    ]
  }'
```

**Response:**
```json
{
  "version": "1.0.0-alpha",
  "context_objects": {
    "patient_info": {
      "Phone Number": "+1234567890",
      "Chat State": "active",
      "Response Quality": "8.5/10"
    },
    "medical_context": [
      "**Medical Sources**: 3 PubMed articles",
      "**Response Length**: 245 characters", 
      "**FAQs Used**: 2 medical FAQs"
    ]
  },
  "actions": {},
  "suggested_responses": [
    {
      "type": "TEXT",
      "title": "Medical Response",
      "body": "Based on medical research, headaches lasting more than 24 hours may require medical attention...",
      "confidence": 0.9
    },
    {
      "type": "TEXT",
      "title": "Medical Disclaimer", 
      "body": "This information is for educational purposes only. Please consult with your healthcare provider for personalized medical advice.",
      "confidence": 0.7
    }
  ]
}
```

**Features:**
- **WhatsApp Integration**: Seamless integration with Turn.io WhatsApp platform
- **Auto-Response**: Converts chat messages to medical consultations
- **Context Display**: Shows patient info and medical context in Turn.io UI
- **Suggested Responses**: Provides multiple response options for agents
- **Self-Evaluation**: Includes response quality scoring

## 🧪 Testing

### Web Interface Testing
The easiest way to test all endpoints is through the web interface:

1. **Start the server**: `python main.py`
2. **Open your browser**: Visit `http://localhost:8000/`
3. **Select an endpoint** from the dropdown
4. **Review the auto-filled example** (or modify it)
5. **Click "Send Request"** to test the API
6. **View results** in the formatted display area

The web UI automatically provides relevant examples for each endpoint:
- **`/ashai`**: Pregnancy nutrition question with Hindi-speaking patient
- **`/evaluator`**: Sample response evaluation with context
- **`/faq`**: Pregnancy nutrition guidelines search
- **`/sources`**: Postpartum depression symptoms search

### Command Line Testing

#### Run All Tests
```bash
python test_webfaq.py
```

#### Test New Endpoints
```bash
python test_telehealth.py
```

#### Quick Example
```bash
python example.py
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
```bash
export PUBMED_EMAIL="your-email@example.com"
export PUBMED_TOOL="ashai-telehealth"
```

## 🏗️ Architecture

### Core Components

1. **Telehealth Agent** (`telehealth.py`)
   - Conversation processing
   - Medical query extraction
   - Personalized response generation
   - Cultural sensitivity

2. **Evaluation Agent** (`evaluator.py`)
   - Multi-criteria assessment
   - Quality scoring
   - Feedback generation

3. **PubMed Integration** (`pubmed.py`)
   - NCBI E-utilities API
   - Article search and retrieval
   - Metadata extraction

4. **API Layer** (`main.py`)
   - FastAPI endpoints
   - Request/response handling
   - Error management

5. **Web Interface** (`templates/index.html`)
   - Interactive UI for testing endpoints
   - Auto-filling examples
   - Real-time API testing

### Data Models

- **TelehealthRequest/Response** - Chat-based interactions
- **EvaluationRequest/Response** - Quality assessment
- **FAQQuery/Response** - Medical Q&A
- **Source** - PubMed article metadata

## 🌏 Cultural Features

### Hindi Language Support
- Automatic Hindi text inclusion for Indian patients
- Cultural context awareness
- Appropriate greetings and phrases

### Cultural Sensitivity
- Location-aware responses (e.g., Kerala, India)
- Regional health considerations
- Traditional medicine awareness

## 🔒 Medical Safety

### Built-in Safeguards
- **Educational Purpose Disclaimers** - All responses include appropriate warnings
- **Healthcare Provider Recommendations** - Always suggest consulting professionals
- **Evidence-Based Information** - All responses backed by PubMed research
- **No Personal Health Information** - No PHI processing or storage

### Quality Assurance
- **Automated Evaluation** - Every response can be quality-assessed
- **Medical Accuracy Scoring** - Evidence-based information validation
- **Safety Warning Detection** - Ensures appropriate disclaimers

## 📊 Use Cases

### For Healthcare Providers
- **Patient Education** - Evidence-based information for patients
- **Quality Assurance** - Evaluate response quality
- **Research Support** - Access to medical literature

### For Patients
- **Health Information** - Reliable medical guidance
- **Cultural Support** - Language and cultural sensitivity
- **Education** - Understanding health conditions

### For Developers
- **API Integration** - Build healthcare applications
- **Custom Evaluation** - Implement quality assessment
- **Research Tools** - Medical literature access

## 🛡️ Security & Compliance

- **No PHI Storage** - No personal health information stored
- **Public Data Only** - Uses only publicly available PubMed data
- **Educational Use** - Designed for educational purposes
- **Professional Guidance** - Always recommends consulting healthcare providers

## 📈 Roadmap

- [ ] **Voice Interface** - Speech-to-text and text-to-speech
- [ ] **Multi-Language Support** - Additional Indian languages
- [ ] **Image Analysis** - Medical image interpretation
- [ ] **Symptom Assessment** - Structured symptom evaluation
- [ ] **Medication Safety** - Drug interaction checking
- [ ] **Emergency Detection** - Critical symptom identification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📞 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the test cases for usage examples

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ for maternal and family health**

*AshAI - Bringing hope and AI together for better health outcomes* 