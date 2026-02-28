🧠 CognAware AI  
Intelligent Cognitive Distortion Detection & Reflective Analytics Platform  

An AI-powered mental wellness assistant designed to transform unstructured human thoughts into structured cognitive insights using Machine Learning and NLP.

Built under the theme: AI for Social Good

🚨 The Core Problem

In today’s high-pressure digital world, individuals frequently experience distorted thinking patterns such as:

- Overgeneralization  
- Catastrophizing  
- Emotional reasoning  
- Black-and-white thinking  

However:

- Most people cannot objectively identify these distortions.
- Self-reflection is subjective and inconsistent.
- Existing wellness apps provide generic motivational advice.
- There is no structured AI system that tracks cognitive distortion trends over time.

The gap is not therapy.  
The gap is early cognitive awareness.

💡 The Proposed Solution

CognAware AI is a full-stack web platform that:

- Accepts user-written thoughts
- Runs ML-based probability classification
- Detects 6 cognitive distortion categories
- Displays top-3 dominant distortions
- Assigns a confidence signal
- Tracks historical distortion trends
- Generates longitudinal cognitive insights

The system does not diagnose mental illness.
It is designed as a structured self-reflection assistant.

⚙️ System Architecture & Workflow

1️⃣ Secure User Authentication
- Registration & Login (Flask-Login)
- Password hashing (Werkzeug)
- User-scoped data isolation

2️⃣ Thought Submission
User inputs a thought via dashboard.

3️⃣ ML Inference Pipeline
- Text → Embedding Model
- Embedding → Classifier
- Probability distribution across 6 distortions
- Top-3 ranking
- Confidence signal generation

4️⃣ Historical Tracking & Trend Engine
- Current vs Previous Average comparison
- Overall distortion intensity
- Pattern movement detection:
  - Increasing
  - Stable
  - Decreasing

📊 Cognitive Distortion Classes

- Overgeneralization  
- Catastrophizing  
- Mind Reading  
- Emotional Reasoning  
- Black & White Thinking  
- Personalization  

Each thought generates a complete probability distribution rather than a binary decision.

🛡️ Security & Data Protection

CognAware AI integrates multiple safeguards:

- 🔐 Password Hashing (No plaintext storage)
- 🔒 Authenticated Route Protection
- 🧍 User-Scoped Data Access Control
- 🧠 ORM-Based Query Protection (SQLAlchemy)
- 🔁 Safe Redirect Validation

🧠 Machine Learning Stack

- Embedding Model (Joblib Artifact)
- Scikit-Learn Classifier (predict_proba based)
- NumPy for vector handling
- Probability normalization layer
- Robust output validation

The system prioritizes:
- Transparency over black-box decisions
- Probability distribution instead of single-label output
- Controlled confidence signaling

💻 Tech Stack

Frontend:
- Jinja Templates
- HTML / CSS

Backend:
- Flask
- SQLAlchemy ORM
- Flask-Login

ML:
- Scikit-Learn
- Joblib
- NumPy

Database:
- SQLite (Prototype)
- PostgreSQL-ready architecture (Planned)

🚀 Core Innovations

- Probability-Based Distortion Transparency
- Longitudinal Cognitive Trend Analysis
- Confidence Signal Classification
- Structured Reflection Over Advice Generation
- Extensible ML Architecture

🔮 Future Scope

- 🚨 Crisis keyword detection & emergency resource integration
- 📊 Interactive timeline visualization (Chart.js)
- 🧠 Transformer-based contextual model upgrade
- 🐳 Dockerized production deployment
- 🛡️ CSRF & advanced production security hardening
- 📱 Mobile journaling app extension

👩‍💻 Team

Developed under AI for Social Good Hackathon  
Team CognAware AI  
- Bushra Ansari  
- Shafia Shaikh
- Saima Ansari
- Laiba Ansari

```bash
git clone https://github.com/imbushraansari/CognAware-AI.git
cd CognAware-AI
