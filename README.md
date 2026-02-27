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
Currently in **Phase 3B Complete**: Full authentication flow with modern SaaS landing page, protected dashboard, and session-based chat interface

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
│   │   ├── utils/
│   │   │   ├── api.js            # Axios instance with cookie support
│   │   │   └── auth.js           # Authentication helper functions
│   │   ├── pages/
│   │   │   ├── HomePage.jsx      # Landing page with login
│   │   │   ├── HomePage.css
│   │   │   ├── Dashboard.jsx     # Main app page (protected)
│   │   │   └── Dashboard.css
│   │   ├── components/
│   │   │   ├── MessageInput.jsx  # Command input component
│   │   │   ├── MessageInput.css
│   │   │   ├── ChatMessage.jsx   # Chat message display
│   │   │   └── ChatMessage.css
│   │   ├── App.jsx               # Routing and protected routes
│   │   ├── App.css               # Global styles
│   │   └── main.jsx              # React entry point with BrowserRouter
│   ├── index.html                # HTML template with Google Fonts
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
npm run dev
```

Server starts on `http://localhost:5173`

---

## Running the Application Locally

### Starting Both Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then visit `http://localhost:5173` in your browser.

---

## Testing the Application

### 1. Test the Landing Page

1. Visit `http://localhost:5173`
2. You should see:
   - Modern SaaS landing page with "JustScheduleIt" logo
   - Elegant serif headline: "Manage your calendar with natural language"
   - Tagline: "AI-powered calendar assistant"
   - "Get Started" button in the hero section
   - "Login with Google" ghost button in header
   - Three feature cards showcasing functionality
3. Click either login button to start OAuth flow

### 2. Test OAuth Login Flow

1. Click "Login with Google" or "Get Started"
2. Sign in with your Google account
3. Grant calendar permissions
4. You'll be redirected to `http://localhost:5173/dashboard`
5. Check browser cookies (DevTools → Application → Cookies):
   - Should see `jwt_token` cookie set (httpOnly)

### 3. Test Dashboard

After logging in, you should see:
- Header with "JustScheduleIt" logo
- Your profile picture (or initial fallback) and name
- Logout button
- Two-column layout:
  - **Left**: Calendar placeholder (Phase 3C will add real calendar)
  - **Right**: Chat interface with welcome message
- Example commands you can try

### 4. Test Chat Interface

1. Type a calendar command in the input box:
   - "schedule a meeting with John tomorrow at 3pm"
   - "cancel my dentist appointment Friday"
   - "move my 2pm meeting to Thursday at 4pm"
   - "what do I have on Friday?"
2. Click Send (or press Enter)
3. You should see:
   - Your message in a blue bubble (right-aligned)
   - Parsed response in a gray bubble (left-aligned) showing:
     - Action type
     - Title
     - Date/time information
     - Confidence score
   - Note: Commands are parsed but not executed yet (Phase 3C)
4. Chat history persists during the session but clears on refresh

### 5. Test Protected Routes

1. Open a new incognito/private browser window
2. Try to visit `http://localhost:5173/dashboard` directly
3. You should be redirected to `/` (homepage) since you're not logged in
4. This confirms protected routes are working correctly

### 6. Verify Database

In Supabase → Table Editor:
- **users** table: Should have your Google profile
- **refresh_tokens** table: Should have encrypted token (looks like gibberish)

### 7. Test Logout

1. Click the "Logout" button in the dashboard header
2. You should be redirected to the homepage
3. JWT cookie is cleared
4. Trying to access `/dashboard` should redirect to `/`

---

## Current Features

### ✅ Working Features

**Authentication & Security:**
- Google OAuth 2.0 login flow
- JWT sessions with httpOnly cookies (XSS-safe)
- Refresh tokens encrypted with Fernet before storage
- Protected API endpoints and routes
- User profile management
- Automatic user creation on first login
- Secure logout functionality

