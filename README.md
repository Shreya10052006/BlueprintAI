# BlueprintAI - AI Project Planner for Students

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Educational-yellow.svg)]()

> **⚠️ IMPORTANT: This project does NOT generate code.**  
> It is a planning mentor that helps students understand and explain their projects.

## 🎓 What is BlueprintAI?

BlueprintAI is an AI-powered project planning assistant designed specifically for college students. It transforms vague project ideas into clear, explainable, presentation-ready blueprints.

### ✅ What This System Does
- Expands vague ideas into structured problem statements
- Evaluates project feasibility honestly
- Explains feature trade-offs (time vs complexity)
- Generates system flows and architecture diagrams
- Recommends tech stacks with justifications
- Prepares students for viva questions
- Creates compelling project pitches

### ❌ What This System Does NOT Do
- Generate programming code
- Create SQL queries
- Write HTML, CSS, or JavaScript
- Build applications automatically

**This is intentional.** Understanding your project deeply before coding leads to better results and confident viva presentations!

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **Idea Expansion** | Converts one-liner ideas into full problem statements |
| **Feasibility Check** | Honest evaluation of whether your idea is buildable |
| **Feature Tradeoffs** | Explains what each feature will cost in time/complexity |
| **System Flow** | Generates step-by-step user journeys |
| **Tech Stack** | Recommends technologies with student-friendly explanations |
| **Viva Prep** | Anticipates reviewer questions with suggested answers |
| **Pitch Generator** | Creates 30-second and 1-minute pitches |
| **Flowcharts** | Visual diagrams for user flows and architecture |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.9+) |
| **Frontend** | Vanilla HTML/CSS/JavaScript |
| **AI Providers** | Gemini 2.5 Flash, Groq LLaMA 3.1, DeepSeek V3 |
| **Persistence** | Firebase Firestore (optional), localStorage |

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- Node.js (optional, for development server)

### Backend Setup

```bash
# Clone the repository
cd STUDENTPLANNER

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your API keys
```

### Environment Variables

Create a `.env` file in the `backend` folder:

```env
# Required: At least one LLM API key
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Firebase for persistence
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
```

**Where to get API keys (all free):**
- **Gemini**: https://aistudio.google.com/app/apikey
- **Groq**: https://console.groq.com/keys
- **OpenRouter**: https://openrouter.ai/keys

## 🏃 Running Locally

### Start the Backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start the Frontend

```bash
cd frontend
python -m http.server 8080
```

### Access the Application
- **Frontend**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
STUDENTPLANNER/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic & LLM calls
│   │   ├── schemas/          # Request/response models
│   │   └── utils/            # Helper functions
│   ├── requirements.txt
│   └── .env                  # Environment variables (create this)
├── frontend/
│   ├── index.html            # Home page
│   ├── dashboard.html        # Blueprint dashboard
│   ├── chat.html             # Interactive mentor chat
│   ├── app.js                # Main JavaScript logic
│   ├── flowchart.js          # Diagram renderer
│   └── styles.css            # Application styles
└── README.md
```

## 🔒 Security Notes

- All API keys are loaded from environment variables
- No secrets are hardcoded in the codebase
- Stack traces are never exposed to users
- Code generation requests are actively blocked

## 🚀 Deployment

### Production Checklist
- [ ] Set proper CORS origins (replace `*` with your domain)
- [ ] Ensure all API keys are configured
- [ ] Set up proper logging infrastructure
- [ ] Configure HTTPS

### Recommended Deployment Platforms
- **Backend**: Railway, Render, or any Python hosting
- **Frontend**: Vercel, Netlify, or any static hosting

## 📝 API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/idea/understand` | POST | Expand a raw idea |
| `/api/idea/evaluate` | POST | Evaluate feasibility |
| `/api/planning/tradeoffs` | POST | Analyze feature costs |
| `/api/planning/flow` | POST | Generate system flow |
| `/api/planning/tech-stack` | POST | Recommend technologies |
| `/api/planning/viva-guide` | POST | Generate viva prep |
| `/api/planning/pitch` | POST | Create project pitch |
| `/api/mentor/chat` | POST | Interactive mentor chat |

## 🤝 Contributing

This project is designed for educational purposes. Contributions that maintain its planning-focused nature are welcome.

## 📄 License

This project is for educational use. Please respect the design decision to focus on planning, not code generation.

---

**Made with ❤️ for students who want to understand their projects, not just build them.**
