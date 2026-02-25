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
Currently in **Phase 3A Complete**: Backend authentication with Google OAuth 2.0, JWT sessions, and Supabase integration

## Project Structure

```
just-schedule-it/
├── backend/                      # Flask API server
│   ├── app.py                    # Main Flask application with auth endpoints
│   ├── auth.py                   # Google OAuth & JWT logic
│   ├── database.py               # Supabase client & database operations
│   ├── config.py                 # Configuration management
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   └── migrations/
│       └── 001_create_tables.sql # Database schema
│
├── frontend/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx               # Main React component
│   │   ├── App.css               # Styling
│   │   └── main.jsx              # React entry point
│   ├── index.html                # HTML template
│   ├── vite.config.js            # Vite configuration (includes proxy)
│   ├── package.json              # Node.js dependencies
│   └── .env.example              # Environment variables template
│
└── README.md
```

## Setup Instructions

### Prerequisites

Before starting, you'll need to set up:

1. **Groq API Key** - Get from [console.groq.com](https://console.groq.com/)
2. **Supabase Project** - Create at [supabase.com](https://supabase.com/)
3. **Google OAuth Credentials** - Set up at [console.cloud.google.com](https://console.cloud.google.com/)

---

### Backend Setup

#### 1. Install Python Dependencies

```bash
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

#### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `backend/.env` and fill in all values:

```bash
# Flask Configuration
FLASK_ENV=development
PORT=5000
CORS_ORIGINS=http://localhost:5173

# Groq API - https://console.groq.com/
GROQ_API_KEY=gsk_your_groq_api_key_here

# Supabase - Project Settings → API
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key_here

# Google OAuth - Google Cloud Console → Credentials
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/callback

# JWT Configuration
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your_generated_jwt_secret
JWT_EXPIRATION=3600

# Encryption for Refresh Tokens
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your_generated_fernet_key
```

#### 3. Set Up Supabase Database

1. Go to your Supabase project dashboard
2. Click **SQL Editor** in the sidebar
3. Create a new query
4. Copy and paste the entire contents of `backend/migrations/001_create_tables.sql`
5. Click **Run** (or press Cmd/Ctrl + Enter)
6. Verify: You should see "Tables created successfully!"

This creates:
- `users` table - Stores Google user profiles
- `refresh_tokens` table - Stores encrypted OAuth tokens

#### 4. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable these APIs:
   - Google Calendar API
   - Google+ API
4. Go to "OAuth consent screen":
   - Choose **External**
   - Fill in app name: "JustScheduleIt"
   - Add scopes:
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - Add your email as a test user
5. Go to "Credentials" → "Create Credentials" → "OAuth client ID":
   - Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:5173`
   - Authorized redirect URIs: `http://localhost:5000/api/auth/callback`
6. Copy the Client ID and Client Secret to your `.env` file

#### 5. Run the Backend

```bash
python app.py
```

Server starts on `http://localhost:5000`

---

### Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Server starts on `http://localhost:5173`

---

## Testing the Application

### 1. Test OAuth Login Flow

1. Make sure both backend and frontend are running
2. Visit: `http://localhost:5000/api/auth/login`
3. Sign in with your Google account
4. Grant calendar permissions
5. You'll be redirected to `http://localhost:5173/dashboard`
6. Check browser cookies (DevTools → Application → Cookies):
   - Should see `jwt_token` cookie set (httpOnly)

### 2. Verify Database

In Supabase → Table Editor:
- **users** table: Should have your Google profile
- **refresh_tokens** table: Should have encrypted token (looks like gibberish)

### 3. Test Protected Endpoint

After logging in, visit: `http://localhost:5000/api/auth/user`

Should return your user info:
```json
{
  "success": true,
  "user": {
    "id": "...",
    "email": "your@email.com",
    "name": "Your Name",
    "picture": "https://..."
  }
}
```

### 4. Test Natural Language Parsing

1. Visit `http://localhost:5173`
2. Type a calendar command:
   - "schedule a meeting with John tomorrow at 3pm"
   - "cancel my dentist appointment Friday"
   - "move my 2pm meeting to Thursday at 4pm"
   - "what do I have on Friday?"
3. Groq API parses and returns structured JSON:
   - Action type (create/delete/move/list)
   - Event title
   - Date and time information
   - Confidence score

---

## Current Features

### ✅ Working Features

**Authentication & Security:**
- Google OAuth 2.0 login
- JWT sessions with httpOnly cookies (XSS-safe)
- Refresh tokens encrypted with Fernet before storage
- Protected API endpoints
- User profile management

**Natural Language Processing:**
- Parse calendar commands with Groq API (Llama 3.1 8B Instant)
- Support for 4 actions: create, delete, move, list
- Intelligent date/time parsing (relative dates like "tomorrow", "Friday")
- Confidence scoring for parsed commands

**Database:**
- User profiles stored in Supabase
- Encrypted refresh token storage
- Automatic user creation on first login

**API Endpoints:**
- `GET /api/health` - Health check
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/user` - Get current user (protected)
- `POST /api/auth/logout` - Logout user (protected)
- `POST /api/message` - Parse natural language command (protected)

### 🚧 In Progress

**Phase 3B - Frontend UI:**
- Login page with "Login with Google" button
- Dashboard with embedded Google Calendar
- Chat interface for command history (session-only, not persisted)

**Phase 3C - Google Calendar API:**
- Execute parsed commands on actual Google Calendar
- Create, delete, move, and list calendar events

---

## Security Features

- ✅ **No secrets in code** - All credentials in `.env` files
- ✅ **httpOnly cookies** - JWTs protected from XSS attacks
- ✅ **Encrypted tokens** - Refresh tokens encrypted with Fernet
- ✅ **CORS configured** - Cross-origin requests restricted
- ✅ **Input validation** - All endpoints validate input
- ✅ **Parameterized queries** - Supabase SDK prevents SQL injection
- ✅ **Service role key** - Backend uses admin key, never exposed to frontend

---

## Development Phases

### Phase 1 ✅ Complete
- [x] Flask backend with simple echo endpoint
- [x] React frontend with text input
- [x] Backend ↔ Frontend communication working

### Phase 2 ✅ Complete
- [x] Integrate Groq API (Llama 3.1 8B Instant)
- [x] Parse natural language commands into structured JSON
- [x] Support 4 actions: create, delete, move, list
- [x] Return consistent JSON with date/time parsing

### Phase 3A ✅ Complete
- [x] Set up Supabase database (users, refresh_tokens tables)
- [x] Implement Google OAuth 2.0 flow
- [x] Add JWT session management with httpOnly cookies
- [x] Encrypt refresh tokens with Fernet
- [x] Protected API endpoints
- [x] User authentication and profile storage

### Phase 3B (Next)
- [ ] Add React Router for page navigation
- [ ] Create HomePage with "Login with Google" button
- [ ] Create Dashboard page structure
- [ ] Implement auth state management in React
- [ ] Configure axios for cookie-based auth

### Phase 3C
- [ ] Integrate Google Calendar API
- [ ] Implement calendar operations:
  - [ ] Create events
  - [ ] Delete events
  - [ ] Move/reschedule events
  - [ ] List events
- [ ] Display custom calendar view with `react-big-calendar`
- [ ] Fetch and render user's actual calendar events

### Phase 3D
- [ ] Build chat interface component
- [ ] Implement session-based chat history (React state only)
- [ ] Display command history in dashboard
- [ ] Polish UI/UX

### Phase 4
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Configure production environment variables
- [ ] Set up production CORS and cookies
- [ ] Update Google OAuth redirect URIs for production
- [ ] Test end-to-end in production

---

## Technology Stack

**Frontend:**
- React 18 with Vite
- Axios for HTTP requests
- React Router (Phase 3B)
- react-big-calendar (Phase 3C)

**Backend:**
- Flask 3.0 with Flask-CORS
- Groq API (Llama 3.1 8B Instant)
- Google OAuth 2.0
- PyJWT for session tokens
- Cryptography (Fernet) for token encryption

**Database:**
- Supabase (PostgreSQL)
- Row Level Security (RLS) enabled

**Deployment:**
- Frontend: Vercel
- Backend: Render

---

## Contributing

This is a personal project. Feel free to fork and adapt for your own use!

---

## License

See LICENSE file for details.