**Frontend UI (Phase 3B):**
- Modern SaaS-style landing page with:
  - Playfair Display serif font for elegant branding
  - Warm cream (#FAF8F5) background for depth
  - Ghost-style outlined login button
  - Solid pill-shaped "Get Started" CTA button
  - Three feature cards showcasing key functionality
  - Fully responsive design
- Protected dashboard with:
  - User profile display with fallback initials
  - Header with logout functionality
  - Two-column layout (calendar + chat)
  - Calendar placeholder (Phase 3C will add real calendar)
- Chat interface with:
  - Message input component
  - Chat message bubbles (user + response)
  - Session-based history (clears on refresh)
  - Parsed command display with confidence scores
- React Router for navigation
- Protected routes with authentication checks
- Cookie-based auth with automatic credential handling

**Natural Language Processing:**
- Parse calendar commands with Groq API (Llama 3.1 8B Instant)
- Support for 4 actions: create, delete, move, list
- Intelligent date/time parsing (relative dates like "tomorrow", "Friday")
- Confidence scoring for parsed commands
- Real-time command parsing and display

**Database:**
- User profiles stored in Supabase
- Encrypted refresh token storage
- Automatic user creation on first login
- Secure database operations with service role key

**API Endpoints:**
- `GET /api/health` - Health check
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/user` - Get current user (protected)
- `POST /api/auth/logout` - Logout user (protected)
- `POST /api/message` - Parse natural language command (protected)

### 🚧 Next Up (Phase 3C)

**Google Calendar Integration:**
- Connect to Google Calendar API
- Execute parsed commands on actual calendar:
  - Create events
  - Delete events
  - Move/reschedule events
  - List events
- Display real calendar in dashboard
- Sync calendar events with backend

---

## Security Features

- ✅ **No secrets in code** - All credentials in `.env` files
- ✅ **httpOnly cookies** - JWTs protected from XSS attacks
- ✅ **Encrypted tokens** - Refresh tokens encrypted with Fernet
- ✅ **CORS configured** - Cross-origin requests restricted
- ✅ **Input validation** - All endpoints validate input
- ✅ **Parameterized queries** - Supabase SDK prevents SQL injection
- ✅ **Service role key** - Backend uses admin key, never exposed to frontend
- ✅ **Protected routes** - Authentication required for dashboard access
- ✅ **Profile picture fallback** - Colored circle with user initials if image fails

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

### Phase 3B ✅ Complete
- [x] Add React Router for page navigation
- [x] Create modern SaaS landing page with:
  - [x] Elegant serif logo (Playfair Display)
  - [x] Hero section with CTA button
  - [x] Feature cards
  - [x] Ghost-style login button
- [x] Create Dashboard page with:
  - [x] User profile header with logout
  - [x] Two-column layout (calendar + chat)
  - [x] Profile picture fallback (colored circle with initial)
- [x] Implement protected routes
- [x] Configure axios for cookie-based auth
- [x] Build chat interface with:
  - [x] Message input component
  - [x] Chat message display
  - [x] Session-based history (React state)
- [x] Responsive design for mobile/tablet

### Phase 3C (Next)
- [ ] Integrate Google Calendar API
- [ ] Implement calendar operations:
  - [ ] Create events
  - [ ] Delete events
  - [ ] Move/reschedule events
  - [ ] List events
- [ ] Display real calendar in dashboard
- [ ] Execute parsed commands on actual Google Calendar

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
- React Router v6 for navigation
- Axios for HTTP requests with cookie support
- Google Fonts (Playfair Display)
- CSS3 with responsive design
- react-big-calendar (Phase 3C)

**Backend:**
- Flask 3.0 with Flask-CORS
- Groq API (Llama 3.1 8B Instant)
- Google OAuth 2.0
- PyJWT for session tokens
- Cryptography (Fernet) for token encryption
- Python-dotenv for environment variables

**Database:**
- Supabase (PostgreSQL)
- Row Level Security (RLS) enabled

**Deployment:**
- Frontend: Vercel
- Backend: Render

---

## Design Philosophy

**Security First:**
- All sensitive tokens stored server-side and encrypted
- httpOnly cookies prevent XSS attacks
- Protected routes ensure authenticated access only
- No secrets exposed to frontend

**User Experience:**
- Modern SaaS aesthetic with warm, inviting colors
- Clean, minimal design
- Responsive layout for all devices
- Session-based chat for ephemeral interactions
- Profile picture fallback for reliability

**Developer Experience:**
- Comprehensive code comments throughout
- Modular component architecture
- Clear separation of concerns
- Environment-based configuration

---

## Contributing

This is a personal project. Feel free to fork and adapt for your own use!

---

## License

See LICENSE file for details.
