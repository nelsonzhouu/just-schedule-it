# just-schedule-it

Manage your Google Calendar using natural language commands.
Type what you want — "schedule a meeting tomorrow at 3pm" or "cancel my dentist appointment" — and it handles the rest.

## Tech Stack
- **Frontend:** React + Vite, hosted on Vercel
- **Backend:** Flask (Python), hosted on Render
- **AI:** Groq API (Llama 3.1 8B Instant)
- **Database:** Supabase (PostgreSQL)
- **Auth:** Google OAuth 2.0 + JWTs
- **Calendar:** Google Calendar API with react-big-calendar

## Status
Currently in **Phase 3C Complete**: Full Google Calendar integration with natural language command execution, real-time calendar view, and conversational AI responses.

## What It Does

**JustScheduleIt** is an AI-powered calendar assistant that lets you manage your Google Calendar using natural language. Instead of clicking through forms, just type what you want:

- **Create events:** "schedule a 30 minute standup at 9am tomorrow"
- **Delete events:** "cancel my meeting on Friday at 3pm"
- **Reschedule events:** "move my dentist appointment to next Tuesday at 2pm"
- **List events:** "what do I have on Monday?"

The app uses Groq's Llama 3.1 model to parse your commands, then executes them on your real Google Calendar. View your calendar in a beautiful week view and see changes happen in real-time.

---

## Current Features

### ✅ Fully Working

