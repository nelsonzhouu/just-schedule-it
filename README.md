# JustScheduleIt

Manage your Google Calendar using natural language commands.

## Live Demo

**[https://just-schedule-it.vercel.app](https://just-schedule-it.vercel.app)**

## About

JustScheduleIt is an AI-powered calendar assistant that lets you manage your Google Calendar naturally. Instead of clicking through forms, just type what you want: "schedule a meeting tomorrow at 3pm" or "move my dentist appointment to next Tuesday at 2pm". The app uses AI to parse your commands and executes them on your real Google Calendar in real-time.

## Features

- **Natural language processing** - Type commands like you speak
- **Create events** - Schedule meetings with custom durations, notes, and reminders
- **Delete events** - Cancel events via command or click the trash icon in the popup
- **Move events** - Reschedule to new dates and times
- **Add notes** - Attach descriptions to events with flexible syntax
- **Set reminders** - Custom notification times or disable reminders entirely
- **List events** - Query single days, weeks, or entire months
- **Interactive calendar** - Week/month/day views with click-to-view event details
- **Timezone-aware** - All operations use your Google Calendar timezone
- **Real-time updates** - Calendar refreshes automatically after each action
- **Secure authentication** - Google OAuth with httpOnly JWT cookies

## Tech Stack

**Frontend:** React, Vite, JavaScript
**Backend:** Flask (Python), Groq API (Llama 3.1), Google Calendar API
**Database:** Supabase (PostgreSQL)
**Auth:** Google OAuth 2.0
**Deployment:** Vercel (frontend), Render (backend)

## Project Structure

```
just-schedule-it/
├── backend/
│   ├── app.py                    # Main Flask app with endpoints
│   ├── calendar_api.py           # Google Calendar integration
│   ├── auth.py                   # OAuth & JWT logic
│   ├── database.py               # Supabase client
│   ├── config.py                 # Environment config
│   ├── requirements.txt
│   ├── Procfile                  # Render deployment
│   ├── .env.example
│   ├── migrations/
│   │   └── 001_create_tables.sql
│   └── tests/
│       ├── conftest.py
│       ├── test_app.py
│       ├── test_auth.py
│       └── test_calendar_api.py
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── components/
│   │   │   ├── Calendar.jsx
│   │   │   ├── MessageInput.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   └── CustomToolbar.jsx
│   │   ├── utils/
│   │   │   ├── api.js
│   │   │   └── auth.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── vite.config.js
│   ├── vercel.json              # Vercel deployment config
│   ├── package.json
│   └── .env.example
│
└── README.md
```

## Local Setup

### Prerequisites

1. **Groq API Key** - Get from [console.groq.com](https://console.groq.com/)
2. **Supabase Project** - Create at [supabase.com](https://supabase.com/)
3. **Google OAuth Credentials** - Set up at [console.cloud.google.com](https://console.cloud.google.com/)
   - Enable Google Calendar API and People API
   - Create OAuth 2.0 credentials with redirect URI: `http://localhost:5000/api/auth/callback`
   - Add scopes: calendar, userinfo.email, userinfo.profile

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in all values (see .env.example for details)

# Set up database
# Go to Supabase → SQL Editor → Run migrations/001_create_tables.sql

# Start backend
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` and log in with Google.

## Running Tests

```bash
cd backend
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest --cov=. --cov-report=html # Coverage report
```

Tests cover date parsing, JWT authentication, fuzzy matching, event notes, reminders, and conversational responses.

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to your branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Feature Ideas

Looking for something to work on? Here are some ideas:

- **Recurring events** - "schedule a standup every Monday at 9am"
- **Event guests** - "invite john@email.com to my meeting tomorrow"
- **Event locations** - "add location: Starbucks on Main St"
- **Google Meet integration** - "create a meeting with a video call link"
- **Improved AI prompting** - Better edge case handling, more examples, error recovery
- **Expand test coverage** - Add frontend tests, integration tests, E2E tests
- **Multi-language support** - Spanish, French, German, etc.
- **Natural language search** - "find all my dentist appointments"
- **Edit events from popup** - Change title, time, notes directly in UI
- **Dark mode** - Theme toggle for night owls
- **Voice input** - Speak your commands instead of typing
- **Mobile app** - React Native version

## Privacy

JustScheduleIt accesses your Google Calendar data only to perform actions you explicitly request through natural language commands. No calendar event data is stored in our database or logged to external services. Only encrypted refresh tokens are stored to maintain your authenticated session. You can revoke access anytime at [Google Account Permissions](https://myaccount.google.com/permissions).

## License

MIT License - See LICENSE file for details.
