# NextHire – Intelligent Mock Interview System

NextHire is an intelligent mock interview platform featuring a **JARVIS-style voice assistant**, automated resume parsing, concept-based answer evaluation, and isolated session feedback storage.

---

## Stage 1 – Foundation + JARVIS Core

### Phase 1: Project Architecture and JARVIS Interface (Completed)
- **Directory Structure**: Complete modular setup for backend (Flask), frontend (HTML5/CSS3/Vanilla JS), database (MySQL 8.x schema), tests, and uploads.
- **JARVIS Interface**: Futuristic black/blue environment, dark gradient background, multi-tiered kinetic HUD arc reactor visual with rotating outer/middle/inner rings, canvas audio waveform visualizer, and 5 interactive assistant states:
  - `IDLE` (Gentle pulse, awaiting candidate prompt)
  - `LISTENING` (Teal-cyan energetic resonance with microphone capture)
  - `THINKING` (Rapid amber/cyan gyroscopic evaluation)
  - `SPEAKING` (Electric blue speech synthesis vocalizing questions)
  - `PROCESSING` (Quantum flux and concept score aggregation)
- **Interview Layout**:
  - Live question display with category, difficulty, and TTS audio playback.
  - Interactive answer interaction area with real-time speech-to-text transcript streaming, audio equalizer bars, and fallback manual editor.
  - Action deck: Voice Mic toggle, Skip Question, Repeat Question, Submit & Next, and End Session.
  - HUD state switcher toolbar for instant testing during project demonstrations.
- **Complete Page Stubs**:
  - `index.html` (Landing & Features)
  - `login.html` & `register.html` (Candidate Authentication)
  - `dashboard.html` (Candidate Portal & Quick Actions)
  - `interview.html` (Core JARVIS Live Interview)
  - `feedback.html` (Isolated Session Feedback & Concept Breakdown)
  - `history.html` (Session Archive)

---

## Directory Structure

```text
NextHire/
│
├── backend/
│   ├── app.py              # Flask Application Factory & Route Dispatcher
│   ├── config.py           # Environment & App Configuration
│   ├── database.py         # PyMySQL Connection & Health Utilities
│   ├── requirements.txt    # Python Dependencies
│   └── routes/
│       ├── __init__.py
│       └── api.py          # Core Health & JARVIS Status APIs
│
├── frontend/
│   ├── index.html          # Landing Page
│   ├── login.html          # Authentication - Login
│   ├── register.html       # Authentication - Register
│   ├── dashboard.html      # Candidate Dashboard
│   ├── interview.html      # Core JARVIS AI Interview Interface
│   ├── feedback.html       # Performance Report
│   ├── history.html        # Session Archives
│   │
│   ├── css/
│   │   ├── style.css       # Global Cyberpunk/Glassmorphic Design System
│   │   └── jarvis.css      # JARVIS Kinetic Visualizer & HUD Styling
│   └── js/
│       ├── main.js         # Shared Utilities & Toast System
│       └── jarvis.js       # Audio Waves, Web Speech API & State Controller
│
├── database/
│   └── schema.sql          # MySQL 8.x Schema with Strict Session Isolation
│
├── uploads/                # Resume Upload Directory (.gitkeep preserved)
├── tests/
│   └── test_phase1.py      # Architecture & Interface Verification Suite
├── .env.example            # Environment Template
├── .gitignore              # Git Ignore Rules
└── README.md               # Project Master Documentation
```

---

## Running the Application

### 1. Install Requirements
```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
```

### 3. Run Test Suite
```bash
python -m unittest tests/test_phase1.py
```

### 4. Start the Application Server
```bash
python backend/app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser:
- Landing Page: `http://127.0.0.1:5000/`
- JARVIS Live Interview: `http://127.0.0.1:5000/interview`
- Dashboard: `http://127.0.0.1:5000/dashboard`
- Login: `http://127.0.0.1:5000/login`
- Register: `http://127.0.0.1:5000/register`
- Feedback: `http://127.0.0.1:5000/feedback`
- History: `http://127.0.0.1:5000/history`
- Health API: `http://127.0.0.1:5000/api/health`