**Natural Language Calendar Management:**
- Parse complex calendar commands using Groq AI (Llama 3.1 8B Instant)
- Support for 4 actions: **create**, **delete**, **move**, **list**
- Intelligent date/time parsing (relative dates like "tomorrow", "next Friday")
- Duration parsing ("30 minute meeting", "2 hour call", "from 1pm to 3pm")
- Fuzzy title matching ("meeting" finds "Team Meeting")
- Time-specific matching ("delete meeting at 3pm" won't delete the 2pm meeting)
- Multiple match confirmation flow with numbered selection
- Conversational responses ("✓ Done! 'Meeting' scheduled for March 1st, 2026 at 3:00 PM")

**Google Calendar Integration:**
- Full Google Calendar API integration
- Create events with custom titles, dates, times, and durations
- Delete events with confirmation when multiple matches found
- Move/reschedule events to new dates and times
- List events for specific dates or date ranges
- Timezone-aware operations (uses user's Google Calendar timezone)
- Real-time calendar updates after each action
- Automatic title capitalization

**Calendar View:**
- Interactive calendar using react-big-calendar
- Week view by default (configurable to month/day/agenda)
- Click events to see details in a popup (title, date, time range)
- Custom toolbar with Today/Back/Next navigation
- Scrolls to 8:00 AM by default for workday view
- Responsive design for mobile and desktop
- Events display with proper timezone handling

**Authentication & Security:**
- Google OAuth 2.0 login flow with Calendar API scope
- JWT sessions with httpOnly cookies (XSS-safe)
- Refresh tokens encrypted with Fernet before storage
- Protected API endpoints and routes
- User profile management
- Automatic user creation on first login
- Secure logout functionality

**Frontend UI:**
- Modern SaaS-style landing page with elegant branding
- Protected dashboard with two-column layout (calendar + chat)
- User profile display with fallback initials
- Chat interface with conversational AI responses
- Session-based chat history (clears on refresh)
- Pending action storage for multi-step confirmations
- Fully responsive design for all devices

**Database:**
- User profiles stored in Supabase
- Encrypted refresh token storage
- Automatic user creation on first login
- Timezone caching to reduce API calls

**API Endpoints:**
- `GET /api/health` - Health check
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/user` - Get current user (protected)
- `POST /api/auth/logout` - Logout user (protected)
- `POST /api/message` - Parse and execute calendar commands (protected)
- `GET /api/calendar/events` - Fetch calendar events for date range (protected)

---

## Project Structure

```
just-schedule-it/
├── backend/                      # Flask API server
│   ├── app.py                    # Main Flask application with all endpoints
│   ├── calendar_api.py           # Google Calendar API integration
│   ├── auth.py                   # Google OAuth & JWT logic
│   ├── database.py               # Supabase client & database operations
│   ├── config.py                 # Configuration management (.env loader)
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   └── migrations/
│       └── 001_create_tables.sql # Database schema (users, refresh_tokens)
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
│   │   │   ├── ChatMessage.jsx   # Chat message display (conversational)
│   │   │   ├── ChatMessage.css
│   │   │   ├── Calendar.jsx      # Google Calendar view (react-big-calendar)
│   │   │   ├── Calendar.css
│   │   │   ├── CustomToolbar.jsx # Custom calendar navigation toolbar
│   │   │   └── CustomToolbar.css
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

---

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
   - **Google Calendar API**
   - **Google+ API** (or People API)
4. Go to "OAuth consent screen":
   - Choose **External** (or Internal if using Google Workspace)
   - Fill in app name: "JustScheduleIt"
   - Add scopes:
     - `https://www.googleapis.com/auth/calendar` (View and edit your calendar)
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - Add your email as a test user (required for External apps in development)
5. Go to "Credentials" → "Create Credentials" → "OAuth client ID":
   - Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:5173`
   - Authorized redirect URIs: `http://localhost:5000/api/auth/callback`
6. Copy the Client ID and Client Secret to your `.env` file

#### 5. Run the Backend

```bash
# Make sure virtual environment is activated
python app.py
```

Server starts on `http://localhost:5000`

---

### Frontend Setup

#### 1. Install Dependencies

In a new terminal:

```bash
cd frontend
npm install
```

#### 2. Configure Environment Variables (Optional)

The frontend uses Vite's proxy for API requests, so no environment variables are required for local development. The proxy is already configured in `vite.config.js`.

For production deployment, create `frontend/.env`:

```bash
VITE_API_URL=https://your-backend-url.onrender.com
```

#### 3. Run the Frontend

```bash
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

You should see:
```
 * Running on http://127.0.0.1:5000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

Then visit `http://localhost:5173` in your browser.

---

## Testing the Application

### 1. Test the Landing Page

1. Visit `http://localhost:5173`
2. You should see:
   - Modern SaaS landing page with "JustScheduleIt" logo
   - Elegant serif headline: "Manage your calendar with natural language"
   - "Get Started" button in the hero section
   - "Login with Google" button in header
   - Three feature cards showcasing functionality
3. Click either login button to start OAuth flow

### 2. Test OAuth Login Flow

1. Click "Login with Google" or "Get Started"
2. Sign in with your Google account
3. Grant calendar permissions when prompted
4. You'll be redirected to `http://localhost:5173/dashboard`
5. Check browser cookies (DevTools → Application → Cookies):
   - Should see `jwt_token` cookie set (httpOnly, secure in production)

### 3. Test Dashboard

After logging in, you should see:
- Header with "JustScheduleIt" logo
- Your profile picture (or initial fallback) and name
- Logout button
- Two-column layout:
  - **Left**: Interactive Google Calendar (week view)
  - **Right**: Chat interface with conversational AI

### 4. Test Calendar View

In the calendar section:
1. Calendar should load showing your current week
2. Any existing Google Calendar events should appear
3. Click **Today** to jump to current date
4. Click **◄** / **►** to navigate weeks
5. Click view buttons to switch between Week/Month/Day/Agenda views
6. Click any event to see a popup with:
   - Event title
   - Formatted date (e.g., "March 4th, 2026")
   - Time range (e.g., "3:00 PM - 4:00 PM")
   - Close button (or click outside/press Escape to close)

### 5. Test Natural Language Commands

Try these commands in the chat interface:

**Create Events:**
```
schedule a meeting with John tomorrow at 3pm
book a 30 minute standup at 9am on Friday
schedule a 2 hour workshop from 1pm to 3pm next Monday
```

**Delete Events:**
```
cancel my meeting tomorrow
delete dentist appointment on Friday at 3pm
```

**Move/Reschedule Events:**
```
move my 3pm meeting to tomorrow at 2pm
reschedule my dentist appointment to next Tuesday at 10am
```

**List Events:**
```
what do I have tomorrow?
show my events on Friday
what's on my calendar next week?
```

**Expected Behavior:**
- Your message appears in a dark bubble (right-aligned)
- AI response appears in a light bubble (left-aligned)
- Responses are conversational: "✓ Done! 'Meeting' scheduled for March 5th, 2026 at 3:00 PM"
- Calendar updates in real-time after each command
- Events appear with proper timezone handling

### 6. Test Multiple Match Confirmation

1. Create two events with similar names:
   - "schedule a team meeting tomorrow at 2pm"
   - "schedule a team meeting tomorrow at 4pm"
2. Try to delete without being specific:
   - "delete team meeting tomorrow"
3. You should see a numbered list:
   ```
   I found multiple matches - which one did you mean?

   1. Team Meeting (2:00 PM - 3:00 PM)
   2. Team Meeting (4:00 PM - 5:00 PM)

   Type 1, 2, 3... to select, or type a new command to cancel.
   ```
4. Type "1" to select the first event
5. Event should be deleted and calendar updates

### 7. Test Fuzzy Matching

The app uses fuzzy/partial word matching for finding events:
- "standup" finds "Daily Standup"
- "meeting" finds "Team Meeting"
- "dentist" finds "Dentist Appointment"

### 8. Test Protected Routes

1. Open a new incognito/private browser window
2. Try to visit `http://localhost:5173/dashboard` directly
3. You should be redirected to `/` (homepage) since you're not logged in
4. This confirms protected routes are working correctly

### 9. Verify Database

In Supabase → Table Editor:
- **users** table: Should have your Google profile (name, email, picture)
- **refresh_tokens** table: Should have encrypted token (looks like gibberish - that's good!)

### 10. Test Logout

1. Click the "Logout" button in the dashboard header
2. You should be redirected to the homepage
3. JWT cookie is cleared
4. Trying to access `/dashboard` should redirect to `/`

---

## Automated Testing

### Running Backend Tests

The backend includes comprehensive automated tests using pytest to ensure critical functions work correctly.

#### Install Test Dependencies

Test dependencies are included in `requirements.txt`. If you've already installed dependencies, you have them. Otherwise:

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

This installs:
- `pytest` - Test framework
- `pytest-mock` - Mocking support
- `pytest-cov` - Coverage reporting
- `freezegun` - Time freezing for deterministic date tests

#### Run All Tests

```bash
cd backend
pytest
```

You should see output like:
```
======================== test session starts ========================
collected 53 items

tests/test_auth.py .............                              [ 24%]
tests/test_calendar_api.py ........................................  [100%]

======================== 53 passed in 1.23s =========================
```

#### Run Tests with Verbose Output

```bash
pytest -v
```

Shows each individual test name as it runs.

#### Run Tests with Coverage Report

```bash
pytest --cov=. --cov-report=term --cov-report=html
```

This generates:
- **Terminal report** - Shows coverage percentage for each file
- **HTML report** - Creates `htmlcov/` directory with detailed coverage report
  - Open `htmlcov/index.html` in your browser to see line-by-line coverage

Example coverage output:
```
----------- coverage: platform darwin, python 3.x.x -----------
Name                    Stmts   Miss  Cover
-------------------------------------------
auth.py                   142     45    68%
calendar_api.py           287    156    46%
config.py                  23      0   100%
-------------------------------------------
TOTAL                     452    201    56%
```

#### Run Specific Tests

```bash
# Run tests from a specific file
pytest tests/test_auth.py

# Run tests from a specific class
pytest tests/test_calendar_api.py::TestParseDatetime

# Run a specific test
pytest tests/test_calendar_api.py::TestParseDatetime::test_parse_tomorrow -v
```

#### Run Tests and Stop on First Failure

```bash
pytest -x
```

Useful for debugging - stops immediately when a test fails.

### What's Being Tested

**`tests/test_calendar_api.py` (40 tests):**

1. **`parse_date_time()`** - Date and time parsing
   - Relative dates: "today", "tomorrow", "friday", "monday"
   - Absolute dates: "2026-03-15"
   - Times: "3pm", "9am", "14:30", "12pm", "12am"
   - Default behavior: missing time defaults to 12pm

2. **`format_date_conversational()`** - Friendly date formatting
   - Ordinal suffixes: 1st, 2nd, 3rd, 4th, 11th, 21st, 31st
   - Month names and year formatting
   - Edge cases: 11th-13th (should be "th" not "st/nd/rd")

3. **`format_time_conversational()`** - Friendly time formatting
   - AM/PM conversion: "9:00 AM", "3:00 PM"
   - Edge cases: midnight (12:00 AM), noon (12:00 PM)

4. **`format_time_range()`** - Time range formatting
   - Normal ranges: "9:00 AM - 10:00 AM"
   - All-day events: returns "All day"

5. **Fuzzy Matching Logic** - Search flexibility
   - "standup" finds "Daily Standup"
   - "meeting" finds "Team Meeting"
   - "dentist" finds "Dentist Appointment"
   - Case-insensitive matching
   - No match returns empty list

**`tests/test_auth.py` (13 tests):**

1. **`create_jwt()`** - JWT token creation
   - Creates valid JWT tokens
   - Payload contains user_id and expiration
   - Expiration set to correct duration
   - Different users get different tokens

2. **`verify_jwt()`** - JWT token verification
   - Valid tokens return user_id
   - Returns None for:
     - Expired tokens
     - Invalid signatures
     - Malformed tokens
     - Empty/None tokens
     - Tokens missing user_id

### Test Features

✅ **Mocked External Services** - No real API calls (Google Calendar, Groq)
✅ **Frozen Time** - Deterministic date tests using freezegun at "2026-02-28 10:00:00"
✅ **Shared Fixtures** - Reusable test data in `conftest.py`
✅ **Fast Execution** - All 53 tests run in ~1-2 seconds
✅ **Comprehensive Coverage** - Tests critical helper functions and edge cases

### Writing New Tests

Tests are located in `backend/tests/`. To add new tests:

1. Add test functions to existing test files, or create a new file: `test_*.py`
2. Use `@freeze_time("2026-02-28 10:00:00")` decorator for date-dependent tests
3. Mock external services using `unittest.mock` or `pytest-mock`
4. Follow naming convention: `test_*` for functions, `Test*` for classes
5. Run `pytest` to verify new tests pass

---

## Technology Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router v6** - Client-side routing and protected routes
- **Axios** - HTTP client with cookie support
- **react-big-calendar** - Interactive calendar component
- **date-fns** - Lightweight date formatting library
- **Google Fonts** - Playfair Display for elegant branding
- **CSS3** - Custom styling with responsive design

### Backend
- **Flask 3.0** - Python web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Flask-Limiter** - Rate limiting middleware for API protection
- **Groq API** - Llama 3.1 8B Instant for natural language parsing
- **Google OAuth 2.0** - Authentication with Calendar API scope
- **Google Calendar API** - Calendar operations (create/delete/move/list)
- **PyJWT** - JWT session token generation
- **Cryptography (Fernet)** - Symmetric encryption for refresh tokens
- **python-dotenv** - Environment variable management
- **python-dateutil** - Advanced date parsing
- **pytz** - Timezone handling

### Testing
- **pytest** - Test framework
- **pytest-mock** - Mocking support for tests
- **pytest-cov** - Code coverage reporting
- **freezegun** - Time freezing for deterministic date tests

### Database
- **Supabase** - PostgreSQL database as a service
- Row Level Security (RLS) enabled
- Service role key for server-side operations

### AI & APIs
- **Groq** - Fast LLM inference (Llama 3.1 8B Instant)
- **Google Calendar API** - Calendar data access and manipulation
- **Google OAuth 2.0** - User authentication and authorization

### Deployment (Phase 4)
- **Frontend:** Vercel (planned)
- **Backend:** Render (planned)

---

## Security Features

- ✅ **No secrets in code** - All credentials in `.env` files (never committed)
- ✅ **httpOnly cookies** - JWTs protected from XSS attacks
- ✅ **Encrypted tokens** - Refresh tokens encrypted with Fernet before database storage
- ✅ **CORS configured** - Cross-origin requests restricted to allowed origins
- ✅ **Input validation** - All endpoints validate and sanitize input:
  - Message commands limited to 500 characters
  - ISO datetime format validation for calendar queries
- ✅ **Rate limiting** - Flask-Limiter protects against abuse:
  - `/api/auth/login`: 10 requests/minute per IP
  - `/api/message`: 30 requests/minute per user
  - `/api/calendar/events`: 60 requests/minute per user
- ✅ **Parameterized queries** - Supabase SDK prevents SQL injection
- ✅ **Service role key** - Backend uses admin key, never exposed to frontend
- ✅ **Protected routes** - Authentication required for dashboard and API access
- ✅ **Timezone-aware operations** - All calendar operations use user's local timezone
- ✅ **Session management** - Flask sessions for multi-step confirmations
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
- [x] Create modern SaaS landing page
- [x] Create Dashboard page with user profile
- [x] Implement protected routes
- [x] Configure axios for cookie-based auth
- [x] Build chat interface with message history
- [x] Responsive design for mobile/tablet

### Phase 3C ✅ Complete
- [x] Integrate Google Calendar API
- [x] Implement calendar operations:
  - [x] Create events with custom duration support
  - [x] Delete events with fuzzy matching and confirmation
  - [x] Move/reschedule events with duration preservation
  - [x] List events with timezone awareness
- [x] Display real calendar in dashboard (react-big-calendar)
- [x] Execute parsed commands on actual Google Calendar
- [x] Add conversational AI responses
- [x] Implement timezone-aware date range searches
- [x] Add multiple match confirmation flow with session storage
- [x] Create custom calendar toolbar
- [x] Add event detail popup on click
- [x] Implement fuzzy title matching
- [x] Add time-specific event filtering
- [x] Add automated backend testing with pytest (53 tests)
- [x] Add security improvements:
  - [x] Rate limiting (Flask-Limiter)
  - [x] Input validation (message length, ISO datetime format)

### Phase 4 (Next)
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Configure production environment variables
- [ ] Set up production CORS and cookies
- [ ] Update Google OAuth redirect URIs for production
- [ ] Test end-to-end in production
- [ ] Configure custom domain (optional)

---

## Design Philosophy

**Security First:**
- All sensitive tokens stored server-side and encrypted
- httpOnly cookies prevent XSS attacks
- Protected routes ensure authenticated access only
- No secrets exposed to frontend
- Timezone-aware operations prevent data leaks

**User Experience:**
- Natural language interface - type like you talk
- Conversational AI responses - friendly, not robotic
- Real-time calendar updates
- Fuzzy matching - "meeting" finds "Team Meeting"
- Multiple match confirmation - never delete the wrong event
- Modern SaaS aesthetic with warm, inviting colors
- Responsive layout for all devices

**Developer Experience:**
- Comprehensive code comments throughout
- Modular component architecture
- Clear separation of concerns (calendar_api.py, auth.py, database.py)
- Environment-based configuration
- Consistent error handling
- Type hints in Python functions

---

## Troubleshooting

### Calendar not showing events
1. Check that you granted Calendar permissions during OAuth
2. Verify Google Calendar API is enabled in Google Cloud Console
3. Check browser console for errors
4. Verify JWT token exists in cookies (DevTools → Application → Cookies)

### "Failed to parse AI response" error
1. Check that GROQ_API_KEY is set correctly in backend/.env
2. Verify Groq API key is valid at [console.groq.com](https://console.groq.com/)
3. Check backend terminal for detailed error messages

### OAuth redirect not working
1. Verify GOOGLE_REDIRECT_URI matches exactly in:
   - backend/.env file
   - Google Cloud Console → Credentials → Authorized redirect URIs
2. Make sure it's `http://localhost:5000/api/auth/callback` for local development

### "No events found" when you know events exist
1. Check timezone - events might be on a different day in your timezone
2. Verify you're searching the correct date
3. Check Google Calendar web interface to confirm events exist

### Multiple match confirmation not working
1. Make sure Flask secret key is set (uses JWT_SECRET)
2. Check browser allows cookies
3. Verify session is not being cleared between requests

---

## Contributing

This is a personal project. Feel free to fork and adapt for your own use!

---

## License

See LICENSE file for details.
