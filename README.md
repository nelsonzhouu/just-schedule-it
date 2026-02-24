# just-schedule-it
Manage your Google Calendar using natural language commands.
Type what you want — "move my 3pm meeting to tomorrow" or 
"cancel all my Friday events" — and it handles the rest.

## Tech Stack
- Frontend: React + Vite, hosted on Vercel
- Backend: Flask (Python), hosted on Render
- AI: Groq API (Llama 3.1)
- Database: Supabase (PostgreSQL)
- Auth: Google OAuth 2.0 + JWTs

## Status
Currently in **Phase 1**: Local Flask + React communication

## Project Structure

```
just-schedule-it/
├── backend/              # Flask API server
│   ├── app.py           # Main Flask application
│   ├── config.py        # Configuration management
│   ├── requirements.txt # Python dependencies
│   └── .env.example     # Environment variables template
│
├── frontend/            # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   ├── App.css      # Styling
│   │   └── main.jsx     # React entry point
│   ├── index.html       # HTML template
│   ├── vite.config.js   # Vite configuration (includes proxy)
│   ├── package.json     # Node.js dependencies
│   └── .env.example     # Environment variables template
│
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create environment file:
   ```bash
   cp .env.example .env
   ```

6. Run the Flask server:
   ```bash
   python app.py
   ```

   The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory (in a new terminal):
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will run on `http://localhost:5173`

### Testing Phase 1

1. Make sure both backend and frontend servers are running
2. Open your browser to `http://localhost:5173`
3. Type a message in the text box and click "Send"
4. You should see the Flask backend echo your message back

## Development Phases

### Phase 1 (Current)
- [x] Flask backend with simple echo endpoint
- [x] React frontend with text input
- [x] Backend ↔ Frontend communication working

### Phase 2 
- [ ] Integrate Groq API (Llama 3.1)
- [ ] Parse natural language commands
- [ ] Return AI-generated responses

### Phase 3
- [ ] Set up Supabase database
- [ ] Implement Google OAuth 2.0
- [ ] Add JWT session management

### Phase 4
- [ ] Integrate Google Calendar API
- [ ] Implement calendar operations (create, update, delete events)
- [ ] Full end-to-end functionality

### Phase 5
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Production configuration and testing
