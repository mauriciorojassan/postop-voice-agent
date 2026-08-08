# Post-Operative Voice Follow-Up Agent (Colombian Spanish)

## 15-Minute Reproducible Setup

1. **Clone & Virtualenv**:
   ```bash
   git clone <repo-url> postop-voice-agent
   cd postop-voice-agent
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Add your Groq API key to .env
   ```

4. **Run Application**:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

5. **Verify**:
   ```bash
   curl -s http://localhost:8000/health
   ```
